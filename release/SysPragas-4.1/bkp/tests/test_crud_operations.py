from pathlib import Path
from decimal import Decimal

from app.application import services


def create_customer(client, auth_headers, suffix="01"):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente {suffix}",
            "cpf_cnpj": f"1234567800{suffix.zfill(4)}",
            "endereco": "Rua Teste, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999990000",
            "contato": "Contato",
        },
    )
    return response.json()


def sample_nfe_xml() -> bytes:
    return """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
      <NFe>
        <infNFe Id="NFe35260312345678000100550010000012341000012345" versao="4.00">
          <ide>
            <cUF>35</cUF>
            <nNF>1234</nNF>
            <dhEmi>2026-03-21T10:30:00-03:00</dhEmi>
          </ide>
          <emit>
            <xNome>Fornecedor XML Ltda</xNome>
            <CNPJ>12345678000100</CNPJ>
          </emit>
          <det nItem="1">
            <prod>
              <cProd>XML-001</cProd>
              <cEAN>SEM GTIN</cEAN>
              <xProd>Inseticida NF</xProd>
              <NCM>38089199</NCM>
              <CFOP>1102</CFOP>
              <uCom>UN</uCom>
              <qCom>3.00</qCom>
              <vUnCom>25.00</vUnCom>
              <vProd>75.00</vProd>
            </prod>
          </det>
          <det nItem="2">
            <prod>
              <cProd>MS-EXIST</cProd>
              <cEAN>SEM GTIN</cEAN>
              <xProd>Produto Existente</xProd>
              <NCM>38089199</NCM>
              <CFOP>1102</CFOP>
              <uCom>UN</uCom>
              <qCom>2.00</qCom>
              <vUnCom>15.00</vUnCom>
              <vProd>30.00</vProd>
            </prod>
          </det>
          <total>
            <ICMSTot>
              <vNF>105.00</vNF>
            </ICMSTot>
          </total>
        </infNFe>
      </NFe>
    </nfeProc>
    """.encode("utf-8")


def sample_products_csv() -> bytes:
    return """nome;principio_ativo;grupo_quimico;toxicidade;concentracao;registro_ms;quantidade_entrada;estoque_minimo;custo_total;fornecedor_nome;referencia;data_entrada;categoria_financeira;observacoes;registrar_financeiro
Produto CSV Novo;Ativo CSV;Grupo CSV;Baixa;2%;CSV-001;5.00;1.00;150.00;Fornecedor CSV;NF-CSV-001;2026-03-21;Compra de estoque;Entrada inicial;true
Produto Existente CSV;Ativo Existente;Grupo Existente;Media;1%;CSV-EXIST;2.50;0.50;80.00;Fornecedor CSV;NF-CSV-002;2026-03-21;Reposicao;Complemento;true
""".encode("utf-8")


