import os
import shutil
from base64 import b64decode
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_syspragas.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["PASSWORD_HASH_ITERATIONS"] = "1000"
os.environ["DEFAULT_ADMIN_USERNAME"] = "admin"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "syspragas123"
os.environ["NFE_PROVIDER"] = "focus_nfe"
os.environ["FOCUS_NFE_API_BASE_URL"] = ""
os.environ["FOCUS_NFE_API_KEY"] = ""

TEST_PNG_BYTES = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5W9JcAAAAASUVORK5CYII="
)

from app.core.config import get_settings
from app.core.security import create_access_token
from app.infrastructure.db import get_session_local, init_db, reset_engine
from app.infrastructure.models import User
from app.main import app

TEST_RUN_ID = str(os.getpid())
TEST_DB_PATH = Path(f"test_syspragas_{TEST_RUN_ID}.db")
TEST_DB_TEMPLATE_PATH = Path(f"test_syspragas_template_{TEST_RUN_ID}.db")
TEST_ASSETS_ROOT = Path("test_assets") / TEST_RUN_ID
TEST_SIGNATURES_DIR = TEST_ASSETS_ROOT / "assinaturas_tecnicas"
TEST_MODELS_DIR = TEST_ASSETS_ROOT / "modelos"


def _set_database_url(db_path: Path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///./{db_path.name}"
    get_settings.cache_clear()
    reset_engine()


def _configure_test_assets() -> None:
    TEST_SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)
    TEST_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_SIGNATURES_DIR / "assinatura_padrao.png").write_bytes(TEST_PNG_BYTES)
    (TEST_MODELS_DIR / "certificado_moldura_oficial.png").write_bytes(TEST_PNG_BYTES)
    os.environ["TECHNICAL_SIGNATURES_DIR"] = str(TEST_SIGNATURES_DIR)
    os.environ["CERTIFICATE_MODELS_DIR"] = str(TEST_MODELS_DIR)
    get_settings.cache_clear()


def _cleanup_file(path: Path) -> None:
    if path.exists():
        path.unlink()


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    _configure_test_assets()
    _cleanup_file(TEST_DB_PATH)
    _cleanup_file(TEST_DB_TEMPLATE_PATH)
    _set_database_url(TEST_DB_TEMPLATE_PATH)
    init_db()
    reset_engine()
    _set_database_url(TEST_DB_PATH)
    yield
    reset_engine()
    _cleanup_file(TEST_DB_PATH)
    _cleanup_file(TEST_DB_TEMPLATE_PATH)
    for asset_path in (
        TEST_SIGNATURES_DIR / "assinatura_padrao.png",
        TEST_MODELS_DIR / "certificado_moldura_oficial.png",
    ):
        _cleanup_file(asset_path)
    for directory in (TEST_SIGNATURES_DIR, TEST_MODELS_DIR, TEST_ASSETS_ROOT, Path("test_assets")):
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()


@pytest.fixture(autouse=True)
def setup_database():
    _set_database_url(TEST_DB_PATH)
    _cleanup_file(TEST_DB_PATH)
    shutil.copyfile(TEST_DB_TEMPLATE_PATH, TEST_DB_PATH)
    yield
    reset_engine()
    _cleanup_file(TEST_DB_PATH)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    session = get_session_local()()
    try:
        admin = session.query(User).filter(User.username == "admin").first()
        assert admin is not None
        token = create_access_token(
            subject=str(admin.id),
            role=admin.role,
            company_id=admin.empresa_prestadora_id,
        )
    finally:
        session.close()
    return {"Authorization": f"Bearer {token}"}
