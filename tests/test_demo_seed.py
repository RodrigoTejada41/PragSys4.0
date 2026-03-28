from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.application.demo_seed_service import DEMO_MAIN_CNPJ, DemoSeedResult, generate_demo_dataset
from app.infrastructure.db import get_session_local
from app.infrastructure.models import CompanyTechnicalData, FinanceEntry, Product, ProviderCompany, Receipt, StockImportLog, StockMovement, WorkOrder


def test_generate_demo_dataset_creates_integrated_company_data():
    output_dir = Path("tmp") / "test-demo-seed"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    session = get_session_local()()
    try:
        result = generate_demo_dataset(session, output_dir=output_dir, replace_existing=True)
    finally:
        session.close()

    assert isinstance(result, DemoSeedResult)
    assert result.company_id != result.branch_company_id
    assert result.admin_username == "admin.demo"
    assert Path(result.files["manifest_json"]).exists()
    assert Path(result.files["sql_dump"]).exists()
    assert Path(result.files["work_order_pdf"]).exists()
    assert Path(result.files["technical_report_pdf"]).exists()
    assert Path(result.files["framed_certificate_pdf"]).exists()

    session = get_session_local()()
    try:
        company = session.query(ProviderCompany).filter(ProviderCompany.cnpj == DEMO_MAIN_CNPJ).one()
        assert session.query(CompanyTechnicalData).filter(CompanyTechnicalData.empresa_prestadora_id == company.id).count() == 1
        assert session.query(Product).filter(Product.empresa_prestadora_id == company.id).count() >= 6
        assert session.query(StockMovement).filter(StockMovement.empresa_prestadora_id == company.id).count() >= 8
        assert session.query(StockImportLog).filter(StockImportLog.empresa_prestadora_id == company.id).count() >= 2
        assert session.query(WorkOrder).filter(WorkOrder.empresa_prestadora_id == company.id).count() >= 4
        assert session.query(FinanceEntry).filter(FinanceEntry.empresa_prestadora_id == company.id).count() >= 6
        assert session.query(Receipt).count() == 1
    finally:
        session.close()

    manifest = json.loads(Path(result.files["manifest_json"]).read_text(encoding="utf-8"))
    assert manifest["companies"]["main"]["cnpj"] == DEMO_MAIN_CNPJ
    assert manifest["counts"]["work_orders"] >= 4
    assert manifest["imports"]["csv"]["produtos_processados"] == 2
    assert manifest["imports"]["xml"]["nota_numero"] == "1234"
    shutil.rmtree(output_dir, ignore_errors=True)
