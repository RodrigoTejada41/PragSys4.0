from typing import Callable, Iterable, Optional

from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.application.services import ensure_license_allows_access, get_user_by_id
from app.core.exceptions import BusinessRuleViolation
from app.core.security import decode_access_token
from app.infrastructure.db import get_db
from app.infrastructure.models import User


def get_current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso nao informado.",
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        user = get_user_by_id(db, user_id)
        ensure_license_allows_access(db, user)
        return user
    except (KeyError, ValueError, BusinessRuleViolation):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado.",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado.",
        )


def get_current_company_id(current_user: User = Depends(get_current_user)) -> Optional[int]:
    return current_user.empresa_prestadora_id


def require_roles(allowed_roles: Iterable[str]) -> Callable:
    allowed = set(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissao para esta operacao.",
            )
        return current_user

    return dependency
