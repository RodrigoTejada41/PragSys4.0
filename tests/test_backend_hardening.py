from datetime import date

import pytest

from app.application.contract_scheduler import claim_daily_job_run, release_daily_job_run
from app.application.settings_service import get_setting_value
from app.core.config import get_settings
from app.infrastructure.models import BackgroundJobRun, SystemSetting


def test_production_requires_secure_runtime_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "<SECRET>")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "syspragas123")
    get_settings.cache_clear()

    with pytest.raises(ValueError):
        get_settings()

    monkeypatch.setenv("JWT_SECRET", "jwt-super-seguro")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "senha-admin-segura")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.is_production is True

    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)
    get_settings.cache_clear()


def test_smtp_password_is_persisted_encrypted(client, auth_headers):
    response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "email": {
                "smtp_host": "smtp.seguro.local",
                "smtp_password": "segredo-super-sensivel",
            }
        },
    )
    assert response.status_code == 200

    from app.infrastructure.db import get_session_local

    session = get_session_local()()
    try:
        record = session.query(SystemSetting).filter(SystemSetting.key == "smtp_password").first()
        assert record is not None
        assert "segredo-super-sensivel" not in record.value
        assert record.value.startswith("enc:v1:")
        assert get_setting_value(session, "smtp_password") == "segredo-super-sensivel"
    finally:
        session.close()


def test_scheduler_claim_is_unique_per_day():
    from app.infrastructure.db import get_session_local

    session = get_session_local()()
    run_date = date(2026, 3, 27)
    try:
        session.query(BackgroundJobRun).filter(BackgroundJobRun.task_name == "contract_maintenance").delete()
        session.commit()

        assert claim_daily_job_run(session, "contract_maintenance", run_date) is True
        assert claim_daily_job_run(session, "contract_maintenance", run_date) is False

        release_daily_job_run(session, "contract_maintenance", run_date)

        assert claim_daily_job_run(session, "contract_maintenance", run_date) is True
    finally:
        session.query(BackgroundJobRun).filter(BackgroundJobRun.task_name == "contract_maintenance").delete()
        session.commit()
        session.close()
