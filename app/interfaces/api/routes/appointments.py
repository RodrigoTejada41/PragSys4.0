from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.schemas import (
    AppointmentCreate,
    AppointmentDashboardRead,
    GoogleCalendarAppointmentSyncRead,
    AppointmentRead,
    AppointmentStatusUpdate,
    AppointmentUpdate,
)
from app.application.scheduling_services import (
    create_appointment,
    get_appointment,
    get_appointment_dashboard,
    list_appointments,
    reopen_appointment,
    update_appointment,
    update_appointment_status,
)
from app.application.google_calendar_service import sync_appointment_with_google_or_request_oauth
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/agendamentos", tags=["agendamentos"])


@router.get(
    "",
    response_model=List[AppointmentRead],
)
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.view"])),
) -> List[AppointmentRead]:
    return list_appointments(db)


@router.get(
    "/dashboard",
    response_model=AppointmentDashboardRead,
)
def get_appointments_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.view"])),
) -> AppointmentDashboardRead:
    return get_appointment_dashboard(db)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentRead,
)
def get_appointment_by_id(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.view"])),
) -> AppointmentRead:
    return get_appointment(db, appointment_id)


@router.post(
    "",
    response_model=AppointmentRead,
)
def post_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.manage"])),
) -> AppointmentRead:
    return create_appointment(db, payload, current_user_id=current_user.id)


@router.put(
    "/{appointment_id}",
    response_model=AppointmentRead,
)
def put_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.manage"])),
) -> AppointmentRead:
    return update_appointment(db, appointment_id, payload, current_user_id=current_user.id)


@router.post(
    "/{appointment_id}/status",
    response_model=AppointmentRead,
)
def post_appointment_status(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.manage"])),
) -> AppointmentRead:
    return update_appointment_status(db, appointment_id, payload, current_user_id=current_user.id)


@router.post(
    "/{appointment_id}/reabrir",
    response_model=AppointmentRead,
)
def post_appointment_reopen(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.manage"])),
) -> AppointmentRead:
    return reopen_appointment(db, appointment_id, current_user_id=current_user.id)


@router.post(
    "/{appointment_id}/sync-google",
    response_model=GoogleCalendarAppointmentSyncRead,
)
def post_appointment_google_sync(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["appointments.manage", "integrations.manage"])),
) -> GoogleCalendarAppointmentSyncRead:
    return GoogleCalendarAppointmentSyncRead(
        **sync_appointment_with_google_or_request_oauth(db, appointment_id, current_user.id)
    )
