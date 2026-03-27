from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import UserCreate, UserRead, UserUpdate
from app.application.services import create_user, delete_user, list_users, update_user
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get(
    "",
    response_model=List[UserRead],
)
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["users.manage"])),
) -> List[UserRead]:
    return list_users(db, current_user=current_user)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def post_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["users.manage"])),
) -> UserRead:
    return create_user(db, payload, current_user=current_user)


@router.put(
    "/{user_id}",
    response_model=UserRead,
)
def put_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["users.manage"])),
) -> UserRead:
    return update_user(db, user_id, payload, current_user=current_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["users.manage", "records.delete"])),
) -> Response:
    delete_user(db, user_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
