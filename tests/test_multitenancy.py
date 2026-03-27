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


def _create_provider_company(client, auth_headers, suffix: str, **overrides) -> dict:
    payload = {
        "razao_social": f"Empresa {suffix} Ltda",
        "nome_fantasia": f"Empresa {suffix}",
        "cnpj": f"{suffix * 4}0001{suffix}",
        "email": f"empresa{suffix}@teste.com",
        "telefone": "11999990000",
        "cidade": "Sao Paulo",
        "estado": "SP",
        "is_active": True,
        "is_provider": True,
        "empresa_pai_id": None,
        "compartilha_visualizacao_estoque": False,
        "usuarios_vinculados_ids": [],
    }
    payload.update(overrides)
    response = client.post("/api/v1/empresas-prestadoras", headers=auth_headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_company_license(client, auth_headers, company_id: int, suffix: str) -> dict:
    response = client.post(
        "/api/v1/licencas",
        headers=auth_headers,
        json={
            "descricao": f"Licenca {suffix}",
            "start_date": "2026-03-20",
            "end_date": "2027-03-20",
            "max_users": 10,
            "status": "ativa",
            "notes": "Licenca para teste",
            "empresa_prestadora_id": company_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_linked_user(client, auth_headers, username: str, company_id: int, role: str = "admin", password: str = "senha123") -> dict:
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": username,
            "username": username,
            "password": password,
            "role": role,
            "is_active": True,
            "empresa_prestadora_id": company_id,
        },
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
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


def test_user_requires_provider_company(client, auth_headers):
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": "Usuario Sem Empresa",
            "username": "semempresa",
            "password": "senha123",
            "role": "admin",
            "is_active": True,
        },
    )
    assert response.status_code == 400
    assert "empresa prestadora" in response.json()["detail"].lower()


def test_stock_visibility_respects_parent_child_relationship_without_merging_balances(client, auth_headers):
    matriz = _create_provider_company(client, auth_headers, "33", compartilha_visualizacao_estoque=True)
    filial = _create_provider_company(
        client,
        auth_headers,
        "44",
        empresa_pai_id=matriz["id"],
        compartilha_visualizacao_estoque=True,
    )
    independente = _create_provider_company(client, auth_headers, "55")

    _create_company_license(client, auth_headers, matriz["id"], "33")
    _create_company_license(client, auth_headers, filial["id"], "44")
    _create_company_license(client, auth_headers, independente["id"], "55")

    matriz_headers = _create_linked_user(client, auth_headers, "matrizadmin", matriz["id"])
    filial_headers = _create_linked_user(client, auth_headers, "filialadmin", filial["id"])
    independente_headers = _create_linked_user(client, auth_headers, "indepadmin", independente["id"])

    product_matriz = client.post(
        "/api/v1/produtos",
        headers=matriz_headers,
        json={
            "nome": "Inseticida Matriz",
            "principio_ativo": "Ativo M",
            "grupo_quimico": "Grupo M",
            "toxicidade": "Media",
            "concentracao": "2%",
            "registro_ms": "MS-M-001",
            "estoque_atual": "10.00",
            "estoque_minimo": "2.00",
        },
    )
    assert product_matriz.status_code == 201, product_matriz.text

    product_filial = client.post(
        "/api/v1/produtos",
        headers=filial_headers,
        json={
            "nome": "Inseticida Filial",
            "principio_ativo": "Ativo F",
            "grupo_quimico": "Grupo F",
            "toxicidade": "Baixa",
            "concentracao": "1%",
            "registro_ms": "MS-F-001",
            "estoque_atual": "4.00",
            "estoque_minimo": "1.00",
        },
    )
    assert product_filial.status_code == 201, product_filial.text

    filial_stock = client.get("/api/v1/produtos/estoque", headers=filial_headers)
    assert filial_stock.status_code == 200, filial_stock.text
    filial_items = filial_stock.json()
    assert {item["empresa_prestadora_id"] for item in filial_items} == {matriz["id"], filial["id"]}
    assert sum(Decimal(item["estoque_atual"]) for item in filial_items if item["empresa_prestadora_id"] == matriz["id"]) == Decimal("10.00")
    assert sum(Decimal(item["estoque_atual"]) for item in filial_items if item["empresa_prestadora_id"] == filial["id"]) == Decimal("4.00")

    products_filial_catalog = client.get("/api/v1/produtos", headers=filial_headers)
    assert products_filial_catalog.status_code == 200
    assert [item["nome"] for item in products_filial_catalog.json()] == ["Inseticida Filial"]

    independente_stock = client.get("/api/v1/produtos/estoque", headers=independente_headers)
    assert independente_stock.status_code == 200
    assert independente_stock.json() == []


def test_stock_movement_history_is_isolated_by_company(client, auth_headers):
    company_a_headers = _create_company_user(client, auth_headers, "estoquea", "66")
    company_b_headers = _create_company_user(client, auth_headers, "estoqueb", "77")

    product_a = client.post(
        "/api/v1/produtos",
        headers=company_a_headers,
        json={
            "nome": "Produto Estoque A",
            "principio_ativo": "Ativo A",
            "grupo_quimico": "Grupo A",
            "toxicidade": "Baixa",
            "concentracao": "1%",
            "registro_ms": "MS-STK-A",
            "estoque_atual": "5.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    response = client.post(
        "/api/v1/produtos/estoque/movimentacoes",
        headers=company_a_headers,
        json={
            "produto_id": product_a["id"],
            "tipo_movimento": "saida",
            "quantidade": "2.00",
            "motivo": "Consumo em manutencao interna",
            "referencia": "AJ-01",
        },
    )
    assert response.status_code == 201, response.text
    movement = response.json()
    assert Decimal(movement["saldo_anterior"]) == Decimal("5.00")
    assert Decimal(movement["saldo_posterior"]) == Decimal("3.00")

    company_a_movements = client.get("/api/v1/produtos/estoque/movimentacoes", headers=company_a_headers)
    assert company_a_movements.status_code == 200
    assert len(company_a_movements.json()) >= 2

    company_b_movements = client.get("/api/v1/produtos/estoque/movimentacoes", headers=company_b_headers)
    assert company_b_movements.status_code == 200
    assert company_b_movements.json() == []
