from datetime import date, timedelta
from email.message import EmailMessage

from app.application import contracts_service


def _create_customer(client, auth_headers, suffix: str = "01") -> int:
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente Contrato {suffix}",
            "cpf_cnpj": f"123456780001{suffix}",
            "email": f"cliente{suffix}@empresa.com",
            "endereco": "Rua dos Contratos, 100",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11988887777",
            "contato": "Financeiro",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_contract_with_file_and_download(client, auth_headers):
    customer_id = _create_customer(client, auth_headers, "11")
    start_date = date.today()
    due_date = start_date + timedelta(days=45)

    response = client.post(
        f"/api/v1/clientes/{customer_id}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato de dedetizacao anual",
            "data_inicio": start_date.isoformat(),
            "data_vencimento": due_date.isoformat(),
            "observacoes": "Cobertura matriz",
        },
        files={"arquivo": ("contrato.pdf", b"%PDF-1.4 contrato", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["cliente_id"] == customer_id
    assert payload["status"] == "ativo"
    assert payload["arquivo_nome_original"] == "contrato.pdf"
    assert payload["arquivo_disponivel"] is True

    listing = client.get(f"/api/v1/clientes/{customer_id}/contratos", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    file_response = client.get(f"/api/v1/contratos/{payload['id']}/arquivo", headers=auth_headers)
    assert file_response.status_code == 200
    assert file_response.headers["content-type"] == "application/pdf"
    assert file_response.content.startswith(b"%PDF-1.4")


def test_contract_status_dashboard_and_update(client, auth_headers):
    customer_id = _create_customer(client, auth_headers, "12")
    today = date.today()

    vencido = client.post(
        f"/api/v1/clientes/{customer_id}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato vencido",
            "data_inicio": (today - timedelta(days=40)).isoformat(),
            "data_vencimento": (today - timedelta(days=1)).isoformat(),
            "observacoes": "",
        },
    )
    assert vencido.status_code == 200
    assert vencido.json()["status"] == "vencido"

    a_vencer = client.post(
        f"/api/v1/clientes/{customer_id}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato quase vencendo",
            "data_inicio": (today - timedelta(days=10)).isoformat(),
            "data_vencimento": (today + timedelta(days=5)).isoformat(),
            "observacoes": "",
        },
    )
    assert a_vencer.status_code == 200
    assert a_vencer.json()["status"] == "a_vencer"

    dashboard = client.get("/api/v1/contratos/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert dashboard_payload["vencidos"] == 1
    assert dashboard_payload["a_vencer"] == 1

    update = client.put(
        f"/api/v1/contratos/{a_vencer.json()['id']}",
        headers=auth_headers,
        data={
            "nome": "Contrato renovado",
            "data_inicio": today.isoformat(),
            "data_vencimento": (today + timedelta(days=90)).isoformat(),
            "observacoes": "Renovado por mais 90 dias",
        },
    )
    assert update.status_code == 200
    assert update.json()["status"] == "ativo"
    assert update.json()["nome"] == "Contrato renovado"


def test_contract_maintenance_sends_notification_once_per_status(client, auth_headers, monkeypatch):
    customer_id = _create_customer(client, auth_headers, "13")
    settings_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "contracts": {
                "alert_days": 15,
                "email_enabled": True,
                "storage_dir": "uploads/contratos",
            }
        },
    )
    assert settings_response.status_code == 200

    today = date.today()
    response = client.post(
        f"/api/v1/clientes/{customer_id}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato em alerta",
            "data_inicio": (today - timedelta(days=30)).isoformat(),
            "data_vencimento": (today + timedelta(days=3)).isoformat(),
            "observacoes": "",
        },
    )
    assert response.status_code == 200

    sent_messages = []

    def _fake_send(message):
        sent_messages.append(message)

    def _fake_build(contract):
        message = EmailMessage()
        message["Subject"] = contract.nome
        return message

    monkeypatch.setattr(contracts_service, "_build_contract_email", _fake_build)
    monkeypatch.setattr(contracts_service, "_send_contract_email_message", _fake_send)

    maintenance = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert maintenance.status_code == 200
    assert maintenance.json()["email_sent"] == 1
    assert len(sent_messages) == 1

    second_run = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert second_run.status_code == 200
    assert second_run.json()["email_sent"] == 0
    assert len(sent_messages) == 1
