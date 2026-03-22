def test_master_can_manage_users_and_licenses(client, auth_headers):
    create_user_response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": "Operador Teste",
            "username": "operador1",
            "password": "senha123",
            "role": "operador",
            "is_active": True,
            "nova_empresa_prestadora": {
                "razao_social": "Prestadora Operador 1 Ltda",
                "nome_fantasia": "Prestadora Operador 1",
                "cnpj": "12345678000190",
                "email": "operador1@prestadora.com",
                "telefone": "11999990000",
                "cidade": "Sao Paulo",
                "estado": "SP",
            },
            "licenca_inicial": {
                "descricao": "Licenca inicial Operador 1",
                "start_date": "2026-03-20",
                "end_date": "2027-03-20",
                "max_users": 5,
                "status": "ativa",
                "notes": "Licenca vinculada a empresa da prestadora",
            },
        },
    )
    assert create_user_response.status_code == 201
    assert create_user_response.json()["role"] == "operador"
    assert create_user_response.json()["empresa_prestadora_nome"] == "Prestadora Operador 1"

    licenses_response = client.get("/api/v1/licencas", headers=auth_headers)
    assert licenses_response.status_code == 200
    assert len(licenses_response.json()) >= 1

    create_license_response = client.post(
        "/api/v1/licencas",
        headers=auth_headers,
        json={
            "descricao": "Renovacao anual",
            "start_date": "2026-03-20",
            "end_date": "2027-03-20",
            "max_users": 15,
            "status": "ativa",
            "notes": "Licenca de teste",
        },
    )
    assert create_license_response.status_code == 201
    assert create_license_response.json()["max_users"] == 15


def test_operador_can_use_os_but_cannot_access_finance_or_license_management(client, auth_headers):
    user_response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": "Tecnico App",
            "username": "tecnicoapp",
            "password": "senha123",
            "role": "operador",
            "is_active": True,
            "nova_empresa_prestadora": {
                "razao_social": "Prestadora Tecnico App Ltda",
                "nome_fantasia": "Prestadora Tecnico",
                "cnpj": "98765432000110",
                "email": "tecnico@prestadora.com",
                "telefone": "11988887777",
                "cidade": "Campinas",
                "estado": "SP",
            },
            "licenca_inicial": {
                "descricao": "Licenca inicial Tecnico",
                "start_date": "2026-03-20",
                "end_date": "2027-03-20",
                "max_users": 3,
                "status": "ativa",
                "notes": "Licenca de teste da prestadora",
            },
        },
    )
    assert user_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "tecnicoapp", "password": "senha123"},
    )
    assert login_response.status_code == 200
    operador_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    cliente_response = client.post(
        "/api/v1/clientes",
        headers=operador_headers,
        json={
            "razao_social": "Cliente Operador",
            "cpf_cnpj": "40404040000100",
            "endereco": "Rua Operador, 1",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11900000000",
            "contato": "Julia",
        },
    )
    assert cliente_response.status_code == 201

    finance_response = client.get("/api/v1/financeiro", headers=operador_headers)
    assert finance_response.status_code == 403

    licenses_response = client.get("/api/v1/licencas", headers=operador_headers)
    assert licenses_response.status_code == 403

    product_response = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Operacional",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "10%",
            "registro_ms": "MS-OPER",
            "estoque_atual": "4.00",
            "estoque_minimo": "1.00",
        },
    )
    technician_response = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Operacional",
            "registro": "TEC-OPER",
            "telefone": "11933334444",
            "ativo": True,
        },
    )
    work_order_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-RBAC-1",
            "cliente_id": cliente_response.json()["id"],
            "tecnico_id": technician_response.json()["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "09:00:00",
            "hora_fim": "10:00:00",
            "local_execucao": "Cozinha",
            "observacoes": "Teste RBAC",
            "garantia_ate": "2026-04-20",
            "status": "aberta",
            "valor_servico": "120.00",
            "produtos": [{"produto_id": product_response.json()["id"], "quantidade": "1.00", "diluicao": "1:10"}],
            "pragas_ids": [],
            "gerar_financeiro": True,
        },
    )
    assert work_order_response.status_code == 200

    efetuar_response = client.post(
        f"/api/v1/os/{work_order_response.json()['id']}/efetuar",
        headers=operador_headers,
    )
    assert efetuar_response.status_code == 200

    baixar_response = client.post(
        f"/api/v1/os/{work_order_response.json()['id']}/baixar",
        headers=operador_headers,
    )
    assert baixar_response.status_code == 403
