from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import PestCreate, PestRead, PestUpdate
from app.application.services import create_pest, delete_pest, list_pests, update_pest
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/pragas", tags=["pragas"])


@router.get(
    "",
    response_model=List[PestRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_pests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> List[PestRead]:
    return list_pests(db, current_user=current_user)


@router.post(
    "",
    response_model=PestRead,
    status_code=status.HTTP_201_CREATED,
)
def post_pest(
    payload: PestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> PestRead:
    return create_pest(db, payload, current_user=current_user)


@router.put(
    "/{pest_id}",
    response_model=PestRead,
)
def put_pest(
    pest_id: int,
    payload: PestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> PestRead:
    return update_pest(db, pest_id, payload, current_user=current_user)


@router.delete(
    "/{pest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_pest(
    pest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> Response:
    delete_pest(db, pest_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
