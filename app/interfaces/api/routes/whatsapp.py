from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.schemas import AppointmentRead, WhatsAppConfigStatusRead, WhatsAppConnectionStatusRead
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles
from app.modules.whatsapp.service import (
    get_whatsapp_configuration_status,
    get_whatsapp_connection_status,
    send_appointment_whatsapp_message,
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get(
    "/configuracao",
    response_model=WhatsAppConfigStatusRead,
)
def get_whatsapp_configuration(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> WhatsAppConfigStatusRead:
    return WhatsAppConfigStatusRead(**get_whatsapp_configuration_status(db))


@router.get(
    "/status",
    response_model=WhatsAppConnectionStatusRead,
)
def get_whatsapp_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WhatsAppConnectionStatusRead:
    return WhatsAppConnectionStatusRead(**get_whatsapp_connection_status(db))


@router.post(
    "/agendamentos/{appointment_id}/enviar",
    response_model=AppointmentRead,
)
def post_appointment_whatsapp_send(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> AppointmentRead:
    return send_appointment_whatsapp_message(
        db,
        appointment_id,
        current_user_id=current_user.id,
        automatic=False,
        raise_on_error=True,
    )
