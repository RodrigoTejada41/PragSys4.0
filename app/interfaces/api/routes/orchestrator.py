from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.application.central_orchestrator_service import (
    audit_service_command,
    create_managed_service,
    get_managed_service,
    get_service_history,
    get_service_health,
    list_managed_services,
    list_service_dependencies,
    run_orchestrator_diagnostics,
    run_recovery_pass,
)
from app.application.schemas import (
    ManagedServiceCreate,
    ManagedServiceRead,
    ServiceCommandResult,
    ServiceDependencyRead,
    ServiceDiagnosticReport,
    ServiceHistoryRead,
    ServiceHealthRead,
    ServiceRecoveryReport,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get(
    "/services",
    response_model=List[ManagedServiceRead],
)
def get_services(
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.view"])),
) -> list[ManagedServiceRead]:
    return list_managed_services(db)


@router.post(
    "/services",
    response_model=ManagedServiceRead,
    status_code=status.HTTP_201_CREATED,
)
def post_service(
    payload: ManagedServiceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.manage"])),
) -> ManagedServiceRead:
    return create_managed_service(db, payload)


@router.get(
    "/services/{service_id}",
    response_model=ManagedServiceRead,
)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.view"])),
) -> ManagedServiceRead:
    return get_managed_service(db, service_id)


@router.get(
    "/services/{service_id}/health",
    response_model=ServiceHealthRead,
)
def get_health(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.view"])),
) -> ServiceHealthRead:
    return get_service_health(db, service_id)


@router.get(
    "/services/{service_id}/history",
    response_model=ServiceHistoryRead,
)
def get_history(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.view"])),
) -> ServiceHistoryRead:
    return get_service_history(db, service_id)


@router.post(
    "/services/{service_id}/start",
    response_model=ServiceCommandResult,
)
def start_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["orchestrator.command"])),
) -> ServiceCommandResult:
    return audit_service_command(db, service_id, "start", current_user)


@router.post(
    "/services/{service_id}/stop",
    response_model=ServiceCommandResult,
)
def stop_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["orchestrator.command"])),
) -> ServiceCommandResult:
    return audit_service_command(db, service_id, "stop", current_user)


@router.post(
    "/services/{service_id}/restart",
    response_model=ServiceCommandResult,
)
def restart_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["orchestrator.command"])),
) -> ServiceCommandResult:
    return audit_service_command(db, service_id, "restart", current_user)


@router.post(
    "/services/{service_id}/reload",
    response_model=ServiceCommandResult,
)
def reload_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["orchestrator.command"])),
) -> ServiceCommandResult:
    return audit_service_command(db, service_id, "reload", current_user)


@router.get(
    "/dependencies",
    response_model=List[ServiceDependencyRead],
)
def get_dependencies(
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.view"])),
) -> list[ServiceDependencyRead]:
    return list_service_dependencies(db)


@router.post(
    "/diagnostics",
    response_model=ServiceDiagnosticReport,
)
def post_diagnostics(
    db: Session = Depends(get_db),
    _: User = Depends(require_access(["master", "admin"], ["orchestrator.view"])),
) -> ServiceDiagnosticReport:
    return run_orchestrator_diagnostics(db)


@router.post(
    "/recovery/run",
    response_model=ServiceRecoveryReport,
)
def post_recovery_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["orchestrator.command"])),
) -> ServiceRecoveryReport:
    return run_recovery_pass(db, current_user)
