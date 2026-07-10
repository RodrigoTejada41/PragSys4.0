from pathlib import Path

from app.core.security import get_password_hash
from app.infrastructure.db import get_session_local
from app.infrastructure.models import User


def test_login_and_me(client):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "syspragas123"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"


def test_docs_require_master_credentials(client):
    unauthorized = client.get("/docs")
    assert unauthorized.status_code == 401

    master = client.get("/docs", auth=("admin", "syspragas123"))
    assert master.status_code == 200
    assert "swagger-ui" in master.text.lower()


def test_docs_forbid_non_master_users(client):
    session = get_session_local()()
    try:
        master = session.query(User).filter(User.username == "admin").first()
        assert master is not None
        operator = User(
            username="operador.docs",
            nome="Operador Docs",
            password_hash=get_password_hash("Senha@123"),
            role="operador",
            is_active=True,
            empresa_prestadora_id=master.empresa_prestadora_id,
        )
        session.add(operator)
        session.commit()
    finally:
        session.close()

    response = client.get("/docs", auth=("operador.docs", "Senha@123"))
    assert response.status_code == 403


def test_security_headers_and_csp_nonce_on_web_app(client):
    response = client.get("/app")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"

    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-inline'" not in csp.split("script-src", 1)[1].split(";", 1)[0]
    assert "nonce-" in csp
    assert '<script nonce="' in response.text
    assert "SysPragas 4.1" in response.text
    assert "Nova ordem de servico" in response.text
    assert "Ordens cadastradas" in response.text


def test_web_token_is_not_persisted_in_local_storage():
    app_js = Path("app/interfaces/web/static/app.js").read_text(encoding="utf-8")

    assert 'localStorage.setItem("syspragas_token"' not in app_js
    assert 'localStorage.getItem("syspragas_token"' not in app_js
    assert "sessionStorage.setItem(TOKEN_STORAGE_KEY" in app_js


def test_favicon_is_served(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
