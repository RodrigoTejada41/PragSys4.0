from pathlib import Path

from app.infrastructure.db import get_session_local
from app.infrastructure.models import Appointment, Customer, FinanceEntry, WorkOrder


def _create_basic_work_order(client, auth_headers):
    customer = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Banco",
            "cpf_cnpj": "12345678000999",
            "endereco": "Rua Banco, 10",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999990000",
            "contato": "Operacao",
        },
    ).json()

    technician = client.post(
        "/api/v1/tecnicos",
        headers=auth_headers,
        json={
            "nome": "Tecnico Banco",
            "registro": "TEC-DB",
            "telefone": "11988887777",
            "ativo": True,
        },
    ).json()

    work_order = client.post(
        "/api/v1/os",
        headers=auth_headers,
        json={
            "numero": "OS-DB-001",
            "cliente_id": customer["id"],
            "tecnico_id": technician["id"],
            "data_execucao": "2026-03-26",
            "hora_inicio": "08:00:00",
            "hora_fim": "09:00:00",
            "local_execucao": "Area tecnica",
            "observacoes": "Fluxo para limpeza operacional",
            "garantia_ate": "2026-04-26",
            "status": "aberta",
            "valor_servico": "180.00",
            "produtos": [],
            "pragas_ids": [],
            "gerar_financeiro": True,
            "gerar_agendamento": True,
            "tipo_servico_agendamento": "Visita operacional",
            "duracao_prevista_minutos": 60,
        },
    )
    assert work_order.status_code == 200
    return customer["id"], work_order.json()["id"]


def test_database_backup_exports_sqlite_file(client, auth_headers):
    response = client.get("/api/v1/settings/database/backup", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "backup_" in response.headers["content-disposition"]
    assert response.content.startswith(b"SQLite format 3")


def test_database_restore_reinstates_previous_state_and_creates_safety_backup(client, auth_headers):
    settings_response = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={"database": {"backup_dir": "test_assets/database_backups"}},
    )
    assert settings_response.status_code == 200

    original = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Original Restore",
            "cpf_cnpj": "12345678000177",
            "endereco": "Rua A, 100",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "telefone": "11999990000",
            "contato": "Cliente original",
        },
    )
    assert original.status_code == 201

    backup_response = client.get("/api/v1/settings/database/backup", headers=auth_headers)
    assert backup_response.status_code == 200

    mutated = client.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "razao_social": "Cliente Mutado Restore",
            "cpf_cnpj": "12345678000188",
            "endereco": "Rua B, 200",
            "cidade": "Campinas",
            "estado": "SP",
            "telefone": "11999991111",
            "contato": "Cliente mutado",
        },
    )
    assert mutated.status_code == 201

    restore_response = client.post(
        "/api/v1/settings/database/restore",
        headers=auth_headers,
        data={"confirmation": "RESTAURAR"},
        files={"file": ("backup_test.db", backup_response.content, "application/octet-stream")},
    )
    assert restore_response.status_code == 200
    payload = restore_response.json()
    assert payload["message"] == "Restauracao concluida com sucesso."
    assert payload["safety_backup_file"].startswith("pre_restore_")

    customers = client.get("/api/v1/clientes", headers=auth_headers)
    assert customers.status_code == 200
    names = {item["razao_social"] for item in customers.json()}
    assert "Cliente Original Restore" in names
    assert "Cliente Mutado Restore" not in names

    safety_path = Path("test_assets/database_backups") / payload["safety_backup_file"]
    assert safety_path.exists()


def test_database_cleanup_removes_operational_data_and_preserves_customers(client, auth_headers):
    customer_id, work_order_id = _create_basic_work_order(client, auth_headers)

    cleanup_response = client.post(
        "/api/v1/settings/database/cleanup",
        headers=auth_headers,
        json={"confirmation": "CONFIRMAR", "include_finance": False},
    )
    assert cleanup_response.status_code == 200
    payload = cleanup_response.json()
    assert payload["message"] == "Limpeza de movimentacoes concluida com sucesso."
    assert payload["details"]["work_orders_removed"] == 1
    assert payload["details"]["appointments_removed"] >= 1
    assert payload["details"]["finance_links_detached"] >= 1

    session = get_session_local()()
    try:
        assert session.query(Customer).filter(Customer.id == customer_id).count() == 1
        assert session.query(WorkOrder).filter(WorkOrder.id == work_order_id).count() == 0
        assert session.query(Appointment).count() == 0
        finance_entries = session.query(FinanceEntry).all()
        assert len(finance_entries) == 1
        assert finance_entries[0].os_id is None
    finally:
        session.close()
