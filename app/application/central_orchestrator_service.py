from __future__ import annotations

from datetime import datetime
import subprocess
from time import perf_counter
from typing import Any, Iterable

import httpx
from sqlalchemy.orm import Session

from app.application.schemas import (
    ManagedServiceCreate,
    ManagedServiceRead,
    ServiceCommandResult,
    ServiceDependencyRead,
    ServiceDiagnosticIssue,
    ServiceDiagnosticReport,
    ServiceHistoryRead,
    ServiceHealthRead,
    ServiceRecoveryActionRead,
    ServiceRecoveryReport,
)
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import ManagedServiceStatus, ServiceRecoveryPolicy
from app.infrastructure.models import ManagedService, ServiceCommandAudit, ServiceDependency, ServiceHealthCheck, User

LOCAL_COMMAND_ALLOWLIST: dict[tuple[str, str], list[str]] = {}


def list_managed_services(db: Session) -> list[ManagedServiceRead]:
    services = db.query(ManagedService).order_by(ManagedService.startup_order, ManagedService.name).all()
    return [_to_service_read(service) for service in services]


def create_managed_service(db: Session, payload: ManagedServiceCreate) -> ManagedServiceRead:
    existing = db.query(ManagedService).filter(ManagedService.name == payload.name).first()
    if existing:
        raise BusinessRuleViolation("Servico ja cadastrado no orquestrador.")

    dependency_names = _normalized_names(payload.dependencies)
    dependencies = _load_dependencies(db, dependency_names)
    if payload.name in dependency_names:
        raise BusinessRuleViolation("Servico nao pode depender dele mesmo.")

    service = ManagedService(
        name=payload.name,
        display_name=payload.display_name,
        service_type=payload.service_type.value,
        executor_type=payload.executor_type.value,
        base_url=payload.base_url,
        health_url=payload.health_url,
        port=payload.port,
        startup_order=payload.startup_order,
        shutdown_order=payload.shutdown_order,
        startup_timeout_seconds=payload.startup_timeout_seconds,
        response_timeout_seconds=payload.response_timeout_seconds,
        max_restart_attempts=payload.max_restart_attempts,
        recovery_policy=payload.recovery_policy.value,
        status=ManagedServiceStatus.REGISTERED.value,
    )
    db.add(service)
    db.flush()
    for dependency in dependencies:
        db.add(ServiceDependency(service_id=service.id, dependency_id=dependency.id))
    db.commit()
    return _get_service_read(db, service.id)


def get_managed_service(db: Session, service_id: int) -> ManagedServiceRead:
    return _get_service_read(db, service_id)


