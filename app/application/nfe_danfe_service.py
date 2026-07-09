from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from textwrap import wrap
from typing import Optional
from xml.etree import ElementTree as ET

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import NfeProcessingStatus
from app.infrastructure.models import NfeInvoice


class NfeDanfeUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class NfeDanfePdf:
    access_key: Optional[str]
    filename: str
    pdf_bytes: bytes
    pdf_base64: str


@dataclass(frozen=True)
class _NfeItem:
    code: str
    description: str
    ncm: str
    cfop: str
    quantity: str
    unit: str
    unit_price: str
    total: str


@dataclass(frozen=True)
class _NfeDanfeData:
    access_key: str
    protocol: str
    model: str
    issuer_name: str
    issuer_cnpj: str
    issuer_ie: str
    issuer_address: str
    recipient_name: str
    recipient_document: str
    recipient_address: str
    nature: str
    number: str
    series: str
    emission_datetime: str
    total_products: str
    total_invoice: str
    additional_info: str
    items: list[_NfeItem]

    @classmethod
    def from_xml(cls, xml_content: str) -> _NfeDanfeData:
        root = ET.fromstring(xml_content)
        ide = _first(root, "ide")
        emit = _first(root, "emit")
        dest = _first(root, "dest")
        total = _first(root, "ICMSTot")
        prot = _first(root, "infProt")
        return cls(
            access_key=_text(prot, "chNFe") or _inf_nfe_id(root).removeprefix("NFe"),
            protocol=_text(prot, "nProt"),
            model=_text(ide, "mod"),
            issuer_name=_text(emit, "xNome"),
            issuer_cnpj=_text(emit, "CNPJ"),
            issuer_ie=_text(emit, "IE"),
            issuer_address=_format_address(_first(emit, "enderEmit")),
            recipient_name=_text(dest, "xNome"),
            recipient_document=_text(dest, "CNPJ") or _text(dest, "CPF"),
            recipient_address=_format_address(_first(dest, "enderDest")),
            nature=_text(ide, "natOp"),
            number=_text(ide, "nNF"),
            series=_text(ide, "serie"),
            emission_datetime=_text(ide, "dhEmi"),
            total_products=_text(total, "vProd"),
            total_invoice=_text(total, "vNF"),
            additional_info=_text(_first(root, "infAdic"), "infCpl"),
            items=_items(root),
        )


def generate_nfe_danfe_pdf(
    xml_content: str,
    *,
    access_key: Optional[str] = None,
    protocol: Optional[str] = None,
) -> NfeDanfePdf:
    data = _NfeDanfeData.from_xml(xml_content)
    _ensure_authorized_nfe(data)
    key = access_key or data.access_key
    if not key:
        raise NfeDanfeUnavailableError("XML NF-e sem chave de acesso.")
    pdf_bytes = _render_pdf(data, key, protocol or data.protocol)
    return NfeDanfePdf(
        access_key=key,
        filename=f"{key}-DANFE-NFE.pdf",
        pdf_bytes=pdf_bytes,
        pdf_base64=base64.b64encode(pdf_bytes).decode("ascii"),
    )


def generate_invoice_nfe_danfe_pdf(db: Session, nfe_id: int) -> NfeDanfePdf:
    invoice = db.query(NfeInvoice).filter(NfeInvoice.id == nfe_id).first()
    if not invoice:
        raise BusinessRuleViolation("Nota fiscal nao encontrada.")
    if invoice.status_processamento != NfeProcessingStatus.AUTORIZADO.value:
        raise NfeDanfeUnavailableError("DANFE NF-e disponivel somente apos autorizacao da SEFAZ.")
    if not invoice.xml_autorizado:
        raise NfeDanfeUnavailableError("NF-e autorizada sem XML autorizado salvo.")
    result = generate_nfe_danfe_pdf(
        invoice.xml_autorizado,
        access_key=invoice.chave_nfe,
        protocol=invoice.protocolo_autorizacao,
    )
    saved_path = _save_invoice_danfe_pdf(invoice, result)
    invoice.danfe_pdf_path = str(saved_path)
    invoice.danfe_pdf_generated_at = datetime.now()
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return result


def _ensure_authorized_nfe(data: _NfeDanfeData) -> None:
    if data.model != "55":
        raise NfeDanfeUnavailableError("XML fiscal nao e NF-e modelo 55.")
    if not data.protocol:
        raise NfeDanfeUnavailableError("XML NF-e sem protocolo de autorizacao.")


def _save_invoice_danfe_pdf(invoice: NfeInvoice, pdf: NfeDanfePdf) -> Path:
    storage_dir = get_settings().nfe_danfe_storage_path
    storage_dir.mkdir(parents=True, exist_ok=True)
    token = _safe_filename_token(pdf.access_key or invoice.chave_nfe or f"nfe-{invoice.id}")
    path = (storage_dir / f"{token}-DANFE-NFE.pdf").resolve()
    if storage_dir.resolve() != path.parent:
        raise NfeDanfeUnavailableError("Caminho de armazenamento DANFE invalido.")
    path.write_bytes(pdf.pdf_bytes)
    return path


def _safe_filename_token(value: str) -> str:
    token = "".join(ch for ch in str(value or "") if ch.isalnum() or ch in {"-", "_"})
    return token[:80] or "nfe"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first(root: Optional[ET.Element], name: str) -> Optional[ET.Element]:
    if root is None:
        return None
    for node in root.iter():
        if _local_name(node.tag) == name:
            return node
    return None


def _text(root: Optional[ET.Element], name: str) -> str:
    node = _first(root, name)
    return (node.text or "").strip() if node is not None and node.text else ""


