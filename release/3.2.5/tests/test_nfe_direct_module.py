from types import SimpleNamespace

import pytest

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.modules.sefaz_nfe.sefaz_client import SefazSoapClient
from app.modules.sefaz_nfe.xml_generator import build_nfe_xml
from app.modules.sefaz_nfe.services import get_direct_sefaz_readiness


def create_customer(client, auth_headers, suffix="971"):
    response = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": f"Cliente NF-e Direta {suffix}",
            "cpf_cnpj": f"1122334400{suffix.zfill(4)}",
            "endereco": "Rua Direta, 10",
            "numero": "10",
            "bairro": "Centro",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "cep": "01001000",
            "telefone": "11998887766",
            "contato": "Fiscal",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_build_nfe_xml_generates_access_key_and_expected_tags(monkeypatch):
    monkeypatch.setenv("COMPANY_CNPJ", "12345678000199")
    monkeypatch.setenv("COMPANY_IE", "123456789")
    monkeypatch.setenv("COMPANY_LEGAL_NAME", "Emitente Direto LTDA")
    monkeypatch.setenv("COMPANY_TRADE_NAME", "Emitente Direto")
    monkeypatch.setenv("COMPANY_STREET", "Rua do Emitente")
    monkeypatch.setenv("COMPANY_NUMBER", "100")
    monkeypatch.setenv("COMPANY_DISTRICT", "Centro")
    monkeypatch.setenv("COMPANY_CITY", "Sao Paulo")
    monkeypatch.setenv("COMPANY_CITY_CODE", "3550308")
    monkeypatch.setenv("COMPANY_STATE", "SP")
    monkeypatch.setenv("COMPANY_STATE_CODE", "35")
    monkeypatch.setenv("COMPANY_ZIP_CODE", "01001000")
    monkeypatch.setenv("COMPANY_PHONE", "1133334444")
    monkeypatch.setenv("SEFAZ_NFE_UF", "SP")
    get_settings.cache_clear()

    invoice = SimpleNamespace(
        id=1,
        numero_nfe="1234",
        cliente_id=1,
        ambiente="homologacao",
        observacoes="Teste XML",
    )
    customer = SimpleNamespace(
        razao_social="Cliente Teste",
        cpf_cnpj="12345678901",
        endereco="Rua Cliente",
        numero="20",
        bairro="Centro",
        cidade="Sao Paulo",
        estado="SP",
        cep="01002000",
        telefone="11999990000",
    )
    items = [
        {
            "descricao": "Servico teste",
            "ncm": "38089199",
            "quantidade": "1.0000",
            "valor_unitario": "100.00",
            "cfop": "5102",
            "unidade_comercial": "UN",
            "aliquota_icms": "18.00",
            "aliquota_pis": "1.65",
            "aliquota_cofins": "7.60",
        }
    ]

    generated = build_nfe_xml(invoice, customer, items)

    assert len(generated.access_key) == 44
    assert "<infNFe" in generated.nfe_xml
    assert "Emitente Direto LTDA" in generated.nfe_xml
    assert "Cliente Teste" in generated.nfe_xml
    assert "38089199" in generated.nfe_xml
    assert "<nNF>1234</nNF>" in generated.nfe_xml
    assert "." not in generated.nfe_xml.split("<dhEmi>", 1)[1].split("</dhEmi>", 1)[0]
    assert "<enviNFe" in generated.envi_nfe_xml
    get_settings.cache_clear()


