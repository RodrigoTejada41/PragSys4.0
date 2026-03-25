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
