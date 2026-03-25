from datetime import date, datetime, timedelta, timezone

from app.core.config import get_settings
from app.infrastructure.models import Appointment, ProviderCompany
from app.infrastructure.db import get_session_local
from app.core.exceptions import BusinessRuleViolation


def create_customer(client, auth_headers, suffix="01"):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente Agenda {suffix}",
            "cpf_cnpj": f"1234567800{suffix.zfill(4)}",
            "endereco": f"Rua Agenda {suffix}",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": f"1199000{suffix.zfill(4)}",
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
            "nome": f"Tecnico Agenda {suffix}",
            "registro": f"TEC-AGENDA-{suffix}",
            "telefone": f"1198000{suffix.zfill(4)}",
            "ativo": True,
        },
    )
    assert response.status_code in {200, 201}
    return response.json()


def create_product(client, auth_headers, suffix="01"):
    response = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": f"Produto Agenda {suffix}",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "5%",
            "registro_ms": f"MS-AGENDA-{suffix}",
            "estoque_atual": "10.00",
            "estoque_minimo": "1.00",
        },
    )
    assert response.status_code in {200, 201}
    return response.json()


def create_work_order_with_schedule(client, auth_headers, customer, technician, product, suffix="01"):
    execution_date = date.today() + timedelta(days=5)
    response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": f"OS-AGENDA-{suffix}",
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": execution_date.isoformat(),
            "hora_inicio": "09:00:00",
            "hora_fim": "10:00:00",
            "local_execucao": "Area tecnica",
            "observacoes": "OS com agendamento automatico",
            "garantia_ate": (execution_date + timedelta(days=30)).isoformat(),
            "status": "aberta",
            "valor_servico": "350.00",
            "produtos": [
                {
                    "produto_id": product["id"],
                    "quantidade": "1.00",
                    "diluicao": "1:20",
                }
            ],
            "pragas_ids": [],
            "gerar_financeiro": True,
            "gerar_agendamento": True,
            "tipo_servico_agendamento": "Controle preventivo",
            "duracao_prevista_minutos": 90,
            "observacoes_internas_agendamento": "Levar checklist",
            "instrucoes_tecnicas_agendamento": "Aplicar em area perimetral",
            "retorno_revisita_agendamento": "Retorno em 30 dias",
            "sincronizar_google_agenda": False,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_create_manual_appointment_and_prevent_technician_conflict(client, auth_headers):
    customer = create_customer(client, auth_headers, "101")
    technician = create_technician(client, auth_headers, "101")
    target_date = (date.today() + timedelta(days=3)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Visita tecnica",
            "data_agendamento": target_date,
            "hora_agendamento": "09:00:00",
            "duracao_prevista_minutos": 90,
            "observacoes": "Atendimento inicial",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert created.status_code == 200
    assert created.json()["status"] == "pendente"

    conflicting = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Retorno",
            "data_agendamento": target_date,
            "hora_agendamento": "09:30:00",
            "duracao_prevista_minutos": 60,
            "observacoes": "Conflito proposital",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert conflicting.status_code == 400
    assert "Conflito de horario" in conflicting.json()["detail"]
    assert "09:00 ate 10:30" in conflicting.json()["detail"]
    assert "09:30 ate 10:30" in conflicting.json()["detail"]


def test_work_order_generates_and_updates_linked_appointment(client, auth_headers):
    customer = create_customer(client, auth_headers, "202")
    technician = create_technician(client, auth_headers, "202")
    product = create_product(client, auth_headers, "202")
    work_order = create_work_order_with_schedule(client, auth_headers, customer, technician, product, "202")

    appointments_response = client.get("/api/v1/agendamentos", headers=auth_headers)
    assert appointments_response.status_code == 200
    appointments = appointments_response.json()
    assert len(appointments) == 1
    appointment = appointments[0]
    assert appointment["os_id"] == work_order["id"]
    assert appointment["tipo_servico"] == "Controle preventivo"
    assert appointment["duracao_prevista_minutos"] == 90

    new_date = (date.today() + timedelta(days=8)).isoformat()
    update_response = client.put(
        f"/api/v1/os/{work_order['id']}",
        headers=auth_headers,
        json={
            "numero": work_order["numero"],
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": new_date,
            "hora_inicio": "13:30:00",
            "hora_fim": "14:30:00",
            "local_execucao": "Area tecnica",
            "observacoes": "OS reagendada",
            "garantia_ate": (date.fromisoformat(new_date) + timedelta(days=30)).isoformat(),
            "status": "aberta",
            "valor_servico": "350.00",
            "produtos": [
                {
                    "produto_id": product["id"],
                    "quantidade": "1.00",
                    "diluicao": "1:20",
                }
            ],
            "pragas_ids": [],
            "gerar_financeiro": True,
            "gerar_agendamento": True,
            "tipo_servico_agendamento": "Controle preventivo",
            "duracao_prevista_minutos": 120,
            "observacoes_internas_agendamento": "Levar checklist atualizado",
            "instrucoes_tecnicas_agendamento": "Aplicar em area externa",
            "retorno_revisita_agendamento": "Retorno em 45 dias",
            "sincronizar_google_agenda": False,
        },
    )

    assert update_response.status_code == 200

    appointment_response = client.get(f"/api/v1/agendamentos/{appointment['id']}", headers=auth_headers)
    assert appointment_response.status_code == 200
    updated_appointment = appointment_response.json()
    assert updated_appointment["data_agendamento"] == new_date
    assert updated_appointment["hora_agendamento"] == "13:30:00"
    assert updated_appointment["duracao_prevista_minutos"] == 120
    assert updated_appointment["status"] == "reagendado"


def test_manual_google_sync_requires_google_flag_enabled(client, auth_headers):
    customer = create_customer(client, auth_headers, "250")
    technician = create_technician(client, auth_headers, "250")
    target_date = (date.today() + timedelta(days=4)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Inspecao preventiva",
            "data_agendamento": target_date,
            "hora_agendamento": "14:00:00",
            "duracao_prevista_minutos": 60,
            "observacoes": "Sem Google ativo",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert created.status_code == 200
    appointment_id = created.json()["id"]

    sync_response = client.post(f"/api/v1/agendamentos/{appointment_id}/sync-google", headers=auth_headers)

    assert sync_response.status_code == 400
    assert "Ative a sincronizacao com Google Agenda" in sync_response.json()["detail"]


def test_legacy_appointment_sync_route_requests_oauth_when_account_not_connected(client, auth_headers, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://testserver/api/v1/google-calendar/oauth/callback")
    monkeypatch.delenv("GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_CALENDAR_ENABLED", raising=False)
    get_settings.cache_clear()

    customer = create_customer(client, auth_headers, "251")
    technician = create_technician(client, auth_headers, "251")
    target_date = (date.today() + timedelta(days=4)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Inspecao via rota legada",
            "data_agendamento": target_date,
            "hora_agendamento": "14:30:00",
            "duracao_prevista_minutos": 60,
            "observacoes": "Sem conta conectada",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": True,
        },
    )

    assert created.status_code == 200
    appointment_id = created.json()["id"]

    sync_response = client.post(f"/api/v1/agendamentos/{appointment_id}/sync-google", headers=auth_headers)

    assert sync_response.status_code == 200
    payload = sync_response.json()
    assert payload["mode"] == "oauth_required"
    assert "accounts.google.com" in payload["authorization_url"]
    get_settings.cache_clear()


def test_google_sync_route_requests_oauth_when_account_not_connected(client, auth_headers, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://testserver/api/v1/google-calendar/oauth/callback")
    monkeypatch.delenv("GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_CALENDAR_ENABLED", raising=False)
    get_settings.cache_clear()

    customer = create_customer(client, auth_headers, "260")
    technician = create_technician(client, auth_headers, "260")
    target_date = (date.today() + timedelta(days=4)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Inspecao com Google",
            "data_agendamento": target_date,
            "hora_agendamento": "15:00:00",
            "duracao_prevista_minutos": 60,
            "observacoes": "Fluxo OAuth",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": True,
        },
    )

    assert created.status_code == 200
    appointment_id = created.json()["id"]

    sync_response = client.post(
        f"/api/v1/google-calendar/appointments/{appointment_id}/sync",
        headers=auth_headers,
    )

    assert sync_response.status_code == 200
    payload = sync_response.json()
    assert payload["mode"] == "oauth_required"
    assert "accounts.google.com" in payload["authorization_url"]
    get_settings.cache_clear()


def test_google_status_and_logout_flow_for_provider_company(client, auth_headers, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://testserver/api/v1/google-calendar/oauth/callback")
    get_settings.cache_clear()

    with get_session_local()() as db:
        company = ProviderCompany(
            razao_social="Google Agenda Teste Ltda",
            nome_fantasia="Agenda Teste",
            cnpj="11222333000199",
            google_calendar_id="primary",
            google_account_email="contato@agenda.teste",
            google_access_token="access-token",
            google_refresh_token="refresh-token",
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        company_id = company.id

    status_response = client.get(f"/api/v1/google-calendar/status?provider_company_id={company_id}", headers=auth_headers)

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "ativo"
    assert status_response.json()["account_email"] == "contato@agenda.teste"

    logout_response = client.post(f"/api/v1/google-calendar/logout?provider_company_id={company_id}", headers=auth_headers)

    assert logout_response.status_code == 200
    payload = logout_response.json()
    assert payload["status"] == "desconectado"
    assert payload["account_email"] is None

    status_after_logout = client.get(f"/api/v1/google-calendar/status?provider_company_id={company_id}", headers=auth_headers)

    assert status_after_logout.status_code == 200
    assert status_after_logout.json()["status"] == "aguardando_conexao"


def test_google_oauth_callback_reenables_google_integration_when_account_connects(client, auth_headers, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://testserver/api/v1/google-calendar/oauth/callback")
    get_settings.cache_clear()

    client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={"integrations": {"google_calendar_enabled": False}},
    )

    with get_session_local()() as db:
        company = db.query(ProviderCompany).order_by(ProviderCompany.id.asc()).first()
        if company is None:
            company = ProviderCompany(
                razao_social="SysPragas",
                nome_fantasia="SysPragas",
                cnpj="12345678000199",
            )
            db.add(company)
            db.commit()
            db.refresh(company)
        company_id = company.id

    def fake_exchange_code_for_tokens(code: str):
        return {
            "access_token": "oauth-access-token",
            "refresh_token": "oauth-refresh-token",
            "expires_in": 3600,
        }

    monkeypatch.setattr(
        "app.application.google_calendar_service._exchange_code_for_tokens",
        fake_exchange_code_for_tokens,
    )
    monkeypatch.setattr(
        "app.application.google_calendar_service._fetch_google_account_email",
        lambda access_token: "google@empresa.teste",
    )

    start_response = client.post("/api/v1/google-calendar/oauth/start", headers=auth_headers)
    assert start_response.status_code == 200
    state_token = start_response.json()["authorization_url"].split("state=", 1)[1]

    callback_response = client.get(
        f"/api/v1/google-calendar/oauth/callback?code=fake-code&state={state_token}",
        headers=auth_headers,
    )

    assert callback_response.status_code == 200

    status_response = client.get("/api/v1/google-calendar/status", headers=auth_headers)
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "ativo"
    assert status_response.json()["account_email"] == "google@empresa.teste"
    assert status_response.json()["company_id"] == company_id

    settings_response = client.get("/api/v1/settings", headers=auth_headers)
    assert settings_response.status_code == 200
    assert settings_response.json()["integrations"]["google_calendar_enabled"] is True


def test_create_appointment_with_google_handles_naive_token_expiration(client, auth_headers, monkeypatch):
    class FakeCalendarResponse:
        content = b'{"id":"google-event-123"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "google-event-123"}

    monkeypatch.setattr("app.application.google_calendar_service.httpx.request", lambda *args, **kwargs: FakeCalendarResponse())

    with get_session_local()() as db:
        company = db.query(ProviderCompany).order_by(ProviderCompany.id.asc()).first()
        company.google_calendar_id = "primary"
        company.google_account_email = "agenda@empresa.teste"
        company.google_access_token = "access-token"
        company.google_refresh_token = "refresh-token"
        company.google_token_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
        db.commit()

    customer = create_customer(client, auth_headers, "271")
    technician = create_technician(client, auth_headers, "271")
    target_date = (date.today() + timedelta(days=5)).isoformat()

    response = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Visita com Google e token legado",
            "data_agendamento": target_date,
            "hora_agendamento": "16:00:00",
            "duracao_prevista_minutos": 60,
            "observacoes": "Nao deve gerar erro 500 por datetime legado",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["google_calendar_event_id"] == "google-event-123"


def test_completing_appointment_updates_linked_work_order(client, auth_headers):
    customer = create_customer(client, auth_headers, "303")
    technician = create_technician(client, auth_headers, "303")
    product = create_product(client, auth_headers, "303")
    work_order = create_work_order_with_schedule(client, auth_headers, customer, technician, product, "303")

    appointments_response = client.get("/api/v1/agendamentos", headers=auth_headers)
    appointment = appointments_response.json()[0]

    conclude_response = client.post(
        f"/api/v1/agendamentos/{appointment['id']}/status",
        headers=auth_headers,
        json={
            "status": "concluido",
            "detalhes": "Atendimento finalizado pela equipe tecnica.",
        },
    )

    assert conclude_response.status_code == 200
    assert conclude_response.json()["status"] == "concluido"

    work_orders_response = client.get("/api/v1/os", headers=auth_headers)
    assert work_orders_response.status_code == 200
    assert work_orders_response.json()[0]["id"] == work_order["id"]
    assert work_orders_response.json()[0]["status"] == "concluida"


def test_disabling_google_sync_removes_existing_calendar_event(client, auth_headers, monkeypatch):
    calls = []

    def fake_google_request(db, user_id, method, path, payload=None):
        calls.append((method, path, payload))
        if method == "POST":
            return {"id": "evt-123"}, "primary"
        if method == "DELETE":
            return None, "primary"
        raise AssertionError(f"Metodo inesperado: {method}")

    monkeypatch.setattr("app.application.scheduling_services.google_calendar_request", fake_google_request)

    customer = create_customer(client, auth_headers, "401")
    technician = create_technician(client, auth_headers, "401")
    target_date = (date.today() + timedelta(days=4)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Visita com Google",
            "data_agendamento": target_date,
            "hora_agendamento": "09:00:00",
            "duracao_prevista_minutos": 60,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": True,
        },
    )

    assert created.status_code == 200
    appointment = created.json()
    assert appointment["google_calendar_event_id"] == "evt-123"
    post_call = next(call for call in calls if call[0] == "POST")
    google_payload = post_call[2]
    assert google_payload["summary"] == f"{customer['razao_social']} | {technician['nome']} | 09:00"
    assert google_payload["location"] == "Rua Agenda 401, Sao Paulo/SP"
    assert "Telefone: 11990000401" in google_payload["description"]
    assert "Horario:" in google_payload["description"]
    assert "Duracao prevista: 60 minutos" in google_payload["description"]
    assert f"Tecnico: {technician['nome']}" in google_payload["description"]

    updated = client.put(
        f"/api/v1/agendamentos/{appointment['id']}",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Visita com Google",
            "data_agendamento": target_date,
            "hora_agendamento": "09:00:00",
            "duracao_prevista_minutos": 60,
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert updated.status_code == 200
    payload = updated.json()
    assert payload["sincronizar_google"] is False
    assert payload["google_sync_status"] == "desconectado"
    assert payload["google_calendar_event_id"] is None
    assert any(call[0] == "DELETE" and call[1] == "events/evt-123" for call in calls)


def test_disabling_work_order_schedule_cancels_rescheduled_linked_appointment(client, auth_headers):
    customer = create_customer(client, auth_headers, "402")
    technician = create_technician(client, auth_headers, "402")
    product = create_product(client, auth_headers, "402")
    work_order = create_work_order_with_schedule(client, auth_headers, customer, technician, product, "402")

    appointments_response = client.get("/api/v1/agendamentos", headers=auth_headers)
    appointment = appointments_response.json()[0]

    first_update_date = (date.today() + timedelta(days=8)).isoformat()
    first_update = client.put(
        f"/api/v1/os/{work_order['id']}",
        headers=auth_headers,
        json={
            "numero": work_order["numero"],
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": first_update_date,
            "hora_inicio": "13:30:00",
            "hora_fim": "14:30:00",
            "local_execucao": "Area tecnica",
            "observacoes": "OS reagendada",
            "garantia_ate": (date.fromisoformat(first_update_date) + timedelta(days=30)).isoformat(),
            "status": "aberta",
            "valor_servico": "350.00",
            "produtos": [{"produto_id": product["id"], "quantidade": "1.00", "diluicao": "1:20"}],
            "pragas_ids": [],
            "gerar_financeiro": True,
            "gerar_agendamento": True,
            "tipo_servico_agendamento": "Controle preventivo",
            "duracao_prevista_minutos": 120,
            "observacoes_internas_agendamento": "Levar checklist atualizado",
            "instrucoes_tecnicas_agendamento": "Aplicar em area externa",
            "retorno_revisita_agendamento": "Retorno em 45 dias",
            "sincronizar_google_agenda": False,
        },
    )

    assert first_update.status_code == 200

    second_update = client.put(
        f"/api/v1/os/{work_order['id']}",
        headers=auth_headers,
        json={
            "numero": work_order["numero"],
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": first_update_date,
            "hora_inicio": "13:30:00",
            "hora_fim": "14:30:00",
            "local_execucao": "Area tecnica",
            "observacoes": "OS sem agenda",
            "garantia_ate": (date.fromisoformat(first_update_date) + timedelta(days=30)).isoformat(),
            "status": "aberta",
            "valor_servico": "350.00",
            "produtos": [{"produto_id": product["id"], "quantidade": "1.00", "diluicao": "1:20"}],
            "pragas_ids": [],
            "gerar_financeiro": True,
            "gerar_agendamento": False,
            "tipo_servico_agendamento": "Controle preventivo",
            "duracao_prevista_minutos": 120,
            "observacoes_internas_agendamento": "Levar checklist atualizado",
            "instrucoes_tecnicas_agendamento": "Aplicar em area externa",
            "retorno_revisita_agendamento": "Retorno em 45 dias",
            "sincronizar_google_agenda": False,
        },
    )

    assert second_update.status_code == 200

    appointment_response = client.get(f"/api/v1/agendamentos/{appointment['id']}", headers=auth_headers)
    assert appointment_response.status_code == 200
    assert appointment_response.json()["status"] == "cancelado"


def test_google_sync_route_does_not_mask_non_auth_errors_as_oauth(client, auth_headers, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret-teste")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://testserver/api/v1/google-calendar/oauth/callback")
    get_settings.cache_clear()

    customer = create_customer(client, auth_headers, "403")
    technician = create_technician(client, auth_headers, "403")
    target_date = (date.today() + timedelta(days=4)).isoformat()

    created = client.post(
        "/api/v1/agendamentos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "tipo_servico": "Inspecao com erro real",
            "data_agendamento": target_date,
            "hora_agendamento": "15:00:00",
            "duracao_prevista_minutos": 60,
            "observacoes": "Fluxo sem mascarar erro",
            "status": "pendente",
            "origem": "manual",
            "sincronizar_google": False,
        },
    )

    assert created.status_code == 200
    appointment_id = created.json()["id"]

    with get_session_local()() as db:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        appointment.sincronizar_google = True
        db.commit()

    def fake_sync(*args, **kwargs):
        raise BusinessRuleViolation("Falha ao sincronizar com Google Agenda: calendarId invalido.")

    monkeypatch.setattr("app.application.scheduling_services.sync_appointment_google_event", fake_sync)

    sync_response = client.post(
        f"/api/v1/google-calendar/appointments/{appointment_id}/sync",
        headers=auth_headers,
    )

    assert sync_response.status_code == 400
    assert "calendarId invalido" in sync_response.json()["detail"]
    get_settings.cache_clear()
