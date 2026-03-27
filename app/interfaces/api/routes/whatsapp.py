from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.schemas import (
    AppointmentRead,
    WhatsAppConfigStatusRead,
    WhatsAppConnectionStatusRead,
    WhatsAppQrSessionRead,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access
from app.modules.whatsapp.service import (
    get_whatsapp_configuration_status,
    get_whatsapp_connection_status,
    logout_whatsapp_session,
    request_whatsapp_qr_session,
    send_appointment_whatsapp_message,
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get(
    "/configuracao",
    response_model=WhatsAppConfigStatusRead,
)
def get_whatsapp_configuration(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["integrations.manage"])),
) -> WhatsAppConfigStatusRead:
    return WhatsAppConfigStatusRead(**get_whatsapp_configuration_status(db))


@router.get(
    "/status",
    response_model=WhatsAppConnectionStatusRead,
)
def get_whatsapp_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.view"])),
) -> WhatsAppConnectionStatusRead:
    return WhatsAppConnectionStatusRead(**get_whatsapp_connection_status(db))


@router.post(
    "/sessao/qr",
    response_model=WhatsAppQrSessionRead,
)
def post_whatsapp_session_qr(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["integrations.manage"])),
) -> WhatsAppQrSessionRead:
    return WhatsAppQrSessionRead(**request_whatsapp_qr_session(db))


@router.post(
    "/sessao/logout",
    response_model=WhatsAppConnectionStatusRead,
)
def post_whatsapp_session_logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["integrations.manage"])),
) -> WhatsAppConnectionStatusRead:
    return WhatsAppConnectionStatusRead(**logout_whatsapp_session(db))


@router.post(
    "/agendamentos/{appointment_id}/enviar",
    response_model=AppointmentRead,
)
def post_appointment_whatsapp_send(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.manage"])),
) -> AppointmentRead:
    return send_appointment_whatsapp_message(
        db,
        appointment_id,
        current_user_id=current_user.id,
        automatic=False,
        raise_on_error=True,
    )
