from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.schemas import (
    AppointmentCreate,
    AppointmentDashboardRead,
    AppointmentRead,
    AppointmentStatusUpdate,
    AppointmentUpdate,
)
from app.application.scheduling_services import (
    create_appointment,
    get_appointment,
    get_appointment_dashboard,
    list_appointments,
    sync_appointment_google_event,
    update_appointment,
    update_appointment_status,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/agendamentos", tags=["agendamentos"])


@router.get(
    "",
    response_model=List[AppointmentRead],
)
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> List[AppointmentRead]:
    return list_appointments(db)


@router.get(
    "/dashboard",
    response_model=AppointmentDashboardRead,
)
def get_appointments_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> AppointmentDashboardRead:
    return get_appointment_dashboard(db)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentRead,
)
def get_appointment_by_id(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> AppointmentRead:
    return get_appointment(db, appointment_id)


@router.post(
    "",
    response_model=AppointmentRead,
)
def post_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
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
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
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
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> AppointmentRead:
    return update_appointment_status(db, appointment_id, payload, current_user_id=current_user.id)


@router.post(
    "/{appointment_id}/sync-google",
    response_model=AppointmentRead,
)
def post_appointment_google_sync(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> AppointmentRead:
    return sync_appointment_google_event(db, appointment_id, current_user_id=current_user.id)
