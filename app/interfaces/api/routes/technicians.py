from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import TechnicianCreate, TechnicianRead, TechnicianUpdate
from app.application.services import (
    create_technician,
    delete_technician,
    list_technicians,
    update_technician,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/tecnicos", tags=["tecnicos"])


@router.get(
    "",
    response_model=List[TechnicianRead],
    dependencies=[Depends(require_access(["master", "admin", "operador"], ["work_orders.view"]))],
)
def get_technicians(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["work_orders.view"])),
) -> List[TechnicianRead]:
    return list_technicians(db, current_user=current_user)


@router.post(
    "",
    response_model=TechnicianRead,
    status_code=status.HTTP_201_CREATED,
)
def post_technician(
    payload: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["work_orders.manage"])),
) -> TechnicianRead:
    return create_technician(db, payload, current_user=current_user)


@router.put(
    "/{technician_id}",
    response_model=TechnicianRead,
)
def put_technician(
    technician_id: int,
    payload: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["work_orders.manage"])),
) -> TechnicianRead:
    return update_technician(db, technician_id, payload, current_user=current_user)


@router.delete(
    "/{technician_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["work_orders.manage", "records.delete"])),
) -> Response:
    delete_technician(db, technician_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
