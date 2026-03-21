from datetime import date, timedelta
from decimal import Decimal


def test_create_work_order_decrements_stock_and_generates_finance(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Mercado Central",
            "cpf_cnpj": "12345678000100",
            "endereco": "Rua A, 100",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999990000",
            "contato": "Mariana",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Inseticida X",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "20%",
            "registro_ms": "MS-123",
            "estoque_atual": "10.00",
            "estoque_minimo": "2.00",
        },
    ).json()

    praga = client.post(
        "/api/v1/pragas",
        headers=auth_headers,
        json={
            "nome_comum": "Barata",
            "nome_cientifico": "Periplaneta americana",
            "descricao": "Infestacao urbana",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Carlos Lima",
            "registro": "TEC-001",
            "telefone": "11988887777",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-1001",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "08:00:00",
            "hora_fim": "09:30:00",
            "local_execucao": "Deposito principal",
            "observacoes": "Aplicacao preventiva",
            "garantia_ate": "2026-04-20",
            "status": "aberta",
            "valor_servico": "450.00",
            "produtos": [
                {
                    "produto_id": produto["id"],
                    "quantidade": "2.50",
                    "diluicao": "1:10",
                }
            ],
            "pragas_ids": [praga["id"]],
            "gerar_financeiro": True,
        },
    )

    assert os_response.status_code == 200
    data = os_response.json()
    assert data["numero"] == "OS-1001"
    assert data["cliente"]["razao_social"] == "Mercado Central"
    assert Decimal(data["produtos"][0]["quantidade"]) == Decimal("2.50")

    produtos_response = client.get("/api/v1/produtos", headers=auth_headers)
    estoque_atual = Decimal(produtos_response.json()[0]["estoque_atual"])
    assert estoque_atual == Decimal("7.50")

    financeiro_response = client.get("/api/v1/financeiro", headers=auth_headers)
    assert financeiro_response.status_code == 200
    assert len(financeiro_response.json()) == 1
    assert Decimal(financeiro_response.json()[0]["valor"]) == Decimal("450.00")


def test_create_work_order_requires_stock(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Condominio Azul",
            "cpf_cnpj": "99999999000100",
            "endereco": "Rua B, 200",
            "cidade": "Campinas",
            "estado": "SP",
            "telefone": "11999991111",
            "contato": "Paulo",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Larvicida Y",
            "principio_ativo": "Bti",
            "grupo_quimico": "Biologico",
            "toxicidade": "Baixa",
            "concentracao": "5%",
            "registro_ms": "MS-456",
            "estoque_atual": "1.00",
            "estoque_minimo": "0.50",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Ana Costa",
            "registro": "TEC-002",
            "telefone": "11977776666",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-2001",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "10:00:00",
            "local_execucao": "Caixa dagua",
            "garantia_ate": "2026-03-25",
            "valor_servico": "150.00",
            "produtos": [
                {
                    "produto_id": produto["id"],
                    "quantidade": "3.00",
                    "diluicao": "1:5",
                }
            ],
            "pragas_ids": [],
            "gerar_financeiro": True,
        },
    )

    assert os_response.status_code == 400
    assert "Estoque insuficiente" in os_response.json()["detail"]


def test_quick_actions_complete_and_settle_work_order_and_finance(client, auth_headers):
    execution_date = date.today() + timedelta(days=5)
    warranty_date = execution_date + timedelta(days=30)

    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Baixa",
            "cpf_cnpj": "55555555000100",
            "endereco": "Rua C, 300",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11911112222",
            "contato": "Renata",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Gel Premium",
            "principio_ativo": "Fipronil",
            "grupo_quimico": "Fenilpirazol",
            "toxicidade": "Baixa",
            "concentracao": "2%",
            "registro_ms": "MS-789",
            "estoque_atual": "5.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Baixa",
            "registro": "TEC-003",
            "telefone": "11922223333",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-3001",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": execution_date.isoformat(),
            "hora_inicio": "14:00:00",
            "hora_fim": "15:00:00",
            "local_execucao": "Area gourmet",
            "observacoes": "Visita de rotina",
            "garantia_ate": warranty_date.isoformat(),
            "status": "aberta",
            "valor_servico": "280.00",
            "produtos": [
                {
                    "produto_id": produto["id"],
                    "quantidade": "1.00",
                    "diluicao": "Pronto uso",
                }
            ],
            "pragas_ids": [],
            "gerar_financeiro": True,
        },
    )
    assert os_response.status_code == 200
    work_order = os_response.json()

    efetuar_response = client.post(f"/api/v1/os/{work_order['id']}/efetuar", headers=auth_headers)
    assert efetuar_response.status_code == 200
    assert efetuar_response.json()["status"] == "concluida"

    financeiro_response = client.get("/api/v1/financeiro", headers=auth_headers)
    assert financeiro_response.status_code == 200
    assert len(financeiro_response.json()) == 1
    linked_entry = financeiro_response.json()[0]
    assert linked_entry["status"] == "pendente"

    pagar_response = client.post(f"/api/v1/financeiro/{linked_entry['id']}/pagar", headers=auth_headers)
    assert pagar_response.status_code == 200
    assert pagar_response.json()["status"] == "pago"

    baixar_response = client.post(f"/api/v1/os/{work_order['id']}/baixar", headers=auth_headers)
    assert baixar_response.status_code == 200
    assert baixar_response.json()["status"] == "concluida"

    financeiro_final = client.get("/api/v1/financeiro", headers=auth_headers)
    assert financeiro_final.status_code == 200
    assert financeiro_final.json()[0]["status"] == "pago"
