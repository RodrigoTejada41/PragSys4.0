from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from typing import Optional, Union

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session, joinedload

from app.application.schemas import ReceiptCreate, ReceiptPreviewRead, ReceiptUpdate
from app.application.services import (
    _apply_finance_payment,
    _clean_required_text,
    _company_identification_lines,
    _draw_bullets,
    _draw_document_frame,
    _draw_key_values,
    _draw_paragraph,
    _draw_section_title,
    _get_customer_or_fail,
    _get_work_order_or_fail,
    _money,
)
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import ReceiptPaymentMethod, WorkOrderType
from app.infrastructure.models import FinanceEntry, Receipt, ReceiptHistory, User, WorkOrder


RECEIPT_PAYMENT_LABELS = {
    ReceiptPaymentMethod.DINHEIRO.value: "Dinheiro",
    ReceiptPaymentMethod.PIX.value: "PIX",
    ReceiptPaymentMethod.TRANSFERENCIA.value: "Transferencia bancaria",
    ReceiptPaymentMethod.CARTAO_CREDITO.value: "Cartao de credito",
    ReceiptPaymentMethod.CARTAO_DEBITO.value: "Cartao de debito",
    ReceiptPaymentMethod.BOLETO.value: "Boleto",
    ReceiptPaymentMethod.CHEQUE.value: "Cheque",
    ReceiptPaymentMethod.OUTROS.value: "Outros",
}

