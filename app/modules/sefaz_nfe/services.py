from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from app.application.fiscal_services import _create_finance_entry_from_invoice, _get_customer_or_fail, _get_nfe_or_fail, _money
from app.application.schemas import NfeCancelRequest, NfeInvoiceCreate, NfeInvoiceUpdate, SefazDirectReadinessRead
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import NfeProcessingStatus, NfeStatus
from app.infrastructure.models import NfeInvoice, Product
from app.infrastructure.db import get_session_local
from app.modules.sefaz_nfe.sefaz_client import SefazResponse, SefazSoapClient
from app.modules.sefaz_nfe.signer import sign_xml_document
from app.modules.sefaz_nfe.xml_generator import build_nfe_xml, validate_xml_against_xsd

NFE_NS = "http://www.portalfiscal.inf.br/nfe"


def _digits_only(value: Optional[str]) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _clean_text(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def _resolve_reference(payload: NfeInvoiceCreate) -> str:
    candidate = _clean_text(payload.referencia_externa) or _clean_text(payload.numero_nfe)
    if not candidate:
        raise BusinessRuleViolation("Informe uma referencia externa valida para a NF-e.")
    normalized = "".join(char for char in candidate if char.isalnum() or char in {"-", "_"})
    if not normalized:
        raise BusinessRuleViolation("A referencia externa da NF-e deve conter apenas letras, numeros, hifen ou underscore.")
    return normalized[:80]


def _company_uf() -> str:
    settings = get_settings()
    uf = (settings.sefaz_nfe_uf or settings.company_state or "").upper()
    if not uf:
        raise BusinessRuleViolation("Configure SEFAZ_NFE_UF ou COMPANY_STATE para a emissao direta.")
    return uf


def _safe_company_uf() -> Optional[str]:
    try:
        return _company_uf()
    except BusinessRuleViolation:
        return None


def _company_cuf() -> str:
    settings = get_settings()
    cuf = _digits_only(settings.company_state_code)
    if len(cuf) == 2:
        return cuf
    from app.modules.sefaz_nfe.xml_generator import UF_CODE_MAP

    uf = _company_uf()
    if uf not in UF_CODE_MAP:
        raise BusinessRuleViolation("Nao foi possivel determinar o codigo IBGE da UF do emitente.")
    return UF_CODE_MAP[uf]


def get_direct_sefaz_readiness() -> SefazDirectReadinessRead:
    settings = get_settings()
    central_certificate_configured = _has_central_certificate()
    current_environment = str(settings.focus_nfe_environment or "homologacao").strip().lower()
    xsd_required = current_environment != "homologacao"
    required_items = [
        "NFE_PROVIDER=sefaz_direct",
        "SEFAZ_NFE_UF",
        "SEFAZ_NFE_CERTIFICATE_PATH",
        "SEFAZ_NFE_CERTIFICATE_PASSWORD",
        "COMPANY_CNPJ",
        "COMPANY_IE",
        "COMPANY_CRT",
        "COMPANY_STREET",
        "COMPANY_NUMBER",
        "COMPANY_DISTRICT",
        "COMPANY_CITY",
        "COMPANY_CITY_CODE",
        "COMPANY_STATE",
        "COMPANY_STATE_CODE",
        "COMPANY_ZIP_CODE",
    ]
    if xsd_required:
        required_items.insert(4, "SEFAZ_NFE_XSD_DIR")
    missing_items: list[str] = []
    notes: list[str] = []

    env_checks = {
        "SEFAZ_NFE_UF": settings.sefaz_nfe_uf or settings.company_state,
        "SEFAZ_NFE_CERTIFICATE_PATH": settings.sefaz_nfe_certificate_path or ("central" if central_certificate_configured else None),
        "SEFAZ_NFE_CERTIFICATE_PASSWORD": settings.sefaz_nfe_certificate_password or ("central" if central_certificate_configured else None),
        "COMPANY_CNPJ": settings.company_cnpj,
        "COMPANY_IE": settings.company_ie,
        "COMPANY_CRT": settings.company_crt,
        "COMPANY_STREET": settings.company_street or settings.company_address,
        "COMPANY_NUMBER": settings.company_number,
        "COMPANY_DISTRICT": settings.company_district,
        "COMPANY_CITY": settings.company_city,
        "COMPANY_CITY_CODE": settings.company_city_code,
        "COMPANY_STATE": settings.company_state or settings.sefaz_nfe_uf,
        "COMPANY_STATE_CODE": settings.company_state_code,
        "COMPANY_ZIP_CODE": settings.company_zip_code,
    }
    for key, value in env_checks.items():
        if not value:
            missing_items.append(key)
    if xsd_required and not settings.sefaz_nfe_xsd_dir:
        missing_items.append("SEFAZ_NFE_XSD_DIR")

    cert_path = settings.sefaz_nfe_certificate_path or None
    xsd_dir = settings.sefaz_nfe_xsd_dir or None
    if cert_path and cert_path != "central" and not Path(cert_path).exists():
        missing_items.append("Arquivo do certificado A1 nao encontrado")
    if xsd_required and xsd_dir and not Path(xsd_dir).exists():
        missing_items.append("Diretorio de XSD nao encontrado")

    provider = str(settings.nfe_provider or "focus_nfe").strip().lower()
    if provider != "sefaz_direct":
        notes.append("O provider atual ainda nao esta em sefaz_direct. A rota /api/v1/nfe continua usando o provider configurado.")
    else:
        notes.append("O provider sefaz_direct esta ativo para a rota /api/v1/nfe.")

    if central_certificate_configured:
        notes.append("Certificado digital central configurado em Configuracoes > Certificado Digital.")
    elif cert_path:
        notes.append("A emissao real depende de um certificado A1 .pfx valido e compativel com o CNPJ transmissor.")
    if xsd_required and xsd_dir:
        notes.append("Os schemas oficiais precisam corresponder ao layout NF-e 4.00 em uso na UF.")
    if not xsd_required and not xsd_dir:
        notes.append("Homologacao sem XSD local esta habilitada. A validacao XSD sera ignorada apenas neste ambiente.")
    elif not xsd_required and xsd_dir:
        notes.append("Homologacao com XSD local configurado. A validacao XSD continuara ativa.")

    return SefazDirectReadinessRead(
        ready=provider == "sefaz_direct" and not missing_items,
        provider=provider,
        environment=current_environment,
        uf=_safe_company_uf(),
        certificate_path=cert_path,
        xsd_dir=xsd_dir,
        required_items=required_items,
        missing_items=missing_items,
        notes=notes,
    )


def _has_central_certificate() -> bool:
    session = get_session_local()()
    try:
        from app.application.digital_certificate_service import has_central_digital_certificate

        return has_central_digital_certificate(session)
    finally:
        session.close()


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
                "quantidade": item.quantidade,
                "valor_unitario": item.valor_unitario,
                "produto_id": item.produto_id,
                "cfop": _clean_text(item.cfop) or "5102",
                "unidade_comercial": _clean_text(item.unidade_comercial) or "UN",
                "aliquota_icms": item.aliquota_icms if item.aliquota_icms is not None else (product.aliquota_icms if product else Decimal("0")),
                "aliquota_ipi": item.aliquota_ipi if item.aliquota_ipi is not None else (product.aliquota_ipi if product else Decimal("0")),
                "aliquota_pis": item.aliquota_pis if item.aliquota_pis is not None else (product.aliquota_pis if product else Decimal("0")),
                "aliquota_cofins": item.aliquota_cofins if item.aliquota_cofins is not None else (product.aliquota_cofins if product else Decimal("0")),
            }
        )
    if not items:
        raise BusinessRuleViolation("Informe ao menos um item para emitir a NF-e.")
    return items


