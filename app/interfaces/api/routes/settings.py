from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.application.database_admin_service import (
    cleanup_operational_data,
    export_database_backup,
    restore_database_backup,
)
from app.application.schemas import (
    DatabaseCleanupRequest,
    DatabaseMaintenanceRead,
    SettingsCompanyRead,
    SystemSettingsRead,
    SystemSettingsUpdate,
)
from app.application.settings_service import (
    get_company_technical_asset_content,
    get_system_settings,
    save_company_signature_from_data_url,
    save_company_technical_asset,
    update_system_settings,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsRead)
def get_settings_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.view"])),
) -> SystemSettingsRead:
    return get_system_settings(db, current_user)


@router.put("", response_model=SystemSettingsRead)
def put_settings_view(
    payload: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> SystemSettingsRead:
    return update_system_settings(db, payload, current_user)


@router.post("/technical-documents/assets/{asset_kind}", response_model=SettingsCompanyRead)
async def upload_company_technical_asset_view(
    asset_kind: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> SettingsCompanyRead:
    content = await file.read()
    return save_company_technical_asset(
        db,
        current_user=current_user,
        asset_kind=asset_kind,
        filename=file.filename or asset_kind,
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )


@router.post("/technical-documents/signature/draw", response_model=SettingsCompanyRead)
def save_drawn_signature_view(
    data_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> SettingsCompanyRead:
    return save_company_signature_from_data_url(
        db,
        current_user=current_user,
        data_url=data_url,
    )


@router.get("/technical-documents/assets/{asset_kind}")
def get_company_technical_asset_view(
    asset_kind: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.view"])),
):
    filename, content_type, content = get_company_technical_asset_content(
        db,
        current_user=current_user,
        asset_kind=asset_kind,
    )
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


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