_UNITS = ["zero", "um", "dois", "tres", "quatro", "cinco", "seis", "sete", "oito", "nove"]
_TEENS = ["dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_TENS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_HUNDREDS = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]
_SCALES = [
    ("", ""),
    ("mil", "mil"),
    ("milhao", "milhoes"),
    ("bilhao", "bilhoes"),
    ("trilhao", "trilhoes"),
]


def _receipt_query(db: Session):
    return db.query(Receipt).options(
        joinedload(Receipt.cliente),
        joinedload(Receipt.ordem_servico),
        joinedload(Receipt.financeiro),
        joinedload(Receipt.historico).joinedload(ReceiptHistory.usuario),
    )


def _format_currency_brl(value: Decimal) -> str:
    return f"R$ {_money(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_date_brl(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _normalize_receipt_description(value: str) -> str:
    return _clean_required_text(value, "Informe a descricao do recibo.")


def _receipt_payment_label(value: Union[ReceiptPaymentMethod, str]) -> str:
    normalized = value.value if hasattr(value, "value") else str(value or "")
    return RECEIPT_PAYMENT_LABELS.get(normalized, "Outros")


def _number_group_to_words(value: int) -> str:
    if value == 0:
        return ""
    if value == 100:
        return "cem"

    hundreds = value // 100
    remainder = value % 100
    parts: list[str] = []

    if hundreds:
        parts.append(_HUNDREDS[hundreds])

    if remainder:
        if remainder < 10:
            parts.append(_UNITS[remainder])
        elif remainder < 20:
            parts.append(_TEENS[remainder - 10])
        else:
            tens = remainder // 10
            units = remainder % 10
            tens_words = _TENS[tens]
            if units:
                tens_words = f"{tens_words} e {_UNITS[units]}"
            parts.append(tens_words)

    return " e ".join(filter(None, parts))


def _join_words(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return " e ".join(parts)
    return ", ".join(parts[:-1]) + f" e {parts[-1]}"


def _number_to_words(value: int) -> str:
    if value == 0:
        return "zero"

    groups: list[int] = []
    while value:
        groups.append(value % 1000)
        value //= 1000

    parts: list[str] = []
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index]
        if group == 0:
            continue

        if index == 1:
            if group == 1:
                parts.append("mil")
            else:
                parts.append(f"{_number_group_to_words(group)} mil")
            continue

        words = _number_group_to_words(group)
        if index >= 2:
            singular, plural = _SCALES[index]
            scale = singular if group == 1 else plural
            parts.append(f"{words} {scale}")
        else:
            parts.append(words)

    return _join_words(parts)


def _currency_to_words(value: Decimal) -> str:
    normalized = _money(value)
    integer_part = int(normalized)
    cents = int((normalized - Decimal(integer_part)) * 100)

    if integer_part == 0:
        reais_text = "zero real"
    else:
        words = _number_to_words(integer_part)
        if integer_part >= 1_000_000 and integer_part % 1_000_000 == 0:
            reais_text = f"{words} de reais"
        else:
            reais_text = f"{words} {'real' if integer_part == 1 else 'reais'}"

    if cents == 0:
        return reais_text

    cents_text = f"{_number_to_words(cents)} {'centavo' if cents == 1 else 'centavos'}"
    if integer_part == 0:
        return cents_text
    return f"{reais_text} e {cents_text}"


def _serialize_receipt_history_entry(entry: ReceiptHistory) -> ReceiptHistory:
    entry.usuario_nome = entry.usuario.nome if entry.usuario else None
    return entry


def _serialize_receipt(receipt: Receipt) -> Receipt:
    receipt.historico = sorted(
        [_serialize_receipt_history_entry(item) for item in receipt.historico],
        key=lambda item: (item.created_at, item.id),
        reverse=True,
    )
    return receipt


def _build_receipt_preview(
    *,
    customer,
    payload: Union[ReceiptCreate, ReceiptUpdate],
    work_order: Optional[WorkOrder],
    description: str,
) -> ReceiptPreviewRead:
    amount_in_words = _currency_to_words(payload.valor)
    formatted_amount = _format_currency_brl(payload.valor)
    formatted_date = _format_date_brl(payload.data_recebimento)
    payment_label = _receipt_payment_label(payload.forma_pagamento)
    os_fragment = f", vinculado a ordem de servico {work_order.numero}" if work_order else ""
    formal_text = (
        f"Recebemos de {customer.razao_social}, inscrito sob o documento {customer.cpf_cnpj}, "
        f"a importancia de {formatted_amount} ({amount_in_words}), em {formatted_date}, "
        f"referente a {description.lower()}, por meio de {payment_label.lower()}{os_fragment}. "
        "Para maior clareza, firmamos o presente recibo para os devidos fins."
    )
    return ReceiptPreviewRead(
        cliente_id=customer.id,
        cliente_nome=customer.razao_social,
        cliente_documento=customer.cpf_cnpj,
        os_id=work_order.id if work_order else None,
        os_numero=work_order.numero if work_order else None,
        valor=_money(payload.valor),
        valor_formatado=formatted_amount,
        valor_por_extenso=amount_in_words,
        forma_pagamento=payload.forma_pagamento,
        forma_pagamento_label=payment_label,
        descricao=description,
        data_recebimento=payload.data_recebimento,
        data_recebimento_formatada=formatted_date,
        texto_formal=formal_text,
    )


def _validate_receipt_payload(
    db: Session,
    payload: Union[ReceiptCreate, ReceiptUpdate],
    *,
    current_receipt_id: Optional[int] = None,
    skip_duplicate_check: bool = False,
):
    customer = _get_customer_or_fail(db, payload.cliente_id)
    work_order = _get_work_order_or_fail(db, payload.os_id) if payload.os_id else None
    if work_order and work_order.cliente_id != customer.id:
        raise BusinessRuleViolation("A OS vinculada ao recibo deve pertencer ao mesmo cliente informado.")
    if work_order and work_order.tipo_os == WorkOrderType.CONTRATO.value:
        raise BusinessRuleViolation("OS vinculadas a contrato nao permitem recibos ou cobrancas avulsas.")

    description = _normalize_receipt_description(payload.descricao)
    if not skip_duplicate_check:
        duplicate_query = db.query(Receipt).filter(
            Receipt.deleted_at.is_(None),
            Receipt.cliente_id == payload.cliente_id,
            Receipt.os_id == payload.os_id,
            Receipt.valor == _money(payload.valor),
            Receipt.forma_pagamento == (
                payload.forma_pagamento.value if hasattr(payload.forma_pagamento, "value") else payload.forma_pagamento
            ),
            Receipt.data_recebimento == payload.data_recebimento,
            Receipt.descricao == description,
        )
        if current_receipt_id is not None:
            duplicate_query = duplicate_query.filter(Receipt.id != current_receipt_id)
        if duplicate_query.first():
            raise BusinessRuleViolation("Ja existe recibo com os mesmos dados principais para este cliente.")

    return customer, work_order, description


def _generate_receipt_number(db: Session, receipt_date: date) -> str:
    prefix = f"REC-{receipt_date.year}-"
    last_receipt = (
        db.query(Receipt)
        .filter(Receipt.numero.like(f"{prefix}%"))
        .order_by(Receipt.id.desc())
        .first()
    )
    sequence = 1
    if last_receipt and last_receipt.numero.startswith(prefix):
        try:
            sequence = int(last_receipt.numero.replace(prefix, "")) + 1
        except ValueError:
            sequence = 1

    candidate = f"{prefix}{sequence:06d}"
    while db.query(Receipt).filter(Receipt.numero == candidate).first():
        sequence += 1
        candidate = f"{prefix}{sequence:06d}"
    return candidate


def _log_receipt_history(
    db: Session,
    receipt: Receipt,
    action: str,
    details: Optional[str],
    *,
    current_user_id: Optional[int] = None,
) -> None:
    db.add(
        ReceiptHistory(
            recibo_id=receipt.id,
            usuario_id=current_user_id,
            acao=action,
            detalhes=details,
        )
    )


def _sync_receipt_finance_entry(db: Session, receipt: Receipt) -> None:
    entry = receipt.financeiro
    if not entry:
        entry = FinanceEntry(recibo_id=receipt.id)
        db.add(entry)
        receipt.financeiro = entry

    entry.tipo = "receita"
    entry.descricao = f"Recebimento do recibo {receipt.numero}"
    entry.valor = _money(receipt.valor)
    entry.valor_pago = Decimal("0.00")
    entry.vencimento = receipt.data_recebimento
    entry.data_pagamento = None
    entry.status = "pendente"
    entry.categoria = "Recibo"
    entry.fornecedor_nome = None
    entry.origem = "recibo"
    entry.referencia = receipt.numero
    entry.parcela_atual = 1
    entry.total_parcelas = 1
    entry.observacoes = receipt.descricao
    entry.cliente_id = receipt.cliente_id
    entry.os_id = receipt.os_id
    entry.nfe_id = None
    entry.recibo_id = receipt.id

    for movement in list(entry.movimentos_caixa):
        db.delete(movement)
    db.flush()
    _apply_finance_payment(db, entry, _money(receipt.valor), receipt.data_recebimento)


def _get_receipt_or_fail(db: Session, receipt_id: int, *, include_deleted: bool = False) -> Receipt:
    query = _receipt_query(db).filter(Receipt.id == receipt_id)
    if not include_deleted:
        query = query.filter(Receipt.deleted_at.is_(None))
    receipt = query.first()
    if not receipt:
        raise BusinessRuleViolation("Recibo nao encontrado.")
    return receipt


def list_receipts(db: Session) -> list[Receipt]:
    receipts = (
        _receipt_query(db)
        .filter(Receipt.deleted_at.is_(None))
        .order_by(Receipt.data_recebimento.desc(), Receipt.id.desc())
        .all()
    )
    return [_serialize_receipt(item) for item in receipts]


def get_receipt(db: Session, receipt_id: int) -> Receipt:
    return _serialize_receipt(_get_receipt_or_fail(db, receipt_id))


def preview_receipt(db: Session, payload: Union[ReceiptCreate, ReceiptUpdate]) -> ReceiptPreviewRead:
    customer, work_order, description = _validate_receipt_payload(db, payload, skip_duplicate_check=True)
    return _build_receipt_preview(
        customer=customer,
        payload=payload,
        work_order=work_order,
        description=description,
    )


def create_receipt(db: Session, payload: ReceiptCreate, *, current_user_id: Optional[int] = None) -> Receipt:
    customer, work_order, description = _validate_receipt_payload(db, payload)
    preview = _build_receipt_preview(
        customer=customer,
        payload=payload,
        work_order=work_order,
        description=description,
    )

    receipt = Receipt(
        numero=_generate_receipt_number(db, payload.data_recebimento),
        cliente_id=customer.id,
        os_id=work_order.id if work_order else None,
        valor=_money(payload.valor),
        forma_pagamento=payload.forma_pagamento.value,
        descricao=description,
        data_recebimento=payload.data_recebimento,
        valor_por_extenso=preview.valor_por_extenso,
        texto_formal=preview.texto_formal,
    )
    db.add(receipt)
    db.flush()
    _sync_receipt_finance_entry(db, receipt)
    _log_receipt_history(
        db,
        receipt,
        "criado",
        f"Recibo gerado para {customer.razao_social} no valor de {preview.valor_formatado}.",
        current_user_id=current_user_id,
    )
    db.commit()
    db.expire_all()
    return get_receipt(db, receipt.id)


def update_receipt(
    db: Session,
    receipt_id: int,
    payload: ReceiptUpdate,
    *,
    current_user_id: Optional[int] = None,
) -> Receipt:
    receipt = _get_receipt_or_fail(db, receipt_id)
    customer, work_order, description = _validate_receipt_payload(db, payload, current_receipt_id=receipt_id)
    preview = _build_receipt_preview(
        customer=customer,
        payload=payload,
        work_order=work_order,
        description=description,
    )

    receipt.cliente_id = customer.id
    receipt.os_id = work_order.id if work_order else None
    receipt.valor = _money(payload.valor)
    receipt.forma_pagamento = payload.forma_pagamento.value
    receipt.descricao = description
    receipt.data_recebimento = payload.data_recebimento
    receipt.valor_por_extenso = preview.valor_por_extenso
    receipt.texto_formal = preview.texto_formal

    _sync_receipt_finance_entry(db, receipt)
    _log_receipt_history(
        db,
        receipt,
        "atualizado",
        f"Recibo atualizado para {preview.valor_formatado} via {_receipt_payment_label(payload.forma_pagamento)}.",
        current_user_id=current_user_id,
    )
    db.commit()
    db.expire_all()
    return get_receipt(db, receipt.id)


def delete_receipt(db: Session, receipt_id: int, *, current_user_id: Optional[int] = None) -> None:
    receipt = _get_receipt_or_fail(db, receipt_id)
    if receipt.financeiro:
        db.delete(receipt.financeiro)
        db.flush()

    receipt.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    receipt.deleted_by_user_id = current_user_id
    _log_receipt_history(
        db,
        receipt,
        "excluido",
        f"Recibo {receipt.numero} removido do fluxo ativo.",
        current_user_id=current_user_id,
    )
    db.commit()


def generate_receipt_pdf(db: Session, receipt_id: int, *, current_user_id: Optional[int] = None) -> bytes:
    receipt = _get_receipt_or_fail(db, receipt_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    subtitle = f"Recibo {receipt.numero} | {_format_date_brl(receipt.data_recebimento)}"
    y = _draw_document_frame(pdf, "Recibo de pagamento", subtitle)

    y = _draw_section_title(pdf, y, "Dados principais")
    y = _draw_key_values(
        pdf,
        y,
        [
            ("Numero", receipt.numero),
            ("Cliente", receipt.cliente.razao_social),
            ("Documento", receipt.cliente.cpf_cnpj),
            ("Data do recebimento", _format_date_brl(receipt.data_recebimento)),
            ("Forma de pagamento", _receipt_payment_label(receipt.forma_pagamento)),
            ("Valor", _format_currency_brl(receipt.valor)),
            ("Valor por extenso", receipt.valor_por_extenso),
            ("OS vinculada", receipt.os_numero or "Nao vinculada"),
        ],
        value_width_chars=76,
    )

    y = _draw_section_title(pdf, y - 2 * mm, "Descricao")
    y = _draw_paragraph(pdf, y, receipt.descricao, width_chars=92)

    y = _draw_section_title(pdf, y - 2 * mm, "Declaracao formal")
    y = _draw_paragraph(pdf, y, receipt.texto_formal, width_chars=94)

    y = _draw_section_title(pdf, y - 2 * mm, "Emitente")
    y = _draw_bullets(pdf, y, _company_identification_lines(), width_chars=82)

    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, 24 * mm, "Assinatura do emitente: ______________________________")
    pdf.drawRightString(190 * mm, 24 * mm, "Assinatura do cliente: ______________________________")
    pdf.showPage()
    pdf.save()

    _log_receipt_history(
        db,
        receipt,
        "pdf_emitido",
        f"PDF do recibo {receipt.numero} gerado.",
        current_user_id=current_user_id,
    )
    db.commit()
    return buffer.getvalue()
