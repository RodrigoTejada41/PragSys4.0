from app.core.security import create_access_token, get_password_hash
from app.infrastructure.db import get_session_local
from app.infrastructure.models import User


def test_assistant_returns_stock_guidance(client, auth_headers):
    response = client.post(
        "/api/v1/assistente/chat",
        json={
            "message": "Como dar baixa no estoque?",
            "current_view": "estoque",
            "current_title": "Estoque",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_module"] == "Estoque"
    assert "Estoque > Operacao" in payload["answer"]
    assert payload["suggestions"]


def test_assistant_blocks_restricted_module_guidance_for_operator(client):
    session = get_session_local()()
    try:
        admin = session.query(User).filter(User.username == "admin").first()
        assert admin is not None
        operator = User(
            username="operador.assistente",
            nome="Operador Assistente",
            password_hash=get_password_hash("Senha@123"),
            role="operador",
            is_active=True,
            empresa_prestadora_id=admin.empresa_prestadora_id,
        )
        session.add(operator)
        session.commit()
        session.refresh(operator)
        token = create_access_token(
            subject=str(operator.id),
            role=operator.role,
            company_id=operator.empresa_prestadora_id,
        )
    finally:
        session.close()

    response = client.post(
        "/api/v1/assistente/chat",
        json={
            "message": "Como cadastrar empresa prestadora?",
            "current_view": "empresas",
            "current_title": "Empresas",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "nao tem permissao" in response.json()["answer"]


def test_assistant_can_open_with_context_only(client, auth_headers):
    response = client.post(
        "/api/v1/assistente/chat",
        json={
            "message": "",
            "current_view": "ordens-nova",
            "current_title": "Nova ordem de servico",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_module"] == "Ordens de servico"
    assert "Estou olhando a tela Ordens de servico" in payload["answer"]