def _rebuild_signed_batch_xml(signed_nfe_xml: str, lote_id: str, ambiente: str) -> str:
    root = ET.Element(f"{{{NFE_NS}}}enviNFe", attrib={"versao": "4.00"})
    id_lote = ET.SubElement(root, f"{{{NFE_NS}}}idLote")
    id_lote.text = lote_id
    ind_sinc = ET.SubElement(root, f"{{{NFE_NS}}}indSinc")
    ind_sinc.text = "1"
    root.append(ET.fromstring(signed_nfe_xml.encode("utf-8")))
    return ET.tostring(root, encoding="utf-8", xml_declaration=False).decode("utf-8")


def _parse_protocol(response: SefazResponse) -> Optional[str]:
    if response.protocol_number:
        return response.protocol_number
    if response.raw_response.count("<nProt>"):
        return response.raw_response.split("<nProt>", 1)[1].split("</nProt>", 1)[0]
    return None


def _compose_authorized_xml(signed_nfe_xml: str, response: SefazResponse) -> Optional[str]:
    if not response.inner_xml:
        return None
    protocol_xml = None
    try:
        response_root = ET.fromstring(response.inner_xml.encode("utf-8"))
    except ET.ParseError:
        return response.inner_xml

    for node in response_root.iter():
        if node.tag.endswith("protNFe"):
            protocol_xml = ET.tostring(node, encoding="unicode")
            break

    if not protocol_xml:
        return response.inner_xml
    return f'<nfeProc xmlns="{NFE_NS}" versao="4.00">{signed_nfe_xml}{protocol_xml}</nfeProc>'


