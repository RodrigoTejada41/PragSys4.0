from datetime import datetime
import sys

from app.infrastructure.db import get_session_local


def _service_payload(name: str, **overrides):
    payload = {
        "name": name,
        "display_name": name.replace("-", " ").title(),
        "service_type": "api",
        "executor_type": "external",
        "base_url": f"http://{name}.local",
        "health_url": f"http://{name}.local/health",
        "port": 8000,
        "startup_order": 10,
        "shutdown_order": 10,
        "startup_timeout_seconds": 30,
        "response_timeout_seconds": 5,
        "max_restart_attempts": 2,
        "recovery_policy": "manual",
        "dependencies": [],
    }
    payload.update(overrides)
    return payload


def test_orchestrator_registers_service_with_dependencies(client, auth_headers):
    database = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("database-local", service_type="database", port=None, health_url=None),
    )
    assert database.status_code == 201, database.text

    crm = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-crm", dependencies=["database-local"]),
    )
    assert crm.status_code == 201, crm.text
    crm_payload = crm.json()
    assert crm_payload["name"] == "api-crm"
    assert crm_payload["dependencies"] == ["database-local"]
    assert crm_payload["status"] == "registered"

    dependencies = client.get("/api/v1/orchestrator/dependencies", headers=auth_headers)
    assert dependencies.status_code == 200
    assert {"service": "api-crm", "depends_on": "database-local"} in dependencies.json()


def test_orchestrator_blocks_admin_without_permission(client, auth_headers):
    company = client.post(
        "/api/v1/empresas-prestadoras",
        headers=auth_headers,
        json={
            "razao_social": "Orchestrator RBAC Ltda",
            "nome_fantasia": "Orchestrator RBAC",
            "cnpj": "91919191000191",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "is_active": True,
            "is_provider": True,
            "usuarios_vinculados_ids": [],
        },
    )
    assert company.status_code == 201, company.text

    license_response = client.post(
        "/api/v1/licencas",
        headers=auth_headers,
        json={
            "descricao": "Licenca Orchestrator RBAC",
            "start_date": "2026-07-09",
            "end_date": "2027-07-09",
            "max_users": 10,
            "status": "ativa",
            "empresa_prestadora_id": company.json()["id"],
        },
    )
    assert license_response.status_code == 201, license_response.text

    user = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": "Admin Sem Orchestrator",
            "username": "admin_sem_orchestrator",
            "password": "senha123",
            "role": "admin",
            "is_active": True,
            "empresa_prestadora_id": company.json()["id"],
            "permissions": {"orchestrator.view": False, "orchestrator.manage": False},
        },
    )
    assert user.status_code == 201, user.text

    login = client.post("/api/v1/auth/login", json={"username": "admin_sem_orchestrator", "password": "senha123"})
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/v1/orchestrator/services", headers=headers)
    assert response.status_code == 403