def test_issue_nfe_dispatches_to_direct_sefaz_provider(client, auth_headers, monkeypatch):
    from app.application import nfe_integration_service

    customer = create_customer(client, auth_headers, "972")
    monkeypatch.setenv("NFE_PROVIDER", "sefaz_direct")
    get_settings.cache_clear()

    def fake_issue_direct_nfe(db, payload):
        return SimpleNamespace(
            id=99,
            numero_nfe=payload.numero_nfe,
            cliente_id=payload.cliente_id,
            cliente=SimpleNamespace(**customer),
            valor_total=payload.valor_total,
            data_emissao=payload.data_emissao,
            data_vencimento=payload.data_vencimento,
            status="emitida",
            finance_entry_id=None,
            referencia_externa="DIRETA001",
            ambiente=payload.ambiente,
            provedor="sefaz_direct",
            status_processamento="autorizado",
            status_externo="100",
            mensagem_retorno="Autorizado o uso da NF-e",
            chave_nfe="35260312345678000199550010000012341000012345",
            protocolo_autorizacao="135260000000001",
            recibo_lote="352600000000001",
            lote_id="000000000000001",
            xml_url=None,
            pdf_url=None,
            xml_enviado="<xml/>",
            xml_autorizado="<procNFe/>",
            webhook_url=None,
            observacoes=None,
            created_at="2026-03-21T00:00:00",
            updated_at="2026-03-21T00:00:00",
        )

    monkeypatch.setattr(nfe_integration_service, "issue_direct_nfe", fake_issue_direct_nfe)

    response = client.post(
        "/api/v1/nfe",
        headers=auth_headers,
        json={
            "numero_nfe": "NFE-DIR-001",
            "cliente_id": customer["id"],
            "valor_total": "100.00",
            "data_emissao": "2026-03-21",
            "data_vencimento": "2026-03-28",
            "status": "emitida",
            "observacoes": "Teste provider direto",
            "gerar_financeiro": False,
            "natureza_operacao": "Venda",
            "ambiente": "homologacao",
            "referencia_externa": "DIRETA001",
            "itens": [
                {
                    "descricao": "Produto Teste",
                    "ncm": "38089199",
                    "quantidade": "1.00",
                    "valor_unitario": "100.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["provedor"] == "sefaz_direct"
    assert payload["status_processamento"] == "autorizado"
    assert payload["protocolo_autorizacao"] == "135260000000001"
    get_settings.cache_clear()


def test_sefaz_readiness_reports_missing_items(client, auth_headers, monkeypatch):
    monkeypatch.setenv("NFE_PROVIDER", "sefaz_direct")
    monkeypatch.setenv("SEFAZ_NFE_CERTIFICATE_PATH", "")
    monkeypatch.setenv("SEFAZ_NFE_CERTIFICATE_PASSWORD", "")
    monkeypatch.setenv("SEFAZ_NFE_XSD_DIR", "")
    monkeypatch.setenv("COMPANY_CNPJ", "")
    monkeypatch.setenv("COMPANY_IE", "")
    monkeypatch.setenv("COMPANY_CITY_CODE", "")
    monkeypatch.setenv("COMPANY_STATE", "")
    monkeypatch.setenv("COMPANY_STATE_CODE", "")
    get_settings.cache_clear()

    response = client.get("/api/v1/nfe/sefaz/readiness", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is False
    assert payload["provider"] == "sefaz_direct"
    assert "SEFAZ_NFE_CERTIFICATE_PATH" in payload["missing_items"]
    assert "COMPANY_CNPJ" in payload["missing_items"]
    get_settings.cache_clear()


def test_sefaz_readiness_allows_missing_xsd_in_homologacao(monkeypatch):
    monkeypatch.setenv("NFE_PROVIDER", "sefaz_direct")
    monkeypatch.setenv("FOCUS_NFE_ENVIRONMENT", "homologacao")
    monkeypatch.setenv("SEFAZ_NFE_UF", "SP")
    monkeypatch.setenv("SEFAZ_NFE_CERTIFICATE_PATH", "E:\\fake\\empresa.pfx")
    monkeypatch.setenv("SEFAZ_NFE_CERTIFICATE_PASSWORD", "segredo")
    monkeypatch.setenv("SEFAZ_NFE_XSD_DIR", "")
    monkeypatch.setenv("COMPANY_CNPJ", "12345678000199")
    monkeypatch.setenv("COMPANY_IE", "123456789")
    monkeypatch.setenv("COMPANY_CRT", "1")
    monkeypatch.setenv("COMPANY_STREET", "Rua Um")
    monkeypatch.setenv("COMPANY_NUMBER", "100")
    monkeypatch.setenv("COMPANY_DISTRICT", "Centro")
    monkeypatch.setenv("COMPANY_CITY", "Sao Paulo")
    monkeypatch.setenv("COMPANY_CITY_CODE", "3550308")
    monkeypatch.setenv("COMPANY_STATE", "SP")
    monkeypatch.setenv("COMPANY_STATE_CODE", "35")
    monkeypatch.setenv("COMPANY_ZIP_CODE", "01001000")
    get_settings.cache_clear()

    readiness = get_direct_sefaz_readiness()

    assert "SEFAZ_NFE_XSD_DIR" not in readiness.missing_items
    assert any("Homologacao sem XSD local" in note for note in readiness.notes)
    get_settings.cache_clear()


def test_validate_xml_against_xsd_blocks_producao_without_xsd(monkeypatch):
    from app.modules.sefaz_nfe.xml_generator import validate_xml_against_xsd

    monkeypatch.setenv("SEFAZ_NFE_XSD_DIR", "")
    get_settings.cache_clear()

    with pytest.raises(BusinessRuleViolation, match="SEFAZ_NFE_XSD_DIR"):
        validate_xml_against_xsd("<teste/>", "enviNFe_v4.00.xsd", environment="producao")

    get_settings.cache_clear()


def test_sefaz_url_resolution_uses_sp_endpoints_by_default(monkeypatch):
    monkeypatch.setenv("SEFAZ_NFE_WS_URLS_JSON", "")
    get_settings.cache_clear()

    client = SefazSoapClient()

    assert client._resolve_url("homologacao", "SP", "NFeAutorizacao") == (
        "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx"
    )
    assert client._resolve_url("producao", "SP", "RecepcaoEvento") == (
        "https://nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx"
    )
    get_settings.cache_clear()


def test_sefaz_tls_verify_can_be_disabled_in_homologacao(monkeypatch):
    monkeypatch.setenv("SEFAZ_NFE_VERIFY_TLS", "false")
    get_settings.cache_clear()

    client = SefazSoapClient()

    assert client._resolve_tls_verify("homologacao") is False
    assert client._resolve_tls_verify("producao") is True
    get_settings.cache_clear()


def test_sefaz_parse_response_prefers_protocol_status_for_processed_batch(monkeypatch):
    monkeypatch.setenv("SEFAZ_NFE_WS_URLS_JSON", "")
    get_settings.cache_clear()

    raw_response = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body>
    <nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">
      <retEnviNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
        <cStat>104</cStat>
        <xMotivo>Lote processado</xMotivo>
        <protNFe versao="4.00">
          <infProt>
            <chNFe>35260362028102000172550010802251271835074000</chNFe>
            <cStat>242</cStat>
            <xMotivo>Rejeição: Mensagem SOAP inválida</xMotivo>
          </infProt>
        </protNFe>
      </retEnviNFe>
    </nfeResultMsg>
  </soap:Body>
</soap:Envelope>"""

    response = SefazSoapClient()._parse_response("NFeAutorizacao", 200, raw_response)

    assert response.c_stat == "242"
    assert response.x_motivo == "Rejeição: Mensagem SOAP inválida"
    assert response.access_key == "35260362028102000172550010802251271835074000"
    get_settings.cache_clear()
