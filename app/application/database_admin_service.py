import logging
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.application.schemas import DatabaseMaintenanceRead
from app.application.settings_service import DEFAULT_SETTINGS, get_setting_value
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.db import init_db, reset_engine
from app.infrastructure.models import (
    Appointment,
    AppointmentHistory,
    AppointmentWhatsAppLog,
    CashLedgerEntry,
    Contract,
    FinanceEntry,
    NfeInvoice,
    Receipt,
    ReceiptHistory,
    WorkOrder,
    WorkOrderPest,
    WorkOrderPhoto,
    WorkOrderProduct,
)

LOGGER = logging.getLogger(__name__)
SQLITE_ALLOWED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}


def export_database_backup() -> Path:
    source_path = _resolve_sqlite_database_path()
    if not source_path.exists():
        raise BusinessRuleViolation("Arquivo do banco de dados nao encontrado para backup.")

    backup_path = Path(tempfile.gettempdir()) / f"backup_{_timestamp()}.db"
    try:
        _backup_sqlite_database(source_path, backup_path, source_read_only=True)
        _validate_sqlite_file(backup_path)
    except Exception:
        _safe_unlink(backup_path)
        raise

    LOGGER.info("database_backup_created file=%s size=%s", backup_path.name, backup_path.stat().st_size)
    return backup_path


def restore_database_backup(
    db: Session,
    *,
    backup_bytes: bytes,
    original_filename: str,
    confirmation: str,
) -> DatabaseMaintenanceRead:
    if confirmation.strip().upper() != "RESTAURAR":
        raise BusinessRuleViolation("Digite RESTAURAR para confirmar a restauracao do banco.")
    if not backup_bytes:
        raise BusinessRuleViolation("Nenhum arquivo de backup foi enviado para restauracao.")

    source_path = _resolve_sqlite_database_path()
    _ensure_sqlite_filename(original_filename)
    upload_path = Path(tempfile.gettempdir()) / f"restore_{uuid4().hex}{Path(original_filename).suffix or '.db'}"
    backup_dir = _build_backup_dir(db)
    upload_path.write_bytes(backup_bytes)

    safety_backup_path: Optional[Path] = None
    try:
        _validate_sqlite_file(upload_path)
        safety_backup_path = backup_dir / f"pre_restore_{_timestamp()}.db"
        _backup_sqlite_database(source_path, safety_backup_path, source_read_only=True)
        _validate_sqlite_file(safety_backup_path)

        db.close()
        reset_engine()

        _backup_sqlite_database(upload_path, source_path)
        _validate_sqlite_file(source_path)

        reset_engine()
        init_db()
    except Exception as exc:
        reset_engine()
        LOGGER.exception("database_restore_failed file=%s error=%s", original_filename, exc)
        raise
    finally:
        _safe_unlink(upload_path)

    LOGGER.info(
        "database_restore_completed file=%s safety_backup=%s",
        original_filename,
        safety_backup_path.name if safety_backup_path else None,
    )
    return DatabaseMaintenanceRead(
        message="Restauracao concluida com sucesso.",
        file_name=Path(original_filename).name,
        backup_dir=str(backup_dir),
        safety_backup_file=safety_backup_path.name if safety_backup_path else None,
    )