def _inf_nfe_id(root: ET.Element) -> str:
    node = _first(root, "infNFe")
    return str(node.attrib.get("Id", "")) if node is not None else ""


def _format_address(node: Optional[ET.Element]) -> str:
    if node is None:
        return ""
    parts = [_text(node, tag) for tag in ("xLgr", "nro", "xBairro", "xMun", "UF", "CEP")]
    return " - ".join(part for part in parts if part)


def _items(root: ET.Element) -> list[_NfeItem]:
    rows: list[_NfeItem] = []
    for det in root.iter():
        if _local_name(det.tag) != "det":
            continue
        prod = _first(det, "prod")
        rows.append(
            _NfeItem(
                code=_text(prod, "cProd"),
                description=_text(prod, "xProd"),
                ncm=_text(prod, "NCM"),
                cfop=_text(prod, "CFOP"),
                quantity=_text(prod, "qCom"),
                unit=_text(prod, "uCom"),
                unit_price=_text(prod, "vUnCom"),
                total=_text(prod, "vProd"),
            )
        )
    return rows


def _render_pdf(data: _NfeDanfeData, access_key: str, protocol: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 24
    y = height - margin

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, y, "DANFE - Documento Auxiliar da Nota Fiscal Eletronica")
    y -= 18
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, y, "NF-e modelo 55")
    y -= 22

    _box(pdf, margin, y - 68, width - margin * 2, 68)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin + 6, y - 14, data.issuer_name or "Emitente nao informado")
    pdf.setFont("Helvetica", 8)
    _wrapped(pdf, data.issuer_address, margin + 6, y - 28, 72)
    pdf.drawString(margin + 6, y - 54, f"CNPJ: {data.issuer_cnpj}  IE: {data.issuer_ie}")
    pdf.drawRightString(width - margin - 6, y - 14, f"No {data.number} Serie {data.series}")
    pdf.drawRightString(width - margin - 6, y - 28, f"Emissao: {_format_datetime(data.emission_datetime)}")
    y -= 82

    _box(pdf, margin, y - 46, width - margin * 2, 46)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(margin + 6, y - 12, "CHAVE DE ACESSO")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(margin + 6, y - 28, _format_access_key(access_key))
    pdf.drawRightString(width - margin - 6, y - 28, f"Protocolo: {protocol}")
    y -= 60

    _section(pdf, "DESTINATARIO / REMETENTE", margin, y)
    y -= 14
    _box(pdf, margin, y - 48, width - margin * 2, 48)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(margin + 6, y - 14, data.recipient_name)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(margin + 6, y - 28, f"CPF/CNPJ: {data.recipient_document}")
    _wrapped(pdf, data.recipient_address, margin + 6, y - 40, 92)
    y -= 64

    _section(pdf, "CALCULO DO IMPOSTO", margin, y)
    y -= 14
    _box(pdf, margin, y - 32, width - margin * 2, 32)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(margin + 6, y - 13, f"Valor produtos: R$ {_money(data.total_products)}")
    pdf.drawRightString(width - margin - 6, y - 13, f"Valor total NF: R$ {_money(data.total_invoice)}")
    y -= 48

    _section(pdf, "DADOS DOS PRODUTOS / SERVICOS", margin, y)
    y -= 14
    _box(pdf, margin, y - 220, width - margin * 2, 220)
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawString(margin + 6, y - 12, "COD")
    pdf.drawString(margin + 48, y - 12, "DESCRICAO")
    pdf.drawString(margin + 260, y - 12, "NCM")
    pdf.drawString(margin + 320, y - 12, "CFOP")
    pdf.drawRightString(width - margin - 84, y - 12, "QTD")
    pdf.drawRightString(width - margin - 40, y - 12, "UNIT")
    pdf.drawRightString(width - margin - 6, y - 12, "TOTAL")
    row_y = y - 25
    pdf.setFont("Helvetica", 7)
    for item in data.items[:16]:
        pdf.drawString(margin + 6, row_y, item.code[:8])
        pdf.drawString(margin + 48, row_y, item.description[:45])
        pdf.drawString(margin + 260, row_y, item.ncm[:8])
        pdf.drawString(margin + 320, row_y, item.cfop[:4])
        pdf.drawRightString(width - margin - 84, row_y, item.quantity)
        pdf.drawRightString(width - margin - 40, row_y, _money(item.unit_price))
        pdf.drawRightString(width - margin - 6, row_y, _money(item.total))
        row_y -= 12
    y -= 236

    _section(pdf, "DADOS ADICIONAIS", margin, y)
    y -= 14
    _box(pdf, margin, y - 58, width - margin * 2, 58)
    pdf.setFont("Helvetica", 7)
    _wrapped(pdf, data.additional_info or "-", margin + 6, y - 13, 110)

    pdf.setFont("Helvetica", 6)
    pdf.drawRightString(width - margin, margin, "Gerado pelo motor NF-e SysPragas")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _box(pdf: canvas.Canvas, x: float, y: float, width: float, height: float) -> None:
    pdf.rect(x, y, width, height)


def _section(pdf: canvas.Canvas, title: str, x: float, y: float) -> None:
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x, y, title)


def _wrapped(pdf: canvas.Canvas, text: str, x: float, y: float, width_chars: int) -> None:
    for index, line in enumerate(wrap(str(text or "-"), width=width_chars)[:3]):
        pdf.drawString(x, y - (index * 9), line)


def _format_datetime(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return value


def _format_access_key(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 44:
        return str(value or "")
    return " ".join(digits[index : index + 4] for index in range(0, len(digits), 4))


def _money(value: str) -> str:
    try:
        return f"{float(value or 0):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    except (TypeError, ValueError):
        return str(value or "0,00")
