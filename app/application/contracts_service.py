import logging
import mimetypes
import smtplib
from datetime import date, datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session, joinedload

from app.application.schemas import ContractCreate, ContractDashboardRead, ContractMaintenanceRead, ContractRead, ContractUpdate
from app.application.settings_service import get_boolean_setting, get_setting_value
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import ContractStatus
from app.infrastructure.models import Contract, Customer, User

from app.application.services import _apply_company_scope, _get_customer_or_fail

LOGGER = logging.getLogger(__name__)

ALLOWED_CONTRACT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
}
ALLOWED_CONTRACT_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "text/plain",
}
MAX_CONTRACT_FILE_BYTES = 10 * 1024 * 1024


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _contract_query(db: Session, current_user: Optional[User] = None):
    return _apply_company_scope(
        db.query(Contract).options(joinedload(Contract.cliente)),
        Contract,
        current_user,
    )


def _get_contract_or_fail(db: Session, contract_id: int, current_user: Optional[User] = None) -> Contract:
    contract = _contract_query(db, current_user=current_user).filter(Contract.id == contract_id).first()
    if not contract:
        raise BusinessRuleViolation("Contrato informado nao existe.")
    return contract


def _get_contract_alert_days(db: Session) -> int:
    return int(get_setting_value(db, "contract_alert_days", 15))


def _get_contract_storage_root(db: Session) -> Path:
    raw_path = str(get_setting_value(db, "contract_storage_dir", "uploads/contratos")).strip() or "uploads/contratos"
    resolved = get_settings().resolve_project_path(raw_path, default="uploads/contratos")
    assert resolved is not None
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _compute_contract_status(expiration_date: date, alert_days: int, today: Optional[date] = None) -> str:
    current_date = today or date.today()
    if current_date > expiration_date:
        return ContractStatus.VENCIDO.value
    if (expiration_date - current_date).days <= alert_days:
        return ContractStatus.A_VENCER.value
    return ContractStatus.ATIVO.value


def _sync_contract_status(contract: Contract, alert_days: int, today: Optional[date] = None) -> bool:
    new_status = _compute_contract_status(contract.data_vencimento, alert_days, today=today)
    if contract.status == new_status:
        return False
    contract.status = new_status
    contract.updated_at = _utc_now_naive()
    return True


def _serialize_contract(contract: Contract, alert_days: int) -> dict:
    _sync_contract_status(contract, alert_days)
    days_until_due = (contract.data_vencimento - date.today()).days
    return ContractRead(
        id=contract.id,
        cliente_id=contract.cliente_id,
        cliente_nome=contract.cliente.razao_social if contract.cliente else "",
        cliente_email=contract.cliente.email if contract.cliente else None,
        nome=contract.nome,
        data_inicio=contract.data_inicio,
        data_vencimento=contract.data_vencimento,
        status=ContractStatus(contract.status),
        observacoes=contract.observacoes,
        arquivo_nome_original=contract.arquivo_nome_original,
        arquivo_content_type=contract.arquivo_content_type,
        arquivo_tamanho=contract.arquivo_tamanho,
        arquivo_disponivel=bool(contract.arquivo_caminho and Path(contract.arquivo_caminho).exists()),
        dias_para_vencimento=days_until_due,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    ).model_dump()


def _serialize_contract_alert(contract: Contract, alert_days: int) -> dict:
    payload = _serialize_contract(contract, alert_days)
    return {
        "id": payload["id"],
        "cliente_id": payload["cliente_id"],
        "cliente_nome": payload["cliente_nome"],
        "nome": payload["nome"],
        "data_vencimento": payload["data_vencimento"],
        "status": payload["status"],
        "dias_para_vencimento": payload["dias_para_vencimento"],
    }


def _validate_contract_payload(payload: ContractCreate | ContractUpdate) -> None:
    if payload.data_vencimento < payload.data_inicio:
        raise BusinessRuleViolation("A data de vencimento nao pode ser anterior a data de inicio.")


def _delete_contract_file(contract: Contract) -> None:
    if contract.arquivo_caminho:
        path = Path(contract.arquivo_caminho)
        if path.exists():
            path.unlink()


def _store_contract_file(db: Session, filename: str, content_type: str, content: bytes) -> dict:
    if not content:
        raise BusinessRuleViolation("O arquivo do contrato esta vazio.")
    if len(content) > MAX_CONTRACT_FILE_BYTES:
        raise BusinessRuleViolation("O arquivo do contrato excede o limite de 10 MB.")

    extension = Path(filename or "").suffix.lower()
    guessed_type = content_type or mimetypes.guess_type(filename or "")[0] or "application/octet-stream"
    if extension not in ALLOWED_CONTRACT_EXTENSIONS:
        raise BusinessRuleViolation("Tipo de arquivo nao permitido para contratos.")
    if guessed_type not in ALLOWED_CONTRACT_CONTENT_TYPES:
        raise BusinessRuleViolation("Content-Type nao permitido para o arquivo do contrato.")

    stored_name = f"{uuid4().hex}{extension}"
    storage_root = _get_contract_storage_root(db)
    target_path = storage_root / stored_name
    target_path.write_bytes(content)

    return {
        "arquivo_nome_original": filename,
        "arquivo_nome_armazenado": stored_name,
        "arquivo_content_type": guessed_type,
        "arquivo_tamanho": len(content),
        "arquivo_caminho": str(target_path),
    }


