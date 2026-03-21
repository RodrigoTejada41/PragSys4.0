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
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/tecnicos", tags=["tecnicos"])


@router.get(
    "",
    response_model=List[TechnicianRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_technicians(db: Session = Depends(get_db)) -> List[TechnicianRead]:
    return list_technicians(db)


@router.post(
    "",
    response_model=TechnicianRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def post_technician(payload: TechnicianCreate, db: Session = Depends(get_db)) -> TechnicianRead:
    return create_technician(db, payload)


@router.put(
    "/{technician_id}",
    response_model=TechnicianRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def put_technician(
    technician_id: int,
    payload: TechnicianUpdate,
    db: Session = Depends(get_db),
) -> TechnicianRead:
    return update_technician(db, technician_id, payload)


@router.delete(
    "/{technician_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def remove_technician(technician_id: int, db: Session = Depends(get_db)) -> Response:
    delete_technician(db, technician_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
