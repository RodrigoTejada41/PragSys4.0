from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import UserCreate, UserRead, UserUpdate
from app.application.services import create_user, delete_user, list_users, update_user
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get(
    "",
    response_model=List[UserRead],
    dependencies=[Depends(require_roles(["master"]))],
)
def get_users(db: Session = Depends(get_db)) -> List[UserRead]:
    return list_users(db)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master"]))],
)
def post_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    return create_user(db, payload)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_roles(["master"]))],
)
def put_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserRead:
    return update_user(db, user_id, payload)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["master"]))],
)
def remove_user(user_id: int, db: Session = Depends(get_db)) -> Response:
    delete_user(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