def test_update_and_delete_core_records(client, auth_headers):
    customer = create_customer(client, auth_headers, "11")
    customer_update = client.put(
        f"/api/v1/clientes/{customer['id']}",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Atualizado",
            "cpf_cnpj": customer["cpf_cnpj"],
            "endereco": "Rua Nova, 20",
            "cidade": "Campinas",
            "estado": "SP",
            "telefone": "11911112222",
            "contato": "Luciana",
        },
    )
    assert customer_update.status_code == 200
    assert customer_update.json()["razao_social"] == "Cliente Atualizado"

    finance_entry = client.post(
        "/api/v1/financeiro",
        headers=auth_headers,
        json={
            "tipo": "receita",
            "descricao": "Receita manual",
            "valor": "100.00",
            "vencimento": "2026-03-25",
            "status": "pendente",
            "cliente_id": customer["id"],
            "os_id": None,
        },
    ).json()

    finance_update = client.put(
        f"/api/v1/financeiro/{finance_entry['id']}",
        headers=auth_headers,
        json={
            "tipo": "despesa",
            "descricao": "Despesa manual",
            "valor": "80.00",
            "vencimento": "2026-03-28",
            "status": "pago",
            "categoria": "Administrativo",
            "cliente_id": customer["id"],
            "os_id": None,
        },
    )
    assert finance_update.status_code == 200
    assert finance_update.json()["tipo"] == "despesa"
    assert Decimal(finance_update.json()["valor_pago"]) == Decimal("80.00")

    delete_customer_fail = client.delete(f"/api/v1/clientes/{customer['id']}", headers=auth_headers)
    assert delete_customer_fail.status_code == 400

    delete_finance = client.delete(f"/api/v1/financeiro/{finance_entry['id']}", headers=auth_headers)
    assert delete_finance.status_code == 400

    open_finance_entry = client.post(
        "/api/v1/financeiro",
        headers=auth_headers,
        json={
            "tipo": "despesa",
            "descricao": "Despesa deletavel",
            "valor": "20.00",
            "vencimento": "2026-04-10",
            "status": "pendente",
            "categoria": "Operacional",
            "cliente_id": None,
            "os_id": None,
        },
    ).json()
    assert client.delete(f"/api/v1/financeiro/{open_finance_entry['id']}", headers=auth_headers).status_code == 204

    product = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Z",
            "principio_ativo": "Ativo Z",
            "grupo_quimico": "Grupo Z",
            "toxicidade": "Baixa",
            "concentracao": "1%",
            "registro_ms": "MS-Z",
            "estoque_atual": "6.00",
            "estoque_minimo": "1.00",
        },
    ).json()
    product_update = client.put(
        f"/api/v1/produtos/{product['id']}",
        headers=auth_headers,
        json={
            "nome": "Produto Z Atualizado",
            "principio_ativo": "Ativo ZZ",
            "grupo_quimico": "Grupo ZZ",
            "toxicidade": "Media",
            "concentracao": "2%",
            "registro_ms": "MS-ZZ",
            "estoque_atual": "8.00",
            "estoque_minimo": "2.00",
        },
    )
    assert product_update.status_code == 200
    assert Decimal(product_update.json()["estoque_atual"]) == Decimal("8.00")
    assert client.delete(f"/api/v1/produtos/{product['id']}", headers=auth_headers).status_code == 204

    pest = client.post(
        "/api/v1/pragas",
        headers=auth_headers,
        json={
            "nome_comum": "Cupim",
            "nome_cientifico": "Isoptera",
            "descricao": "Ataque em madeira",
        },
    ).json()
    pest_update = client.put(
        f"/api/v1/pragas/{pest['id']}",
        headers=auth_headers,
        json={
            "nome_comum": "Cupim subterraneo",
            "nome_cientifico": "Isoptera sp",
            "descricao": "Ataque severo",
        },
    )
    assert pest_update.status_code == 200
    assert client.delete(f"/api/v1/pragas/{pest['id']}", headers=auth_headers).status_code == 204

    technician = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Livre",
            "registro": "TEC-LIVRE",
            "telefone": "11988880000",
            "ativo": True,
        },
    ).json()
    technician_update = client.put(
        f"/api/v1/tecnicos/{technician['id']}",
        headers=auth_headers,
        json={
            "nome": "Tecnico Atualizado",
            "registro": "TEC-LIVRE",
            "telefone": "11900001111",
            "ativo": False,
        },
    )
    assert technician_update.status_code == 200
    assert technician_update.json()["ativo"] is False
    assert client.delete(f"/api/v1/tecnicos/{technician['id']}", headers=auth_headers).status_code == 204


