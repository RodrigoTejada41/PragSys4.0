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

    def _fake_send(message, smtp_settings=None):
        sent_messages.append((message, smtp_settings))

    def _fake_build(contract, smtp_settings=None):
        message = EmailMessage()
        message["Subject"] = contract.nome
        message["X-SMTP-Host"] = str((smtp_settings or {}).get("smtp_host") or "")
        return message

    monkeypatch.setattr(contracts_service, "_build_contract_email", _fake_build)
    monkeypatch.setattr(contracts_service, "_send_contract_email_message", _fake_send)

    maintenance = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert maintenance.status_code == 200
    assert maintenance.json()["email_sent"] == 1
    assert len(sent_messages) == 1
    assert sent_messages[0][0]["X-SMTP-Host"] == ""
    assert sent_messages[0][1]["smtp_port"] == 587

    second_run = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert second_run.status_code == 200
    assert second_run.json()["email_sent"] == 0
    assert len(sent_messages) == 1


def test_contract_maintenance_uses_persisted_smtp_settings(client, auth_headers, monkeypatch):
    customer_id = _create_customer(client, auth_headers, "17")
    settings_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "contracts": {
                "alert_days": 15,
                "email_enabled": True,
                "storage_dir": "uploads/contratos",
            },
            "email": {
                "smtp_host": "smtp.persistido.local",
                "smtp_port": 2525,
                "smtp_username": "mailer",
                "smtp_password": "segredo",
                "smtp_use_tls": True,
                "smtp_use_ssl": False,
                "smtp_sender_email": "contratos@empresa.com",
                "smtp_sender_name": "Contratos SysPragas",
            },
        },
    )
    assert settings_response.status_code == 200

    today = date.today()
    response = client.post(
        f"/api/v1/clientes/{customer_id}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato com SMTP persistido",
            "data_inicio": (today - timedelta(days=10)).isoformat(),
            "data_vencimento": (today + timedelta(days=2)).isoformat(),
            "observacoes": "",
        },
    )
    assert response.status_code == 200

    captured = {}

    def _fake_build(contract, smtp_settings=None):
        captured["build"] = smtp_settings
        message = EmailMessage()
        message["Subject"] = contract.nome
        return message

    def _fake_send(message, smtp_settings=None):
        captured["send"] = smtp_settings

    monkeypatch.setattr(contracts_service, "_build_contract_email", _fake_build)
    monkeypatch.setattr(contracts_service, "_send_contract_email_message", _fake_send)

    maintenance = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert maintenance.status_code == 200
    assert maintenance.json()["email_sent"] == 1
    assert captured["build"]["smtp_host"] == "smtp.persistido.local"
    assert captured["build"]["smtp_port"] == 2525
    assert captured["build"]["smtp_sender_email"] == "contratos@empresa.com"
    assert captured["send"]["smtp_username"] == "mailer"


def test_contract_maintenance_generates_recurring_charge_once_per_period(client, auth_headers):
    customer_id = _create_customer(client, auth_headers, "14")
    today = date.today()
    response = client.post(
        f"/api/v1/clientes/{customer_id}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato recorrente mensal",
            "data_inicio": today.replace(day=1).isoformat(),
            "data_vencimento": (today + timedelta(days=120)).isoformat(),
            "valor_mensal": "250.00",
            "tipo_cobranca": "mensal",
            "dia_vencimento": str(min(today.day, 10)),
            "gerar_cobranca_automatica": "true",
            "observacoes": "",
        },
    )
    assert response.status_code == 200
    contract = response.json()
    assert contract["gerar_cobranca_automatica"] is True

    first_run = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert first_run.status_code == 200
    assert first_run.json()["charges_generated"] == 1

    finance = client.get("/api/v1/financeiro", headers=auth_headers)
    assert finance.status_code == 200
    charges = [item for item in finance.json() if item["contrato_id"] == contract["id"]]
    assert len(charges) == 1
    assert charges[0]["origem"] == "contrato"
    assert charges[0]["valor"] == "250.00"

    second_run = client.post("/api/v1/contratos/rotina/sincronizar", headers=auth_headers)
    assert second_run.status_code == 200
    assert second_run.json()["charges_generated"] == 0


def test_contract_reports_filters_and_exports(client, auth_headers):
    customer_a = _create_customer(client, auth_headers, "15")
    customer_b = _create_customer(client, auth_headers, "16")
    today = date.today()

    response_a = client.post(
        f"/api/v1/clientes/{customer_a}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato ativo com cobranca",
            "data_inicio": today.isoformat(),
            "data_vencimento": (today + timedelta(days=90)).isoformat(),
            "valor_mensal": "180.00",
            "tipo_cobranca": "mensal",
            "dia_vencimento": "10",
            "gerar_cobranca_automatica": "true",
            "observacoes": "",
        },
    )
    assert response_a.status_code == 200

    response_b = client.post(
        f"/api/v1/clientes/{customer_b}/contratos",
        headers=auth_headers,
        data={
            "nome": "Contrato vencido sem cobranca",
            "data_inicio": (today - timedelta(days=120)).isoformat(),
            "data_vencimento": (today - timedelta(days=1)).isoformat(),
            "valor_mensal": "0",
            "tipo_cobranca": "personalizado",
            "gerar_cobranca_automatica": "false",
            "observacoes": "",
        },
    )
    assert response_b.status_code == 200

    report = client.get("/api/v1/contratos/relatorios?cliente_id=%s&cobranca_ativa=true" % customer_a, headers=auth_headers)
    assert report.status_code == 200
    payload = report.json()
    assert payload["resumo"]["total_contratos"] == 1
    assert payload["itens"][0]["cliente_id"] == customer_a
    assert payload["itens"][0]["gerar_cobranca_automatica"] is True

    xlsx_report = client.get("/api/v1/contratos/relatorios.xlsx", headers=auth_headers)
    assert xlsx_report.status_code == 200
    assert xlsx_report.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert xlsx_report.content.startswith(b"PK")

    pdf_report = client.get("/api/v1/contratos/relatorios.pdf", headers=auth_headers)
    assert pdf_report.status_code == 200
    assert pdf_report.headers["content-type"].startswith("application/pdf")
    assert pdf_report.content.startswith(b"%PDF")
