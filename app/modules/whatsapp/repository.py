from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.infrastructure.models import AppointmentWhatsAppLog


def create_appointment_whatsapp_log(
    db: Session,
    *,
    appointment_id: int,
    user_id: Optional[int],
    provider: str,
    status: str,
    destination_phone: str,
    message: str,
    automatic: bool,
    error_message: Optional[str] = None,
    external_message_id: Optional[str] = None,
    external_response: Optional[str] = None,
) -> AppointmentWhatsAppLog:
    log_entry = AppointmentWhatsAppLog(
        agendamento_id=appointment_id,
        usuario_id=user_id,
        provider=provider,
        status=status,
        destino_telefone=destination_phone,
        mensagem=message,
        automatico=automatic,
        erro=error_message,
        external_message_id=external_message_id,
        resposta_externa=external_response,
    )
    db.add(log_entry)
    db.flush()
    return log_entry

