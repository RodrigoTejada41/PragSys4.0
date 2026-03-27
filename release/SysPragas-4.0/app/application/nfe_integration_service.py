from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.application.fiscal_services import _create_finance_entry_from_invoice, _get_customer_or_fail, _get_nfe_or_fail, _money, list_nfe_invoices
from app.application.schemas import NfeCancelRequest, NfeInvoiceCreate, NfeInvoiceRead, NfeInvoiceUpdate, NfeWebhookEvent
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import NfeEnvironment, NfeProcessingStatus, NfeStatus
from app.infrastructure.external_api.focus_nfe import FocusNfeApiError, FocusNfeClient
from app.infrastructure.models import NfeInvoice, Product
from app.modules.sefaz_nfe.services import cancel_direct_nfe, get_direct_nfe_status, issue_direct_nfe, update_direct_nfe_local

logger = logging.getLogger(__name__)


def _use_direct_sefaz_provider() -> bool:
    return str(get_settings().nfe_provider or "").strip().lower() == "sefaz_direct"


def _digits_only(value: Optional[str]) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _clean_text(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def _json_dump(payload: Optional[dict[str, Any]]) -> Optional[str]:
    if not payload:
        return None
    return json.dumps(payload, ensure_ascii=True, default=str)


def _resolve_reference(payload: NfeInvoiceCreate) -> str:
    candidate = _clean_text(payload.referencia_externa) or _clean_text(payload.numero_nfe)
    if not candidate:
        raise BusinessRuleViolation("Informe uma referencia externa valida para a NF-e.")
    normalized = "".join(char for char in candidate if char.isalnum() or char in {"-", "_"})
    if not normalized:
        raise BusinessRuleViolation("A referencia externa da NF-e deve conter apenas letras, numeros, hifen ou underscore.")
    return normalized[:80]


def _normalize_processing_status(raw_status: Optional[str], local_status: str) -> str:
    normalized = str(raw_status or "").strip().lower()
    if normalized in {"autorizado", "autorizada"}:
        return NfeProcessingStatus.AUTORIZADO.value
    if normalized in {"cancelado", "cancelada"}:
        return NfeProcessingStatus.CANCELADO.value
    if normalized in {"rejeitado", "rejeitada", "erro_autorizacao", "erro_validacao"}:
        return NfeProcessingStatus.REJEITADO.value
    if normalized.startswith("processando"):
        return NfeProcessingStatus.PROCESSANDO.value
    if local_status == NfeStatus.CANCELADA.value:
        return NfeProcessingStatus.CANCELADO.value
    return NfeProcessingStatus.PENDENTE_ENVIO.value


def _build_download_url(client: FocusNfeClient, payload: dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if value:
            return client.resolve_download_url(value)
    return None


def _apply_external_response(invoice: NfeInvoice, response_payload: dict[str, Any], client: FocusNfeClient) -> None:
    external_status = response_payload.get("status") or response_payload.get("situacao") or response_payload.get("status_sefaz")
    invoice.status_externo = _clean_text(str(external_status) if external_status is not None else None)
    invoice.status_processamento = _normalize_processing_status(invoice.status_externo, invoice.status)
    if invoice.status_processamento == NfeProcessingStatus.CANCELADO.value:
        invoice.status = NfeStatus.CANCELADA.value
    elif invoice.status == NfeStatus.CANCELADA.value and invoice.status_processamento != NfeProcessingStatus.CANCELADO.value:
        invoice.status_processamento = NfeProcessingStatus.CANCELADO.value
    invoice.mensagem_retorno = _clean_text(
        response_payload.get("mensagem_sefaz")
        or response_payload.get("mensagem")
        or response_payload.get("message")
    )
    invoice.chave_nfe = _clean_text(response_payload.get("chave_nfe") or response_payload.get("chave"))
    invoice.xml_url = _build_download_url(
        client,
        response_payload,
        "xml_url",
        "url_xml",
        "caminho_xml_nota_fiscal",
        "caminho_xml",
    )
    invoice.pdf_url = _build_download_url(
        client,
        response_payload,
        "pdf_url",
        "url_danfe",
        "caminho_danfe",
    )
    invoice.resposta_externa = _json_dump(response_payload)


def _build_items_payload(db: Session, payload: NfeInvoiceCreate) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in payload.itens:
        product = db.query(Product).filter(Product.id == item.produto_id).first() if item.produto_id else None
        description = _clean_text(item.descricao or (product.nome if product else None))
        if not description:
            raise BusinessRuleViolation("Cada item da NF-e precisa de descricao.")
        ncm = _digits_only(item.ncm or (product.ncm if product else ""))[:8]
        if not ncm:
            raise BusinessRuleViolation(f"O item '{description}' precisa de NCM para emissao da NF-e.")
        items.append(
            {
                "descricao": description,
                "ncm": ncm,
                "quantidade": float(item.quantidade),
                "valor_unitario": float(item.valor_unitario),
                "cfop": _clean_text(item.cfop),
                "unidade_comercial": _clean_text(item.unidade_comercial) or "UN",
                "aliquota_icms": float(item.aliquota_icms if item.aliquota_icms is not None else (product.aliquota_icms if product else 0)),
                "aliquota_ipi": float(item.aliquota_ipi if item.aliquota_ipi is not None else (product.aliquota_ipi if product else 0)),
                "aliquota_pis": float(item.aliquota_pis if item.aliquota_pis is not None else (product.aliquota_pis if product else 0)),
                "aliquota_cofins": float(item.aliquota_cofins if item.aliquota_cofins is not None else (product.aliquota_cofins if product else 0)),
            }
        )
    return items


def _build_external_payload(db: Session, payload: NfeInvoiceCreate, invoice: NfeInvoice) -> dict[str, Any]:
    settings = get_settings()
    customer = invoice.cliente
    customer_document = _digits_only(customer.cpf_cnpj)
    emitente_cnpj = _digits_only(payload.cnpj_emitente or settings.company_cnpj)
    if not emitente_cnpj:
        raise BusinessRuleViolation("Configure o CNPJ do emitente para usar a integracao real de NF-e.")

    items = _build_items_payload(db, payload)
    if not items:
        raise BusinessRuleViolation("Informe ao menos um item para emitir a NF-e na API externa.")

    external_payload: dict[str, Any] = {
        "natureza_operacao": _clean_text(payload.natureza_operacao) or "Venda",
        "data_emissao": payload.data_emissao.isoformat(),
        "cnpj_emitente": emitente_cnpj,
        "nome_emitente": _clean_text(payload.nome_emitente or settings.company_legal_name or settings.company_name),
        "nome_destinatario": _clean_text(payload.nome_destinatario or customer.razao_social),
        "valor_total": float(_money(payload.valor_total)),
        "itens": items,
    }
    if len(customer_document) == 11:
        external_payload["cpf_destinatario"] = _digits_only(payload.cpf_destinatario) or customer_document
    elif len(customer_document) == 14:
        external_payload["cnpj_destinatario"] = _digits_only(payload.cnpj_destinatario) or customer_document
    elif payload.cpf_destinatario:
        external_payload["cpf_destinatario"] = _digits_only(payload.cpf_destinatario)
    elif payload.cnpj_destinatario:
        external_payload["cnpj_destinatario"] = _digits_only(payload.cnpj_destinatario)

    if payload.payload_externo:
        external_payload.update(payload.payload_externo)

    return {key: value for key, value in external_payload.items() if value not in (None, "", [], {})}


def issue_nfe(db: Session, payload: NfeInvoiceCreate) -> NfeInvoice:
    if _use_direct_sefaz_provider():
        return issue_direct_nfe(db, payload)

    if payload.data_vencimento < payload.data_emissao:
        raise BusinessRuleViolation("A data de vencimento da NF-e nao pode ser anterior a emissao.")
    if db.query(NfeInvoice).filter(NfeInvoice.numero_nfe == payload.numero_nfe).first():
        raise BusinessRuleViolation("Ja existe uma NF-e com este numero.")

    reference = _resolve_reference(payload)
    if db.query(NfeInvoice).filter(NfeInvoice.referencia_externa == reference).first():
        raise BusinessRuleViolation("Ja existe uma NF-e com esta referencia externa.")

    customer = _get_customer_or_fail(db, payload.cliente_id)
    invoice = NfeInvoice(
        numero_nfe=_clean_text(payload.numero_nfe) or payload.numero_nfe,
        cliente_id=customer.id,
        valor_total=_money(payload.valor_total),
        data_emissao=payload.data_emissao,
        data_vencimento=payload.data_vencimento,
        status=payload.status.value,
        referencia_externa=reference,
        ambiente=payload.ambiente.value,
        provedor="focus_nfe",
        status_processamento=NfeProcessingStatus.PENDENTE_ENVIO.value,
        observacoes=_clean_text(payload.observacoes),
        webhook_url=_clean_text(payload.webhook_url),
    )
    db.add(invoice)
    db.flush()
    db.refresh(invoice)

    client = FocusNfeClient(environment=payload.ambiente)
    payload_snapshot: Optional[dict[str, Any]] = None
    if client.is_configured():
        payload_snapshot = _build_external_payload(db, payload, invoice)
        invoice.payload_enviado = _json_dump(payload_snapshot)
        try:
            response_payload = client.emit_invoice(reference, payload_snapshot)
            _apply_external_response(invoice, response_payload, client)
        except FocusNfeApiError as exc:
            invoice.status_processamento = NfeProcessingStatus.ERRO_INTEGRACAO.value
            invoice.mensagem_retorno = exc.message
            invoice.resposta_externa = _json_dump(exc.payload)
            db.commit()
            logger.exception("Falha ao emitir NF-e na Focus NFe. referencia=%s", reference)
            raise BusinessRuleViolation(exc.message) from exc
    else:
        invoice.mensagem_retorno = "Integracao externa nao configurada. NF-e registrada apenas no controle interno."

    if (
        payload.gerar_financeiro
        and not invoice.financeiro
        and invoice.status_processamento not in {NfeProcessingStatus.REJEITADO.value, NfeProcessingStatus.ERRO_INTEGRACAO.value}
    ):
        _create_finance_entry_from_invoice(db, invoice)

    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def get_nfe_status(db: Session, nfe_id: int, *, sync_with_provider: bool = True) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if invoice.provedor == "sefaz_direct" or _use_direct_sefaz_provider():
        return get_direct_nfe_status(db, nfe_id, sync_with_sefaz=sync_with_provider)
    if not sync_with_provider or not invoice.referencia_externa:
        return invoice

    client = FocusNfeClient(environment=invoice.ambiente or get_settings().focus_nfe_environment)
    if not client.is_configured():
        return invoice

    try:
        response_payload = client.get_invoice(invoice.referencia_externa)
        _apply_external_response(invoice, response_payload, client)
        db.commit()
    except FocusNfeApiError as exc:
        logger.exception("Falha ao consultar NF-e na Focus NFe. referencia=%s", invoice.referencia_externa)
        invoice.status_processamento = NfeProcessingStatus.ERRO_INTEGRACAO.value
        invoice.mensagem_retorno = exc.message
        invoice.resposta_externa = _json_dump(exc.payload)
        db.commit()
        raise BusinessRuleViolation(exc.message) from exc

    return _get_nfe_or_fail(db, invoice.id)


def cancel_nfe(db: Session, nfe_id: int, payload: Optional[NfeCancelRequest] = None) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if invoice.provedor == "sefaz_direct" or _use_direct_sefaz_provider():
        return cancel_direct_nfe(db, nfe_id, payload)
    request_payload = payload or NfeCancelRequest()

    if invoice.status == NfeStatus.CANCELADA.value:
        return invoice

    if invoice.referencia_externa:
        client = FocusNfeClient(environment=invoice.ambiente or get_settings().focus_nfe_environment)
        if client.is_configured():
            try:
                response_payload = client.cancel_invoice(invoice.referencia_externa, justification=request_payload.justificativa)
                _apply_external_response(invoice, response_payload, client)
            except FocusNfeApiError as exc:
                logger.exception("Falha ao cancelar NF-e na Focus NFe. referencia=%s", invoice.referencia_externa)
                invoice.status_processamento = NfeProcessingStatus.ERRO_INTEGRACAO.value
                invoice.mensagem_retorno = exc.message
                invoice.resposta_externa = _json_dump(exc.payload)
                db.commit()
                raise BusinessRuleViolation(exc.message) from exc

    invoice.status = NfeStatus.CANCELADA.value
    if invoice.status_processamento != NfeProcessingStatus.ERRO_INTEGRACAO.value:
        invoice.status_processamento = NfeProcessingStatus.CANCELADO.value
    if request_payload.justificativa:
        complement = f"Cancelamento: {request_payload.justificativa}"
        invoice.observacoes = f"{invoice.observacoes}\n{complement}".strip() if invoice.observacoes else complement
    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def process_nfe_webhook(db: Session, payload: NfeWebhookEvent) -> NfeInvoice:
    if _use_direct_sefaz_provider():
        raise BusinessRuleViolation("Webhook nao se aplica a emissao direta na SEFAZ.")
    invoice = db.query(NfeInvoice).filter(NfeInvoice.referencia_externa == payload.referencia).first()
    if not invoice:
        raise BusinessRuleViolation("NF-e vinculada ao webhook nao encontrada.")

    client = FocusNfeClient(environment=invoice.ambiente or get_settings().focus_nfe_environment)
    response_payload = {
        "status": payload.status,
        "chave_nfe": payload.chave_nfe,
        "caminho_xml_nota_fiscal": payload.caminho_xml_nota_fiscal,
        "caminho_danfe": payload.caminho_danfe,
        "mensagem_sefaz": payload.mensagem_sefaz,
    }
    if payload.payload:
        response_payload.update(payload.payload)
    _apply_external_response(invoice, response_payload, client)
    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def list_nfe_with_integration(
    db: Session,
    *,
    customer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> list[NfeInvoice]:
    return list_nfe_invoices(
        db,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
        search=search,
    )


def update_nfe_local(db: Session, nfe_id: int, payload: NfeInvoiceUpdate) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if invoice.provedor == "sefaz_direct" or _use_direct_sefaz_provider():
        return update_direct_nfe_local(db, nfe_id, payload)

    if payload.data_vencimento < payload.data_emissao:
        raise BusinessRuleViolation("A data de vencimento da NF-e nao pode ser anterior a emissao.")
    duplicate = db.query(NfeInvoice).filter(NfeInvoice.numero_nfe == payload.numero_nfe, NfeInvoice.id != nfe_id).first()
    if duplicate:
        raise BusinessRuleViolation("Ja existe outra NF-e com este numero.")

    customer = _get_customer_or_fail(db, payload.cliente_id)
    invoice.numero_nfe = _clean_text(payload.numero_nfe) or payload.numero_nfe
    invoice.cliente_id = customer.id
    invoice.valor_total = _money(payload.valor_total)
    invoice.data_emissao = payload.data_emissao
    invoice.data_vencimento = payload.data_vencimento
    invoice.status = payload.status.value
    invoice.observacoes = _clean_text(payload.observacoes)
    invoice.webhook_url = _clean_text(payload.webhook_url)
    if payload.referencia_externa:
        normalized_reference = _resolve_reference(
            NfeInvoiceCreate(
                **payload.model_dump(),
                gerar_financeiro=False,
                natureza_operacao="Venda",
                itens=[],
            )
        )
        duplicate_reference = db.query(NfeInvoice).filter(
            NfeInvoice.referencia_externa == normalized_reference,
            NfeInvoice.id != nfe_id,
        ).first()
        if duplicate_reference:
            raise BusinessRuleViolation("Ja existe outra NF-e com esta referencia externa.")
        invoice.referencia_externa = normalized_reference
    invoice.ambiente = payload.ambiente.value

    if invoice.financeiro:
        if invoice.financeiro.status == "pago":
            raise BusinessRuleViolation("NF-e com lancamento financeiro ja pago nao pode ser alterada.")
        invoice.financeiro.descricao = f"NF-e {invoice.numero_nfe} | {customer.razao_social}"
        invoice.financeiro.valor = _money(invoice.valor_total)
        invoice.financeiro.vencimento = invoice.data_vencimento
        invoice.financeiro.cliente_id = invoice.cliente_id
        invoice.financeiro.referencia = invoice.numero_nfe

    db.commit()
    return _get_nfe_or_fail(db, invoice.id)