def list_contracts(db: Session, current_user: Optional[User] = None) -> list[dict]:
    alert_days = _get_contract_alert_days(db)
    items = _contract_query(db, current_user=current_user).order_by(Contract.data_vencimento.asc(), Contract.id.desc()).all()
    changed = any(_sync_contract_status(item, alert_days) for item in items)
    if changed:
        db.commit()
    return [_serialize_contract(item, alert_days) for item in items]


def list_customer_contracts(db: Session, customer_id: int, current_user: Optional[User] = None) -> list[dict]:
    _get_customer_or_fail(db, customer_id, current_user=current_user)
    alert_days = _get_contract_alert_days(db)
    items = (
        _contract_query(db, current_user=current_user)
        .filter(Contract.cliente_id == customer_id)
        .order_by(Contract.data_vencimento.asc(), Contract.id.desc())
        .all()
    )
    changed = any(_sync_contract_status(item, alert_days) for item in items)
    if changed:
        db.commit()
    return [_serialize_contract(item, alert_days) for item in items]


def get_contract(db: Session, contract_id: int, current_user: Optional[User] = None) -> dict:
    contract = _get_contract_or_fail(db, contract_id, current_user=current_user)
    alert_days = _get_contract_alert_days(db)
    if _sync_contract_status(contract, alert_days):
        db.commit()
        db.refresh(contract)
    return _serialize_contract(contract, alert_days)


def create_contract(
    db: Session,
    customer_id: int,
    payload: ContractCreate,
    *,
    file_payload: Optional[tuple[str, str, bytes]] = None,
    current_user: Optional[User] = None,
) -> dict:
    _validate_contract_payload(payload)
    customer = _get_customer_or_fail(db, customer_id, current_user=current_user)
    alert_days = _get_contract_alert_days(db)

    contract = Contract(
        cliente_id=customer.id,
        nome=payload.nome.strip(),
        data_inicio=payload.data_inicio,
        data_vencimento=payload.data_vencimento,
        status=_compute_contract_status(payload.data_vencimento, alert_days),
        observacoes=(payload.observacoes or None),
        empresa_prestadora_id=customer.empresa_prestadora_id,
    )
    if file_payload:
        filename, content_type, content = file_payload
        for key, value in _store_contract_file(db, filename, content_type, content).items():
            setattr(contract, key, value)

    db.add(contract)
    db.commit()
    db.refresh(contract)
    LOGGER.info("contract_created contract_id=%s customer_id=%s", contract.id, customer.id)
    return _serialize_contract(contract, alert_days)


def update_contract(
    db: Session,
    contract_id: int,
    payload: ContractUpdate,
    *,
    file_payload: Optional[tuple[str, str, bytes]] = None,
    current_user: Optional[User] = None,
) -> dict:
    _validate_contract_payload(payload)
    contract = _get_contract_or_fail(db, contract_id, current_user=current_user)
    alert_days = _get_contract_alert_days(db)

    contract.nome = payload.nome.strip()
    contract.data_inicio = payload.data_inicio
    contract.data_vencimento = payload.data_vencimento
    contract.observacoes = payload.observacoes or None
    contract.status = _compute_contract_status(payload.data_vencimento, alert_days)

    if file_payload:
        old_path = contract.arquivo_caminho
        filename, content_type, content = file_payload
        for key, value in _store_contract_file(db, filename, content_type, content).items():
            setattr(contract, key, value)
        if old_path and old_path != contract.arquivo_caminho:
            old_file = Path(old_path)
            if old_file.exists():
                old_file.unlink()

    db.commit()
    db.refresh(contract)
    LOGGER.info("contract_updated contract_id=%s", contract.id)
    return _serialize_contract(contract, alert_days)


def delete_contract(db: Session, contract_id: int, current_user: Optional[User] = None) -> None:
    contract = _get_contract_or_fail(db, contract_id, current_user=current_user)
    _delete_contract_file(contract)
    db.delete(contract)
    db.commit()
    LOGGER.info("contract_deleted contract_id=%s", contract_id)


