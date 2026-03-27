from io import BytesIO

from reportlab.pdfgen import canvas


def _create_company_user(client, auth_headers, username: str, company_suffix: str) -> dict:
    cnpj = f"{company_suffix * 4}0001{company_suffix}"
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": f"Admin {company_suffix}",
            "username": username,
            "password": "senha123",
            "role": "admin",
            "is_active": True,
            "nova_empresa_prestadora": {
                "razao_social": f"Prestadora {company_suffix} Ltda",
                "nome_fantasia": f"Prestadora {company_suffix}",
                "cnpj": cnpj,
                "email": f"{username}@empresa.com",
                "telefone": "11999990000",
                "cidade": "Sao Paulo",
                "estado": "SP",
            },
            "licenca_inicial": {
                "descricao": f"Licenca {company_suffix}",
                "start_date": "2026-03-20",
                "end_date": "2027-03-20",
                "max_users": 10,
                "status": "ativa",
                "notes": "Licenca de teste multempresa",
            },
        },
    )
    assert response.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "senha123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _build_regulatory_pdf(*lines: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 800
    for line in lines:
        pdf.drawString(40, y, line)
        y -= 18
    pdf.save()
    return buffer.getvalue()


def test_admin_can_read_and_update_system_settings(client, auth_headers):
    response = client.get("/api/v1/settings", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert "integrations" in payload
    assert "contracts" in payload
    assert "system" in payload
    assert "email" in payload
    assert "database" in payload
    assert "company" in payload
    assert payload["system"]["operation_mode"] in {"local", "rede"}

    update_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "integrations": {
                "google_calendar_enabled": True,
                "whatsapp_enabled": False,
                "whatsapp_auto_send": False,
                "whatsapp_default_message": "Agendamento atualizado automaticamente.",
            },
            "contracts": {
                "alert_days": 30,
                "email_enabled": True,
                "storage_dir": "uploads/contratos-teste",
            },
            "email": {
                "smtp_host": "smtp.empresa.com",
                "smtp_port": 465,
                "smtp_username": "smtp-user",
                "smtp_password": "senha-super-secreta",
                "smtp_use_tls": False,
                "smtp_use_ssl": True,
                "smtp_sender_email": "naoresponda@empresa.com",
                "smtp_sender_name": "SysPragas",
            },
            "database": {
                "backup_dir": "test_assets/backups",
            },
            "company": {
                "legal_name": "SysPragas Compliance Ltda",
                "trade_name": "SysPragas Pro",
                "cnpj": "99888777000166",
                "address": "Av. Regulada, 900 - Sao Paulo/SP",
                "phone": "1130304040",
                "technical_responsible_name": "Dra. Helena Prado",
                "technical_registry_type": "CRQ",
                "technical_registry_number": "445566",
                "technical_registry_state": "SP",
                "sanitary_license_number": "LS-0099",
                "sanitary_license_expiry": "31/12/2026",
                "environmental_license_number": "LA-7788",
                "environmental_license_expiry": "31/12/2026",
                "toxicology_center_name": "CEATOX SP",
                "toxicology_center_phone": "0800 722 6001",
            },
            "system": {
                "multiempresa_enabled": False,
                "operation_mode": "rede",
                "notifications_enabled": False,
                "appointment_default_google_sync": True,
            },
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["integrations"]["google_calendar_enabled"] is True
    assert updated["integrations"]["whatsapp_enabled"] is False
    assert updated["integrations"]["whatsapp_auto_send"] is False
    assert updated["integrations"]["whatsapp_default_message"] == "Agendamento atualizado automaticamente."
    assert updated["contracts"]["alert_days"] == 30
    assert updated["contracts"]["email_enabled"] is True
    assert updated["contracts"]["storage_dir"] == "uploads/contratos-teste"
    assert updated["email"]["smtp_host"] == "smtp.empresa.com"
    assert updated["email"]["smtp_port"] == 465
    assert updated["email"]["smtp_username"] == "smtp-user"
    assert updated["email"]["smtp_use_tls"] is False
    assert updated["email"]["smtp_use_ssl"] is True
    assert updated["email"]["smtp_sender_email"] == "naoresponda@empresa.com"
    assert updated["email"]["smtp_sender_name"] == "SysPragas"
    assert updated["email"]["smtp_password_configured"] is True
    assert updated["database"]["backup_dir"] == "test_assets/backups"
    assert updated["database"]["engine"] == "sqlite"
    assert updated["database"]["database_file_name"].endswith(".db")
    assert updated["company"]["legal_name"] == "SysPragas Compliance Ltda"
    assert updated["company"]["trade_name"] == "SysPragas Pro"
    assert updated["company"]["technical_responsible_name"] == "Dra. Helena Prado"
    assert updated["company"]["technical_registry_type"] == "CRQ"
    assert updated["company"]["technical_registry_number"] == "445566"
    assert updated["company"]["technical_registry_state"] == "SP"
    assert updated["company"]["technical_responsible_registry"] == "CRQ 445566 / SP"
    assert updated["company"]["sanitary_license_number"] == "LS-0099"
    assert updated["company"]["environmental_license_number"] == "LA-7788"
    assert updated["company"]["toxicology_center_name"] == "CEATOX SP"
    assert updated["company"]["toxicology_center_phone"] == "0800 722 6001"
    assert updated["company"]["sanitary_license_file"]["has_file"] is False
    assert updated["company"]["technical_signature"]["has_file"] is False
    assert updated["system"]["multiempresa_enabled"] is False
    assert updated["system"]["operation_mode"] == "rede"
    assert updated["system"]["notifications_enabled"] is False
    assert updated["system"]["appointment_default_google_sync"] is True


def test_admin_can_upload_company_technical_assets(client, auth_headers):
    signature_response = client.post(
        "/api/v1/settings/technical-documents/assets/signature",
        headers=auth_headers,
        files={"file": ("assinatura.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00", "image/png")},
    )
    assert signature_response.status_code == 200
    signature_payload = signature_response.json()
    assert signature_payload["technical_signature"]["has_file"] is True
    assert signature_payload["technical_signature"]["filename"] == "assinatura.png"

    license_response = client.post(
        "/api/v1/settings/technical-documents/assets/sanitary_license",
        headers=auth_headers,
        files={"file": ("licenca.pdf", b"%PDF-1.4\n%teste", "application/pdf")},
    )
    assert license_response.status_code == 200
    license_payload = license_response.json()
    assert license_payload["sanitary_license_file"]["has_file"] is True
    assert license_payload["sanitary_license_file"]["filename"] == "licenca.pdf"

    download_response = client.get(
        "/api/v1/settings/technical-documents/assets/sanitary_license",
        headers=auth_headers,
    )
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF")


def test_pdf_upload_extracts_regulatory_fields_automatically(client, auth_headers):
    pdf_content = _build_regulatory_pdf(
        "Razao Social: Laboratorio Delta Ltda",
        "Endereco da empresa: Rua Tecnica 500 - Sao Paulo/SP",
        "Responsavel Tecnico: Dra. Helena Prado",
        "Registro Profissional: CRQ 445566",
        "Centro de Informacao Toxicologica: CEATOX",
        "Telefone CIT: 0800 722 6001",
        "Licenca ambiental: LA-7788",
        "Validade: 31/12/2027",
    )

    upload_response = client.post(
        "/api/v1/settings/technical-documents/assets/environmental_license",
        headers=auth_headers,
        files={"file": ("licenca-ambiental.pdf", pdf_content, "application/pdf")},
    )

    assert upload_response.status_code == 200
    company = upload_response.json()
    assert company["legal_name"] == "Laboratorio Delta Ltda"
    assert company["address"] == "Rua Tecnica 500 - Sao Paulo/SP"
    assert company["technical_responsible_name"] == "Dra. Helena Prado"
    assert company["technical_registry_type"] == "CRQ"
    assert company["technical_registry_number"] == "445566"
    assert company["environmental_license_number"] == "LA-7788"
    assert company["environmental_license_expiry"] == "31/12/2027"
    assert company["toxicology_center_name"] == "CEATOX"
    assert company["toxicology_center_phone"] == "0800 722 6001"


def test_pdf_upload_extracts_regulatory_fields_with_accents(client, auth_headers):
    pdf_content = _build_regulatory_pdf(
        "Razão Social: Clínica Ápice Ltda",
        "Endereço da empresa: Rua São Bento, 250 - São Paulo/SP",
        "Responsável Técnico: Dr. João Álvares",
        "Registro Profissional: CRBio 12345 / SP",
        "Centro de Informação Toxicológica: CEATOX",
        "Telefone CIT: 0800 722 6001",
        "Licença ambiental nº: la-9001",
    )

    upload_response = client.post(
        "/api/v1/settings/technical-documents/assets/environmental_license",
        headers=auth_headers,
        files={"file": ("licenca-ambiental-acento.pdf", pdf_content, "application/pdf")},
    )

    assert upload_response.status_code == 200
    company = upload_response.json()
    assert company["legal_name"] == "Clínica Ápice Ltda"
    assert company["address"] == "Rua São Bento, 250 - São Paulo/SP"
    assert company["technical_responsible_name"] == "Dr. João Álvares"
    assert company["technical_registry_type"] == "CRBio"
    assert company["technical_registry_number"] == "12345"
    assert company["technical_registry_state"] == "SP"
    assert company["environmental_license_number"] == "LA-9001"
    assert company["toxicology_center_phone"] == "0800 722 6001"


def test_pdf_upload_extracts_fields_from_realistic_license_layout(client, auth_headers):
    pdf_content = _build_regulatory_pdf(
        "LICENÇA AMBIENTAL (TESTE)",
        "Órgão Emissor: Secretaria Municipal do Meio Ambiente",
        "Município: Carapicuíba - SP",
        "Número da Licença: LA-TESTE-0001/2026",
        "Data de Emissão: 01/01/2026",
        "Validade: 01/01/2027",
        "Razão Social: EMPRESA MODELO CONTROLE DE PRAGAS LTDA",
        "CNPJ: 00.000.000/0001-00",
        "Endereço: Rua Exemplo, 123 - Centro - Carapicuíba/SP",
        "Atividade Licenciada: Controle de pragas urbanas",
        "Responsável Técnico: João da Silva",
        "Registro: CRBio 123456/01-D",
    )

    upload_response = client.post(
        "/api/v1/settings/technical-documents/assets/environmental_license",
        headers=auth_headers,
        files={"file": ("licenca-ambiental-real.pdf", pdf_content, "application/pdf")},
    )

    assert upload_response.status_code == 200
    company = upload_response.json()
    assert company["legal_name"] == "EMPRESA MODELO CONTROLE DE PRAGAS LTDA"
    assert company["address"] == "Rua Exemplo, 123 - Centro - Carapicuíba/SP"
    assert company["technical_responsible_name"] == "João da Silva"
    assert company["technical_registry_type"] == "CRBio"
    assert company["technical_registry_number"] == "123456"
    assert company["environmental_license_number"] == "LA-TESTE-0001/2026"
    assert company["environmental_license_expiry"] == "01/01/2027"


def test_pdf_upload_extracts_sanitary_license_expiry(client, auth_headers):
    pdf_content = _build_regulatory_pdf(
        "LICENÇA SANITÁRIA (TESTE)",
        "Número da Licença: LS-TESTE-0001/2026",
        "Validade: 15/08/2027",
        "Razão Social: EMPRESA MODELO CONTROLE DE PRAGAS LTDA",
        "Endereço: Rua Exemplo, 123 - Centro - Carapicuíba/SP",
        "Responsável Técnico: João da Silva",
        "Registro: CRBio 123456/01-D",
    )

    upload_response = client.post(
        "/api/v1/settings/technical-documents/assets/sanitary_license",
        headers=auth_headers,
        files={"file": ("licenca-sanitaria-real.pdf", pdf_content, "application/pdf")},
    )

    assert upload_response.status_code == 200
    company = upload_response.json()
    assert company["sanitary_license_number"] == "LS-TESTE-0001/2026"
    assert company["sanitary_license_expiry"] == "15/08/2027"


def test_operador_cannot_access_system_settings(client, auth_headers):
    create_user_response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nome": "Operador Config",
            "username": "operadorconfig",
            "password": "senha123",
            "role": "operador",
            "is_active": True,
            "nova_empresa_prestadora": {
                "razao_social": "Prestadora Operador Config Ltda",
                "nome_fantasia": "Prestadora Operador Config",
                "cnpj": "12312312000199",
                "email": "operadorconfig@empresa.com",
                "telefone": "11999998888",
                "cidade": "Sao Paulo",
                "estado": "SP",
            },
            "licenca_inicial": {
                "descricao": "Licenca operador config",
                "start_date": "2026-03-20",
                "end_date": "2027-03-20",
                "max_users": 3,
                "status": "ativa",
                "notes": "Licenca de teste",
            },
        },
    )
    assert create_user_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "operadorconfig", "password": "senha123"},
    )
    operador_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = client.get("/api/v1/settings", headers=operador_headers)

    assert response.status_code == 403


