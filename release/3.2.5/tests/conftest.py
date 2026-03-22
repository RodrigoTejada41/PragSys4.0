import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_syspragas.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["DEFAULT_ADMIN_USERNAME"] = "admin"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "syspragas123"

from app.core.config import get_settings
from app.infrastructure.db import Base, get_engine, init_db, reset_engine
from app.main import app


@pytest.fixture(autouse=True)
def setup_database():
    get_settings.cache_clear()
    reset_engine()
    db_file = Path("test_syspragas.db")
    if db_file.exists():
        db_file.unlink()
    init_db()
    yield
    Base.metadata.drop_all(bind=get_engine())
    reset_engine()
    if db_file.exists():
        db_file.unlink()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "syspragas123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
