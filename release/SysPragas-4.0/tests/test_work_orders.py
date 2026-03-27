from datetime import date, timedelta
from decimal import Decimal


SAMPLE_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf"
    b"\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


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


def test_create_open_work_order_allows_empty_products(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Sem Produto",
            "cpf_cnpj": "88888888000100",
            "endereco": "Rua Sem Produto, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11955550000",
            "contato": "Patricia",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Cadastro Inicial",
            "registro": "TEC-SEM-PROD",
            "telefone": "11944440000",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-SEM-PRODUTO",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "10:00:00",
            "local_execucao": "Area externa",
            "garantia_ate": "2026-04-20",
            "status": "aberta",
            "valor_servico": "120.00",
            "produtos": [],
            "pragas_ids": [],
            "gerar_financeiro": True,
            "gerar_agendamento": False,
        },
    )

    assert os_response.status_code == 200
    data = os_response.json()
    assert data["numero"] == "OS-SEM-PRODUTO"
    assert data["produtos"] == []

    financeiro_response = client.get("/api/v1/financeiro", headers=auth_headers)
    assert financeiro_response.status_code == 200
    assert len(financeiro_response.json()) == 1
    assert Decimal(financeiro_response.json()[0]["valor"]) == Decimal("120.00")


def test_create_in_progress_work_order_requires_products(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Status Sem Produto",
            "cpf_cnpj": "77777777000100",
            "endereco": "Rua Status, 20",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11933330000",
            "contato": "Marcos",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Status",
            "registro": "TEC-STATUS",
            "telefone": "11922220000",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-STATUS-SEM-PROD",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "11:00:00",
            "local_execucao": "Area tecnica",
            "garantia_ate": "2026-04-20",
            "status": "em_execucao",
            "valor_servico": "120.00",
            "produtos": [],
            "pragas_ids": [],
            "gerar_financeiro": False,
            "gerar_agendamento": False,
        },
    )

    assert os_response.status_code == 400
    assert "ao menos um produto" in os_response.json()["detail"].lower()


def test_create_work_order_rejects_duplicate_products(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Produto Duplicado",
            "cpf_cnpj": "10101010000100",
            "endereco": "Rua D, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999990001",
            "contato": "Luiza",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Duplicado",
            "principio_ativo": "Deltametrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "2%",
            "registro_ms": "MS-DUPL",
            "estoque_atual": "10.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Duplicado",
            "registro": "TEC-DUPL",
            "telefone": "11988880001",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-DUPLICADA",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "08:00:00",
            "hora_fim": "09:00:00",
            "local_execucao": "Area interna",
            "garantia_ate": "2026-04-20",
            "valor_servico": "190.00",
            "produtos": [
                {"produto_id": produto["id"], "quantidade": "1.00", "diluicao": "1:10"},
                {"produto_id": produto["id"], "quantidade": "0.50", "diluicao": "1:20"},
            ],
            "pragas_ids": [],
            "gerar_financeiro": True,
        },
    )

    assert os_response.status_code == 400
    assert "mesmo produto" in os_response.json()["detail"]


def test_create_work_order_rejects_end_time_before_start(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Horario",
            "cpf_cnpj": "20202020000100",
            "endereco": "Rua E, 20",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999990002",
            "contato": "Bruno",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Horario",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "3%",
            "registro_ms": "MS-HORA",
            "estoque_atual": "10.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Horario",
            "registro": "TEC-HORA",
            "telefone": "11988880002",
            "ativo": True,
        },
    ).json()

    os_response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-HORA-1",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "10:00:00",
            "hora_fim": "09:30:00",
            "local_execucao": "Copa",
            "garantia_ate": "2026-04-20",
            "valor_servico": "210.00",
            "produtos": [{"produto_id": produto["id"], "quantidade": "1.00", "diluicao": "1:10"}],
            "pragas_ids": [],
            "gerar_financeiro": True,
        },
    )

    assert os_response.status_code == 400
    assert "hora final" in os_response.json()["detail"].lower()


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


def test_work_order_allows_photo_upload_and_removal(client, auth_headers):
    execution_date = date.today() + timedelta(days=2)
    warranty_date = execution_date + timedelta(days=30)

    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Foto",
            "cpf_cnpj": "22222222000100",
            "endereco": "Rua Foto, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11955556666",
            "contato": "Helena",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Foto",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "5%",
            "registro_ms": "MS-FOTO",
            "estoque_atual": "4.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Foto",
            "registro": "TEC-FOTO",
            "telefone": "11944445555",
            "ativo": True,
        },
    ).json()

    work_order = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-FOTO-1",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": execution_date.isoformat(),
            "hora_inicio": "09:00:00",
            "hora_fim": "10:00:00",
            "local_execucao": "Cozinha industrial",
            "observacoes": "Registrar fotos do atendimento",
            "garantia_ate": warranty_date.isoformat(),
            "status": "aberta",
            "valor_servico": "220.00",
            "produtos": [
                {
                    "produto_id": produto["id"],
                    "quantidade": "1.00",
                    "diluicao": "1:20",
                }
            ],
            "pragas_ids": [],
            "gerar_financeiro": True,
        },
    ).json()

    upload_response = client.post(
        f"/api/v1/os/{work_order['id']}/fotos",
        headers=auth_headers,
        files=[("files", ("ambiente.png", SAMPLE_PNG, "image/png"))],
    )
    assert upload_response.status_code == 200
    uploaded = upload_response.json()
    assert len(uploaded["fotos"]) == 1
    assert uploaded["fotos"][0]["filename"] == "ambiente.png"
    assert uploaded["fotos"][0]["url"] == f"/api/v1/os/fotos/{uploaded['fotos'][0]['id']}"

    image_response = client.get(uploaded["fotos"][0]["url"], headers=auth_headers)
    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/png"
    assert image_response.content == SAMPLE_PNG

    delete_response = client.delete(
        f"/api/v1/os/{work_order['id']}/fotos/{uploaded['fotos'][0]['id']}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["fotos"] == []
