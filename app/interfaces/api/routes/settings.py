from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.schemas import SystemSettingsRead, SystemSettingsUpdate
from app.application.settings_service import get_system_settings, update_system_settings
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsRead)
def get_settings_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> SystemSettingsRead:
    return get_system_settings(db)


@router.put("", response_model=SystemSettingsRead)
def put_settings_view(
    payload: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> SystemSettingsRead:
    return update_system_settings(db, payload, current_user)
