def _create_provider_company(client, auth_headers, suffix: str) -> dict:
    response = client.post(
        "/api/v1/empresas-prestadoras",
        headers=auth_headers,
        json={
            "razao_social": f"Empresa {suffix} Ltda",
            "nome_fantasia": f"Empresa {suffix}",
            "cnpj": f"{suffix * 4}0001{suffix}",
            "email": f"empresa{suffix}@teste.com",
            "telefone": "11999990000",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "is_active": True,
            "is_provider": True,
            "usuarios_vinculados_ids": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_license(client, auth_headers, company_id: int, suffix: str) -> None:
    response = client.post(
        "/api/v1/licencas",
        headers=auth_headers,
        json={
            "descricao": f"Licenca {suffix}",
            "start_date": "2026-03-20",
            "end_date": "2027-03-20",
            "max_users": 10,
            "status": "ativa",
            "empresa_prestadora_id": company_id,
        },
    )
    assert response.status_code == 201, response.text


def _create_user(client, auth_headers, *, username: str, role: str, company_id: int, permissions: dict | None = None) -> dict:
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": username,
            "username": username,
            "password": "senha123",
            "role": role,
            "is_active": True,
            "empresa_prestadora_id": company_id,
            "permissions": permissions or {},
        },
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"username": username, "password": "senha123"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_master_has_global_access(client, auth_headers):
    company = _create_provider_company(client, auth_headers, "81")
    assert company["id"] > 0
    _create_license(client, auth_headers, company["id"], "81")


def test_admin_cannot_manage_provider_companies_or_licenses(client, auth_headers):
    company = _create_provider_company(client, auth_headers, "82")
    _create_license(client, auth_headers, company["id"], "82")
    admin_headers = _create_user(client, auth_headers, username="adminrbac", role="admin", company_id=company["id"])

    company_response = client.post(
        "/api/v1/empresas-prestadoras",
        headers=admin_headers,
        json={
            "razao_social": "Nao Pode Ltda",
            "nome_fantasia": "Nao Pode",
            "cnpj": "83838383000183",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "is_active": True,
            "is_provider": True,
            "usuarios_vinculados_ids": [],
        },
    )
    assert company_response.status_code == 403

    license_response = client.post(
        "/api/v1/licencas",
        headers=admin_headers,
        json={
            "descricao": "Licenca indevida",
            "start_date": "2026-03-20",
            "end_date": "2027-03-20",
            "max_users": 10,
            "status": "ativa",
            "empresa_prestadora_id": company["id"],
        },
    )
    assert license_response.status_code == 403


def test_admin_custom_permission_can_block_finance_access(client, auth_headers):
    company = _create_provider_company(client, auth_headers, "84")
    _create_license(client, auth_headers, company["id"], "84")
    admin_headers = _create_user(
        client,
        auth_headers,
        username="adminnofin",
        role="admin",
        company_id=company["id"],
        permissions={"finance.view": False, "finance.manage": False},
    )

    response = client.get("/api/v1/financeiro", headers=admin_headers)
    assert response.status_code == 403


def test_operador_respects_granular_permissions(client, auth_headers):
    company = _create_provider_company(client, auth_headers, "85")
    _create_license(client, auth_headers, company["id"], "85")
    operator_headers = _create_user(
        client,
        auth_headers,
        username="operedit",
        role="operador",
        company_id=company["id"],
        permissions={"customers.edit": True, "stock.view": True},
    )

    customer_create = client.post(
        "/api/v1/clientes",
        headers=operator_headers,
        json={
            "razao_social": "Cliente Operador",
            "cpf_cnpj": "85858585000185",
            "endereco": "Rua Operador, 1",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11911111111",
            "contato": "Contato Operador",
        },
    )
    assert customer_create.status_code == 201, customer_create.text

    stock_view = client.get("/api/v1/produtos/estoque", headers=operator_headers)
    assert stock_view.status_code == 200
