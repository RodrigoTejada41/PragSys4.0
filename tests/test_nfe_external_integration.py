def create_customer(client, auth_headers, suffix="951"):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente NFe Externa {suffix}",
            "cpf_cnpj": f"1231231200{suffix.zfill(4)}",
            "endereco": "Rua Integracao, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11911112222",
            "contato": "Fiscal",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_product(client, auth_headers, suffix="951"):
    response = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": f"Produto NFe {suffix}",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "5%",
            "registro_ms": f"MS-NFE-{suffix}",
            "ncm": "38089199",
            "estoque_atual": "10.00",
            "estoque_minimo": "1.00",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_issue_nfe_calls_focus_and_persists_metadata(client, auth_headers, monkeypatch):
    from app.infrastructure.external_api.focus_nfe import FocusNfeClient

    customer = create_customer(client, auth_headers, "952")
    product = create_product(client, auth_headers, "952")

    monkeypatch.setattr(FocusNfeClient, "is_configured", lambda self: True)
    monkeypatch.setattr(
        FocusNfeClient,
        "emit_invoice",
        lambda self, reference, payload: {
            "status": "processando_autorizacao",
            "mensagem_sefaz": "Nota recebida para processamento",
            "caminho_xml_nota_fiscal": "/download/xml/arquivo.xml",
            "caminho_danfe": "/download/pdf/danfe.pdf",
            "referencia": reference,
            "payload_recebido": payload,
        },
    )

    response = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-EXT-001",
            "cliente_id": customer["id"],
            "valor_total": "100.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-28",
            "status": "emitida",
            "observacoes": "Emissao externa",
            "gerar_financeiro": True,
            "natureza_operacao": "Venda",
            "ambiente": "homologacao",
            "referencia_externa": "EXT001",
            "cnpj_emitente": "12345678000199",
            "nome_emitente": "Emitente Teste Ltda",
            "itens": [
                {
                    "descricao": "Produto Teste",
                    "produto_id": product["id"],
                    "ncm": "38089199",
                    "quantidade": "1.00",
                    "valor_unitario": "100.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["referencia_externa"] == "EXT001"
    assert payload["provedor"] == "focus_nfe"
    assert payload["status_processamento"] == "processando"
    assert payload["finance_entry_id"] is not None
    assert payload["xml_url"].endswith("/download/xml/arquivo.xml")
    assert payload["pdf_url"].endswith("/download/pdf/danfe.pdf")


def test_focus_webhook_requires_secret_when_configured(client, auth_headers, monkeypatch):
    from app.core.config import get_settings
    from app.infrastructure.external_api.focus_nfe import FocusNfeClient

    customer = create_customer(client, auth_headers, "955")
    product = create_product(client, auth_headers, "955")

    monkeypatch.setattr(FocusNfeClient, "is_configured", lambda self: True)
    monkeypatch.setattr(
        FocusNfeClient,
        "emit_invoice",
        lambda self, reference, payload: {
            "status": "processando_autorizacao",
            "referencia": reference,
        },
    )

    invoice = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-EXT-004",
            "cliente_id": customer["id"],
            "valor_total": "100.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-28",
            "status": "emitida",
            "gerar_financeiro": True,
            "natureza_operacao": "Venda",
            "ambiente": "homologacao",
            "referencia_externa": "EXT004",
            "cnpj_emitente": "12345678000199",
            "nome_emitente": "Emitente Teste Ltda",
            "itens": [
                {
                    "descricao": "Produto Teste 4",
                    "produto_id": product["id"],
                    "ncm": "38089199",
                    "quantidade": "1.00",
                    "valor_unitario": "100.00",
                }
            ],
        },
    ).json()

    monkeypatch.setenv("FOCUS_NFE_WEBHOOK_SECRET", "segredo-fiscal")
    get_settings.cache_clear()

    try:
        payload = {
            "referencia": invoice["referencia_externa"],
            "status": "autorizado",
            "chave_nfe": "35260312345678000199550010000000041000000040",
        }

        rejected = client.post("/api/v1/nfe/webhooks/focus", json=payload)
        assert rejected.status_code == 401

        accepted = client.post(
            "/api/v1/nfe/webhooks/focus",
            headers={"X-Focus-Nfe-Webhook-Secret": "segredo-fiscal"},
            json=payload,
        )
        assert accepted.status_code == 202
        assert accepted.json()["status_processamento"] == "autorizado"
    finally:
        get_settings.cache_clear()


