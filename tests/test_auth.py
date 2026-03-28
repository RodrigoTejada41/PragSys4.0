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