def get_contract_file_content(db: Session, contract_id: int, current_user: Optional[User] = None) -> tuple[str, str, bytes]:
    contract = _get_contract_or_fail(db, contract_id, current_user=current_user)
    if not contract.arquivo_caminho or not Path(contract.arquivo_caminho).exists():
        raise BusinessRuleViolation("Nenhum arquivo disponivel para este contrato.")
    return (
        contract.arquivo_nome_original or f"contrato-{contract.id}",
        contract.arquivo_content_type or "application/octet-stream",
        Path(contract.arquivo_caminho).read_bytes(),
    )


def get_contract_dashboard(db: Session, current_user: Optional[User] = None) -> dict:
    alert_days = _get_contract_alert_days(db)
    items = _contract_query(db, current_user=current_user).order_by(Contract.data_vencimento.asc(), Contract.id.desc()).all()
    changed = any(_sync_contract_status(item, alert_days) for item in items)
    if changed:
        db.commit()

    vencidos = [item for item in items if item.status == ContractStatus.VENCIDO.value]
    a_vencer = [item for item in items if item.status == ContractStatus.A_VENCER.value]
    ativos = [item for item in items if item.status == ContractStatus.ATIVO.value]
    return ContractDashboardRead(
        total=len(items),
        ativos=len(ativos),
        vencidos=len(vencidos),
        a_vencer=len(a_vencer),
        alert_days=alert_days,
        vencidos_alertas=[_serialize_contract_alert(item, alert_days) for item in vencidos[:8]],
        a_vencer_alertas=[_serialize_contract_alert(item, alert_days) for item in a_vencer[:8]],
    ).model_dump()


def _build_contract_email(contract: Contract) -> EmailMessage:
    settings = get_settings()
    sender_email = settings.smtp_sender_email or settings.company_email
    if not sender_email:
        raise BusinessRuleViolation("SMTP sem remetente configurado para notificacoes de contratos.")
    if not settings.smtp_host:
        raise BusinessRuleViolation("SMTP nao configurado para notificacoes de contratos.")
    if not contract.cliente or not contract.cliente.email:
        raise BusinessRuleViolation("Cliente sem e-mail cadastrado para notificacao de contrato.")

    status_label = "vencido" if contract.status == ContractStatus.VENCIDO.value else "proximo do vencimento"
    message = EmailMessage()
    message["Subject"] = f"Contrato {contract.nome} {status_label}"
    message["From"] = (
        f"{settings.smtp_sender_name} <{sender_email}>"
        if settings.smtp_sender_name
        else sender_email
    )
    message["To"] = contract.cliente.email
    message.set_content(
        "\n".join(
            [
                f"Ola {contract.cliente.contato or contract.cliente.razao_social},",
                "",
                "Identificamos uma atualizacao importante no contrato abaixo:",
                f"Cliente: {contract.cliente.razao_social}",
                f"Contrato: {contract.nome}",
                f"Vencimento: {contract.data_vencimento.strftime('%d/%m/%Y')}",
                f"Status: {'Vencido' if contract.status == ContractStatus.VENCIDO.value else 'A vencer'}",
                "",
                "Solicitamos avaliar a renovacao ou regularizacao o quanto antes.",
                "",
                "Atenciosamente,",
                settings.company_name,
            ]
        )
    )
    return message


def _send_contract_email_message(message: EmailMessage) -> None:
    settings = get_settings()
    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password or "")
            server.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password or "")
        server.send_message(message)


def run_contract_maintenance(db: Session, current_user: Optional[User] = None) -> dict:
    alert_days = _get_contract_alert_days(db)
    email_enabled = get_boolean_setting(db, "contract_email_enabled", fallback=False)
    notifications_enabled = get_boolean_setting(db, "notifications_enabled", fallback=True)
    today = date.today()
    processed = 0
    updated_statuses = 0
    email_sent = 0
    email_failed = 0

    items = _contract_query(db, current_user=current_user).order_by(Contract.data_vencimento.asc(), Contract.id.asc()).all()
    for contract in items:
        processed += 1
        if _sync_contract_status(contract, alert_days, today=today):
            updated_statuses += 1

        should_notify = (
            notifications_enabled
            and email_enabled
            and contract.status in {ContractStatus.A_VENCER.value, ContractStatus.VENCIDO.value}
            and contract.last_notification_status != contract.status
        )
        if not should_notify:
            continue

        try:
            message = _build_contract_email(contract)
            _send_contract_email_message(message)
            contract.last_notification_status = contract.status
            contract.last_notification_sent_at = _utc_now_naive()
            contract.last_notification_error = None
            email_sent += 1
            LOGGER.info("contract_notification_sent contract_id=%s status=%s", contract.id, contract.status)
        except Exception as exc:
            contract.last_notification_error = str(exc)
            email_failed += 1
            LOGGER.warning(
                "contract_notification_failed contract_id=%s status=%s error=%s",
                contract.id,
                contract.status,
                exc,
            )

    db.commit()
    return ContractMaintenanceRead(
        processed=processed,
        updated_statuses=updated_statuses,
        email_sent=email_sent,
        email_failed=email_failed,
    ).model_dump()
