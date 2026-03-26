from decimal import Decimal


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


def test_company_data_isolated_across_core_modules(client, auth_headers):
    company_a_headers = _create_company_user(client, auth_headers, "admina", "11")
    company_b_headers = _create_company_user(client, auth_headers, "adminb", "22")

    customer = client.post(
        "/api/v1/clientes",
        headers=company_a_headers,
        json={
            "razao_social": "Cliente Empresa A",
            "cpf_cnpj": "11111111000111",
            "endereco": "Rua A, 1",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11911111111",
            "contato": "Contato A",
        },
    ).json()

    product = client.post(
        "/api/v1/produtos",
        headers=company_a_headers,
        json={
            "nome": "Produto Empresa A",
            "principio_ativo": "Ativo A",
            "grupo_quimico": "Grupo A",
            "toxicidade": "Baixa",
            "concentracao": "1%",
            "registro_ms": "MS-A-001",
            "estoque_atual": "10.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    pest = client.post(
        "/api/v1/pragas",
        headers=company_a_headers,
        json={
            "nome_comum": "Praga A",
            "nome_cientifico": "Species A",
            "descricao": "Descricao A",
        },
    ).json()

    technician = client.post(
        "/api/v1/tecnicos",
        headers=company_a_headers,
        json={
            "nome": "Tecnico Empresa A",
            "registro": "TEC-A-001",
            "telefone": "11922222222",
            "ativo": True,
        },
    ).json()

    work_order = client.post(
        "/api/v1/os",
        headers=company_a_headers,
        json={
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": "2026-03-21",
            "hora_inicio": "08:00:00",
            "hora_fim": "09:00:00",
            "local_execucao": "Unidade A",
            "observacoes": "Teste multempresa",
            "garantia_ate": "2026-04-21",
            "status": "aberta",
            "valor_servico": "250.00",
            "produtos": [{"produto_id": product["id"], "quantidade": "1.00", "diluicao": "1:10"}],
            "pragas_ids": [pest["id"]],
            "gerar_financeiro": True,
        },
    ).json()

    assert client.get("/api/v1/clientes", headers=company_b_headers).json() == []
    assert client.get("/api/v1/produtos", headers=company_b_headers).json() == []
    assert client.get("/api/v1/pragas", headers=company_b_headers).json() == []
    assert client.get("/api/v1/tecnicos", headers=company_b_headers).json() == []
    assert client.get("/api/v1/os", headers=company_b_headers).json() == []
    assert client.get("/api/v1/financeiro", headers=company_b_headers).json() == []

    customer_update = client.put(
        f"/api/v1/clientes/{customer['id']}",
        headers=company_b_headers,
        json={
            "razao_social": "Cliente Invadido",
            "cpf_cnpj": customer["cpf_cnpj"],
            "endereco": "Rua B, 2",
            "cidade": "Campinas",
            "estado": "SP",
            "telefone": "11900000000",
            "contato": "Contato B",
        },
    )
    assert customer_update.status_code == 400

    finance_entries = client.get("/api/v1/financeiro", headers=company_a_headers).json()
    assert len(finance_entries) == 1
    assert Decimal(finance_entries[0]["valor"]) == Decimal("250.00")

    finance_delete = client.delete(
        f"/api/v1/financeiro/{finance_entries[0]['id']}",
        headers=company_b_headers,
    )
    assert finance_delete.status_code == 400

    work_order_pdf = client.get(
        f"/api/v1/os/{work_order['id']}/pdf",
        headers=company_b_headers,
    )
    assert work_order_pdf.status_code == 400
