from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.application.database_admin_service import (
    cleanup_operational_data,
    export_database_backup,
    restore_database_backup,
)
from app.application.digital_certificate_service import (
    apply_certificate_company_data,
    get_digital_certificate,
    remove_digital_certificate,
    save_digital_certificate,
    test_stored_digital_certificate,
    validate_digital_certificate_upload,
)
from app.application.schemas import (
    DatabaseCleanupRequest,
    DatabaseMaintenanceRead,
    DigitalCertificateInfoRead,
    DigitalCertificateValidationRead,
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


@router.get("/digital-certificate", response_model=DigitalCertificateInfoRead)
def get_digital_certificate_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.view"])),
) -> DigitalCertificateInfoRead:
    return get_digital_certificate(db, current_user)


@router.post("/digital-certificate/validate", response_model=DigitalCertificateValidationRead)
async def validate_digital_certificate_view(
    file: UploadFile = File(...),
    password: str = Form(...),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DigitalCertificateValidationRead:
    _ = current_user
    content = await file.read()
    return validate_digital_certificate_upload(
        filename=file.filename or "certificado.pfx",
        content=content,
        password=password,
    )


@router.post("/digital-certificate", response_model=DigitalCertificateInfoRead)
async def save_digital_certificate_view(
    file: UploadFile = File(...),
    password: str = Form(...),
    apply_company_data: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DigitalCertificateInfoRead:
    content = await file.read()
    return save_digital_certificate(
        db,
        current_user=current_user,
        filename=file.filename or "certificado.pfx",
        content_type=file.content_type or "application/x-pkcs12",
        content=content,
        password=password,
        apply_company_data=apply_company_data,
    )


@router.post("/digital-certificate/test", response_model=DigitalCertificateValidationRead)
def test_digital_certificate_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DigitalCertificateValidationRead:
    return test_stored_digital_certificate(db, current_user)


@router.post("/digital-certificate/apply-company", response_model=DigitalCertificateInfoRead)
def apply_digital_certificate_company_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DigitalCertificateInfoRead:
    return apply_certificate_company_data(db, current_user=current_user)


@router.delete("/digital-certificate", response_model=DigitalCertificateInfoRead)
def delete_digital_certificate_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["settings.manage"])),
) -> DigitalCertificateInfoRead:
    return remove_digital_certificate(db, current_user)


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
