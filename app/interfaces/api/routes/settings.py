from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.application.database_admin_service import (
    cleanup_operational_data,
    export_database_backup,
    restore_database_backup,
)
from app.application.schemas import (
    DatabaseCleanupRequest,
    DatabaseMaintenanceRead,
    SystemSettingsRead,
    SystemSettingsUpdate,
)
from app.application.settings_service import get_system_settings, update_system_settings
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsRead)
def get_settings_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.view"])),
) -> SystemSettingsRead:
    return get_system_settings(db)


@router.put("", response_model=SystemSettingsRead)
def put_settings_view(
    payload: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> SystemSettingsRead:
    return update_system_settings(db, payload, current_user)


@router.get("/database/backup")
def download_database_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
):
    backup_path = export_database_backup()
    background_tasks.add_task(_cleanup_temp_backup, backup_path)
    return FileResponse(
        path=backup_path,
        media_type="application/octet-stream",
        filename=backup_path.name,
    )


@router.post("/database/restore", response_model=DatabaseMaintenanceRead)
async def restore_database_view(
    file: UploadFile = File(...),
    confirmation: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DatabaseMaintenanceRead:
    file_bytes = await file.read()
    return restore_database_backup(
        db,
        backup_bytes=file_bytes,
        original_filename=file.filename or "backup.db",
        confirmation=confirmation,
    )


@router.post("/database/cleanup", response_model=DatabaseMaintenanceRead)
def cleanup_database_view(
    payload: DatabaseCleanupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DatabaseMaintenanceRead:
    return cleanup_operational_data(
        db,
        confirmation=payload.confirmation,
        include_finance=payload.include_finance,
    )


def _cleanup_temp_backup(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except PermissionError:
        pass
