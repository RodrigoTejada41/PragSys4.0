import os
from base64 import b64decode
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_syspragas.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["DEFAULT_ADMIN_USERNAME"] = "admin"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "syspragas123"
os.environ["NFE_PROVIDER"] = "focus_nfe"
os.environ["FOCUS_NFE_API_BASE_URL"] = ""
os.environ["FOCUS_NFE_API_KEY"] = ""

TEST_PNG_BYTES = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5W9JcAAAAASUVORK5CYII="
)

from app.core.config import get_settings
from app.infrastructure.db import Base, get_engine, init_db, reset_engine
from app.main import app


@pytest.fixture(autouse=True)
def setup_database():
    get_settings.cache_clear()
    reset_engine()
    db_file = Path("test_syspragas.db")
    signatures_dir = Path("test_assets/assinaturas_tecnicas")
    models_dir = Path("test_assets/modelos")
    signatures_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    (signatures_dir / "assinatura_padrao.png").write_bytes(TEST_PNG_BYTES)
    (models_dir / "certificado_moldura_oficial.png").write_bytes(TEST_PNG_BYTES)
    os.environ["TECHNICAL_SIGNATURES_DIR"] = str(signatures_dir)
    os.environ["CERTIFICATE_MODELS_DIR"] = str(models_dir)
    if db_file.exists():
        db_file.unlink()
    init_db()
    yield
    Base.metadata.drop_all(bind=get_engine())
    reset_engine()
    if db_file.exists():
        db_file.unlink()
    for asset_path in (signatures_dir / "assinatura_padrao.png", models_dir / "certificado_moldura_oficial.png"):
        if asset_path.exists():
            asset_path.unlink()
    for directory in (signatures_dir, models_dir, Path("test_assets")):
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()


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
