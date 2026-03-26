from types import SimpleNamespace

from app.core.config import get_settings
from app.application.services import (
    _build_framed_sanitary_certificate_text,
    _build_standard_sanitary_certificate_text,
    _build_standard_sanitary_declaration,
    _classify_food_risk_environment,
)


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

    endpoints = {
        f"/api/v1/os/{work_order['id']}/pdf": f'inline; filename="os-{work_order["id"]}.pdf"',
        f"/api/v1/os/{work_order['id']}/relatorio-tecnico.pdf": f'inline; filename="relatorio-tecnico-{work_order["id"]}.pdf"',
        f"/api/v1/os/{work_order['id']}/certificado-sanitario.pdf": f'inline; filename="certificado-sanitario-{work_order["id"]}.pdf"',
        f"/api/v1/os/{work_order['id']}/certificado-garantia.pdf": 'inline; filename="certificado_industria_delta.pdf"',
        f"/api/v1/os/{work_order['id']}/certificado-moldura.pdf": f'inline; filename="certificado-moldura-{work_order["id"]}.pdf"',
    }

    for endpoint, expected_disposition in endpoints.items():
        response = client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == expected_disposition
        assert response.content.startswith(b"%PDF")
        assert len(response.content) > 1200


def test_framed_certificate_text_covers_food_risk_compliance_language():
    work_order = SimpleNamespace(
        cliente=SimpleNamespace(razao_social="Industria Delta"),
        local_execucao="Armazem de alimentos e doca de expedicao",
        observacoes="Fluxo logistico com armazenamento e circulacao de alimentos embalados.",
    )

    risk_environment = _classify_food_risk_environment(work_order)
    certificate_text = _build_framed_sanitary_certificate_text(work_order)

    assert "armazenagem e logistica de alimentos" in risk_environment
    assert "RDC 622/2022" in certificate_text
    assert "RDC 216/2004" in certificate_text
    assert "RDC 275/2002" in certificate_text
    assert "controle de vetores e pragas urbanas" in certificate_text
    assert "seguranca dos alimentos" in certificate_text
    assert "controle de contaminacao" in certificate_text
    assert "minimizacao de riscos a saude" in certificate_text
    assert "seguranca ambiental" in certificate_text


def test_standard_certificate_text_covers_food_risk_compliance_language():
    work_order = SimpleNamespace(
        cliente=SimpleNamespace(razao_social="Industria Delta"),
        local_execucao="Area de manipulacao e estoque de alimentos",
        observacoes="Recebimento, fracionamento e armazenamento de alimentos embalados.",
    )

    certificate_text = _build_standard_sanitary_certificate_text(work_order)
    declaration = _build_standard_sanitary_declaration(work_order)

    assert "RDC 622/2022" in certificate_text
    assert "controle de vetores e pragas urbanas" in certificate_text
    assert "seguranca dos alimentos" in certificate_text
    assert "controle de contaminacao" in certificate_text
    assert "minimizacao de riscos a saude" in certificate_text
    assert "RDC 216/2004" in declaration
    assert "RDC 275/2002" in declaration
    assert "boas praticas sanitarias" in declaration
    assert "seguranca ambiental" in declaration


def test_certificate_generation_keeps_working_when_signature_is_missing(client, auth_headers, monkeypatch):
    monkeypatch.setenv("TECHNICAL_SIGNATURES_DIR", "test_assets/assinaturas_vazias")
    monkeypatch.setenv("CERTIFICATE_MODELS_DIR", "test_assets/modelos")
    get_settings.cache_clear()

    work_order = _create_base_work_order(client, auth_headers)
    response = client.get(f"/api/v1/os/{work_order['id']}/certificado-sanitario.pdf", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    get_settings.cache_clear()


def test_certificate_generation_falls_back_when_template_is_missing(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CERTIFICATE_MODELS_DIR", "test_assets/modelos_vazios")
    get_settings.cache_clear()

    work_order = _create_base_work_order(client, auth_headers)
    response = client.get(f"/api/v1/os/{work_order['id']}/certificado-moldura.pdf", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    get_settings.cache_clear()


def test_guarantee_certificate_is_generated_from_visual_template(client, auth_headers):
    work_order = _create_base_work_order(client, auth_headers)
    response = client.get(f"/api/v1/os/{work_order['id']}/certificado-garantia.pdf", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'inline; filename="certificado_industria_delta.pdf"'
    assert response.content.startswith(b"%PDF")