def _resolve_processing_status(c_stat: Optional[str]) -> str:
    if c_stat in {"100", "150"}:
        return NfeProcessingStatus.AUTORIZADO.value
    if c_stat in {"101", "135", "155"}:
        return NfeProcessingStatus.CANCELADO.value
    if c_stat in {"103", "105"}:
        return NfeProcessingStatus.PROCESSANDO.value
    if c_stat in {"104", "106"}:
        return NfeProcessingStatus.PROCESSANDO.value
    return NfeProcessingStatus.REJEITADO.value


def _apply_authorization_response(invoice: NfeInvoice, response: SefazResponse, signed_nfe_xml: str) -> None:
    invoice.status_externo = response.c_stat
    invoice.mensagem_retorno = response.x_motivo
    invoice.recibo_lote = response.receipt_number or invoice.recibo_lote
    invoice.protocolo_autorizacao = _parse_protocol(response) or invoice.protocolo_autorizacao
    invoice.chave_nfe = response.access_key or invoice.chave_nfe
    processing_status = _resolve_processing_status(response.c_stat)
    invoice.status_processamento = processing_status
    if processing_status == NfeProcessingStatus.AUTORIZADO.value:
        invoice.status = NfeStatus.EMITIDA.value
        invoice.xml_autorizado = _compose_authorized_xml(signed_nfe_xml, response)
    elif processing_status == NfeProcessingStatus.CANCELADO.value:
        invoice.status = NfeStatus.CANCELADA.value
    invoice.resposta_externa = response.raw_response


def _requires_receipt_poll(response: SefazResponse) -> bool:
    return response.c_stat in {"103", "104"} and bool(response.receipt_number)


def _reapply_stored_authorization_response(invoice: NfeInvoice) -> bool:
    if not invoice.resposta_externa:
        return False
    response = SefazSoapClient()._parse_response("NFeAutorizacao", 200, invoice.resposta_externa)
    if response.c_stat == invoice.status_externo and response.protocol_number == invoice.protocolo_autorizacao:
        return False
    _apply_authorization_response(invoice, response, invoice.xml_enviado or "")
    return True


