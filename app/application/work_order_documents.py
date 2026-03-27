from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.application.certificate_assets import resolve_technical_signature_path
from app.core.exceptions import BusinessRuleViolation


PLACEHOLDER_SNIPPETS = (
    "nao configurad",
    "0800 nao configurado",
)


def generate_work_order_document_pdf(work_order, settings) -> bytes:
    _validate_work_order_document_requirements(settings)

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=f"Ordem de Servico {work_order.numero}",
    )
    styles = _build_styles()
    story: List = []

    story.extend(_build_header(styles, work_order, settings))
    story.extend(_build_identification_section(styles, work_order))
    story.extend(_build_client_section(styles, work_order))
    story.extend(_build_service_section(styles, work_order))
    story.extend(_build_products_section(styles, work_order))
    story.extend(_build_orientations_section(styles))
    story.extend(_build_observations_section(styles, work_order))
    story.extend(_build_legal_section(styles, settings))
    story.extend(_build_signatures_section(styles, work_order, settings))

    document.build(story)
    return buffer.getvalue()


def _validate_work_order_document_requirements(settings) -> None:
    required_fields = [
        ("Responsavel tecnico", settings.technical_responsible_name),
        ("Registro profissional", settings.technical_responsible_registry),
        ("Licenca sanitaria", settings.sanitary_license_number),
        ("Licenca ambiental", settings.environmental_license_number),
        ("Endereco da empresa", settings.company_address),
        ("CIT", settings.toxicology_center_phone),
    ]
    missing = [label for label, value in required_fields if _is_missing_config(value)]
    if missing:
        raise BusinessRuleViolation(
            "Nao foi possivel gerar a ordem de servico. Configure antes: "
            + ", ".join(missing)
            + "."
        )


def _is_missing_config(value: Optional[str]) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return True
    return any(snippet in normalized for snippet in PLACEHOLDER_SNIPPETS)


def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "WorkOrderTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#17392b"),
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "WorkOrderSubtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=11,
            textColor=colors.HexColor("#5a6b62"),
        ),
        "section": ParagraphStyle(
            "WorkOrderSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.8,
            leading=13,
            textColor=colors.HexColor("#1f4334"),
            spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "WorkOrderLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=10.5,
            textColor=colors.HexColor("#4d5c54"),
        ),
        "value": ParagraphStyle(
            "WorkOrderValue",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=11.6,
            textColor=colors.HexColor("#203028"),
        ),
        "small": ParagraphStyle(
            "WorkOrderSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            textColor=colors.HexColor("#63736a"),
        ),
        "signature": ParagraphStyle(
            "WorkOrderSignature",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=10.5,
            textColor=colors.HexColor("#203028"),
            alignment=TA_CENTER,
        ),
        "signature_hint": ParagraphStyle(
            "WorkOrderSignatureHint",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.8,
            leading=9.5,
            textColor=colors.HexColor("#6c7a72"),
            alignment=TA_CENTER,
        ),
        "center_meta": ParagraphStyle(
            "WorkOrderCenterMeta",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.6,
            leading=10.4,
            textColor=colors.HexColor("#17392b"),
            alignment=TA_CENTER,
        ),
    }
    return styles


def _build_header(styles, work_order, settings) -> List:
    company_name = _safe_text(settings.company_trade_name, settings.company_legal_name)
    company_meta = [
        Paragraph(company_name, styles["title"]),
        Paragraph(
            f"{_safe_text(settings.company_legal_name)} | CNPJ: {_safe_text(settings.company_cnpj, 'Nao informado')}",
            styles["subtitle"],
        ),
        Paragraph(
            f"{_safe_text(settings.company_address)} | Telefone: {_safe_text(settings.company_phone, 'Nao informado')}",
            styles["subtitle"],
        ),
    ]
    left_content = [*company_meta]

    right_data = [
        [Paragraph("ORDEM DE SERVICO", styles["center_meta"])],
        [Paragraph(f"Numero: {work_order.numero}", styles["center_meta"])],
        [Paragraph(f"Data da execucao: {_format_date(work_order.data_execucao)}", styles["small"])],
        [Paragraph(f"Emissao do documento: {_format_date(date.today())}", styles["small"])],
        [Paragraph(f"Status: {_format_status(work_order.status)}", styles["small"])],
    ]
    right_table = Table(right_data, colWidths=[54 * mm])
    right_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f0e8")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f3f8f4")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#c6d8cb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#d7e3da")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    header = Table(
        [[left_content, right_table]],
        colWidths=[118 * mm, 58 * mm],
        hAlign="LEFT",
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [header, Spacer(1, 6 * mm), HRFlowable(color=colors.HexColor("#d3ddd5"), thickness=1), Spacer(1, 4 * mm)]


