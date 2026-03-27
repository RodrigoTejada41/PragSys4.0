from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Union

from sqlalchemy.orm import Session, joinedload

from app.application.schemas import (
    NfeInvoiceCreate,
    NfeInvoiceUpdate,
    SimplesNationalConfigCreate,
    SimplesNationalConfigUpdate,
)
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import FinanceStatus, NfeStatus
from app.infrastructure.models import Customer, FinanceEntry, NcmTaxProfile, NfeInvoice, Product, SimplesNationalConfig

MONEY_QUANTIZER = Decimal("0.01")
ALIQUOT_QUANTIZER = Decimal("0.0001")


def _money(value: Optional[Union[Decimal, int, float]]) -> Decimal:
    return Decimal(value or 0).quantize(MONEY_QUANTIZER)


def _aliquot(value: Optional[Union[Decimal, int, float]]) -> Decimal:
    return Decimal(value or 0).quantize(ALIQUOT_QUANTIZER)


def _normalize_ncm_code(value: Optional[str]) -> Optional[str]:
    digits = "".join(char for char in str(value or "") if char.isdigit())
    return digits[:8] if digits else None


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def _clean_required_text(value: Optional[str], message: str) -> str:
    cleaned = _clean_optional_text(value)
    if not cleaned:
        raise BusinessRuleViolation(message)
    return cleaned


def _get_customer_or_fail(db: Session, customer_id: int) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise BusinessRuleViolation("Cliente informado nao existe.")
    return customer


def _get_nfe_or_fail(db: Session, nfe_id: int) -> NfeInvoice:
    invoice = (
        db.query(NfeInvoice)
        .populate_existing()
        .options(joinedload(NfeInvoice.cliente), joinedload(NfeInvoice.financeiro))
        .filter(NfeInvoice.id == nfe_id)
        .first()
    )
    if not invoice:
        raise BusinessRuleViolation("Nota fiscal nao encontrada.")
    return invoice


def _get_ncm_profile(db: Session, codigo: str) -> Optional[NcmTaxProfile]:
    return db.query(NcmTaxProfile).filter(NcmTaxProfile.codigo == codigo).first()


def _fetch_external_ncm_profile(codigo: str) -> Optional[dict]:
    settings = get_settings()
    if not settings.ncm_external_source_url:
        return None

    from app.application.services import _fetch_json  # import local para evitar acoplamento circular no import time

    url = settings.ncm_external_source_url.rstrip("/")
    payload = _fetch_json(f"{url}/{codigo}")
    if not payload:
        return None
    return {
        "codigo": _normalize_ncm_code(payload.get("codigo") or codigo) or codigo,
        "descricao": payload.get("descricao") or payload.get("description") or "NCM importado",
        "aliquota_icms": _aliquot(payload.get("aliquota_icms") or payload.get("icms") or 0),
        "aliquota_ipi": _aliquot(payload.get("aliquota_ipi") or payload.get("ipi") or 0),
        "aliquota_pis": _aliquot(payload.get("aliquota_pis") or payload.get("pis") or 0),
        "aliquota_cofins": _aliquot(payload.get("aliquota_cofins") or payload.get("cofins") or 0),
        "fonte_dados": "api_externa",
    }


def get_or_refresh_ncm_profile(db: Session, codigo: str) -> Optional[NcmTaxProfile]:
    normalized_code = _normalize_ncm_code(codigo)
    if not normalized_code:
        return None

    profile = _get_ncm_profile(db, normalized_code)
    if profile:
        return profile

    external_payload = _fetch_external_ncm_profile(normalized_code)
    if not external_payload:
        return None

    profile = NcmTaxProfile(**external_payload)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def search_ncm_profiles(db: Session, query: Optional[str] = None, limit: int = 10) -> list[NcmTaxProfile]:
    lookup = " ".join(str(query or "").split()).strip()
    statement = db.query(NcmTaxProfile)
    if lookup:
        normalized_code = _normalize_ncm_code(lookup)
        if normalized_code:
            statement = statement.filter(NcmTaxProfile.codigo.contains(normalized_code))
        else:
            statement = statement.filter(NcmTaxProfile.descricao.ilike(f"%{lookup}%"))
    return statement.order_by(NcmTaxProfile.codigo.asc()).limit(max(1, min(limit, 30))).all()


