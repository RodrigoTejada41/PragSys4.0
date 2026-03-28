from decimal import Decimal
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


def _create_provider_company(client, auth_headers, suffix: str, **overrides) -> dict:
    payload = {
        "razao_social": f"Empresa Estoque {suffix} Ltda",
        "nome_fantasia": f"Empresa Estoque {suffix}",
        "cnpj": f"{suffix * 4}0001{suffix}",
        "email": f"estoque{suffix}@teste.com",
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


def _create_license(client, auth_headers, company_id: int, suffix: str) -> None:
    response = client.post(
        "/api/v1/licencas",
        headers=auth_headers,
        json={
            "descricao": f"Licenca Estoque {suffix}",
            "start_date": "2026-03-20",
            "end_date": "2027-03-20",
            "max_users": 10,
            "status": "ativa",
            "empresa_prestadora_id": company_id,
        },
    )
    assert response.status_code == 201, response.text


def _create_user(client, auth_headers, *, username: str, role: str, company_id: int, permissions: dict | None = None) -> dict:
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": username,
            "username": username,
            "password": "senha123",
            "role": role,
            "is_active": True,
            "empresa_prestadora_id": company_id,
            "permissions": permissions or {},
        },
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"username": username, "password": "senha123"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _build_products_xlsx() -> bytes:
    workbook = BytesIO()
    headers = [
        "nome",
        "principio_ativo",
        "grupo_quimico",
        "toxicidade",
        "concentracao",
        "registro_ms",
        "categoria",
        "unidade_medida",
        "quantidade_entrada",
        "estoque_minimo",
        "custo_total",
        "fornecedor_nome",
        "referencia",
        "data_entrada",
        "categoria_financeira",
        "observacoes",
        "registrar_financeiro",
    ]
    row = [
        "Produto XLSX",
        "Ativo XLSX",
        "Grupo XLSX",
        "Baixa",
        "10%",
        "XLSX-001",
        "Importado",
        "ML",
        "1500",
        "250",
        "99.90",
        "Fornecedor XLSX",
        "PLAN-001",
        "2026-03-27",
        "Compra de estoque",
        "Carga inicial",
        "true",
    ]

    strings = []
    string_index = {}

    def shared_index(value: str) -> int:
        if value not in string_index:
            string_index[value] = len(strings)
            strings.append(value)
        return string_index[value]

    def col_letter(index: int) -> str:
        result = ""
        current = index
        while current > 0:
            current, remainder = divmod(current - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def build_row_xml(row_number: int, values: list[str]) -> str:
        cells = []
        for column_index, value in enumerate(values, start=1):
            cell_ref = f"{col_letter(column_index)}{row_number}"
            if isinstance(value, str) and value not in {"1500", "250", "99.90"}:
                cells.append(f'<c r="{cell_ref}" t="s"><v>{shared_index(value)}</v></c>')
            else:
                cells.append(f'<c r="{cell_ref}"><v>{value}</v></c>')
        return f'<row r="{row_number}">{"".join(cells)}</row>'

    sheet_rows = build_row_xml(1, headers) + build_row_xml(2, row)
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{sheet_rows}</sheetData>'
        '</worksheet>'
    )
    shared_strings_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
        + ''.join(f'<si><t>{value}</t></si>' for value in strings)
        + '</sst>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Plan1" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        '</Relationships>'
    )
    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '</Types>'
    )

    with ZipFile(workbook, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        archive.writestr("xl/sharedStrings.xml", shared_strings_xml)

    return workbook.getvalue()


def test_import_products_from_xlsx_updates_stock_and_logs(client, auth_headers):
    response = client.post(
        "/api/v1/produtos/importar-xlsx?registrar_financeiro=true",
        headers=auth_headers,
        files={
            "xlsx_file": (
                "produtos.xlsx",
                _build_products_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["produtos_processados"] == 1
    assert payload["produtos_criados"] == 1
    assert payload["lancamentos_financeiros"] == 1

    products = client.get("/api/v1/produtos", headers=auth_headers).json()
    product = next(item for item in products if item["registro_ms"] == "XLSX-001")
    assert product["categoria"] == "Importado"
    assert product["unidade_medida"] == "ML"
    assert Decimal(product["estoque_atual"]) == Decimal("1500.00")

    logs = client.get("/api/v1/produtos/estoque/importacoes", headers=auth_headers)
    assert logs.status_code == 200
    assert logs.json()[0]["tipo_arquivo"] == "xlsx"
    assert logs.json()[0]["nome_arquivo"] == "produtos.xlsx"


def test_stock_balance_supports_unit_conversion(client, auth_headers):
    product = client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "nome": "Produto Litro",
            "categoria": "Liquido",
            "unidade_medida": "L",
            "principio_ativo": "Ativo L",
            "grupo_quimico": "Grupo L",
            "toxicidade": "Media",
            "concentracao": "5%",
            "registro_ms": "L-001",
            "estoque_atual": "2.00",
            "estoque_minimo": "0.50",
        },
    ).json()

    balance = client.post(
        "/api/v1/produtos/estoque/balanco",
        headers=auth_headers,
        json={
            "produto_id": product["id"],
            "saldo_contado": "2500",
            "unidade_medida": "ML",
            "motivo": "Inventario trimestral",
            "referencia": "BAL-2500ML",
        },
    )
    assert balance.status_code == 201, balance.text
    payload = balance.json()
    assert payload["unidade_medida"] == "L"
    assert Decimal(payload["saldo_posterior"]) == Decimal("2.50")

    positions = client.get("/api/v1/produtos/estoque", headers=auth_headers).json()
    current = next(item for item in positions if item["produto_id"] == product["id"])
    assert current["unidade_medida"] == "L"
    assert Decimal(current["estoque_atual"]) == Decimal("2.50")


def test_stock_transfer_between_linked_companies_keeps_balances_separate(client, auth_headers):
    matriz = _create_provider_company(client, auth_headers, "91", compartilha_visualizacao_estoque=True)
    filial = _create_provider_company(
        client,
        auth_headers,
        "92",
        empresa_pai_id=matriz["id"],
        compartilha_visualizacao_estoque=True,
    )
    _create_license(client, auth_headers, matriz["id"], "91")
    _create_license(client, auth_headers, filial["id"], "92")

    matriz_headers = _create_user(
        client,
        auth_headers,
        username="transferadmin",
        role="admin",
        company_id=matriz["id"],
        permissions={"stock.view": True, "stock.manage": True, "stock.move": True},
    )

    product = client.post(
        "/api/v1/produtos",
        headers=matriz_headers,
        json={
            "nome": "Produto Transferencia",
            "categoria": "Operacional",
            "unidade_medida": "KG",
            "principio_ativo": "Ativo T",
            "grupo_quimico": "Grupo T",
            "toxicidade": "Baixa",
            "concentracao": "3%",
            "registro_ms": "TRF-001",
            "estoque_atual": "5.00",
            "estoque_minimo": "1.00",
        },
    ).json()

    companies_response = client.get("/api/v1/produtos/estoque/empresas", headers=matriz_headers)
    assert companies_response.status_code == 200, companies_response.text
    company_ids = {item["id"] for item in companies_response.json()}
    assert {matriz["id"], filial["id"]}.issubset(company_ids)

    transfer = client.post(
        "/api/v1/produtos/estoque/transferencias",
        headers=matriz_headers,
        json={
            "produto_id": product["id"],
            "empresa_destino_id": filial["id"],
            "quantidade": "500",
            "unidade_medida": "G",
            "motivo": "Reposicao filial",
            "referencia": "TRF-500G",
        },
    )
    assert transfer.status_code == 201, transfer.text
    movements = transfer.json()
    assert len(movements) == 2
    assert {item["empresa_prestadora_id"] for item in movements} == {matriz["id"], filial["id"]}

    matriz_positions = client.get(f"/api/v1/produtos/estoque?empresa_id={matriz['id']}", headers=matriz_headers).json()
    matriz_item = next(item for item in matriz_positions if item["produto_id"] == product["id"])
    assert Decimal(matriz_item["estoque_atual"]) == Decimal("4.50")

    filial_headers = _create_user(
        client,
        auth_headers,
        username="transferfilial",
        role="admin",
        company_id=filial["id"],
        permissions={"stock.view": True, "stock.manage": True, "stock.move": True},
    )
    filial_positions = client.get(f"/api/v1/produtos/estoque?empresa_id={filial['id']}", headers=filial_headers).json()
    filial_item = next(item for item in filial_positions if item["registro_ms"] == "TRF-001")
    assert Decimal(filial_item["estoque_atual"]) == Decimal("0.50")
    assert filial_item["unidade_medida"] == "KG"