def _build_cancel_event_xml(invoice: NfeInvoice, justification: str) -> str:
    tp_amb = "2" if (invoice.ambiente or "homologacao") == "homologacao" else "1"
    cuf = _company_cuf()
    event_id = f"ID110111{invoice.chave_nfe}01"
    root = ET.Element(f"{{{NFE_NS}}}envEvento", attrib={"versao": "1.00"})
    id_lote = ET.SubElement(root, f"{{{NFE_NS}}}idLote")
    id_lote.text = invoice.lote_id or "1"
    evento = ET.SubElement(root, f"{{{NFE_NS}}}evento", attrib={"versao": "1.00"})
    inf_evento = ET.SubElement(evento, f"{{{NFE_NS}}}infEvento", attrib={"Id": event_id})
    for tag, value in {
        "cOrgao": cuf,
        "tpAmb": tp_amb,
        "CNPJ": _digits_only(get_settings().company_cnpj),
        "chNFe": invoice.chave_nfe,
        "dhEvento": date.today().isoformat() + "T00:00:00-03:00",
        "tpEvento": "110111",
        "nSeqEvento": "1",
        "verEvento": "1.00",
    }.items():
        child = ET.SubElement(inf_evento, f"{{{NFE_NS}}}{tag}")
        child.text = value
    det_evento = ET.SubElement(inf_evento, f"{{{NFE_NS}}}detEvento", attrib={"versao": "1.00"})
    desc_evento = ET.SubElement(det_evento, f"{{{NFE_NS}}}descEvento")
    desc_evento.text = "Cancelamento"
    x_just = ET.SubElement(det_evento, f"{{{NFE_NS}}}xJust")
    x_just.text = justification
    return ET.tostring(root, encoding="utf-8", xml_declaration=False).decode("utf-8")


def _issue_direct(db: Session, invoice: NfeInvoice, payload: NfeInvoiceCreate) -> NfeInvoice:
    customer = invoice.cliente
    items = _build_items_payload(db, payload)
    generated = build_nfe_xml(invoice, customer, items)
    signed_nfe_xml = sign_xml_document(generated.nfe_xml, f"#NFe{generated.access_key}")
    signed_batch_xml = _rebuild_signed_batch_xml(signed_nfe_xml, generated.lote_id, invoice.ambiente or "homologacao")

    validate_xml_against_xsd(signed_batch_xml, "enviNFe_v4.00.xsd", environment=invoice.ambiente)

    invoice.xml_enviado = signed_nfe_xml
    invoice.payload_enviado = signed_batch_xml
    invoice.chave_nfe = generated.access_key
    invoice.lote_id = generated.lote_id
    invoice.provedor = "sefaz_direct"

    client = SefazSoapClient()
    auth_response = client.authorize_batch(
        uf=_company_uf(),
        ambiente=invoice.ambiente or "homologacao",
        cuf=_company_cuf(),
        envi_nfe_xml=signed_batch_xml,
    )
    _apply_authorization_response(invoice, auth_response, signed_nfe_xml)

    if _requires_receipt_poll(auth_response):
        receipt_response = client.query_receipt(
            uf=_company_uf(),
            ambiente=invoice.ambiente or "homologacao",
            cuf=_company_cuf(),
            recibo=auth_response.receipt_number or "",
        )
        _apply_authorization_response(invoice, receipt_response, signed_nfe_xml)

    return invoice