def cleanup_operational_data(
    db: Session,
    *,
    confirmation: str,
    include_finance: bool,
) -> DatabaseMaintenanceRead:
    if confirmation.strip().upper() != "CONFIRMAR":
        raise BusinessRuleViolation("Digite CONFIRMAR para autorizar a limpeza das movimentacoes.")

    counts: dict[str, int] = {}
    try:
        counts["appointment_whatsapp_logs_removed"] = db.query(AppointmentWhatsAppLog).delete(synchronize_session=False)
        counts["appointment_history_removed"] = db.query(AppointmentHistory).delete(synchronize_session=False)
        counts["appointments_removed"] = db.query(Appointment).delete(synchronize_session=False)

        counts["contract_notifications_reset"] = db.query(Contract).update(
            {
                Contract.last_notification_status: None,
                Contract.last_notification_sent_at: None,
                Contract.last_notification_error: None,
            },
            synchronize_session=False,
        )

        if include_finance:
            counts["cash_ledger_removed"] = db.query(CashLedgerEntry).delete(synchronize_session=False)
            counts["finance_removed"] = db.query(FinanceEntry).delete(synchronize_session=False)
            counts["receipt_history_removed"] = db.query(ReceiptHistory).delete(synchronize_session=False)
            counts["receipts_removed"] = db.query(Receipt).delete(synchronize_session=False)
            counts["nfe_removed"] = db.query(NfeInvoice).delete(synchronize_session=False)
        else:
            counts["finance_links_detached"] = (
                db.query(FinanceEntry)
                .filter(FinanceEntry.os_id.is_not(None))
                .update({FinanceEntry.os_id: None}, synchronize_session=False)
            )
            counts["receipt_links_detached"] = (
                db.query(Receipt)
                .filter(Receipt.os_id.is_not(None))
                .update({Receipt.os_id: None}, synchronize_session=False)
            )

        counts["work_order_photos_removed"] = db.query(WorkOrderPhoto).delete(synchronize_session=False)
        counts["work_order_products_removed"] = db.query(WorkOrderProduct).delete(synchronize_session=False)
        counts["work_order_pests_removed"] = db.query(WorkOrderPest).delete(synchronize_session=False)
        counts["work_orders_removed"] = db.query(WorkOrder).delete(synchronize_session=False)

        db.commit()
    except Exception as exc:
        db.rollback()
        LOGGER.exception("database_cleanup_failed include_finance=%s error=%s", include_finance, exc)
        raise

    LOGGER.warning("database_cleanup_completed include_finance=%s details=%s", include_finance, counts)
    return DatabaseMaintenanceRead(
        message="Limpeza de movimentacoes concluida com sucesso.",
        details=counts,
    )


def _resolve_sqlite_database_path() -> Path:
    settings = get_settings()
    url = make_url(settings.database_url)
    if url.drivername != "sqlite":
        raise BusinessRuleViolation("O gerenciamento automatico de banco esta disponivel apenas para SQLite nesta versao.")
    if not url.database or url.database == ":memory:":
        raise BusinessRuleViolation("Banco SQLite em memoria nao suporta backup e restauracao persistentes.")
    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    return db_path.resolve()


def _backup_sqlite_database(source_path: Path, target_path: Path, source_read_only: bool = False) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    source_dsn = f"file:{source_path.as_posix()}?mode=ro" if source_read_only else str(source_path)
    with sqlite3.connect(source_dsn, uri=source_read_only) as source_conn:
        with sqlite3.connect(str(target_path)) as target_conn:
            source_conn.backup(target_conn)


def _validate_sqlite_file(candidate_path: Path) -> None:
    _ensure_sqlite_filename(candidate_path.name)
    if not candidate_path.exists() or candidate_path.stat().st_size == 0:
        raise BusinessRuleViolation("Arquivo de banco invalido ou vazio.")
    try:
        with sqlite3.connect(f"file:{candidate_path.as_posix()}?mode=ro", uri=True) as connection:
            connection.execute("PRAGMA schema_version").fetchone()
            connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    except sqlite3.DatabaseError as exc:
        raise BusinessRuleViolation("O arquivo informado nao e um backup SQLite valido.") from exc


def _ensure_sqlite_filename(file_name: str) -> None:
    suffix = Path(file_name or "").suffix.lower()
    if suffix not in SQLITE_ALLOWED_EXTENSIONS:
        raise BusinessRuleViolation("Use um arquivo de backup SQLite com extensao .db, .sqlite ou .sqlite3.")


def _build_backup_dir(db: Session) -> Path:
    configured = str(get_setting_value(db, "database_backup_dir", DEFAULT_SETTINGS["database_backup_dir"])).strip()
    if not configured:
        raise BusinessRuleViolation("O diretorio de backup do banco nao esta configurado.")
    path = Path(configured)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_unlink(path: Optional[Path]) -> None:
    try:
        if path and path.exists():
            path.unlink()
    except PermissionError:
        pass


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