def _build_identification_section(styles, work_order) -> List:
    rows = [
        ("Numero automatico", work_order.numero),
        ("Tipo da OS", _format_status(work_order.tipo_os)),
        ("Data do atendimento", _format_date(work_order.data_execucao)),
        ("Hora de inicio", _format_time(work_order.hora_inicio)),
        ("Hora de termino", _format_time(work_order.hora_fim, fallback="Nao registrada")),
        ("Status operacional", _format_status(work_order.status)),
    ]
    return _build_info_section("Identificacao da OS", rows, styles)


def _build_client_section(styles, work_order) -> List:
    customer = work_order.cliente
    rows = [
        ("Razao social", customer.razao_social),
        ("Documento", _safe_text(customer.cpf_cnpj, "Nao informado")),
        ("Contato", _safe_text(customer.contato, "Nao informado")),
        ("Telefone", _safe_text(customer.telefone, "Nao informado")),
        ("Endereco", _build_customer_address(customer)),
    ]
    return _build_info_section("Cliente", rows, styles)


def _build_service_section(styles, work_order) -> List:
    pest_names = ", ".join(item.praga.nome_comum for item in work_order.pragas) if work_order.pragas else "Monitoramento preventivo"
    rows = [
        ("Servico executado", _format_status(work_order.tipo_os)),
        ("Local de execucao", _safe_text(work_order.local_execucao, "Nao informado")),
        ("Tecnico executor", work_order.tecnico.nome),
        ("Pragas alvo", pest_names),
        ("Prazo de assistencia", _assistance_text(work_order)),
        ("Valor do servico", f"R$ {Decimal(work_order.valor_servico):.2f}"),
    ]
    return _build_info_section("Servico executado", rows, styles)


