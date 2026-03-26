def test_root_redirects_to_web_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/app"


def test_web_app_returns_html(client):
    response = client.get("/app")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SysPragas" in response.text
    assert "Config. do sistema" in response.text
    assert "/static/vendor/adminlte/css/adminlte.min.css" in response.text
    assert "/static/vendor/datatables/js/jquery.dataTables.min.js" in response.text
    assert "/static/app.js?v=" in response.text


def test_static_app_js_includes_appointment_availability_feedback(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "Disponibilidade" in response.text
    assert "Nenhum conflito encontrado para este tecnico." in response.text
    assert "Tentar sincronizar no Google" in response.text
    assert "Enviar WhatsApp ao salvar este agendamento" in response.text
    assert "WhatsApp indisponivel" in response.text
    assert "Conectar via QR" in response.text
    assert "Conectar WhatsApp" in response.text
    assert "Autenticacao por QR Code" in response.text
    assert "Reabrir agendamento" in response.text
    assert "Periodo inicial" in response.text
    assert "Periodo final" in response.text
    assert "Reabrir OS" in response.text
    assert "Reimprimir OS" in response.text
    assert "Visualizar OS" in response.text
    assert "Abrir moldura" in response.text
    assert "Baixar moldura" in response.text
    assert "Moldura recomendada" in response.text
    assert "Sanitario padrao" in response.text
