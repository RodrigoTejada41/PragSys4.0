import logging
import mimetypes
import smtplib
from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from email.message import EmailMessage
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session, joinedload, selectinload

from app.application.schemas import (
    ContractCreate,
    ContractDashboardRead,
    ContractMaintenanceRead,
    ContractRead,
    ContractReportFiltersRead,
    ContractReportItemRead,
    ContractReportRead,
    ContractReportSummaryRead,
    ContractUpdate,
)
from app.application.settings_service import get_boolean_setting, get_setting_value
from app.application.xlsx_export import build_simple_xlsx
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import ContractBillingType, ContractStatus, FinanceStatus
from app.infrastructure.models import Contract, FinanceEntry, User

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


def _money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _contract_query(db: Session, current_user: Optional[User] = None):
    return _apply_company_scope(
        db.query(Contract).options(
            joinedload(Contract.cliente),
            selectinload(Contract.financeiros),
        ),
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


def _resolve_contract_due_day(payload_or_contract: ContractCreate | ContractUpdate | Contract) -> int:
    configured_day = getattr(payload_or_contract, "dia_vencimento", None)
    if configured_day:
        return int(configured_day)
    return int(payload_or_contract.data_vencimento.day)


def _latest_contract_charge(contract: Contract) -> Optional[FinanceEntry]:
    charges = sorted(
        contract.financeiros or [],
        key=lambda item: (item.vencimento, item.id),
        reverse=True,
    )
    return charges[0] if charges else None


def _contract_charge_counters(contract: Contract) -> tuple[int, int, int]:
    total = len(contract.financeiros or [])
    pending = 0
    overdue = 0
    for entry in contract.financeiros or []:
        if entry.status != FinanceStatus.PAGO.value:
            pending += 1
        if entry.status == FinanceStatus.ATRASADO.value:
            overdue += 1
    return total, pending, overdue


def _serialize_contract(contract: Contract, alert_days: int) -> dict:
    _sync_contract_status(contract, alert_days)
    latest_charge = _latest_contract_charge(contract)
    total_charges, pending_charges, overdue_charges = _contract_charge_counters(contract)
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
        valor_mensal=_money(contract.valor_mensal),
        tipo_cobranca=ContractBillingType(contract.tipo_cobranca),
        dia_vencimento=contract.dia_vencimento,
        gerar_cobranca_automatica=bool(contract.gerar_cobranca_automatica),
        observacoes=contract.observacoes,
        arquivo_nome_original=contract.arquivo_nome_original,
        arquivo_content_type=contract.arquivo_content_type,
        arquivo_tamanho=contract.arquivo_tamanho,
        arquivo_disponivel=bool(contract.arquivo_caminho and Path(contract.arquivo_caminho).exists()),
        dias_para_vencimento=days_until_due,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        ultima_cobranca_gerada_em=latest_charge.vencimento if latest_charge else None,
        ultima_cobranca_status=FinanceStatus(latest_charge.status) if latest_charge else None,
        ultima_cobranca_valor=_money(latest_charge.valor) if latest_charge else None,
        quantidade_cobrancas=total_charges,
        quantidade_cobrancas_pendentes=pending_charges,
        quantidade_cobrancas_vencidas=overdue_charges,
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
    if payload.gerar_cobranca_automatica and _money(payload.valor_mensal) <= Decimal("0.00"):
        raise BusinessRuleViolation("Informe um valor mensal maior que zero para gerar cobranca automatica.")


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
    LOGGER.info("contract_file_stored filename=%s path=%s", filename, target_path)

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
        valor_mensal=_money(payload.valor_mensal),
        tipo_cobranca=payload.tipo_cobranca.value,
        dia_vencimento=_resolve_contract_due_day(payload),
        gerar_cobranca_automatica=bool(payload.gerar_cobranca_automatica),
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
    contract.valor_mensal = _money(payload.valor_mensal)
    contract.tipo_cobranca = payload.tipo_cobranca.value
    contract.dia_vencimento = _resolve_contract_due_day(payload)
    contract.gerar_cobranca_automatica = bool(payload.gerar_cobranca_automatica)
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
    if contract.financeiros:
        raise BusinessRuleViolation("Nao e permitido excluir contrato com cobrancas financeiras vinculadas.")
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
    today = date.today()
    billing_due_soon = 0
    billing_overdue = 0
    for contract in items:
        for entry in contract.financeiros or []:
            if entry.status == FinanceStatus.ATRASADO.value:
                billing_overdue += 1
            elif entry.status == FinanceStatus.PENDENTE.value and 0 <= (entry.vencimento - today).days <= alert_days:
                billing_due_soon += 1
    return ContractDashboardRead(
        total=len(items),
        ativos=len(ativos),
        vencidos=len(vencidos),
        a_vencer=len(a_vencer),
        alert_days=alert_days,
        vencidos_alertas=[_serialize_contract_alert(item, alert_days) for item in vencidos[:8]],
        a_vencer_alertas=[_serialize_contract_alert(item, alert_days) for item in a_vencer[:8]],
        cobrancas_vencidas=billing_overdue,
        cobrancas_a_vencer=billing_due_soon,
        valor_mensal_previsto=_money(sum((Decimal(item.valor_mensal) for item in items if Decimal(item.valor_mensal) > 0), Decimal("0.00"))),
    ).model_dump()


def _get_contract_smtp_settings(db: Session) -> dict[str, object]:
    settings = get_settings()
    return {
        "smtp_host": str(get_setting_value(db, "smtp_host", settings.smtp_host) or "").strip() or None,
        "smtp_port": int(get_setting_value(db, "smtp_port", settings.smtp_port)),
        "smtp_username": str(get_setting_value(db, "smtp_username", settings.smtp_username) or "").strip() or None,
        "smtp_password": get_setting_value(db, "smtp_password", settings.smtp_password),
        "smtp_use_tls": bool(get_setting_value(db, "smtp_use_tls", settings.smtp_use_tls)),
        "smtp_use_ssl": bool(get_setting_value(db, "smtp_use_ssl", settings.smtp_use_ssl)),
        "smtp_sender_email": str(get_setting_value(db, "smtp_sender_email", settings.smtp_sender_email) or "").strip() or None,
        "smtp_sender_name": str(get_setting_value(db, "smtp_sender_name", settings.smtp_sender_name) or "").strip() or None,
        "company_email": settings.company_email,
        "company_name": settings.company_name,
    }


def _default_contract_smtp_settings() -> dict[str, object]:
    settings = get_settings()
    return {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_username": settings.smtp_username,
        "smtp_password": settings.smtp_password,
        "smtp_use_tls": settings.smtp_use_tls,
        "smtp_use_ssl": settings.smtp_use_ssl,
        "smtp_sender_email": settings.smtp_sender_email,
        "smtp_sender_name": settings.smtp_sender_name,
        "company_email": settings.company_email,
        "company_name": settings.company_name,
    }


def _build_contract_email(contract: Contract, smtp_settings: Optional[dict[str, object]] = None) -> EmailMessage:
    settings = smtp_settings or _default_contract_smtp_settings()
    sender_email = settings["smtp_sender_email"] or settings["company_email"]
    if not sender_email:
        raise BusinessRuleViolation("SMTP sem remetente configurado para notificacoes de contratos.")
    if not settings["smtp_host"]:
        raise BusinessRuleViolation("SMTP nao configurado para notificacoes de contratos.")
    if not contract.cliente or not contract.cliente.email:
        raise BusinessRuleViolation("Cliente sem e-mail cadastrado para notificacao de contrato.")

    status_label = "vencido" if contract.status == ContractStatus.VENCIDO.value else "proximo do vencimento"
    message = EmailMessage()
    message["Subject"] = f"Contrato {contract.nome} {status_label}"
    message["From"] = (
        f"{settings['smtp_sender_name']} <{sender_email}>"
        if settings["smtp_sender_name"]
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
                str(settings["company_name"]),
            ]
        )
    )
    return message