def issue_direct_nfe(db: Session, payload: NfeInvoiceCreate) -> NfeInvoice:
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
        provedor="sefaz_direct",
        status_processamento=NfeProcessingStatus.PENDENTE_ENVIO.value,
        observacoes=_clean_text(payload.observacoes),
    )
    db.add(invoice)
    db.flush()
    db.refresh(invoice)
    db.refresh(customer)

    try:
        _issue_direct(db, invoice, payload)
    except BusinessRuleViolation:
        invoice.status_processamento = NfeProcessingStatus.ERRO_INTEGRACAO.value
        db.commit()
        raise

    if payload.gerar_financeiro and not invoice.financeiro and invoice.status_processamento != NfeProcessingStatus.REJEITADO.value:
        _create_finance_entry_from_invoice(db, invoice)

    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def get_direct_nfe_status(db: Session, nfe_id: int, *, sync_with_sefaz: bool = True) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if invoice.provedor != "sefaz_direct":
        return invoice

    if _reapply_stored_authorization_response(invoice):
        db.commit()
        invoice = _get_nfe_or_fail(db, nfe_id)

    if not sync_with_sefaz or not invoice.recibo_lote:
        return invoice

    if invoice.status_processamento in {NfeProcessingStatus.AUTORIZADO.value, NfeProcessingStatus.CANCELADO.value}:
        return invoice

    response = SefazSoapClient().query_receipt(
        uf=_company_uf(),
        ambiente=invoice.ambiente or "homologacao",
        cuf=_company_cuf(),
        recibo=invoice.recibo_lote,
    )
    _apply_authorization_response(invoice, response, invoice.xml_enviado or "")
    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def cancel_direct_nfe(db: Session, nfe_id: int, payload: Optional[NfeCancelRequest] = None) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    request_payload = payload or NfeCancelRequest()
    justification = _clean_text(request_payload.justificativa) or "Cancelamento solicitado pelo emitente."

    if invoice.status == NfeStatus.CANCELADA.value:
        return invoice
    if not invoice.chave_nfe or not invoice.protocolo_autorizacao:
        raise BusinessRuleViolation("A NF-e precisa estar autorizada e com protocolo para cancelar na SEFAZ.")

    event_xml = _build_cancel_event_xml(invoice, justification)
    signed_event_xml = sign_xml_document(event_xml, f"#ID110111{invoice.chave_nfe}01")
    validate_xml_against_xsd(signed_event_xml, "envEventoCancNFe_v1.00.xsd", environment=invoice.ambiente)

    response = SefazSoapClient().send_event(
        uf=_company_uf(),
        ambiente=invoice.ambiente or "homologacao",
        cuf=_company_cuf(),
        event_xml=signed_event_xml,
    )
    invoice.resposta_externa = response.raw_response
    invoice.status_externo = response.c_stat
    invoice.mensagem_retorno = response.x_motivo

    if "<cStat>135</cStat>" in response.raw_response or "<cStat>155</cStat>" in response.raw_response:
        invoice.status = NfeStatus.CANCELADA.value
        invoice.status_processamento = NfeProcessingStatus.CANCELADO.value
    elif response.c_stat == "128":
        invoice.status_processamento = NfeProcessingStatus.PROCESSANDO.value
    else:
        invoice.status_processamento = NfeProcessingStatus.REJEITADO.value
        db.commit()
        raise BusinessRuleViolation(response.x_motivo or "SEFAZ rejeitou o evento de cancelamento.")

    db.commit()
    return _get_nfe_or_fail(db, invoice.id)


def update_direct_nfe_local(db: Session, nfe_id: int, payload: NfeInvoiceUpdate) -> NfeInvoice:
    invoice = _get_nfe_or_fail(db, nfe_id)
    if invoice.status_processamento in {NfeProcessingStatus.AUTORIZADO.value, NfeProcessingStatus.CANCELADO.value}:
        raise BusinessRuleViolation("NF-e ja transmitida diretamente para a SEFAZ nao pode ser alterada localmente.")
    invoice.numero_nfe = _clean_text(payload.numero_nfe) or payload.numero_nfe
    invoice.valor_total = _money(payload.valor_total)
    invoice.data_emissao = payload.data_emissao
    invoice.data_vencimento = payload.data_vencimento
    invoice.status = payload.status.value
    invoice.observacoes = _clean_text(payload.observacoes)
    invoice.ambiente = payload.ambiente.value
    db.commit()
    return _get_nfe_or_fail(db, invoice.id)
