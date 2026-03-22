from decimal import Decimal


def create_customer(client, auth_headers, suffix="901"):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente Financeiro {suffix}",
            "cpf_cnpj": f"9988776600{suffix.zfill(4)}",
            "endereco": "Rua Fiscal, 100",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999998888",
            "contato": "Financeiro",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_product_applies_ncm_tax_profile_and_allows_manual_override(client, auth_headers):
    product_response = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Fiscal",
            "principio_ativo": "Deltametrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "2%",
            "registro_ms": "MS-FISCAL-1",
            "ncm": "38089199",
            "estoque_atual": "3.00",
            "estoque_minimo": "1.00",
        },
    )

    assert product_response.status_code == 201
    product = product_response.json()
    assert product["ncm"] == "38089199"
    assert "Inseticidas" in product["ncm_descricao"]
    assert Decimal(product["aliquota_icms"]) == Decimal("18.0000")
    assert Decimal(product["aliquota_pis"]) == Decimal("1.6500")

    update_response = client.put(
        f"/api/v1/produtos/{product['id']}",
        headers=auth_headers,
        json={
            "nome": "Produto Fiscal Manual",
            "principio_ativo": "Deltametrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "2%",
            "registro_ms": "MS-FISCAL-1",
            "ncm": "38089199",
            "ncm_descricao": "Classificacao manual",
            "aliquota_icms": "12.0000",
            "aliquota_ipi": "1.5000",
            "aliquota_pis": "0.6500",
            "aliquota_cofins": "3.0000",
            "override_tributacao": True,
            "estoque_atual": "3.00",
            "estoque_minimo": "1.00",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["override_tributacao"] is True
    assert updated["ncm_descricao"] == "Classificacao manual"
    assert Decimal(updated["aliquota_icms"]) == Decimal("12.0000")
    assert Decimal(updated["aliquota_cofins"]) == Decimal("3.0000")


def test_nfe_creation_generates_financial_entry_and_supports_search(client, auth_headers):
    customer = create_customer(client, auth_headers, "902")

    nfe_response = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-9001",
            "cliente_id": customer["id"],
            "valor_total": "1250.50",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-28",
            "status": "emitida",
            "observacoes": "Titulo gerado automaticamente",
            "gerar_financeiro": True,
        },
    )

    assert nfe_response.status_code == 201
    invoice = nfe_response.json()
    assert invoice["finance_entry_id"] is not None

    finance_response = client.get("/api/v1/financeiro?search=NFE-9001", headers=auth_headers)
    assert finance_response.status_code == 200
    assert len(finance_response.json()) == 1
    entry = finance_response.json()[0]
    assert entry["nfe_id"] == invoice["id"]
    assert entry["cliente_id"] == customer["id"]
    assert Decimal(entry["valor"]) == Decimal("1250.50")


def test_financial_entry_linked_to_nfe_cannot_be_changed_directly(client, auth_headers):
    customer = create_customer(client, auth_headers, "903")

    invoice = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-9002",
            "cliente_id": customer["id"],
            "valor_total": "800.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-30",
            "status": "emitida",
            "observacoes": None,
            "gerar_financeiro": True,
        },
    ).json()

    finance_id = invoice["finance_entry_id"]
    update_finance = client.put(
        f"/api/v1/financeiro/{finance_id}",
        headers=auth_headers,
        json={
            "tipo": "receita",
            "descricao": "Tentativa manual",
            "valor": "10.00",
            "vencimento": "2026-03-30",
            "status": "pendente",
            "cliente_id": customer["id"],
            "nfe_id": invoice["id"],
        },
    )
    assert update_finance.status_code == 400
    assert "NF-e" in update_finance.json()["detail"]

    delete_finance = client.delete(f"/api/v1/financeiro/{finance_id}", headers=auth_headers)
    assert delete_finance.status_code == 400
    assert "NF-e" in delete_finance.json()["detail"]

    update_invoice = client.put(
        f"/api/v1/nfe/{invoice['id']}",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-9002",
            "cliente_id": customer["id"],
            "valor_total": "950.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-04-02",
            "status": "emitida",
            "observacoes": "Atualizada",
        },
    )
    assert update_invoice.status_code == 200

    finance_after = client.get("/api/v1/financeiro?search=NFE-9002", headers=auth_headers)
    entry = finance_after.json()[0]
    assert Decimal(entry["valor"]) == Decimal("950.00")
    assert entry["vencimento"] == "2026-04-02"


def test_simples_summary_and_cash_flow_summary_reflect_issued_nfe(client, auth_headers):
    customer = create_customer(client, auth_headers, "904")

    invoice = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-9003",
            "cliente_id": customer["id"],
            "valor_total": "1500.00",
            "data_emissao": "2026-03-10",
            "data_vencimento": "2026-03-20",
            "status": "emitida",
            "observacoes": "Resumo mensal",
            "gerar_financeiro": True,
        },
    ).json()

    configs_response = client.get("/api/v1/fiscal/simples", headers=auth_headers)
    assert configs_response.status_code == 200
    assert len(configs_response.json()) >= 1

    summary_response = client.get("/api/v1/fiscal/simples/resumo/2026/3", headers=auth_headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["referencia"] == "2026-03"
    assert Decimal(summary["faturamento_bruto"]) == Decimal("1500.00")
    assert Decimal(summary["imposto_estimado"]) == Decimal("90.00")

    pay_response = client.post(f"/api/v1/financeiro/{invoice['finance_entry_id']}/pagar", headers=auth_headers)
    assert pay_response.status_code == 200

    cash_flow_response = client.get("/api/v1/fiscal/fluxo-caixa/resumo?period=monthly", headers=auth_headers)
    assert cash_flow_response.status_code == 200
    cash_flow = cash_flow_response.json()
    assert Decimal(cash_flow["recebido"]) == Decimal("1500.00")
    assert cash_flow["quantidade_recebida"] >= 1
