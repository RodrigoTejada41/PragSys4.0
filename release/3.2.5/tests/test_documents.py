def _create_base_work_order(client, auth_headers):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Industria Delta",
            "cpf_cnpj": "55555555000100",
            "endereco": "Av. Industrial, 500",
            "cidade": "Sorocaba",
            "estado": "SP",
            "telefone": "11922223333",
            "contato": "Fernanda",
        },
    ).json()

    produto = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Inseticida Documento",
            "principio_ativo": "Fipronil",
            "grupo_quimico": "Fenilpirazol",
            "toxicidade": "Moderada",
            "concentracao": "12%",
            "registro_ms": "MS-DOC",
            "estoque_atual": "15.00",
            "estoque_minimo": "3.00",
        },
    ).json()

    praga = client.post(
        "/api/v1/pragas",
        headers=auth_headers,
        json={
            "nome_comum": "Roedor",
            "nome_cientifico": "Rattus norvegicus",
            "descricao": "Atividade em area de estoque",
        },
    ).json()

    tecnico = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Marcos Rocha",
            "registro": "TEC-DOC-01",
            "telefone": "11944445555",
            "ativo": True,
        },
    ).json()

    return client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-DOC-01",
            "cliente_id": cliente["id"],
            "tecnico_id": tecnico["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "07:30:00",
            "hora_fim": "09:15:00",
            "local_execucao": "Armazem e doca",
            "observacoes": "Monitoramento intensificado com aplicacao perimetral.",
            "garantia_ate": "2026-04-20",
            "status": "concluida",
            "valor_servico": "650.00",
            "produtos": [
                {
                    "produto_id": produto["id"],
                    "quantidade": "3.00",
                    "diluicao": "1:25",
                }
            ],
            "pragas_ids": [praga["id"]],
            "gerar_financeiro": True,
        },
    ).json()


def test_all_work_order_documents_are_generated(client, auth_headers):
    work_order = _create_base_work_order(client, auth_headers)

    endpoints = [
        f"/api/v1/os/{work_order['id']}/pdf",
        f"/api/v1/os/{work_order['id']}/relatorio-tecnico.pdf",
        f"/api/v1/os/{work_order['id']}/certificado-sanitario.pdf",
        f"/api/v1/os/{work_order['id']}/certificado-moldura.pdf",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        assert len(response.content) > 1200