def get_service_health(db: Session, service_id: int) -> ServiceHealthRead:
    service = _get_service(db, service_id)
    if not service.health_url:
        health = _persist_health(
            db,
            service,
            {
                "status": "unhealthy",
                "last_error": "Servico sem health_url configurado.",
                "checked_at": datetime.now(),
            },
        )
        return _to_health_read(health)

    try:
        payload = fetch_service_health(
            health_url=service.health_url,
            timeout_seconds=service.response_timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001 - health check must capture connector failures
        payload = {
            "status": "unhealthy",
            "last_error": str(exc),
            "checked_at": datetime.now(),
        }
    health = _persist_health(db, service, payload)
    return _to_health_read(health)


def fetch_service_health(*, health_url: str, timeout_seconds: int) -> dict[str, Any]:
    started = perf_counter()
    response = httpx.get(health_url, timeout=timeout_seconds)
    response.raise_for_status()
    elapsed_ms = int((perf_counter() - started) * 1000)
    payload = response.json() if response.content else {}
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("response_time_ms", elapsed_ms)
    payload.setdefault("checked_at", datetime.now())
    return payload


def list_service_dependencies(db: Session) -> list[ServiceDependencyRead]:
    rows = db.query(ServiceDependency).join(ServiceDependency.service).all()
    return [
        ServiceDependencyRead(service=row.service.name, depends_on=row.dependency.name)
        for row in rows
    ]


def run_orchestrator_diagnostics(db: Session) -> ServiceDiagnosticReport:
    services = db.query(ManagedService).order_by(ManagedService.name).all()
    issues: list[ServiceDiagnosticIssue] = []
    ports: dict[int, list[ManagedService]] = {}

    for service in services:
        if not service.health_url:
            issues.append(
                ServiceDiagnosticIssue(
                    service=service.name,
                    code="missing_health_url",
                    severity="warning",
                    message="Servico sem endpoint de health check configurado.",
                )
            )
        if service.port is not None:
            ports.setdefault(service.port, []).append(service)
        for dependency in service.dependencies:
            if dependency.dependency is None:
                issues.append(
                    ServiceDiagnosticIssue(
                        service=service.name,
                        code="missing_dependency",
                        severity="error",
                        message="Servico possui dependencia nao resolvida.",
                    )
                )

    for port, port_services in ports.items():
        if len(port_services) <= 1:
            continue
        for service in port_services:
            issues.append(
                ServiceDiagnosticIssue(
                    service=service.name,
                    code="duplicate_port",
                    severity="error",
                    message=f"Porta {port} esta configurada em mais de um servico.",
                )
            )

    status = "ok"
    if any(issue.severity == "error" for issue in issues):
        status = "warning"
    elif issues:
        status = "warning"

    return ServiceDiagnosticReport(
        status=status,
        service_count=len(services),
        issue_count=len(issues),
        issues=issues,
    )


def get_service_history(db: Session, service_id: int) -> ServiceHistoryRead:
    service = _get_service(db, service_id)
    health_checks = (
        db.query(ServiceHealthCheck)
        .filter(ServiceHealthCheck.service_id == service.id)
        .order_by(ServiceHealthCheck.checked_at.desc(), ServiceHealthCheck.id.desc())
        .limit(50)
        .all()
    )
    commands = (
        db.query(ServiceCommandAudit)
        .filter(ServiceCommandAudit.service_id == service.id)
        .order_by(ServiceCommandAudit.created_at.desc(), ServiceCommandAudit.id.desc())
        .limit(50)
        .all()
    )
    return ServiceHistoryRead(
        service_id=service.id,
        health_checks=[_to_health_read(health) for health in health_checks],
        commands=[
            {
                "command": command.command,
                "status": command.status,
                "detail": command.detail,
                "created_at": command.created_at,
            }
            for command in commands
        ],
    )


def run_recovery_pass(db: Session, current_user: User) -> ServiceRecoveryReport:
    candidates = (
        db.query(ManagedService)
        .filter(
            ManagedService.recovery_policy == ServiceRecoveryPolicy.RESTART_ON_FAILURE.value,
            ManagedService.status.in_([ManagedServiceStatus.UNHEALTHY.value, ManagedServiceStatus.DEGRADED.value]),
        )
        .order_by(ManagedService.startup_order, ManagedService.name)
        .all()
    )
    actions: list[ServiceRecoveryActionRead] = []
    for service in candidates:
        attempts_used = _restart_attempt_count(db, service.id)
        max_attempts = service.max_restart_attempts
        if attempts_used >= max_attempts:
            actions.append(
                ServiceRecoveryActionRead(
                    service_id=service.id,
                    service=service.name,
                    action="restart",
                    status="limit_exhausted",
                    attempts_used=attempts_used,
                    max_attempts=max_attempts,
                    message="Limite de tentativas de recuperacao atingido.",
                )
            )
            continue

        result = audit_service_command(db, service.id, "restart", current_user)
        actions.append(
            ServiceRecoveryActionRead(
                service_id=service.id,
                service=service.name,
                action=result.command,
                status=result.status,
                attempts_used=attempts_used + 1,
                max_attempts=max_attempts,
                message="Restart auditado para recuperacao automatica.",
            )
        )

    status = "ok"
    if any(action.status == "accepted" for action in actions):
        status = "actions_taken"
    if actions and all(action.status == "limit_exhausted" for action in actions):
        status = "blocked"
    return ServiceRecoveryReport(status=status, action_count=len(actions), actions=actions)


def audit_service_command(db: Session, service_id: int, command: str, current_user: User) -> ServiceCommandResult:
    service = _get_service(db, service_id)
    if service.executor_type == "local_windows":
        return _execute_allowlisted_local_command(db, service, command, current_user)

    audit = ServiceCommandAudit(
        service_id=service.id,
        command=command,
        status="accepted",
        detail="Comando registrado para executor externo.",
        requested_by_user_id=current_user.id,
    )
    db.add(audit)
    db.commit()
    return ServiceCommandResult(
        service_id=service.id,
        command=command,
        status="accepted",
        message="Comando registrado e auditado.",
    )


def _execute_allowlisted_local_command(
    db: Session,
    service: ManagedService,
    command: str,
    current_user: User,
) -> ServiceCommandResult:
    argv = LOCAL_COMMAND_ALLOWLIST.get((service.name, command))
    if not argv:
        detail = "Comando local bloqueado: allowlist nao configurada."
        _record_command_audit(db, service, command, "blocked", detail, current_user)
        return ServiceCommandResult(
            service_id=service.id,
            command=command,
            status="blocked",
            message=detail,
        )

    completed = subprocess.run(  # noqa: S603 - argv vem de allowlist interna, sem shell.
        argv,
        capture_output=True,
        text=True,
        timeout=service.startup_timeout_seconds,
        shell=False,
    )
    output = (completed.stdout or completed.stderr or "").strip()
    status = "executed" if completed.returncode == 0 else "failed"
    detail = output[:500] if output else f"Processo finalizado com codigo {completed.returncode}."
    _record_command_audit(db, service, command, status, detail, current_user)
    return ServiceCommandResult(
        service_id=service.id,
        command=command,
        status=status,
        message=detail,
    )


def _record_command_audit(
    db: Session,
    service: ManagedService,
    command: str,
    status: str,
    detail: str,
    current_user: User,
) -> None:
    audit = ServiceCommandAudit(
        service_id=service.id,
        command=command,
        status=status,
        detail=detail,
        requested_by_user_id=current_user.id,
    )
    db.add(audit)
    db.commit()


def _restart_attempt_count(db: Session, service_id: int) -> int:
    return (
        db.query(ServiceCommandAudit)
        .filter(
            ServiceCommandAudit.service_id == service_id,
            ServiceCommandAudit.command == "restart",
            ServiceCommandAudit.status == "accepted",
        )
        .count()
    )


def _load_dependencies(db: Session, names: Iterable[str]) -> list[ManagedService]:
    normalized = list(names)
    if not normalized:
        return []
    dependencies = db.query(ManagedService).filter(ManagedService.name.in_(normalized)).all()
    found = {dependency.name for dependency in dependencies}
    missing = [name for name in normalized if name not in found]
    if missing:
        raise BusinessRuleViolation(f"Dependencia nao cadastrada: {', '.join(missing)}.")
    return dependencies


def _normalized_names(names: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for name in names:
        value = str(name or "").strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _get_service(db: Session, service_id: int) -> ManagedService:
    service = db.get(ManagedService, service_id)
    if not service:
        raise BusinessRuleViolation("Servico nao encontrado no orquestrador.")
    return service


def _get_service_read(db: Session, service_id: int) -> ManagedServiceRead:
    return _to_service_read(_get_service(db, service_id))


def _to_service_read(service: ManagedService) -> ManagedServiceRead:
    return ManagedServiceRead(
        id=service.id,
        name=service.name,
        display_name=service.display_name,
        service_type=service.service_type,
        executor_type=service.executor_type,
        base_url=service.base_url,
        health_url=service.health_url,
        port=service.port,
        startup_order=service.startup_order,
        shutdown_order=service.shutdown_order,
        startup_timeout_seconds=service.startup_timeout_seconds,
        response_timeout_seconds=service.response_timeout_seconds,
        max_restart_attempts=service.max_restart_attempts,
        recovery_policy=service.recovery_policy,
        status=service.status,
        dependencies=[dependency.dependency.name for dependency in service.dependencies],
        last_health_at=service.last_health_at,
        last_error=service.last_error,
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


def _persist_health(db: Session, service: ManagedService, payload: dict[str, Any]) -> ServiceHealthCheck:
    status = _normalize_health_status(str(payload.get("status") or "unhealthy"))
    checked_at = payload.get("checked_at")
    if not isinstance(checked_at, datetime):
        checked_at = datetime.now()
    health = ServiceHealthCheck(
        service_id=service.id,
        status=status,
        response_time_ms=payload.get("response_time_ms"),
        version=payload.get("version"),
        cpu_percent=payload.get("cpu_percent"),
        memory_percent=payload.get("memory_percent"),
        disk_percent=payload.get("disk_percent"),
        active_connections=payload.get("active_connections"),
        last_error=payload.get("last_error"),
        uptime_seconds=payload.get("uptime_seconds"),
        checked_at=checked_at,
    )
    service.status = status
    service.last_health_at = checked_at
    service.last_error = payload.get("last_error")
    db.add(health)
    db.add(service)
    db.commit()
    db.refresh(health)
    return health


def _normalize_health_status(status: str) -> str:
    normalized = status.lower().strip()
    if normalized in {"ok", "healthy", "up"}:
        return ManagedServiceStatus.HEALTHY.value
    if normalized in {"degraded", "warning"}:
        return ManagedServiceStatus.DEGRADED.value
    return ManagedServiceStatus.UNHEALTHY.value


def _to_health_read(health: ServiceHealthCheck) -> ServiceHealthRead:
    return ServiceHealthRead(
        service_id=health.service_id,
        status=health.status,
        response_time_ms=health.response_time_ms,
        version=health.version,
        cpu_percent=float(health.cpu_percent) if health.cpu_percent is not None else None,
        memory_percent=float(health.memory_percent) if health.memory_percent is not None else None,
        disk_percent=float(health.disk_percent) if health.disk_percent is not None else None,
        active_connections=health.active_connections,
        last_error=health.last_error,
        uptime_seconds=health.uptime_seconds,
        checked_at=health.checked_at,
    )
