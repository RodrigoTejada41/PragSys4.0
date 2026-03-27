from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.schemas import LoginRequest, TokenResponse, UserRead
from app.application.services import authenticate_user
from app.infrastructure.db import get_db
from app.interfaces.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = authenticate_user(db, payload.username, payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)) -> UserRead:
    return current_user
