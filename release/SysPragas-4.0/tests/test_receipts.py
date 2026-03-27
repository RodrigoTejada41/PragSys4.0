from decimal import Decimal


def create_customer(client, auth_headers, suffix="001"):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente Recibo {suffix}",
            "cpf_cnpj": f"1122334400{suffix.zfill(4)}",
            "endereco": "Rua do Recibo, 100",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11998887766",
            "contato": "Financeiro",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_technician(client, auth_headers, suffix="001"):
    response = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": f"Tecnico Recibo {suffix}",
            "registro": f"TEC-REC-{suffix}",
            "telefone": "11997776655",
            "ativo": True,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_work_order(client, auth_headers, customer_id, technician_id, suffix="001"):
    response = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": f"OS-REC-{suffix}",
            "cliente_id": customer_id,
            "tecnico_id": technician_id,
            "data_execucao": "2026-03-23",
            "hora_inicio": "08:00:00",
            "local_execucao": "Sala administrativa",
            "garantia_ate": "2026-04-23",
            "status": "aberta",
            "valor_servico": "280.00",
            "produtos": [],
            "pragas_ids": [],
            "gerar_financeiro": False,
            "gerar_agendamento": False,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_receipt_preview_create_and_duplicate_guard(client, auth_headers):
    customer = create_customer(client, auth_headers, "501")
    technician = create_technician(client, auth_headers, "501")
    work_order = create_work_order(client, auth_headers, customer["id"], technician["id"], "501")

    payload = {
        "cliente_id": customer["id"],
        "os_id": work_order["id"],
        "valor": "280.00",
        "forma_pagamento": "pix",
        "descricao": "Pagamento integral do servico executado",
        "data_recebimento": "2026-03-23",
    }

    preview_response = client.post("/api/v1/recibos/preview", headers=auth_headers, json=payload)
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["cliente_nome"] == customer["razao_social"]
    assert preview["os_numero"] == work_order["numero"]
    assert preview["valor_por_extenso"] == "duzentos e oitenta reais"
    assert "Recebemos de" in preview["texto_formal"]

    create_response = client.post("/api/v1/recibos", headers=auth_headers, json=payload)
    assert create_response.status_code == 201
    receipt = create_response.json()
    assert receipt["numero"].startswith("REC-2026-")
    assert receipt["finance_entry_id"] is not None
    assert receipt["historico"][0]["acao"] == "criado"

    finance_response = client.get(f"/api/v1/financeiro?search={receipt['numero']}", headers=auth_headers)
    assert finance_response.status_code == 200
    finance_entry = finance_response.json()[0]
    assert finance_entry["recibo_id"] == receipt["id"]
    assert finance_entry["status"] == "pago"
    assert Decimal(finance_entry["valor"]) == Decimal("280.00")
    assert Decimal(finance_entry["valor_pago"]) == Decimal("280.00")

    cash_response = client.get("/api/v1/financeiro/caixa", headers=auth_headers)
    assert cash_response.status_code == 200
    assert any(item["referencia"] == receipt["numero"] for item in cash_response.json())

    duplicate_response = client.post("/api/v1/recibos", headers=auth_headers, json=payload)
    assert duplicate_response.status_code == 400
    assert "mesmos dados principais" in duplicate_response.json()["detail"]


def test_receipt_update_syncs_finance_and_blocks_direct_finance_edit(client, auth_headers):
    customer = create_customer(client, auth_headers, "502")
    technician = create_technician(client, auth_headers, "502")
    work_order = create_work_order(client, auth_headers, customer["id"], technician["id"], "502")

    receipt = client.post(
        "/api/v1/recibos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "os_id": work_order["id"],
            "valor": "300.00",
            "forma_pagamento": "pix",
            "descricao": "Recebimento inicial",
            "data_recebimento": "2026-03-23",
        },
    ).json()

    update_response = client.put(
        f"/api/v1/recibos/{receipt['id']}",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "os_id": work_order["id"],
            "valor": "355.40",
            "forma_pagamento": "transferencia",
            "descricao": "Recebimento ajustado apos conciliacao",
            "data_recebimento": "2026-03-24",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert Decimal(updated["valor"]) == Decimal("355.40")
    assert updated["forma_pagamento"] == "transferencia"
    assert updated["historico"][0]["acao"] == "atualizado"

    finance_response = client.get(f"/api/v1/financeiro?search={updated['numero']}", headers=auth_headers)
    finance_entry = finance_response.json()[0]
    assert Decimal(finance_entry["valor"]) == Decimal("355.40")
    assert Decimal(finance_entry["valor_pago"]) == Decimal("355.40")
    assert finance_entry["data_pagamento"] == "2026-03-24"

    blocked_update = client.put(
        f"/api/v1/financeiro/{finance_entry['id']}",
        headers=auth_headers,
        json={
            "tipo": "receita",
            "descricao": "Tentativa direta",
            "valor": "10.00",
            "vencimento": "2026-03-24",
            "status": "pago",
            "categoria": "Recibo",
            "origem": "recibo",
            "referencia": updated["numero"],
            "parcela_atual": 1,
            "total_parcelas": 1,
            "cliente_id": customer["id"],
            "os_id": work_order["id"],
            "nfe_id": None,
        },
    )
    assert blocked_update.status_code == 400
    assert "recibo" in blocked_update.json()["detail"].lower()

    blocked_delete = client.delete(f"/api/v1/financeiro/{finance_entry['id']}", headers=auth_headers)
    assert blocked_delete.status_code == 400
    assert "recibo" in blocked_delete.json()["detail"].lower()


def test_receipt_pdf_and_controlled_delete_remove_financial_link(client, auth_headers):
    customer = create_customer(client, auth_headers, "503")
    receipt = client.post(
        "/api/v1/recibos",
        headers=auth_headers,
        json={
            "cliente_id": customer["id"],
            "os_id": None,
            "valor": "150.00",
            "forma_pagamento": "dinheiro",
            "descricao": "Pagamento avulso sem OS",
            "data_recebimento": "2026-03-25",
        },
    ).json()

    pdf_response = client.get(f"/api/v1/recibos/{receipt['id']}/pdf", headers=auth_headers)
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")
    assert len(pdf_response.content) > 1200

    delete_response = client.delete(f"/api/v1/recibos/{receipt['id']}", headers=auth_headers)
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/recibos", headers=auth_headers)
    assert list_response.status_code == 200
    assert all(item["id"] != receipt["id"] for item in list_response.json())

    finance_response = client.get(f"/api/v1/financeiro?search={receipt['numero']}", headers=auth_headers)
    assert finance_response.status_code == 200
    assert finance_response.json() == []

    get_deleted_response = client.get(f"/api/v1/recibos/{receipt['id']}", headers=auth_headers)
    assert get_deleted_response.status_code == 400
    assert "Recibo nao encontrado" in get_deleted_response.json()["detail"]
