from __future__ import annotations

from datetime import datetime
from string import Formatter
from typing import Optional

from app.core.exceptions import BusinessRuleViolation


def digits_only(value: Optional[str]) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def normalize_whatsapp_phone(value: Optional[str]) -> str:
    digits = digits_only(value)
    if len(digits) in {10, 11}:
        digits = f"55{digits}"
    if len(digits) not in {12, 13} or not digits.startswith("55"):
        raise BusinessRuleViolation("Telefone do cliente invalido para envio via WhatsApp.")
    return digits


def format_brazilian_date(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value or "")


def format_brazilian_time(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value or "")[:5]


DEFAULT_APPOINTMENT_WHATSAPP_TEMPLATE = """Ola {nome_cliente}, tudo bem?

Seu agendamento foi confirmado com sucesso!

Data: {data}
Hora: {hora}
Tecnico: {tecnico}
Servico: {servico}

Qualquer duvida estamos a disposicao."""


def _safe_format_template(template: str, values: dict[str, str]) -> str:
    formatter = Formatter()
    parts: list[str] = []
    for literal_text, field_name, format_spec, conversion in formatter.parse(template):
        parts.append(literal_text)
        if field_name is None:
            continue
        replacement = values.get(field_name, "{" + field_name + "}")
        parts.append(replacement)
    return "".join(parts)


def build_appointment_whatsapp_message(appointment, template: Optional[str] = None) -> str:
    customer_name = getattr(appointment, "cliente_nome", None) or appointment.cliente.razao_social
    technician_name = getattr(appointment, "tecnico_nome", None) or (appointment.tecnico.nome if appointment.tecnico else None)
    if not technician_name:
        raise BusinessRuleViolation("Defina o tecnico responsavel antes de enviar WhatsApp para este agendamento.")
    service_type = str(appointment.tipo_servico or "").strip()
    selected_template = str(template or DEFAULT_APPOINTMENT_WHATSAPP_TEMPLATE).strip() or DEFAULT_APPOINTMENT_WHATSAPP_TEMPLATE
    values = {
        "nome_cliente": customer_name,
        "data": format_brazilian_date(appointment.data_agendamento),
        "hora": format_brazilian_time(appointment.hora_agendamento),
        "tecnico": technician_name,
        "servico": service_type or "-",
        "telefone": digits_only(getattr(appointment, "telefone", None)),
        "os_numero": getattr(appointment, "os_numero", None) or "",
    }
    return _safe_format_template(selected_template, values)


def compact_error_message(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def iso_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()