def apply_tax_profile_to_product(
    db: Session,
    product: Product,
    *,
    ncm_code: Optional[str],
    manual_override: bool,
    manual_rates: Optional[dict] = None,
) -> Product:
    normalized_ncm = _normalize_ncm_code(ncm_code)
    product.ncm = normalized_ncm

    if manual_override:
        manual_rates = manual_rates or {}
        product.override_tributacao = True
        product.ncm_descricao = _clean_optional_text(manual_rates.get("ncm_descricao")) or product.ncm_descricao
        product.aliquota_icms = _aliquot(manual_rates.get("aliquota_icms"))
        product.aliquota_ipi = _aliquot(manual_rates.get("aliquota_ipi"))
        product.aliquota_pis = _aliquot(manual_rates.get("aliquota_pis"))
        product.aliquota_cofins = _aliquot(manual_rates.get("aliquota_cofins"))
        return product

    product.override_tributacao = False
    if not normalized_ncm:
        product.ncm_descricao = None
        product.aliquota_icms = Decimal("0.0000")
        product.aliquota_ipi = Decimal("0.0000")
        product.aliquota_pis = Decimal("0.0000")
        product.aliquota_cofins = Decimal("0.0000")
        return product

    profile = get_or_refresh_ncm_profile(db, normalized_ncm)
    if not profile:
        raise BusinessRuleViolation("NCM informado nao foi encontrado na base fiscal local nem em fonte externa configurada.")

    product.ncm_descricao = profile.descricao
    product.aliquota_icms = _aliquot(profile.aliquota_icms)
    product.aliquota_ipi = _aliquot(profile.aliquota_ipi)
    product.aliquota_pis = _aliquot(profile.aliquota_pis)
    product.aliquota_cofins = _aliquot(profile.aliquota_cofins)
    return product