def test_update_and_delete_work_order_reconcile_stock_and_finance(client, auth_headers):
    customer = create_customer(client, auth_headers, "22")
    product = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Inseticida Editavel",
            "principio_ativo": "Permetrina",
            "grupo_quimico": "Piretroide",
            "toxicidade": "Moderada",
            "concentracao": "10%",
            "registro_ms": "MS-EDIT",
            "estoque_atual": "10.00",
            "estoque_minimo": "2.00",
        },
    ).json()
    pest = client.post(
        "/api/v1/pragas",
        headers=auth_headers,
        json={
            "nome_comum": "Formiga",
            "nome_cientifico": "Formicidae",
            "descricao": "Colonia em area interna",
        },
    ).json()
    technician = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico OS",
            "registro": "TEC-OS-01",
            "telefone": "11933334444",
            "ativo": True,
        },
    ).json()

    work_order = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-EDIT-1",
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": "2026-03-20",
            "hora_inicio": "08:00:00",
            "hora_fim": "09:00:00",
            "local_execucao": "Galpao",
            "observacoes": "Primeira versao",
            "garantia_ate": "2026-04-01",
            "status": "aberta",
            "valor_servico": "300.00",
            "produtos": [{"produto_id": product["id"], "quantidade": "2.50", "diluicao": "1:20"}],
            "pragas_ids": [pest["id"]],
            "gerar_financeiro": True,
        },
    ).json()

    update_response = client.put(
        f"/api/v1/os/{work_order['id']}",
        headers=auth_headers,
        json={
            "numero": "OS-EDIT-1",
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": "2026-03-21",
            "hora_inicio": "10:00:00",
            "hora_fim": "11:00:00",
            "local_execucao": "Area externa",
            "observacoes": "Versao atualizada",
            "garantia_ate": "2026-04-15",
            "status": "concluida",
            "valor_servico": "500.00",
            "produtos": [{"produto_id": product["id"], "quantidade": "1.50", "diluicao": "1:15"}],
            "pragas_ids": [pest["id"]],
            "gerar_financeiro": True,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "concluida"
    assert update_response.json()["numero"] == work_order["numero"]

    products_response = client.get("/api/v1/produtos", headers=auth_headers)
    assert Decimal(products_response.json()[0]["estoque_atual"]) == Decimal("8.50")

    finance_response = client.get("/api/v1/financeiro", headers=auth_headers)
    assert len(finance_response.json()) == 1
    assert Decimal(finance_response.json()[0]["valor"]) == Decimal("500.00")

    linked_finance_id = finance_response.json()[0]["id"]
    finance_update = client.put(
        f"/api/v1/financeiro/{linked_finance_id}",
        headers=auth_headers,
        json={
            "tipo": "receita",
            "descricao": "Nao deve atualizar",
            "valor": "10.00",
            "vencimento": "2026-03-30",
            "status": "pendente",
            "cliente_id": customer["id"],
            "os_id": work_order["id"],
        },
    )
    assert finance_update.status_code == 400

    delete_response = client.delete(f"/api/v1/os/{work_order['id']}", headers=auth_headers)
    assert delete_response.status_code == 204

    products_after_delete = client.get("/api/v1/produtos", headers=auth_headers)
    assert Decimal(products_after_delete.json()[0]["estoque_atual"]) == Decimal("10.00")

    finance_after_delete = client.get("/api/v1/financeiro", headers=auth_headers)
    assert finance_after_delete.json() == []


def test_partial_finance_payment_creates_cash_ledger(client, auth_headers):
    customer = create_customer(client, auth_headers, "33")
    finance_entry = client.post(
        "/api/v1/financeiro",
        headers=auth_headers,
        json={
            "tipo": "receita",
            "descricao": "Recebimento parcelado",
            "valor": "150.00",
            "vencimento": "2026-04-05",
            "status": "pendente",
            "categoria": "Servico",
            "cliente_id": customer["id"],
            "os_id": None,
        },
    ).json()

    partial_payment = client.post(
        f"/api/v1/financeiro/{finance_entry['id']}/pagar",
        headers=auth_headers,
        json={"valor": "40.00", "data_pagamento": "2026-03-21"},
    )
    assert partial_payment.status_code == 200
    assert Decimal(partial_payment.json()["valor_pago"]) == Decimal("40.00")
    assert Decimal(partial_payment.json()["saldo_aberto"]) == Decimal("110.00")
    assert partial_payment.json()["status"] == "pendente"

    ledger_response = client.get("/api/v1/financeiro/caixa", headers=auth_headers)
    assert ledger_response.status_code == 200
    assert len(ledger_response.json()) == 1
    assert ledger_response.json()[0]["tipo"] == "entrada"
    assert Decimal(ledger_response.json()[0]["valor"]) == Decimal("40.00")

    final_payment = client.post(
        f"/api/v1/financeiro/{finance_entry['id']}/pagar",
        headers=auth_headers,
        json={"valor": "110.00", "data_pagamento": "2026-03-22"},
    )
    assert final_payment.status_code == 200
    assert final_payment.json()["status"] == "pago"
    assert Decimal(final_payment.json()["saldo_aberto"]) == Decimal("0.00")


def test_import_products_from_invoice_xml_updates_stock_and_finance(client, auth_headers):
    existing_product = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Existente",
            "principio_ativo": "Ativo",
            "grupo_quimico": "Grupo",
            "toxicidade": "Baixa",
            "concentracao": "1%",
            "registro_ms": "MS-EXIST",
            "estoque_atual": "4.00",
            "estoque_minimo": "1.00",
        },
    )
    assert existing_product.status_code == 201

    response = client.post(
        "/api/v1/produtos/importar-xml?registrar_financeiro=true",
        headers=auth_headers,
        files={"xml_file": ("nota.xml", sample_nfe_xml(), "application/xml")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["nota_numero"] == "1234"
    assert payload["financeiro_criado"] is True
    assert payload["produtos_criados"] == 1
    assert payload["produtos_atualizados"] == 1

    products_response = client.get("/api/v1/produtos", headers=auth_headers)
    assert products_response.status_code == 200
    products = products_response.json()
    imported_product = next(item for item in products if item["registro_ms"] == "XML-001")
    updated_product = next(item for item in products if item["registro_ms"] == "MS-EXIST")
    assert Decimal(imported_product["estoque_atual"]) == Decimal("3.00")
    assert Decimal(updated_product["estoque_atual"]) == Decimal("6.00")

    finance_response = client.get("/api/v1/financeiro", headers=auth_headers)
    assert finance_response.status_code == 200
    imported_finance = next(item for item in finance_response.json() if item["origem"] == "xml_nfe")
    assert imported_finance["tipo"] == "despesa"
    assert imported_finance["categoria"] == "Compra de estoque"
    assert Decimal(imported_finance["valor"]) == Decimal("105.00")

    duplicate_response = client.post(
        "/api/v1/produtos/importar-xml?registrar_financeiro=true",
        headers=auth_headers,
        files={"xml_file": ("nota.xml", sample_nfe_xml(), "application/xml")},
    )
    assert duplicate_response.status_code == 400


def test_import_products_from_csv_updates_stock_and_finance(client, auth_headers):
    existing_product = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Existente CSV",
            "principio_ativo": "Ativo",
            "grupo_quimico": "Grupo",
            "toxicidade": "Baixa",
            "concentracao": "1%",
            "registro_ms": "CSV-EXIST",
            "estoque_atual": "1.00",
            "estoque_minimo": "0.50",
        },
    )
    assert existing_product.status_code == 201

    response = client.post(
        "/api/v1/produtos/importar-csv?registrar_financeiro=true",
        headers=auth_headers,
        files={"csv_file": ("produtos.csv", sample_products_csv(), "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["produtos_processados"] == 2
    assert payload["produtos_criados"] == 1
    assert payload["produtos_atualizados"] == 1
    assert payload["lancamentos_financeiros"] == 2
    assert Decimal(payload["valor_financeiro_total"]) == Decimal("230.00")

    products_response = client.get("/api/v1/produtos", headers=auth_headers)
    products = products_response.json()
    created_product = next(item for item in products if item["registro_ms"] == "CSV-001")
    updated_product = next(item for item in products if item["registro_ms"] == "CSV-EXIST")
    assert Decimal(created_product["estoque_atual"]) == Decimal("5.00")
    assert Decimal(updated_product["estoque_atual"]) == Decimal("3.50")

    finance_response = client.get("/api/v1/financeiro", headers=auth_headers)
    imported_entries = [item for item in finance_response.json() if item["origem"] == "csv_import"]
    assert len(imported_entries) == 2
    assert sum(Decimal(item["valor"]) for item in imported_entries) == Decimal("230.00")


def test_import_templates_are_available():
    csv_template = Path("app/interfaces/web/static/import_templates/modelo_importacao_produtos_v3_1.csv")
    xlsx_template = Path("app/interfaces/web/static/import_templates/modelo_importacao_produtos_v3_1.xlsx")
    assert csv_template.exists()
    assert xlsx_template.exists()


def test_customer_lookup_endpoints_return_company_and_address_data(client, auth_headers, monkeypatch):
    def fake_fetch_json(url):
        if "cnpj" in url:
            return {
                "razao_social": "Empresa Consulta Ltda",
                "nome_fantasia": "Empresa Consulta",
                "ddd_telefone_1": "1133779922",
                "email": "contato@empresa.com",
                "cep": "01001000",
                "logradouro": "Praca da Se",
                "numero": "100",
                "complemento": "Sala 5",
                "bairro": "Se",
                "municipio": "Sao Paulo",
                "uf": "SP",
            }
        return {
            "cep": "01001-000",
            "logradouro": "Praca da Se",
            "bairro": "Se",
            "localidade": "Sao Paulo",
            "uf": "SP",
        }

    monkeypatch.setattr(services, "_fetch_json", fake_fetch_json)

    cnpj_response = client.get("/api/v1/clientes/consultar-cnpj/12345678000199", headers=auth_headers)
    assert cnpj_response.status_code == 200
    assert cnpj_response.json()["razao_social"] == "Empresa Consulta Ltda"
    assert cnpj_response.json()["cidade"] == "Sao Paulo"

    provider_cnpj_response = client.get("/api/v1/empresas-prestadoras/consultar-cnpj/12345678000199", headers=auth_headers)
    assert provider_cnpj_response.status_code == 200
    assert provider_cnpj_response.json()["nome_fantasia"] == "Empresa Consulta"
    assert provider_cnpj_response.json()["cep"] == "01001000"

    cep_response = client.get("/api/v1/clientes/consultar-cep/01001000", headers=auth_headers)
    assert cep_response.status_code == 200
    assert cep_response.json()["endereco"] == "Praca da Se"
    assert cep_response.json()["estado"] == "SP"