def _send_contract_email_message(message: EmailMessage, smtp_settings: Optional[dict[str, object]] = None) -> None:
    settings = smtp_settings or _default_contract_smtp_settings()
    if settings["smtp_use_ssl"]:
        with smtplib.SMTP_SSL(str(settings["smtp_host"]), int(settings["smtp_port"]), timeout=20) as server:
            if settings["smtp_username"]:
                server.login(str(settings["smtp_username"]), str(settings["smtp_password"] or ""))
            server.send_message(message)
        return

    with smtplib.SMTP(str(settings["smtp_host"]), int(settings["smtp_port"]), timeout=20) as server:
        if settings["smtp_use_tls"]:
            server.starttls()
        if settings["smtp_username"]:
            server.login(str(settings["smtp_username"]), str(settings["smtp_password"] or ""))
        server.send_message(message)


def _add_months(reference_date: date, months: int) -> date:
    month_index = reference_date.month - 1 + months
    year = reference_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(reference_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _build_period_due_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def _iter_contract_charge_due_dates(contract: Contract, today: date) -> list[date]:
    due_dates: list[date] = []
    due_day = _resolve_contract_due_day(contract)
    billing_type = ContractBillingType(contract.tipo_cobranca)

    if billing_type == ContractBillingType.MENSAL:
        cursor = date(contract.data_inicio.year, contract.data_inicio.month, 1)
        end_cursor = date(today.year, today.month, 1)
        while cursor <= end_cursor:
            due_date = _build_period_due_date(cursor.year, cursor.month, due_day)
            if contract.data_inicio <= due_date <= contract.data_vencimento:
                due_dates.append(due_date)
            cursor = _add_months(cursor, 1)
        return due_dates

    if billing_type == ContractBillingType.ANUAL:
        for year in range(contract.data_inicio.year, today.year + 1):
            due_date = _build_period_due_date(year, contract.data_inicio.month, due_day)
            if contract.data_inicio <= due_date <= contract.data_vencimento and due_date <= today:
                due_dates.append(due_date)
        return due_dates

    due_date = contract.data_vencimento
    current_month_floor = date(today.year, today.month, 1)
    if date(due_date.year, due_date.month, 1) <= current_month_floor:
        due_dates.append(due_date)
    return due_dates


def _contract_charge_reference(contract: Contract, due_date: date) -> str:
    billing_type = ContractBillingType(contract.tipo_cobranca)
    if billing_type == ContractBillingType.MENSAL:
        return f"CTR-{contract.id}-M-{due_date.strftime('%Y%m')}"
    if billing_type == ContractBillingType.ANUAL:
        return f"CTR-{contract.id}-A-{due_date.strftime('%Y')}"
    return f"CTR-{contract.id}-P-{due_date.strftime('%Y%m%d')}"


def _contract_charge_description(contract: Contract, due_date: date) -> str:
    billing_type = ContractBillingType(contract.tipo_cobranca)
    if billing_type == ContractBillingType.MENSAL:
        return f"Contrato {contract.nome} - {due_date.strftime('%m/%Y')}"
    if billing_type == ContractBillingType.ANUAL:
        return f"Contrato {contract.nome} - Anual {due_date.strftime('%Y')}"
    return f"Contrato {contract.nome} - Cobranca personalizada"


def _contract_charge_exists(contract: Contract, reference: str) -> bool:
    return any((entry.referencia or "") == reference for entry in contract.financeiros or [])


def _create_contract_charge(db: Session, contract: Contract, due_date: date, today: date) -> bool:
    if _money(contract.valor_mensal) <= Decimal("0.00"):
        return False

    reference = _contract_charge_reference(contract, due_date)
    if _contract_charge_exists(contract, reference):
        return False

    charge = FinanceEntry(
        tipo="receita",
        descricao=_contract_charge_description(contract, due_date),
        valor=_money(contract.valor_mensal),
        valor_pago=Decimal("0.00"),
        vencimento=due_date,
        status=FinanceStatus.PENDENTE.value if due_date >= today else FinanceStatus.ATRASADO.value,
        categoria="Contrato",
        origem="contrato",
        referencia=reference,
        parcela_atual=1,
        total_parcelas=1,
        observacoes=f"Cobranca automatica gerada para o contrato {contract.nome}.",
        cliente_id=contract.cliente_id,
        contrato_id=contract.id,
        empresa_prestadora_id=contract.empresa_prestadora_id,
    )
    charge.contrato = contract
    db.add(charge)
    LOGGER.info(
        "contract_charge_generated contract_id=%s reference=%s due_date=%s value=%s",
        contract.id,
        reference,
        due_date.isoformat(),
        charge.valor,
    )
    return True


def _build_contract_report(
    db: Session,
    *,
    cliente_id: Optional[int] = None,
    status: Optional[str] = None,
    data_inicio_de: Optional[date] = None,
    data_inicio_ate: Optional[date] = None,
    data_vencimento_de: Optional[date] = None,
    data_vencimento_ate: Optional[date] = None,
    cobranca_ativa: Optional[bool] = None,
    current_user: Optional[User] = None,
) -> ContractReportRead:
    alert_days = _get_contract_alert_days(db)
    query = _contract_query(db, current_user=current_user)
    if cliente_id:
        query = query.filter(Contract.cliente_id == cliente_id)
    if status:
        query = query.filter(Contract.status == status)
    if data_inicio_de:
        query = query.filter(Contract.data_inicio >= data_inicio_de)
    if data_inicio_ate:
        query = query.filter(Contract.data_inicio <= data_inicio_ate)
    if data_vencimento_de:
        query = query.filter(Contract.data_vencimento >= data_vencimento_de)
    if data_vencimento_ate:
        query = query.filter(Contract.data_vencimento <= data_vencimento_ate)
    if cobranca_ativa is not None:
        query = query.filter(Contract.gerar_cobranca_automatica.is_(cobranca_ativa))

    items = query.order_by(Contract.data_vencimento.asc(), Contract.id.desc()).all()
    changed = any(_sync_contract_status(item, alert_days) for item in items)
    if changed:
        db.commit()

    report_items: list[ContractReportItemRead] = []
    for contract in items:
        latest_charge = _latest_contract_charge(contract)
        financial_status = "Sem cobranca"
        if latest_charge:
            financial_status = "Pago" if latest_charge.status == FinanceStatus.PAGO.value else "Pendente"
        report_items.append(
            ContractReportItemRead(
                contrato_id=contract.id,
                cliente_id=contract.cliente_id,
                cliente_nome=contract.cliente.razao_social if contract.cliente else "",
                nome=contract.nome,
                data_inicio=contract.data_inicio,
                data_vencimento=contract.data_vencimento,
                status=ContractStatus(contract.status),
                valor_mensal=_money(contract.valor_mensal),
                tipo_cobranca=ContractBillingType(contract.tipo_cobranca),
                gerar_cobranca_automatica=bool(contract.gerar_cobranca_automatica),
                ultima_cobranca_gerada_em=latest_charge.vencimento if latest_charge else None,
                situacao_financeira=financial_status,
                ultimo_lancamento_id=latest_charge.id if latest_charge else None,
                ultimo_lancamento_status=FinanceStatus(latest_charge.status) if latest_charge else None,
                ultimo_lancamento_valor=_money(latest_charge.valor) if latest_charge else None,
                total_cobrancas=len(contract.financeiros or []),
            )
        )

    return ContractReportRead(
        filtros=ContractReportFiltersRead(
            cliente_id=cliente_id,
            status=ContractStatus(status) if status else None,
            data_inicio_de=data_inicio_de,
            data_inicio_ate=data_inicio_ate,
            data_vencimento_de=data_vencimento_de,
            data_vencimento_ate=data_vencimento_ate,
            cobranca_ativa=cobranca_ativa,
        ),
        resumo=ContractReportSummaryRead(
            total_contratos=len(report_items),
            ativos=sum(1 for item in report_items if item.status == ContractStatus.ATIVO),
            vencidos=sum(1 for item in report_items if item.status == ContractStatus.VENCIDO),
            a_vencer=sum(1 for item in report_items if item.status == ContractStatus.A_VENCER),
            com_cobranca_ativa=sum(1 for item in report_items if item.gerar_cobranca_automatica),
            valor_total_mensal_previsto=_money(sum((item.valor_mensal for item in report_items), Decimal("0.00"))),
        ),
        itens=report_items,
    )


def get_contract_report(
    db: Session,
    *,
    cliente_id: Optional[int] = None,
    status: Optional[str] = None,
    data_inicio_de: Optional[date] = None,
    data_inicio_ate: Optional[date] = None,
    data_vencimento_de: Optional[date] = None,
    data_vencimento_ate: Optional[date] = None,
    cobranca_ativa: Optional[bool] = None,
    current_user: Optional[User] = None,
) -> dict:
    return _build_contract_report(
        db,
        cliente_id=cliente_id,
        status=status,
        data_inicio_de=data_inicio_de,
        data_inicio_ate=data_inicio_ate,
        data_vencimento_de=data_vencimento_de,
        data_vencimento_ate=data_vencimento_ate,
        cobranca_ativa=cobranca_ativa,
        current_user=current_user,
    ).model_dump()


def export_contract_report_xlsx(
    db: Session,
    *,
    cliente_id: Optional[int] = None,
    status: Optional[str] = None,
    data_inicio_de: Optional[date] = None,
    data_inicio_ate: Optional[date] = None,
    data_vencimento_de: Optional[date] = None,
    data_vencimento_ate: Optional[date] = None,
    cobranca_ativa: Optional[bool] = None,
    current_user: Optional[User] = None,
) -> tuple[str, bytes]:
    report = _build_contract_report(
        db,
        cliente_id=cliente_id,
        status=status,
        data_inicio_de=data_inicio_de,
        data_inicio_ate=data_inicio_ate,
        data_vencimento_de=data_vencimento_de,
        data_vencimento_ate=data_vencimento_ate,
        cobranca_ativa=cobranca_ativa,
        current_user=current_user,
    )
    headers = [
        "Cliente",
        "Contrato",
        "Inicio",
        "Vencimento",
        "Status",
        "Valor Mensal",
        "Tipo de Cobranca",
        "Cobranca Automatica",
        "Ultima Cobranca",
        "Situacao Financeira",
        "Ultimo Lancamento",
    ]
    rows = [
        [
            item.cliente_nome,
            item.nome,
            item.data_inicio,
            item.data_vencimento,
            item.status.value,
            item.valor_mensal,
            item.tipo_cobranca.value,
            "Sim" if item.gerar_cobranca_automatica else "Nao",
            item.ultima_cobranca_gerada_em or "",
            item.situacao_financeira,
            item.ultimo_lancamento_id or "",
        ]
        for item in report.itens
    ]
    filename = f"relatorio_contratos_{date.today().strftime('%Y%m%d')}.xlsx"
    return filename, build_simple_xlsx("Contratos", headers, rows)


def export_contract_report_pdf(
    db: Session,
    *,
    cliente_id: Optional[int] = None,
    status: Optional[str] = None,
    data_inicio_de: Optional[date] = None,
    data_inicio_ate: Optional[date] = None,
    data_vencimento_de: Optional[date] = None,
    data_vencimento_ate: Optional[date] = None,
    cobranca_ativa: Optional[bool] = None,
    current_user: Optional[User] = None,
) -> tuple[str, bytes]:
    report = _build_contract_report(
        db,
        cliente_id=cliente_id,
        status=status,
        data_inicio_de=data_inicio_de,
        data_inicio_ate=data_inicio_ate,
        data_vencimento_de=data_vencimento_de,
        data_vencimento_ate=data_vencimento_ate,
        cobranca_ativa=cobranca_ativa,
        current_user=current_user,
    )
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def start_page() -> float:
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(18 * mm, height - 18 * mm, "Relatorio de Contratos")
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.HexColor("#4B5A4F"))
        pdf.drawString(18 * mm, height - 25 * mm, f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        pdf.setFillColor(colors.black)
        pdf.drawString(18 * mm, height - 33 * mm, f"Total: {report.resumo.total_contratos} contrato(s)")
        pdf.drawString(18 * mm, height - 39 * mm, f"Ativos: {report.resumo.ativos} | A vencer: {report.resumo.a_vencer} | Vencidos: {report.resumo.vencidos}")
        pdf.drawString(18 * mm, height - 45 * mm, f"Valor mensal previsto: R$ {report.resumo.valor_total_mensal_previsto}")
        return height - 55 * mm

    y = start_page()
    for item in report.itens:
        if y < 35 * mm:
            pdf.showPage()
            y = start_page()
        pdf.setStrokeColor(colors.HexColor("#D8E1D7"))
        pdf.line(18 * mm, y + 2 * mm, width - 18 * mm, y + 2 * mm)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(18 * mm, y - 3 * mm, f"{item.cliente_nome} | {item.nome}")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(18 * mm, y - 9 * mm, f"Inicio: {item.data_inicio.strftime('%d/%m/%Y')} | Vencimento: {item.data_vencimento.strftime('%d/%m/%Y')}")
        pdf.drawString(18 * mm, y - 15 * mm, f"Status: {item.status.value} | Cobranca: {item.tipo_cobranca.value} | Auto: {'Sim' if item.gerar_cobranca_automatica else 'Nao'}")
        pdf.drawString(18 * mm, y - 21 * mm, f"Valor mensal: R$ {item.valor_mensal} | Financeiro: {item.situacao_financeira}")
        last_charge = item.ultima_cobranca_gerada_em.strftime("%d/%m/%Y") if item.ultima_cobranca_gerada_em else "-"
        pdf.drawString(18 * mm, y - 27 * mm, f"Ultima cobranca: {last_charge} | Lancamento: {item.ultimo_lancamento_id or '-'}")
        y -= 34 * mm

    pdf.save()
    filename = f"relatorio_contratos_{date.today().strftime('%Y%m%d')}.pdf"
    return filename, buffer.getvalue()


def run_contract_maintenance(db: Session, current_user: Optional[User] = None) -> dict:
    alert_days = _get_contract_alert_days(db)
    email_enabled = get_boolean_setting(db, "contract_email_enabled", fallback=False)
    notifications_enabled = get_boolean_setting(db, "notifications_enabled", fallback=True)
    smtp_settings = _get_contract_smtp_settings(db)
    today = date.today()
    processed = 0
    updated_statuses = 0
    email_sent = 0
    email_failed = 0
    charges_generated = 0

    items = _contract_query(db, current_user=current_user).order_by(Contract.data_vencimento.asc(), Contract.id.asc()).all()
    for contract in items:
        processed += 1
        if _sync_contract_status(contract, alert_days, today=today):
            updated_statuses += 1

        if contract.gerar_cobranca_automatica and contract.status in {ContractStatus.ATIVO.value, ContractStatus.A_VENCER.value}:
            for due_date in _iter_contract_charge_due_dates(contract, today):
                if _create_contract_charge(db, contract, due_date, today):
                    charges_generated += 1

        should_notify = (
            notifications_enabled
            and email_enabled
            and contract.status in {ContractStatus.A_VENCER.value, ContractStatus.VENCIDO.value}
            and contract.last_notification_status != contract.status
        )
        if not should_notify:
            continue

        try:
            message = _build_contract_email(contract, smtp_settings)
            _send_contract_email_message(message, smtp_settings)
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
        charges_generated=charges_generated,
    ).model_dump()
