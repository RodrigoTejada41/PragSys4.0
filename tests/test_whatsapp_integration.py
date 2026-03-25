from datetime import date, timedelta

import httpx

from app.core.config import get_settings
from app.modules.whatsapp.service import WhatsAppSendResult


def create_customer(client, auth_headers, suffix="01", phone=None):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente WhatsApp {suffix}",
            "cpf_cnpj": f"9988776600{suffix.zfill(4)}",
            "endereco": f"Rua WhatsApp {suffix}",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": phone or f"1199555{suffix.zfill(4)}",
            "contato": "Operacao",
        },
    )
    assert response.status_code in {200, 201}
    return response.json()


def create_technician(client, auth_headers, suffix="01"):
    response = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": f"Tecnico WhatsApp {suffix}",
            "registro": f"TEC-WPP-{suffix}",
            "telefone": f"1198444{suffix.zfill(4)}",
            "ativo": True,
        },
    )
    assert response.status_code in {200, 201}
    return response.json()


def configure_whatsapp(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_PROVIDER", "custom")
    monkeypatch.setenv("WHATSAPP_API_BASE_URL", "https://whatsapp.example.test/send")
    monkeypatch.delenv("WHATSAPP_MESSAGE_API_URL", raising=False)
    monkeypatch.setenv("WHATSAPP_AUTH_TOKEN", "token-teste")
    monkeypatch.setenv("WHATSAPP_SENDER_ID", "sender-teste")
    monkeypatch.setenv("WHATSAPP_INSTANCE_NAME", "instancia-teste")
    monkeypatch.setenv("WHATSAPP_STATUS_API_URL", "https://whatsapp.example.test/status")
    monkeypatch.delenv("WHATSAPP_QR_API_URL", raising=False)
    monkeypatch.delenv("WHATSAPP_CONNECT_API_URL", raising=False)
    monkeypatch.delenv("WHATSAPP_LOGOUT_API_URL", raising=False)
    get_settings.cache_clear()


def configure_whatsapp_qr(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_PROVIDER", "evolution")
    monkeypatch.setenv("WHATSAPP_API_BASE_URL", "https://whatsapp.example.test")
    monkeypatch.delenv("WHATSAPP_MESSAGE_API_URL", raising=False)
    monkeypatch.setenv("WHATSAPP_API_KEY", "api-key-teste")
    monkeypatch.delenv("WHATSAPP_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("WHATSAPP_INSTANCE_NAME", "instancia-qr")
    monkeypatch.delenv("WHATSAPP_STATUS_API_URL", raising=False)
    monkeypatch.delenv("WHATSAPP_QR_API_URL", raising=False)
    monkeypatch.delenv("WHATSAPP_CONNECT_API_URL", raising=False)
    monkeypatch.delenv("WHATSAPP_LOGOUT_API_URL", raising=False)
    get_settings.cache_clear()


def test_whatsapp_status_endpoint_reports_active_connection(client, auth_headers, monkeypatch):
    configure_whatsapp(monkeypatch)

    class FakeResponse:
        status_code = 200
        content = b'{"status":"connected","instance_name":"instancia-teste"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "connected", "instance_name": "instancia-teste"}

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.get", lambda *args, **kwargs: FakeResponse())

    response = client.get("/api/v1/whatsapp/status", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ativo"
    assert payload["instance_name"] == "instancia-teste"
    assert payload["error_message"] is None


def test_whatsapp_status_endpoint_reports_error_on_timeout(client, auth_headers, monkeypatch):
    configure_whatsapp(monkeypatch)

    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.get", raise_timeout)

    response = client.get("/api/v1/whatsapp/status", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "erro"
    assert "Timeout" in payload["error_message"]


def test_whatsapp_status_respects_persisted_system_toggle_over_env_default(client, auth_headers, monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "false")
    monkeypatch.setenv("WHATSAPP_PROVIDER", "evolution")
    monkeypatch.setenv("WHATSAPP_API_BASE_URL", "https://whatsapp.example.test")
    monkeypatch.setenv("WHATSAPP_API_KEY", "api-key-teste")
    monkeypatch.setenv("WHATSAPP_INSTANCE_NAME", "instancia-qr")
    monkeypatch.delenv("WHATSAPP_STATUS_API_URL", raising=False)
    get_settings.cache_clear()

    settings_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "integrations": {
                "whatsapp_enabled": True,
            }
        },
    )
    assert settings_response.status_code == 200

    class FakeResponse:
        status_code = 200
        content = b'{"instance":{"instanceName":"instancia-qr","state":"connecting"}}'

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "instance": {
                    "instanceName": "instancia-qr",
                    "state": "connecting",
                }
            }

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.get", lambda *args, **kwargs: FakeResponse())

    response = client.get("/api/v1/whatsapp/status", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "aguardando_conexao"
    assert payload["supports_qr"] is True
    assert payload["configured"] is True


def test_whatsapp_status_endpoint_reports_qr_connector_details(client, auth_headers, monkeypatch):
    configure_whatsapp_qr(monkeypatch)

    class FakeResponse:
        status_code = 200
        content = b'{"instance":{"instanceName":"instancia-qr","state":"open","ownerJid":"5511999999999@s.whatsapp.net"}}'

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "instance": {
                    "instanceName": "instancia-qr",
                    "state": "open",
                    "ownerJid": "5511999999999@s.whatsapp.net",
                }
            }

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.get", lambda *args, **kwargs: FakeResponse())

    response = client.get("/api/v1/whatsapp/status", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ativo"
    assert payload["supports_qr"] is True
    assert payload["session_persistent"] is True
    assert payload["connected_phone"] == "5511999999999@s.whatsapp.net"


def test_whatsapp_qr_session_endpoint_returns_qr_payload(client, auth_headers, monkeypatch):
    configure_whatsapp_qr(monkeypatch)

    class FakeResponse:
        status_code = 200
        content = b'{"code":"qr-content","pairingCode":"ABC-123","base64":"ZmFrZS1xci1pbWFnZQ==","status":"open"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "code": "qr-content",
                "pairingCode": "ABC-123",
                "base64": "ZmFrZS1xci1pbWFnZQ==",
                "status": "open",
            }

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.get", lambda *args, **kwargs: FakeResponse())

    response = client.post("/api/v1/whatsapp/sessao/qr", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "evolution"
    assert payload["qr_code"] == "qr-content"
    assert payload["pairing_code"] == "ABC-123"
    assert payload["qr_image_data_url"].startswith("data:image/png;base64,")


def test_whatsapp_logout_endpoint_disconnects_qr_session(client, auth_headers, monkeypatch):
    configure_whatsapp_qr(monkeypatch)

    class FakeDeleteResponse:
        status_code = 200
        content = b'{"status":"SUCCESS"}'

        def raise_for_status(self):
            return None

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.delete", lambda *args, **kwargs: FakeDeleteResponse())

    response = client.post("/api/v1/whatsapp/sessao/logout", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "desconectado"
    assert "desconectada" in payload["error_message"]


def test_create_appointment_sends_whatsapp_automatically(client, auth_headers, monkeypatch):
    configure_whatsapp(monkeypatch)

    class FakeClient:
        def send_message(self, destination_phone, message):
            assert destination_phone.startswith("55")
            assert "Ola Cliente WhatsApp 501, tudo bem?" in message
            assert "Tecnico: Tecnico WhatsApp 501" in message
            assert "Servico: Controle preventivo" in message
            return WhatsAppSendResult(
                provider="custom",
                external_message_id="msg-001",
                raw_response={"message_id": "msg-001"},
            )

    monkeypatch.setattr("app.modules.whatsapp.service._build_client", lambda config: FakeClient())

    customer = create_customer(client, auth_headers, "501")
    technician = create_technician(client, auth_headers, "501")
    target_date = (date.today() + timedelta(days=2)).isoformat()

    response = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Controle preventivo",
            "data_agendamento": target_date,
            "hora_agendamento": "08:30:00",
            "duracao_prevista_minutos": 60,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["whatsapp_status"] == "enviado"
    assert payload["whatsapp_ultimo_erro"] is None
    assert len(payload["whatsapp_logs"]) == 1
    assert payload["whatsapp_logs"][0]["automatico"] is True
    assert payload["whatsapp_logs"][0]["external_message_id"] == "msg-001"


def test_create_appointment_sends_whatsapp_via_qr_connector(client, auth_headers, monkeypatch):
    configure_whatsapp_qr(monkeypatch)

    class FakeResponse:
        status_code = 200
        content = b'{"key":{"id":"msg-evolution-001"}}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"key": {"id": "msg-evolution-001"}}

    def fake_post(url, json=None, headers=None, timeout=None):
        assert url == "https://whatsapp.example.test/message/sendText/instancia-qr"
        assert json["number"].startswith("55")
        assert "Controle preventivo QR" in json["text"]
        assert headers["apikey"] == "api-key-teste"
        return FakeResponse()

    monkeypatch.setattr("app.modules.whatsapp.service.httpx.post", fake_post)

    customer = create_customer(client, auth_headers, "505")
    technician = create_technician(client, auth_headers, "505")
    target_date = (date.today() + timedelta(days=6)).isoformat()

    response = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Controle preventivo QR",
            "data_agendamento": target_date,
            "hora_agendamento": "15:45:00",
            "duracao_prevista_minutos": 60,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["whatsapp_status"] == "enviado"
    assert payload["whatsapp_logs"][0]["provider"] == "evolution"
    assert payload["whatsapp_logs"][0]["external_message_id"] == "msg-evolution-001"


def test_create_appointment_keeps_record_and_logs_whatsapp_failure_for_invalid_phone(client, auth_headers, monkeypatch):
    configure_whatsapp(monkeypatch)
    monkeypatch.setattr("app.modules.whatsapp.service._build_client", lambda config: None)

    customer = create_customer(client, auth_headers, "502", phone="123")
    technician = create_technician(client, auth_headers, "502")
    target_date = (date.today() + timedelta(days=3)).isoformat()

    response = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Inspecao",
            "data_agendamento": target_date,
            "hora_agendamento": "10:00:00",
            "duracao_prevista_minutos": 45,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["whatsapp_status"] == "falha"
    assert "Telefone do cliente invalido" in payload["whatsapp_ultimo_erro"]
    assert len(payload["whatsapp_logs"]) == 1


def test_manual_whatsapp_resend_creates_new_log_entry(client, auth_headers, monkeypatch):
    configure_whatsapp(monkeypatch)
    send_counter = {"count": 0}

    class FakeClient:
        def send_message(self, destination_phone, message):
            send_counter["count"] += 1
            return WhatsAppSendResult(
                provider="custom",
                external_message_id=f"msg-{send_counter['count']}",
                raw_response={"message_id": f"msg-{send_counter['count']}"},
            )

    monkeypatch.setattr("app.modules.whatsapp.service._build_client", lambda config: FakeClient())

    customer = create_customer(client, auth_headers, "503")
    technician = create_technician(client, auth_headers, "503")
    target_date = (date.today() + timedelta(days=4)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Monitoramento",
            "data_agendamento": target_date,
            "hora_agendamento": "11:15:00",
            "duracao_prevista_minutos": 50,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert created.status_code == 200
    appointment_id = created.json()["id"]

    resend = client.post(
        f"/api/v1/whatsapp/agendamentos/{appointment_id}/enviar",
        headers=auth_headers,
    )

    assert resend.status_code == 200
    payload = resend.json()
    assert payload["whatsapp_status"] == "enviado"
    assert len(payload["whatsapp_logs"]) == 2
    assert payload["whatsapp_logs"][0]["automatico"] is False
    assert payload["whatsapp_logs"][0]["external_message_id"] == "msg-2"


def test_update_appointment_sends_whatsapp_automatically(client, auth_headers, monkeypatch):
    configure_whatsapp(monkeypatch)
    sent_messages = []

    class FakeClient:
        def send_message(self, destination_phone, message):
            sent_messages.append((destination_phone, message))
            return WhatsAppSendResult(
                provider="custom",
                external_message_id=f"msg-{len(sent_messages)}",
                raw_response={"message_id": f"msg-{len(sent_messages)}"},
            )

    monkeypatch.setattr("app.modules.whatsapp.service._build_client", lambda config: FakeClient())

    customer = create_customer(client, auth_headers, "504")
    technician = create_technician(client, auth_headers, "504")
    target_date = (date.today() + timedelta(days=5)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Controle inicial",
            "data_agendamento": target_date,
            "hora_agendamento": "13:00:00",
            "duracao_prevista_minutos": 60,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
            "enviar_whatsapp": False,
        },
    )

    assert created.status_code == 200
    assert len(sent_messages) == 0

    updated = client.put(
        f"/api/v1/agendamentos/{created.json()['id']}",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Controle inicial revisado",
            "data_agendamento": target_date,
            "hora_agendamento": "14:15:00",
            "duracao_prevista_minutos": 90,
            "status": "confirmado",
            "origem": "manual",
            "sincronizar_google": False,
            "enviar_whatsapp": True,
        },
    )

    assert updated.status_code == 200
    payload = updated.json()
    assert payload["whatsapp_status"] == "enviado"
    assert len(payload["whatsapp_logs"]) == 1
    assert payload["whatsapp_logs"][0]["automatico"] is True
    assert "Hora: 14:15" in sent_messages[0][1]
    assert "Servico: Controle inicial revisado" in sent_messages[0][1]
