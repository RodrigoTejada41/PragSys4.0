def test_root_redirects_to_web_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/app"


def test_web_app_returns_html(client):
    response = client.get("/app")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SysPragas" in response.text
    assert "/static/vendor/adminlte/css/adminlte.min.css" in response.text
    assert "/static/vendor/datatables/js/jquery.dataTables.min.js" in response.text