def _build_products_section(styles, work_order) -> List:
    content: List = [_section_title("Produtos aplicados", styles)]
    headers = [
        Paragraph("Produto", styles["label"]),
        Paragraph("Principio ativo", styles["label"]),
        Paragraph("Registro MS", styles["label"]),
        Paragraph("Diluicao", styles["label"]),
        Paragraph("Quantidade", styles["label"]),
    ]
    rows = [headers]
    if work_order.produtos:
        for item in work_order.produtos:
            rows.append(
                [
                    Paragraph(_safe_text(item.produto.nome), styles["value"]),
                    Paragraph(_safe_text(item.produto.principio_ativo, "-"), styles["value"]),
                    Paragraph(_safe_text(item.produto.registro_ms, "-"), styles["value"]),
                    Paragraph(_safe_text(item.diluicao, "-"), styles["value"]),
                    Paragraph(str(item.quantidade), styles["value"]),
                ]
            )
    else:
        rows.append(
            [
                Paragraph("Nenhum produto registrado para esta OS.", styles["value"]),
                "",
                "",
                "",
                "",
            ]
        )

    table = Table(rows, colWidths=[52 * mm, 40 * mm, 28 * mm, 24 * mm, 24 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f1ea")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17392b")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cddbd0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e4dc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8faf8")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    content.extend([table, Spacer(1, 4 * mm)])
    return content


def _build_orientations_section(styles) -> List:
    items = [
        "Manter pessoas e animais afastados das areas tratadas durante o periodo de seguranca orientado pela empresa.",
        "Nao remover barreiras quimicas, iscas ou dispositivos aplicados sem orientacao tecnica.",
        "Em caso de intercorrencia com o produto utilizado, acionar imediatamente o CIT informado neste documento.",
    ]
    return _build_bullet_section("Orientacoes", items, styles)


def _build_observations_section(styles, work_order) -> List:
    text = _safe_text(work_order.observacoes, "Sem observacoes adicionais registradas.")
    return [
        _section_title("Observacoes", styles),
        _text_box(text, styles),
        Spacer(1, 4 * mm),
    ]


def _build_legal_section(styles, settings) -> List:
    rows = [
        ("Responsavel tecnico", settings.technical_responsible_name),
        ("Registro profissional", settings.technical_responsible_registry),
        ("Licenca sanitaria", _license_line(settings.sanitary_license_number, settings.sanitary_license_expiry)),
        ("Licenca ambiental", _license_line(settings.environmental_license_number, settings.environmental_license_expiry)),
        ("Endereco da empresa", settings.company_address),
        ("CIT", settings.toxicology_center_phone),
    ]
    return _build_info_section("Dados legais da empresa", rows, styles)


def _build_signatures_section(styles, work_order, settings) -> List:
    signature_path = resolve_technical_signature_path(work_order.tecnico)
    technical_signature = _signature_cell(
        styles,
        label="Responsavel tecnico",
        signer=f"{settings.technical_responsible_name} | {settings.technical_responsible_registry}",
        signature_path=signature_path,
    )
    customer_signature = _signature_cell(
        styles,
        label="Cliente / responsavel no local",
        signer=work_order.cliente.razao_social,
        signature_path=None,
        hint="Assinatura manual no ato da execucao",
    )
    signatures = Table([[technical_signature, customer_signature]], colWidths=[86 * mm, 86 * mm])
    signatures.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d7e0d8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#dde6df")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return [_section_title("Assinaturas", styles), signatures]


def _build_info_section(title: str, rows, styles) -> List:
    table_rows = []
    for label, value in rows:
        table_rows.append(
            [
                Paragraph(label, styles["label"]),
                Paragraph(_safe_text(value, "Nao informado"), styles["value"]),
            ]
        )
    table = Table(table_rows, colWidths=[43 * mm, 133 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f6f3")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d4ded6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#dce5dd")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [_section_title(title, styles), table, Spacer(1, 4 * mm)]


def _build_bullet_section(title: str, items: List[str], styles) -> List:
    rows = []
    for item in items:
        rows.append([Paragraph("•", styles["label"]), Paragraph(item, styles["value"])])
    table = Table(rows, colWidths=[8 * mm, 168 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d4ded6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#dce5dd")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [_section_title(title, styles), table, Spacer(1, 4 * mm)]


def _section_title(title: str, styles):
    return Paragraph(title, styles["section"])


def _text_box(text: str, styles):
    table = Table([[Paragraph(text, styles["value"])]], colWidths=[176 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d4ded6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _signature_cell(styles, *, label: str, signer: str, signature_path=None, hint: Optional[str] = None):
    elements: List = []
    if signature_path:
        image = ImageReader(str(signature_path))
        image_width, image_height = image.getSize()
        max_width = 50 * mm
        max_height = 16 * mm
        scale = min(max_width / image_width, max_height / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale
        from reportlab.platypus import Image

        elements.append(Image(str(signature_path), width=draw_width, height=draw_height))
    else:
        elements.append(Paragraph(hint or "Assinatura tecnica pendente no cadastro", styles["signature_hint"]))

    elements.append(Spacer(1, 6 * mm))
    elements.append(HRFlowable(width="92%", color=colors.HexColor("#98aaa0"), thickness=1))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(_safe_text(signer, "Nao informado"), styles["signature"]))
    elements.append(Paragraph(label, styles["signature_hint"]))
    return elements


def _license_line(number: Optional[str], expiry: Optional[str]) -> str:
    if expiry and "nao configurad" not in str(expiry).lower():
        return f"{number} | validade: {expiry}"
    return _safe_text(number, "Nao informado")


def _safe_text(value: Optional[str], fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _build_customer_address(customer) -> str:
    parts = [
        _safe_text(customer.endereco),
        f"{_safe_text(customer.cidade)} / {_safe_text(customer.estado)}".strip(" /"),
    ]
    return " - ".join(part for part in parts if part.strip(" -/"))


def _format_date(value) -> str:
    if not value:
        return "Nao informado"
    return value.strftime("%d/%m/%Y")


def _format_time(value, fallback: str = "Nao informado") -> str:
    if not value:
        return fallback
    return value.strftime("%H:%M")


def _format_status(value: Optional[str]) -> str:
    text = _safe_text(value, "Nao informado")
    return text.replace("_", " ").title()


def _days_in_words(days: int) -> str:
    units = {
        0: "zero",
        1: "um",
        2: "dois",
        3: "tres",
        4: "quatro",
        5: "cinco",
        6: "seis",
        7: "sete",
        8: "oito",
        9: "nove",
        10: "dez",
        11: "onze",
        12: "doze",
        13: "treze",
        14: "quatorze",
        15: "quinze",
        16: "dezesseis",
        17: "dezessete",
        18: "dezoito",
        19: "dezenove",
    }
    tens = {
        20: "vinte",
        30: "trinta",
        40: "quarenta",
        50: "cinquenta",
        60: "sessenta",
        70: "setenta",
        80: "oitenta",
        90: "noventa",
    }
    if days < 20:
        return units[days]
    if days < 100:
        base = (days // 10) * 10
        remainder = days % 10
        return tens[base] if remainder == 0 else f"{tens[base]} e {units[remainder]}"
    hundreds = days // 100
    remainder = days % 100
    hundreds_map = {1: "cento", 2: "duzentos", 3: "trezentos"}
    prefix = "cem" if days == 100 else hundreds_map.get(hundreds, str(days))
    if remainder == 0:
        return prefix
    return f"{prefix} e {_days_in_words(remainder)}"


def _assistance_text(work_order) -> str:
    delta = (work_order.garantia_ate - work_order.data_execucao).days
    if delta < 0:
        delta = 0
    return f"{delta} ({_days_in_words(delta)}) dias, ate {_format_date(work_order.garantia_ate)}"