def list_nfe_invoices(
    db: Session,
    *,
    customer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> list[NfeInvoice]:
    query = db.query(NfeInvoice).options(joinedload(NfeInvoice.cliente), joinedload(NfeInvoice.financeiro))
    if customer_id:
        query = query.filter(NfeInvoice.cliente_id == customer_id)
    if start_date:
        query = query.filter(NfeInvoice.data_emissao >= start_date)
    if end_date:
        query = query.filter(NfeInvoice.data_emissao <= end_date)
    if status_filter:
        query = query.filter(NfeInvoice.status == status_filter)
    if search:
        lookup = search.strip()
        query = query.join(Customer).filter(
            (NfeInvoice.numero_nfe.ilike(f"%{lookup}%"))
            | (Customer.razao_social.ilike(f"%{lookup}%"))
        )
    invoices = query.order_by(NfeInvoice.data_emissao.desc(), NfeInvoice.id.desc()).all()
    return invoices


def _create_finance_entry_from_invoice(db: Session, invoice: NfeInvoice) -> FinanceEntry:
    entry = FinanceEntry(
        tipo="receita",
        descricao=f"NF-e {invoice.numero_nfe} | {invoice.cliente.razao_social}",
        valor=_money(invoice.valor_total),
        valor_pago=Decimal("0.00"),
        vencimento=invoice.data_vencimento,
        status=FinanceStatus.PENDENTE.value,
        categoria="NF-e",
        origem="nfe",
        referencia=invoice.numero_nfe,
        cliente_id=invoice.cliente_id,
        nfe_id=invoice.id,
    )
    db.add(entry)
    db.flush()
    return entry


def create_nfe_invoice(db: Session, payload: NfeInvoiceCreate) -> NfeInvoice:
    numero_nfe = _clean_required_text(payload.numero_nfe, "Informe o numero da NF-e.")
    if payload.data_vencimento < payload.data_emissao:
        raise BusinessRuleViolation("A data de vencimento da NF-e nao pode ser anterior a emissao.")
    if db.query(NfeInvoice).filter(NfeInvoice.numero_nfe == numero_nfe).first():
        raise BusinessRuleViolation("Ja existe uma NF-e com este numero.")

    customer = _get_customer_or_fail(db, payload.cliente_id)
    invoice = NfeInvoice(
        numero_nfe=numero_nfe,
        cliente_id=customer.id,
        valor_total=_money(payload.valor_total),
        data_emissao=payload.data_emissao,
        data_vencimento=payload.data_vencimento,
        status=payload.status.value,
        observacoes=_clean_optional_text(payload.observacoes),
    )
    db.add(invoice)
    db.flush()

    if payload.gerar_financeiro:
        _create_finance_entry_from_invoice(db, invoice)

    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def update_nfe_invoice(db: Session, nfe_id: int, payload: NfeInvoiceUpdate) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if payload.data_vencimento < payload.data_emissao:
        raise BusinessRuleViolation("A data de vencimento da NF-e nao pode ser anterior a emissao.")
    duplicate = db.query(NfeInvoice).filter(NfeInvoice.numero_nfe == payload.numero_nfe, NfeInvoice.id != nfe_id).first()
    if duplicate:
        raise BusinessRuleViolation("Ja existe outra NF-e com este numero.")

    customer = _get_customer_or_fail(db, payload.cliente_id)
    invoice.numero_nfe = _clean_required_text(payload.numero_nfe, "Informe o numero da NF-e.")
    invoice.cliente_id = customer.id
    invoice.valor_total = _money(payload.valor_total)
    invoice.data_emissao = payload.data_emissao
    invoice.data_vencimento = payload.data_vencimento
    invoice.status = payload.status.value
    invoice.observacoes = _clean_optional_text(payload.observacoes)

    if invoice.financeiro:
        if invoice.financeiro.status == FinanceStatus.PAGO.value:
            raise BusinessRuleViolation("NF-e com lancamento financeiro ja pago nao pode ser alterada.")
        invoice.financeiro.descricao = f"NF-e {invoice.numero_nfe} | {customer.razao_social}"
        invoice.financeiro.valor = _money(invoice.valor_total)
        invoice.financeiro.vencimento = invoice.data_vencimento
        invoice.financeiro.cliente_id = invoice.cliente_id
        invoice.financeiro.referencia = invoice.numero_nfe

    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def delete_nfe_invoice(db: Session, nfe_id: int) -> None:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if invoice.financeiro and (invoice.financeiro.status == FinanceStatus.PAGO.value or invoice.financeiro.valor_pago > 0):
        raise BusinessRuleViolation("Nao e permitido excluir NF-e com titulo financeiro baixado.")
    if invoice.financeiro:
        db.delete(invoice.financeiro)
    db.delete(invoice)
    db.commit()


def list_simples_configs(db: Session) -> list[SimplesNationalConfig]:
    return db.query(SimplesNationalConfig).order_by(SimplesNationalConfig.faixa_faturamento_inicio.asc()).all()


def create_simples_config(db: Session, payload: SimplesNationalConfigCreate) -> SimplesNationalConfig:
    if payload.faixa_faturamento_fim is not None and payload.faixa_faturamento_fim < payload.faixa_faturamento_inicio:
        raise BusinessRuleViolation("A faixa final do Simples Nacional nao pode ser menor que a faixa inicial.")
    if payload.vigente:
        db.query(SimplesNationalConfig).filter(SimplesNationalConfig.vigente.is_(True)).update({"vigente": False})
    config = SimplesNationalConfig(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_simples_config(db: Session, config_id: int, payload: SimplesNationalConfigUpdate) -> SimplesNationalConfig:
    config = db.query(SimplesNationalConfig).filter(SimplesNationalConfig.id == config_id).first()
    if not config:
        raise BusinessRuleViolation("Configuracao do Simples Nacional nao encontrada.")
    if payload.faixa_faturamento_fim is not None and payload.faixa_faturamento_fim < payload.faixa_faturamento_inicio:
        raise BusinessRuleViolation("A faixa final do Simples Nacional nao pode ser menor que a faixa inicial.")
    if payload.vigente:
        db.query(SimplesNationalConfig).filter(SimplesNationalConfig.id != config_id, SimplesNationalConfig.vigente.is_(True)).update({"vigente": False})
    for field, value in payload.model_dump().items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config


def _resolve_simples_config_for_revenue(db: Session, monthly_revenue: Decimal) -> Optional[SimplesNationalConfig]:
    configs = list_simples_configs(db)
    for config in configs:
        upper = Decimal(config.faixa_faturamento_fim) if config.faixa_faturamento_fim is not None else None
        if Decimal(config.faixa_faturamento_inicio) <= monthly_revenue and (upper is None or monthly_revenue <= upper):
            return config
    return db.query(SimplesNationalConfig).filter(SimplesNationalConfig.vigente.is_(True)).order_by(SimplesNationalConfig.id.desc()).first()


def get_simples_nacional_monthly_summary(db: Session, year: int, month: int) -> dict:
    start_date = date(year, month, 1)
    end_date = date(year + (month // 12), (month % 12) + 1, 1) if month < 12 else date(year + 1, 1, 1)
    invoices = (
        db.query(NfeInvoice)
        .filter(NfeInvoice.status == NfeStatus.EMITIDA.value, NfeInvoice.data_emissao >= start_date, NfeInvoice.data_emissao < end_date)
        .all()
    )
    gross_revenue = sum((Decimal(item.valor_total) for item in invoices), Decimal("0.00"))
    config = _resolve_simples_config_for_revenue(db, gross_revenue)
    applied_rate = _aliquot(config.aliquota if config else 0)
    estimated_tax = _money(gross_revenue * (applied_rate / Decimal("100")))
    return {
        "referencia": f"{year:04d}-{month:02d}",
        "faturamento_bruto": _money(gross_revenue),
        "aliquota_aplicada": applied_rate,
        "anexo": config.anexo if config else None,
        "imposto_estimado": estimated_tax,
        "notas_emitidas": len(invoices),
    }


def get_cash_flow_summary(db: Session, period: str = "monthly") -> dict:
    entries = db.query(FinanceEntry).filter(FinanceEntry.tipo == "receita").all()
    received = sum((Decimal(entry.valor_pago) for entry in entries), Decimal("0.00"))
    pending = sum(
        (_money(Decimal(entry.valor) - Decimal(entry.valor_pago)) for entry in entries if entry.status == FinanceStatus.PENDENTE.value),
        Decimal("0.00"),
    )
    overdue = sum(
        (_money(Decimal(entry.valor) - Decimal(entry.valor_pago)) for entry in entries if entry.status == FinanceStatus.ATRASADO.value),
        Decimal("0.00"),
    )
    return {
        "periodo": period,
        "recebido": _money(received),
        "pendente": _money(pending),
        "vencido": _money(overdue),
        "quantidade_recebida": len([entry for entry in entries if Decimal(entry.valor_pago) > 0]),
        "quantidade_pendente": len([entry for entry in entries if entry.status == FinanceStatus.PENDENTE.value]),
        "quantidade_vencida": len([entry for entry in entries if entry.status == FinanceStatus.ATRASADO.value]),
    }