def test_orchestrator_health_check_persists_history(client, auth_headers, monkeypatch):
    service = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-pdv", port=8010),
    )
    assert service.status_code == 201, service.text

    def fake_fetch_health(*, health_url: str, timeout_seconds: int):
        assert health_url == "http://api-pdv.local/health"
        assert timeout_seconds == 5
        return {
            "status": "ok",
            "response_time_ms": 12,
            "version": "4.1.0",
            "cpu_percent": 3.5,
            "memory_percent": 22.1,
            "disk_percent": 40.0,
            "active_connections": 2,
            "last_error": None,
            "uptime_seconds": 3600,
            "checked_at": datetime(2026, 7, 9, 12, 0, 0),
        }

    monkeypatch.setattr("app.application.central_orchestrator_service.fetch_service_health", fake_fetch_health)

    response = client.get(f"/api/v1/orchestrator/services/{service.json()['id']}/health", headers=auth_headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["response_time_ms"] == 12
    assert payload["version"] == "4.1.0"

    session = get_session_local()()
    try:
        from app.infrastructure.models import ServiceHealthCheck

        rows = session.query(ServiceHealthCheck).filter(ServiceHealthCheck.service_id == service.json()["id"]).all()
        assert len(rows) == 1
        assert rows[0].status == "healthy"
    finally:
        session.close()


def test_orchestrator_reload_command_is_audited(client, auth_headers):
    service = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-financeiro", port=8020),
    )
    assert service.status_code == 201, service.text

    response = client.post(f"/api/v1/orchestrator/services/{service.json()['id']}/reload", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "accepted"

    session = get_session_local()()
    try:
        from app.infrastructure.models import ServiceCommandAudit

        audits = session.query(ServiceCommandAudit).filter(ServiceCommandAudit.service_id == service.json()["id"]).all()
        assert len(audits) == 1
        assert audits[0].command == "reload"
        assert audits[0].status == "accepted"
    finally:
        session.close()


def test_orchestrator_lifecycle_commands_are_audited_without_process_execution(client, auth_headers):
    service = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-cozinha", port=8030),
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]

    for command in ("start", "stop", "restart"):
        response = client.post(f"/api/v1/orchestrator/services/{service_id}/{command}", headers=auth_headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["command"] == command
        assert payload["status"] == "accepted"
        assert payload["audited"] is True

    session = get_session_local()()
    try:
        from app.infrastructure.models import ServiceCommandAudit

        audits = (
            session.query(ServiceCommandAudit)
            .filter(ServiceCommandAudit.service_id == service_id)
            .order_by(ServiceCommandAudit.id)
            .all()
        )
        assert [audit.command for audit in audits] == ["start", "stop", "restart"]
        assert {audit.status for audit in audits} == {"accepted"}
    finally:
        session.close()


def test_orchestrator_diagnostics_reports_port_conflicts_and_missing_health_url(client, auth_headers):
    database = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("database-diagnostics", service_type="database", port=None, health_url=None),
    )
    assert database.status_code == 201, database.text

    first_api = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-diagnostics-a", port=8040, dependencies=["database-diagnostics"]),
    )
    assert first_api.status_code == 201, first_api.text

    second_api = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-diagnostics-b", port=8040, dependencies=["database-diagnostics"]),
    )
    assert second_api.status_code == 201, second_api.text

    response = client.post("/api/v1/orchestrator/diagnostics", headers=auth_headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["service_count"] == 3
    assert payload["issue_count"] == 3
    assert payload["status"] == "warning"
    issues = {(issue["service"], issue["code"]) for issue in payload["issues"]}
    assert ("api-diagnostics-a", "duplicate_port") in issues
    assert ("api-diagnostics-b", "duplicate_port") in issues
    assert ("database-diagnostics", "missing_health_url") in issues
    assert all(issue["code"] != "missing_dependency" for issue in payload["issues"])


def test_orchestrator_service_detail_and_history_expose_health_and_commands(client, auth_headers, monkeypatch):
    service = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload("api-history", port=8050),
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]

    def fake_fetch_health(*, health_url: str, timeout_seconds: int):
        return {
            "status": "ok",
            "response_time_ms": 9,
            "version": "4.1.1",
            "checked_at": datetime(2026, 7, 9, 13, 0, 0),
        }

    monkeypatch.setattr("app.application.central_orchestrator_service.fetch_service_health", fake_fetch_health)

    health = client.get(f"/api/v1/orchestrator/services/{service_id}/health", headers=auth_headers)
    assert health.status_code == 200, health.text

    command = client.post(f"/api/v1/orchestrator/services/{service_id}/restart", headers=auth_headers)
    assert command.status_code == 200, command.text

    detail = client.get(f"/api/v1/orchestrator/services/{service_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["name"] == "api-history"
    assert detail.json()["status"] == "healthy"

    history = client.get(f"/api/v1/orchestrator/services/{service_id}/history", headers=auth_headers)
    assert history.status_code == 200, history.text
    payload = history.json()
    assert payload["service_id"] == service_id
    assert payload["health_checks"][0]["status"] == "healthy"
    assert payload["health_checks"][0]["version"] == "4.1.1"
    assert payload["commands"][0]["command"] == "restart"
    assert payload["commands"][0]["status"] == "accepted"


def test_orchestrator_recovery_restarts_unhealthy_service_until_attempt_limit(client, auth_headers):
    service = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload(
            "api-recovery",
            port=8060,
            health_url=None,
            recovery_policy="restart_on_failure",
            max_restart_attempts=1,
        ),
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]

    health = client.get(f"/api/v1/orchestrator/services/{service_id}/health", headers=auth_headers)
    assert health.status_code == 200, health.text
    assert health.json()["status"] == "unhealthy"

    first = client.post("/api/v1/orchestrator/recovery/run", headers=auth_headers)
    assert first.status_code == 200, first.text
    first_payload = first.json()
    assert first_payload["status"] == "actions_taken"
    assert first_payload["action_count"] == 1
    assert first_payload["actions"][0]["service"] == "api-recovery"
    assert first_payload["actions"][0]["action"] == "restart"
    assert first_payload["actions"][0]["status"] == "accepted"

    second = client.post("/api/v1/orchestrator/recovery/run", headers=auth_headers)
    assert second.status_code == 200, second.text
    second_payload = second.json()
    assert second_payload["status"] == "blocked"
    assert second_payload["actions"][0]["status"] == "limit_exhausted"

    session = get_session_local()()
    try:
        from app.infrastructure.models import ServiceCommandAudit

        audits = session.query(ServiceCommandAudit).filter(ServiceCommandAudit.service_id == service_id).all()
        assert [audit.command for audit in audits] == ["restart"]
    finally:
        session.close()


def test_orchestrator_local_windows_executor_runs_only_allowlisted_command(client, auth_headers, monkeypatch):
    service = client.post(
        "/api/v1/orchestrator/services",
        headers=auth_headers,
        json=_service_payload(
            "api-local-executor",
            port=8070,
            executor_type="local_windows",
        ),
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]

    blocked = client.post(f"/api/v1/orchestrator/services/{service_id}/reload", headers=auth_headers)
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["status"] == "blocked"

    monkeypatch.setattr(
        "app.application.central_orchestrator_service.LOCAL_COMMAND_ALLOWLIST",
        {("api-local-executor", "reload"): [sys.executable, "-c", "print('executor-ok')"]},
    )

    executed = client.post(f"/api/v1/orchestrator/services/{service_id}/reload", headers=auth_headers)
    assert executed.status_code == 200, executed.text
    payload = executed.json()
    assert payload["status"] == "executed"
    assert "executor-ok" in payload["message"]

    session = get_session_local()()
    try:
        from app.infrastructure.models import ServiceCommandAudit

        audits = (
            session.query(ServiceCommandAudit)
            .filter(ServiceCommandAudit.service_id == service_id)
            .order_by(ServiceCommandAudit.id)
            .all()
        )
        assert [audit.status for audit in audits] == ["blocked", "executed"]
    finally:
        session.close()