def test_get_nfe_by_id_syncs_authorized_status(client, auth_headers, monkeypatch):
    from app.infrastructure.external_api.focus_nfe import FocusNfeClient

    customer = create_customer(client, auth_headers, "953")
    product = create_product(client, auth_headers, "953")

    monkeypatch.setattr(FocusNfeClient, "is_configured", lambda self: True)
    monkeypatch.setattr(
        FocusNfeClient,
        "emit_invoice",
        lambda self, reference, payload: {
            "status": "processando_autorizacao",
            "referencia": reference,
        },
    )
    monkeypatch.setattr(
        FocusNfeClient,
        "get_invoice",
        lambda self, reference: {
            "status": "autorizado",
            "chave_nfe": "35260312345678000199550010000000011000000010",
            "caminho_xml_nota_fiscal": "/download/xml/autorizada.xml",
            "caminho_danfe": "/download/pdf/autorizada.pdf",
            "mensagem_sefaz": "Autorizado o uso da NF-e",
            "referencia": reference,
        },
    )

    invoice = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-EXT-002",
            "cliente_id": customer["id"],
            "valor_total": "100.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-28",
            "status": "emitida",
            "gerar_financeiro": True,
            "natureza_operacao": "Venda",
            "ambiente": "homologacao",
            "referencia_externa": "EXT002",
            "cnpj_emitente": "12345678000199",
            "nome_emitente": "Emitente Teste Ltda",
            "itens": [
                {
                    "descricao": "Produto Teste 2",
                    "produto_id": product["id"],
                    "ncm": "38089199",
                    "quantidade": "1.00",
                    "valor_unitario": "100.00",
                }
            ],
        },
    ).json()

    response = client.get(f"/api/v1/nfe/{invoice['id']}?sync=true", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_processamento"] == "autorizado"
    assert payload["status_externo"] == "autorizado"
    assert payload["chave_nfe"] == "35260312345678000199550010000000011000000010"
    assert payload["xml_url"].endswith("/download/xml/autorizada.xml")
    assert payload["pdf_url"].endswith("/download/pdf/autorizada.pdf")


def test_delete_nfe_cancels_invoice_instead_of_removing_record(client, auth_headers, monkeypatch):
    from app.infrastructure.external_api.focus_nfe import FocusNfeClient

    customer = create_customer(client, auth_headers, "954")
    product = create_product(client, auth_headers, "954")

    monkeypatch.setattr(FocusNfeClient, "is_configured", lambda self: True)
    monkeypatch.setattr(FocusNfeClient, "emit_invoice", lambda self, reference, payload: {"status": "autorizado"})
    monkeypatch.setattr(
        FocusNfeClient,
        "cancel_invoice",
        lambda self, reference, justification=None: {
            "status": "cancelado",
            "mensagem_sefaz": justification or "Cancelada com sucesso",
        },
    )

    invoice = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-EXT-003",
            "cliente_id": customer["id"],
            "valor_total": "100.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-28",
            "status": "emitida",
            "gerar_financeiro": True,
            "natureza_operacao": "Venda",
            "ambiente": "homologacao",
            "referencia_externa": "EXT003",
            "cnpj_emitente": "12345678000199",
            "nome_emitente": "Emitente Teste Ltda",
            "itens": [
                {
                    "descricao": "Produto Teste 3",
                    "produto_id": product["id"],
                    "ncm": "38089199",
                    "quantidade": "1.00",
                    "valor_unitario": "100.00",
                }
            ],
        },
    ).json()

    response = client.request(
        "DELETE",
        f"/api/v1/nfe/{invoice['id']}",
        headers=auth_headers,
        json={"justificativa": "Erro de emissao"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "cancelada"
    assert payload["status_processamento"] == "cancelado"
    assert "Erro de emissao" in (payload["mensagem_retorno"] or payload["observacoes"] or "")

    list_response = client.get("/api/v1/nfe", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
