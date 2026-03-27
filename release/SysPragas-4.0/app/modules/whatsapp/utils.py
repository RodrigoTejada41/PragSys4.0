from __future__ import annotations

from datetime import datetime
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


def build_appointment_whatsapp_message(appointment) -> str:
    customer_name = getattr(appointment, "cliente_nome", None) or appointment.cliente.razao_social
    technician_name = getattr(appointment, "tecnico_nome", None) or (appointment.tecnico.nome if appointment.tecnico else None)
    if not technician_name:
        raise BusinessRuleViolation("Defina o tecnico responsavel antes de enviar WhatsApp para este agendamento.")
    service_type = str(appointment.tipo_servico or "").strip()
    message_lines = [
        f"Ola, {customer_name}.",
        "Seu agendamento foi confirmado com sucesso.",
        f"Data: {format_brazilian_date(appointment.data_agendamento)}",
        f"Horario: {format_brazilian_time(appointment.hora_agendamento)}",
        f"Tecnico responsavel: {technician_name}",
    ]
    if service_type:
        message_lines.append(f"Servico: {service_type}")
    if getattr(appointment, "os_numero", None):
        message_lines.append(f"OS vinculada: {appointment.os_numero}")
    message_lines.append("Em caso de duvidas, responda esta mensagem ou entre em contato com a equipe.")
    return "\n".join(message_lines)


def compact_error_message(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def iso_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()
