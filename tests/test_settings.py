def _create_company_user(client, auth_headers, username: str, company_suffix: str) -> dict:
    cnpj = f"{company_suffix * 4}0001{company_suffix}"
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": f"Admin {company_suffix}",
            "username": username,
            "password": "senha123",
            "role": "admin",
            "is_active": True,
            "nova_empresa_prestadora": {
                "razao_social": f"Prestadora {company_suffix} Ltda",
                "nome_fantasia": f"Prestadora {company_suffix}",
                "cnpj": cnpj,
                "email": f"{username}@empresa.com",
                "telefone": "11999990000",
                "cidade": "Sao Paulo",
                "estado": "SP",
            },
            "licenca_inicial": {
                "descricao": f"Licenca {company_suffix}",
                "start_date": "2026-03-20",
                "end_date": "2027-03-20",
                "max_users": 10,
                "status": "ativa",
                "notes": "Licenca de teste multempresa",
            },
        },
    )
    assert response.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "senha123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_admin_can_read_and_update_system_settings(client, auth_headers):
    response = client.get("/api/v1/settings", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert "integrations" in payload
    assert "contracts" in payload
    assert "system" in payload
    assert payload["system"]["operation_mode"] in {"local", "rede"}

    update_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "integrations": {
                "google_calendar_enabled": True,
                "whatsapp_enabled": False,
                "whatsapp_auto_send": False,
                "whatsapp_default_message": "Agendamento atualizado automaticamente.",
            },
            "contracts": {
                "alert_days": 30,
                "email_enabled": True,
                "storage_dir": "uploads/contratos-teste",
            },
            "system": {
                "multiempresa_enabled": False,
                "operation_mode": "rede",
                "notifications_enabled": False,
                "appointment_default_google_sync": True,
            },
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["integrations"]["google_calendar_enabled"] is True
    assert updated["integrations"]["whatsapp_enabled"] is False
    assert updated["integrations"]["whatsapp_auto_send"] is False
    assert updated["integrations"]["whatsapp_default_message"] == "Agendamento atualizado automaticamente."
    assert updated["contracts"]["alert_days"] == 30
    assert updated["contracts"]["email_enabled"] is True
    assert updated["contracts"]["storage_dir"] == "uploads/contratos-teste"
    assert updated["system"]["multiempresa_enabled"] is False
    assert updated["system"]["operation_mode"] == "rede"
    assert updated["system"]["notifications_enabled"] is False
    assert updated["system"]["appointment_default_google_sync"] is True


def test_operador_cannot_access_system_settings(client, auth_headers):
    create_user_response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": "Operador Config",
            "username": "operadorconfig",
            "password": "senha123",
            "role": "operador",
            "is_active": True,
            "nova_empresa_prestadora": {
                "razao_social": "Prestadora Operador Config Ltda",
                "nome_fantasia": "Prestadora Operador Config",
                "cnpj": "12312312000199",
                "email": "operadorconfig@empresa.com",
                "telefone": "11999998888",
                "cidade": "Sao Paulo",
                "estado": "SP",
            },
            "licenca_inicial": {
                "descricao": "Licenca operador config",
                "start_date": "2026-03-20",
                "end_date": "2027-03-20",
                "max_users": 3,
                "status": "ativa",
                "notes": "Licenca de teste",
            },
        },
    )
    assert create_user_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "operadorconfig", "password": "senha123"},
    )
    operador_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = client.get("/api/v1/settings", headers=operador_headers)

    assert response.status_code == 403


def test_disabling_multiempresa_removes_company_scope_from_core_queries(client, auth_headers):
    company_a_headers = _create_company_user(client, auth_headers, "adminseta", "31")
    company_b_headers = _create_company_user(client, auth_headers, "adminsetb", "42")

    create_customer_response = client.post(
        "/api/v1/clientes",
        headers=company_a_headers,
        json={
            "razao_social": "Cliente Empresa A",
            "cpf_cnpj": "31313131000131",
            "endereco": "Rua A, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11911112222",
            "contato": "Contato A",
        },
    )
    assert create_customer_response.status_code == 201

    isolated_response = client.get("/api/v1/clientes", headers=company_b_headers)
    assert isolated_response.status_code == 200
    assert isolated_response.json() == []

    disable_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={"system": {"multiempresa_enabled": False}},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["system"]["multiempresa_enabled"] is False

    shared_response = client.get("/api/v1/clientes", headers=company_b_headers)

    assert shared_response.status_code == 200
    assert len(shared_response.json()) == 1
    assert shared_response.json()[0]["razao_social"] == "Cliente Empresa A"
