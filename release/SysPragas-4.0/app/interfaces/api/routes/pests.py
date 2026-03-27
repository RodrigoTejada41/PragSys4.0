from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import PestCreate, PestRead, PestUpdate
from app.application.services import create_pest, delete_pest, list_pests, update_pest
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/pragas", tags=["pragas"])


@router.get(
    "",
    response_model=List[PestRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_pests(db: Session = Depends(get_db)) -> List[PestRead]:
    return list_pests(db)


@router.post(
    "",
    response_model=PestRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def post_pest(payload: PestCreate, db: Session = Depends(get_db)) -> PestRead:
    return create_pest(db, payload)


@router.put(
    "/{pest_id}",
    response_model=PestRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def put_pest(pest_id: int, payload: PestUpdate, db: Session = Depends(get_db)) -> PestRead:
    return update_pest(db, pest_id, payload)


@router.delete(
    "/{pest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def remove_pest(pest_id: int, db: Session = Depends(get_db)) -> Response:
    delete_pest(db, pest_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