def test_disabling_multiempresa_removes_company_scope_from_core_queries(client, auth_headers):
    company_a_headers = _create_company_user(client, auth_headers, "adminseta", "31")
    company_b_headers = _create_company_user(client, auth_headers, "adminsetb", "42")

    create_customer_response = client.post(
        "/api/v1/clientes",
        headers=company_a_headers,
        json={
            "razao_social": "Cliente Empresa A",
            "cpf_cnpj": "31313131000131",
            "endereco": "Rua A, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11911112222",
            "contato": "Contato A",
        },
    )
    assert create_customer_response.status_code == 201

    isolated_response = client.get("/api/v1/clientes", headers=company_b_headers)
    assert isolated_response.status_code == 200
    assert isolated_response.json() == []

    disable_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={"system": {"multiempresa_enabled": False}},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["system"]["multiempresa_enabled"] is False

    shared_response = client.get("/api/v1/clientes", headers=company_b_headers)

    assert shared_response.status_code == 200
    assert len(shared_response.json()) == 1
    assert shared_response.json()[0]["razao_social"] == "Cliente Empresa A"


def test_company_technical_assets_remain_isolated_per_company(client, auth_headers):
    company_a_headers = _create_company_user(client, auth_headers, "admtecha", "51")
    company_b_headers = _create_company_user(client, auth_headers, "admtechb", "62")

    upload_response = client.post(
        "/api/v1/settings/technical-documents/assets/environmental_license",
        headers=company_a_headers,
        files={"file": ("ambiental-a.pdf", b"%PDF-1.4\nempresa-a", "application/pdf")},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["environmental_license_file"]["filename"] == "ambiental-a.pdf"

    company_b_settings = client.get("/api/v1/settings", headers=company_b_headers)
    assert company_b_settings.status_code == 200
    assert company_b_settings.json()["company"]["environmental_license_file"]["has_file"] is False

    company_b_download = client.get(
        "/api/v1/settings/technical-documents/assets/environmental_license",
        headers=company_b_headers,
    )
    assert company_b_download.status_code == 400
