from __future__ import annotations

import base64
import io
import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.contracts_service import create_contract, run_contract_maintenance
from app.application.receipt_services import create_receipt, generate_receipt_pdf
from app.application.schemas import (
    ContractCreate,
    CustomerCreate,
    FinanceEntryCreate,
    FinancePaymentRequest,
    LicenseCreate,
    PestCreate,
    ProductCreate,
    ProviderCompanyCreate,
    ReceiptCreate,
    SettingsCompanyUpdate,
    StockBalanceCreate,
    StockInventoryCountCreate,
    StockInventoryFinalizeCreate,
    StockInventorySessionCreate,
    StockLocationCreate,
    StockMovementCreate,
    StockTransferCreate,
    StockWarehouseCreate,
    SystemSettingsUpdate,
    TechnicianCreate,
    UserCreate,
    WorkOrderCreate,
    WorkOrderProductCreate,
)
from app.application.services import (
    create_customer,
    create_finance_entry,
    create_license,
    create_pest,
    create_product,
    create_provider_company,
    create_stock_balance,
    create_stock_inventory_session,
    create_stock_location,
    create_stock_movement,
    create_stock_transfer,
    create_stock_warehouse,
    create_technician,
    create_user,
    create_work_order,
    finalize_stock_inventory_session,
    generate_framed_sanitary_certificate_pdf,
    generate_guarantee_certificate_pdf,
    generate_sanitary_certificate_pdf,
    generate_technical_report_pdf,
    generate_work_order_pdf,
    import_products_from_csv,
    import_products_from_invoice_xml,
    mark_finance_entry_as_paid,
    mark_work_order_as_completed,
    register_stock_inventory_count,
)
from app.application.settings_service import save_company_signature_from_data_url, save_company_technical_asset, update_system_settings
from app.core.config import get_settings
from app.core.permissions import get_default_permissions_for_role
from app.domain.enums import (
    ContractBillingType,
    FinanceStatus,
    FinanceType,
    LicenseStatus,
    ReceiptPaymentMethod,
    UserRole,
    WorkOrderStatus,
    WorkOrderType,
)
from app.infrastructure.models import (
    Appointment,
    AppointmentHistory,
    AppointmentWhatsAppLog,
    CashLedgerEntry,
    CompanyTechnicalData,
    Contract,
    Customer,
    FinanceEntry,
    License,
    Pest,
    Product,
    ProviderCompany,
    Receipt,
    ReceiptHistory,
    StockImportLog,
    StockInventoryItem,
    StockInventorySession,
    StockLocation,
    StockLocationBalance,
    StockMovement,
    StockWarehouse,
    Technician,
    User,
    WorkOrder,
    WorkOrderPest,
    WorkOrderPhoto,
    WorkOrderProduct,
)

DEMO_MAIN_CNPJ = "11222333000181"
DEMO_BRANCH_CNPJ = "11222333000199"
DEMO_USER_PASSWORD = "Demo@123"
DEMO_SIGNATURE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5W9JcAAAAASUVORK5CYII="
)


@dataclass
class DemoSeedResult:
    generated_at: str
    output_dir: str
    company_id: int
    branch_company_id: int
    master_username: str
    admin_username: str
    operator_username: str
    branch_admin_username: str
    created_counts: dict[str, int]
    files: dict[str, str]
    identifiers: dict[str, Any]


# MARKER: rest of file follows in appended chunks
def generate_demo_dataset(
    db: Session,
    *,
    output_dir: str | Path = "output/demo_seed",
    replace_existing: bool = True,
) -> DemoSeedResult:
    base_dir = Path(output_dir)
    assets_dir = base_dir / "assets"
    documents_dir = base_dir / "documents"
    base_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    documents_dir.mkdir(parents=True, exist_ok=True)

    if replace_existing:
        _purge_existing_demo_data(db)

    global_master = _get_global_master_user(db)
    today = date.today()

    main_company = create_provider_company(
        db,
        ProviderCompanyCreate(
            razao_social="Dedetiza Prime Servicos Ambientais Ltda",
            nome_fantasia="Dedetiza Prime",
            cnpj=DEMO_MAIN_CNPJ,
            email="contato@dedetizaprime.demo",
            telefone="1131554400",
            cep="04567000",
            endereco="Avenida das Nacoes Unidas, 18801",
            bairro="Vila Almeida",
            cidade="Sao Paulo",
            estado="SP",
            is_active=True,
            is_provider=True,
            compartilha_visualizacao_estoque=False,
        ),
    )
    branch_company = create_provider_company(
        db,
        ProviderCompanyCreate(
            razao_social="Dedetiza Prime Filial Centro Ltda",
            nome_fantasia="Dedetiza Prime Centro",
            cnpj=DEMO_BRANCH_CNPJ,
            email="centro@dedetizaprime.demo",
            telefone="1131554410",
            cep="13010000",
            endereco="Rua Barreto Leme, 1450",
            bairro="Centro",
            cidade="Campinas",
            estado="SP",
            is_active=True,
            is_provider=True,
            empresa_pai_id=main_company.id,
            compartilha_visualizacao_estoque=True,
        ),
    )
    main_company.compartilha_visualizacao_estoque = True
    db.add(main_company)
    db.commit()
    db.refresh(main_company)

    create_license(
        db,
        LicenseCreate(
            descricao="Licenca demonstracao Dedetiza Prime",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=365),
            max_users=25,
            status=LicenseStatus.ATIVA,
            notes="Licenca criada automaticamente para ambiente demonstracao.",
            empresa_prestadora_id=main_company.id,
        ),
    )
    create_license(
        db,
        LicenseCreate(
            descricao="Licenca filial demonstracao",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=365),
            max_users=10,
            status=LicenseStatus.ATIVA,
            notes="Licenca filial criada automaticamente para ambiente demonstracao.",
            empresa_prestadora_id=branch_company.id,
        ),
    )

    master_demo = create_user(
        db,
        UserCreate(
            nome="Master Demonstracao",
            username="master.demo",
            password=DEMO_USER_PASSWORD,
            role=UserRole.MASTER,
            empresa_prestadora_id=main_company.id,
            permissions=get_default_permissions_for_role(UserRole.MASTER.value),
        ),
        current_user=global_master,
    )
    admin_demo = create_user(
        db,
        UserCreate(
            nome="Administrador Demonstracao",
            username="admin.demo",
            password=DEMO_USER_PASSWORD,
            role=UserRole.ADMIN,
            empresa_prestadora_id=main_company.id,
            permissions=get_default_permissions_for_role(UserRole.ADMIN.value),
        ),
        current_user=global_master,
    )
    operator_permissions = get_default_permissions_for_role(UserRole.OPERADOR.value)
    operator_permissions.update(
        {
            "stock.move": True,
            "contracts.manage": True,
        }
    )
    operator_demo = create_user(
        db,
        UserCreate(
            nome="Operador Campo Demonstracao",
            username="operador.demo",
            password=DEMO_USER_PASSWORD,
            role=UserRole.OPERADOR,
            empresa_prestadora_id=main_company.id,
            permissions=operator_permissions,
        ),
        current_user=global_master,
    )
    branch_admin = create_user(
        db,
        UserCreate(
            nome="Administrador Filial Centro",
            username="admin.filial.demo",
            password=DEMO_USER_PASSWORD,
            role=UserRole.ADMIN,
            empresa_prestadora_id=branch_company.id,
            permissions=get_default_permissions_for_role(UserRole.ADMIN.value),
        ),
        current_user=global_master,
    )

    _configure_company_technical_profile(db, admin_demo, assets_dir)
    _configure_company_technical_profile(
        db,
        branch_admin,
        assets_dir,
        legal_name="Dedetiza Prime Filial Centro Ltda",
        trade_name="Dedetiza Prime Centro",
        cnpj=DEMO_BRANCH_CNPJ,
        address="Rua Barreto Leme, 1450 - Centro - Campinas/SP - CEP 13010-000",
        phone="(11) 3155-4410",
        technical_name="Biologa Fernanda Costa",
        registry_number="654321",
        sanitary_number="LS-CAMP-2026-3001",
        sanitary_expiry="30/11/2026",
        environmental_number="LA-CAMP-2026-3001",
        environmental_expiry="15/12/2026",
        toxicology_phone="0800-555-1234",
    )

    main_warehouse = create_stock_warehouse(
        db,
        StockWarehouseCreate(
            empresa_prestadora_id=main_company.id,
            nome="Armazem Principal",
            codigo="ARM-PRINCIPAL",
            descricao="Estoque central da matriz para demonstracoes integradas.",
            tipo="armazem",
            ativo=True,
            padrao=False,
        ),
        current_user=admin_demo,
    )
    chemical_location = create_stock_location(
        db,
        StockLocationCreate(
            armazem_id=main_warehouse.id,
            nome="Setor Quimicos A",
            codigo="SETOR-A",
            descricao="Prateleiras para produtos liquidos e granulados.",
            ativo=True,
            padrao=True,
        ),
        current_user=admin_demo,
    )
    vehicle_warehouse = create_stock_warehouse(
        db,
        StockWarehouseCreate(
            empresa_prestadora_id=main_company.id,
            nome="Veiculo Equipe Alpha",
            codigo="VEIC-ALPHA",
            descricao="Estoque embarcado para atendimentos em campo.",
            tipo="veiculo",
            ativo=True,
            padrao=False,
        ),
        current_user=admin_demo,
    )
    vehicle_location = create_stock_location(
        db,
        StockLocationCreate(
            armazem_id=vehicle_warehouse.id,
            nome="Bau Tecnico",
            codigo="BAU-01",
            descricao="Compartimento principal do veiculo.",
            ativo=True,
            padrao=True,
        ),
        current_user=admin_demo,
    )
    branch_warehouse = create_stock_warehouse(
        db,
        StockWarehouseCreate(
            empresa_prestadora_id=branch_company.id,
            nome="Armazem Filial Centro",
            codigo="ARM-CENTRO",
            descricao="Estoque da filial para revisitas e redistribuicao.",
            tipo="armazem",
            ativo=True,
            padrao=False,
        ),
        current_user=branch_admin,
    )
    branch_location = create_stock_location(
        db,
        StockLocationCreate(
            armazem_id=branch_warehouse.id,
            nome="Prateleira A1",
            codigo="A1",
            descricao="Posicao principal da filial.",
            ativo=True,
            padrao=True,
        ),
        current_user=branch_admin,
    )

    pests = [
        create_pest(
            db,
            PestCreate(
                nome_comum="Barata",
                nome_cientifico="Periplaneta americana",
                descricao="Praga urbana de alta recorrencia.",
            ),
            current_user=admin_demo,
        ),
        create_pest(
            db,
            PestCreate(
                nome_comum="Cupim",
                nome_cientifico="Coptotermes gestroi",
                descricao="Cupim subterraneo para cenarios residenciais e corporativos.",
            ),
            current_user=admin_demo,
        ),
        create_pest(
            db,
            PestCreate(
                nome_comum="Roedor",
                nome_cientifico="Rattus norvegicus",
                descricao="Controle preventivo e corretivo de roedores.",
            ),
            current_user=admin_demo,
        ),
    ]
    technicians = [
        create_technician(
            db,
            TechnicianCreate(
                nome="Carlos Mendes",
                registro="TEC-DEMO-001",
                telefone="11988880001",
                ativo=True,
            ),
            current_user=admin_demo,
        ),
        create_technician(
            db,
            TechnicianCreate(
                nome="Luciana Prado",
                registro="TEC-DEMO-002",
                telefone="11988880002",
                ativo=True,
            ),
            current_user=admin_demo,
        ),
    ]

    create_product(
        db,
        ProductCreate(
            nome="Produto Existente XML",
            principio_ativo="Deltametrina",
            grupo_quimico="Piretroide",
            toxicidade="Media",
            concentracao="2%",
            registro_ms="MS-EXIST",
            categoria="Inseticida",
            unidade_medida="UN",
            codigo_barras="7891000001001",
            ncm="38089199",
            estoque_atual=Decimal("4.00"),
            estoque_minimo=Decimal("1.00"),
        ),
        current_user=admin_demo,
    )
    create_product(
        db,
        ProductCreate(
            nome="Produto Existente CSV",
            principio_ativo="Fipronil",
            grupo_quimico="Fenilpirazol",
            toxicidade="Baixa",
            concentracao="1%",
            registro_ms="CSV-EXIST",
            categoria="Gel",
            unidade_medida="UN",
            codigo_barras="7891000001002",
            ncm="38089199",
            estoque_atual=Decimal("1.00"),
            estoque_minimo=Decimal("0.50"),
        ),
        current_user=admin_demo,
    )
    ml_product = create_product(
        db,
        ProductCreate(
            nome="Inseticida Premium",
            principio_ativo="Lambda-cialotrina",
            grupo_quimico="Piretroide",
            toxicidade="Media",
            concentracao="25 g/L",
            registro_ms="MS-DEMO-ML-001",
            categoria="Inseticida liquido",
            unidade_medida="ML",
            codigo_barras="7891000002001",
            ncm="38089199",
            estoque_atual=Decimal("5000.00"),
            estoque_minimo=Decimal("1200.00"),
        ),
        current_user=admin_demo,
    )
    kg_product = create_product(
        db,
        ProductCreate(
            nome="Raticida Granulado",
            principio_ativo="Bromadiolona",
            grupo_quimico="Cumarinico",
            toxicidade="Alta",
            concentracao="0,005%",
            registro_ms="MS-DEMO-KG-001",
            categoria="Raticida",
            unidade_medida="KG",
            codigo_barras="7891000002002",
            ncm="38089199",
            estoque_atual=Decimal("25.00"),
            estoque_minimo=Decimal("8.00"),
        ),
        current_user=admin_demo,
    )
    unit_product = create_product(
        db,
        ProductCreate(
            nome="Armadilha Adesiva Premium",
            principio_ativo="Sem principio ativo",
            grupo_quimico="Fisico",
            toxicidade="Nao aplicavel",
            concentracao="Nao aplicavel",
            registro_ms="MS-DEMO-UN-001",
            categoria="Armadilha",
            unidade_medida="UN",
            codigo_barras="7891000002003",
            ncm="39269090",
            estoque_atual=Decimal("120.00"),
            estoque_minimo=Decimal("30.00"),
        ),
        current_user=admin_demo,
    )

    csv_result = import_products_from_csv(
        db,
        _build_sample_products_csv(),
        create_finance_entry=True,
        current_user=admin_demo,
        original_filename="entrada_demo.csv",
    )
    xml_result = import_products_from_invoice_xml(
        db,
        _build_sample_nfe_xml(),
        create_finance_entry=True,
        current_user=admin_demo,
        original_filename="nota_demo.xml",
    )

    create_stock_movement(
        db,
        StockMovementCreate(
            produto_id=ml_product.id,
            tipo_movimento="entrada",
            quantidade=Decimal("1500.00"),
            unidade_medida="ML",
            motivo="Reposicao de demonstracao",
            observacoes="Complemento de estoque no setor principal.",
            referencia="MOV-DEMO-001",
            armazem_id=main_warehouse.id,
            local_id=chemical_location.id,
        ),
        current_user=admin_demo,
    )
    create_stock_movement(
        db,
        StockMovementCreate(
            produto_id=kg_product.id,
            tipo_movimento="entrada",
            quantidade=Decimal("3.50"),
            unidade_medida="KG",
            motivo="Abastecimento do veiculo tecnico",
            observacoes="Carga inicial do atendimento externo.",
            referencia="MOV-DEMO-002",
            armazem_id=vehicle_warehouse.id,
            local_id=vehicle_location.id,
        ),
        current_user=admin_demo,
    )
    create_stock_balance(
        db,
        StockBalanceCreate(
            produto_id=unit_product.id,
            saldo_contado=Decimal("118.00"),
            unidade_medida="UN",
            motivo="Ajuste por conferencia inicial",
            observacoes="Duas armadilhas danificadas foram descartadas.",
            referencia="BAL-DEMO-001",
        ),
        current_user=admin_demo,
    )
    create_stock_transfer(
        db,
        StockTransferCreate(
            produto_id=ml_product.id,
            empresa_destino_id=branch_company.id,
            quantidade=Decimal("600.00"),
            unidade_medida="ML",
            motivo="Reforco da filial para campanha comercial",
            observacoes="Transferencia entre matriz e filial vinculada.",
            referencia="TRF-DEMO-001",
            armazem_origem_id=main_warehouse.id,
            local_origem_id=chemical_location.id,
            armazem_destino_id=branch_warehouse.id,
            local_destino_id=branch_location.id,
        ),
        current_user=admin_demo,
    )

    inventory_session = create_stock_inventory_session(
        db,
        StockInventorySessionCreate(
            armazem_id=main_warehouse.id,
            local_id=chemical_location.id,
            observacoes="Inventario assistido para demonstracao comercial.",
        ),
        current_user=admin_demo,
    )
    register_stock_inventory_count(
        db,
        inventory_session.id,
        StockInventoryCountCreate(produto_id=ml_product.id, quantidade=Decimal("5600.00"), unidade_medida="ML"),
        current_user=admin_demo,
    )
    register_stock_inventory_count(
        db,
        inventory_session.id,
        StockInventoryCountCreate(codigo=unit_product.codigo_barras, quantidade=Decimal("118.00"), unidade_medida="UN"),
        current_user=admin_demo,
    )
    finalize_stock_inventory_session(
        db,
        inventory_session.id,
        StockInventoryFinalizeCreate(aplicar_ajustes=True, motivo_ajuste="Ajuste final do inventario demonstracao"),
        current_user=admin_demo,
    )

    customers = [
        create_customer(
            db,
            CustomerCreate(
                razao_social="Mariana Alves",
                cpf_cnpj="12345678901",
                email="mariana.alves@cliente.demo",
                cep="01311000",
                endereco="Rua Augusta",
                numero="1500",
                complemento="Apto 42",
                bairro="Consolacao",
                cidade="Sao Paulo",
                estado="SP",
                telefone="11970000001",
                contato="Mariana Alves",
            ),
            current_user=admin_demo,
        ),
        create_customer(
            db,
            CustomerCreate(
                razao_social="Supermercado Horizonte Ltda",
                cpf_cnpj="22333444000155",
                email="facilities@horizonte.demo",
                cep="13015020",
                endereco="Avenida Moraes Salles",
                numero="2200",
                complemento="Loja 1",
                bairro="Centro",
                cidade="Campinas",
                estado="SP",
                telefone="1933004400",
                contato="Rafael Souza",
            ),
            current_user=admin_demo,
        ),
        create_customer(
            db,
            CustomerCreate(
                razao_social="Condominio Bosque Azul",
                cpf_cnpj="33444555000166",
                email="sindico@bosqueazul.demo",
                cep="04794000",
                endereco="Rua Arlindo Veiga",
                numero="85",
                complemento="Portaria",
                bairro="Santo Amaro",
                cidade="Sao Paulo",
                estado="SP",
                telefone="11970000003",
                contato="Patricia Lima",
            ),
            current_user=admin_demo,
        ),
        create_customer(
            db,
            CustomerCreate(
                razao_social="Industria Delta Quimica S.A.",
                cpf_cnpj="44555666000177",
                email="compras@deltaquimica.demo",
                cep="09910010",
                endereco="Rodovia Anchieta",
                numero="5000",
                complemento="Galpao B",
                bairro="Jardim Primavera",
                cidade="Sao Bernardo do Campo",
                estado="SP",
                telefone="1140005500",
                contato="Denise Rocha",
            ),
            current_user=admin_demo,
        ),
    ]

    active_contract = create_contract(
        db,
        customers[1].id,
        ContractCreate(
            nome="Contrato Preventivo Mensal Horizonte",
            data_inicio=today - timedelta(days=90),
            data_vencimento=today + timedelta(days=180),
            valor_mensal=Decimal("1850.00"),
            tipo_cobranca=ContractBillingType.MENSAL,
            dia_vencimento=10,
            gerar_cobranca_automatica=False,
            observacoes="Contrato ativo sem geracao automatica de cobranca por OS.",
        ),
        file_payload=(
            "contrato-horizonte.pdf",
            "application/pdf",
            _build_mock_pdf(
                "Contrato Horizonte",
                [
                    "Contrato preventivo mensal",
                    "Cliente: Supermercado Horizonte Ltda",
                ],
            ),
        ),
        current_user=admin_demo,
    )
    expiring_contract = create_contract(
        db,
        customers[2].id,
        ContractCreate(
            nome="Contrato Condominio Bosque Azul",
            data_inicio=today - timedelta(days=330),
            data_vencimento=today + timedelta(days=12),
            valor_mensal=Decimal("1320.00"),
            tipo_cobranca=ContractBillingType.MENSAL,
            dia_vencimento=5,
            gerar_cobranca_automatica=True,
            observacoes="Contrato com alerta de vencimento e cobranca automatica.",
        ),
        current_user=admin_demo,
    )
    expired_contract = create_contract(
        db,
        customers[3].id,
        ContractCreate(
            nome="Contrato Industria Delta - legado",
            data_inicio=today - timedelta(days=420),
            data_vencimento=today - timedelta(days=15),
            valor_mensal=Decimal("2750.00"),
            tipo_cobranca=ContractBillingType.PERSONALIZADO,
            dia_vencimento=15,
            gerar_cobranca_automatica=False,
            observacoes="Contrato expirado para cenarios de alerta e renovacao.",
        ),
        current_user=admin_demo,
    )
    maintenance_summary = run_contract_maintenance(db, current_user=admin_demo)

    manual_expense = create_finance_entry(
        db,
        FinanceEntryCreate(
            tipo=FinanceType.DESPESA,
            descricao="Manutencao da bomba costal",
            valor=Decimal("420.00"),
            vencimento=today - timedelta(days=3),
            status=FinanceStatus.ATRASADO,
            categoria="Operacional",
            fornecedor_nome="Oficina Campo Seguro",
            origem="manual",
            referencia="FIN-DEMO-DESP-001",
            total_parcelas=1,
            parcela_atual=1,
            observacoes="Despesa operacional para demonstracao do contas a pagar.",
            cliente_id=None,
            contrato_id=None,
            os_id=None,
            nfe_id=None,
        ),
        current_user=admin_demo,
    )
    manual_revenue = create_finance_entry(
        db,
        FinanceEntryCreate(
            tipo=FinanceType.RECEITA,
            descricao="Receita avulsa de higienizacao tecnica",
            valor=Decimal("980.00"),
            vencimento=today - timedelta(days=10),
            status=FinanceStatus.PAGO,
            categoria="Servico avulso",
            fornecedor_nome=None,
            origem="manual",
            referencia="ASAAS-MOCK-001",
            total_parcelas=1,
            parcela_atual=1,
            observacoes="Boleto mock integrado ao fluxo financeiro para demonstracao.",
            cliente_id=customers[0].id,
            contrato_id=None,
            os_id=None,
            nfe_id=None,
        ),
        current_user=admin_demo,
    )

    work_orders = []
    work_orders.append(
        create_work_order(
            db,
            WorkOrderCreate(
                cliente_id=customers[0].id,
                tecnico_id=technicians[0].id,
                data_execucao=today + timedelta(days=1),
                hora_inicio=time(9, 0),
                hora_fim=time(10, 30),
                local_execucao="Residencia principal - cozinha e lavanderia",
                observacoes="OS aberta para visita agendada.",
                garantia_ate=today + timedelta(days=30),
                status=WorkOrderStatus.ABERTA,
                tipo_os=WorkOrderType.AVULSA,
                valor_servico=Decimal("380.00"),
                produtos=[WorkOrderProductCreate(produto_id=unit_product.id, quantidade=Decimal("2.00"), diluicao="Instalacao direta")],
                pragas_ids=[pests[0].id],
                gerar_financeiro=True,
                gerar_agendamento=True,
                tipo_servico_agendamento="Controle preventivo",
                duracao_prevista_minutos=90,
            ),
            current_user_id=operator_demo.id,
        )
    )
    work_orders.append(
        create_work_order(
            db,
            WorkOrderCreate(
                cliente_id=customers[0].id,
                tecnico_id=technicians[1].id,
                data_execucao=today,
                hora_inicio=time(14, 0),
                hora_fim=time(15, 30),
                local_execucao="Area gourmet e quintal",
                observacoes="OS em andamento para demonstracao de campo.",
                garantia_ate=today + timedelta(days=45),
                status=WorkOrderStatus.EM_EXECUCAO,
                tipo_os=WorkOrderType.AVULSA,
                valor_servico=Decimal("460.00"),
                produtos=[WorkOrderProductCreate(produto_id=ml_product.id, quantidade=Decimal("350.00"), diluicao="Diluir em 5L")],
                pragas_ids=[pests[0].id, pests[2].id],
                gerar_financeiro=True,
                gerar_agendamento=True,
                tipo_servico_agendamento="Aplicacao complementar",
                duracao_prevista_minutos=90,
            ),
            current_user_id=operator_demo.id,
        )
    )
    completed_contract_os = create_work_order(
        db,
        WorkOrderCreate(
            cliente_id=customers[1].id,
            tecnico_id=technicians[0].id,
            data_execucao=today - timedelta(days=7),
            hora_inicio=time(8, 30),
            hora_fim=time(10, 0),
            local_execucao="Deposito e area de recebimento",
            observacoes="Visita mensal prevista em contrato ativo.",
            garantia_ate=today + timedelta(days=60),
            status=WorkOrderStatus.ABERTA,
            tipo_os=WorkOrderType.CONTRATO,
            valor_servico=Decimal("0.00"),
            produtos=[WorkOrderProductCreate(produto_id=kg_product.id, quantidade=Decimal("1.20"), diluicao="Aplicacao em iscas")],
            pragas_ids=[pests[2].id],
            gerar_financeiro=True,
            gerar_agendamento=True,
            tipo_servico_agendamento="Visita contratual",
            duracao_prevista_minutos=90,
        ),
        current_user_id=operator_demo.id,
    )
    completed_contract_os = mark_work_order_as_completed(db, completed_contract_os.id, current_user_id=admin_demo.id)
    work_orders.append(completed_contract_os)

    completed_avulsa_os = create_work_order(
        db,
        WorkOrderCreate(
            cliente_id=customers[2].id,
            tecnico_id=technicians[1].id,
            data_execucao=today - timedelta(days=14),
            hora_inicio=time(7, 45),
            hora_fim=time(9, 15),
            local_execucao="Portaria, hall e casa de bombas",
            observacoes="Atendimento avulso concluido com emissao de recibo.",
            garantia_ate=today + timedelta(days=90),
            status=WorkOrderStatus.ABERTA,
            tipo_os=WorkOrderType.AVULSA,
            valor_servico=Decimal("650.00"),
            produtos=[
                WorkOrderProductCreate(produto_id=ml_product.id, quantidade=Decimal("420.00"), diluicao="Diluir em 8L"),
                WorkOrderProductCreate(produto_id=unit_product.id, quantidade=Decimal("4.00"), diluicao="Instalacao direta"),
            ],
            pragas_ids=[pests[0].id, pests[1].id],
            gerar_financeiro=True,
            gerar_agendamento=True,
            tipo_servico_agendamento="Atendimento emergencial",
            duracao_prevista_minutos=120,
        ),
        current_user_id=operator_demo.id,
    )
    completed_avulsa_os = mark_work_order_as_completed(db, completed_avulsa_os.id, current_user_id=admin_demo.id)
    work_orders.append(completed_avulsa_os)

    for work_order in (completed_contract_os, completed_avulsa_os):
        db.add(
            WorkOrderPhoto(
                os_id=work_order.id,
                filename=f"os-{work_order.numero.lower()}-foto-01.png",
                content_type="image/png",
                image_data=_signature_png_bytes(),
            )
        )
    db.commit()

    receipt = create_receipt(
        db,
        ReceiptCreate(
            cliente_id=customers[2].id,
            os_id=completed_avulsa_os.id,
            valor=Decimal("650.00"),
            forma_pagamento=ReceiptPaymentMethod.PIX,
            descricao="Recebimento integral do atendimento emergencial do condominio.",
            data_recebimento=today - timedelta(days=13),
        ),
        current_user_id=admin_demo.id,
    )

    os_finance_entry = db.execute(
        select(FinanceEntry).where(FinanceEntry.os_id == work_orders[1].id).order_by(FinanceEntry.id.asc())
    ).scalars().first()
    if os_finance_entry is not None:
        mark_finance_entry_as_paid(
            db,
            os_finance_entry.id,
            FinancePaymentRequest(valor=Decimal(os_finance_entry.saldo_aberto), data_pagamento=today),
            current_user=admin_demo,
        )

    generated_files = _generate_document_pack(db, completed_avulsa_os.id, receipt.id, documents_dir, admin_demo)

    blueprint_path = base_dir / "dataset_blueprint.json"
    blueprint_path.write_text(
        json.dumps(_build_blueprint_json(main_company.id, branch_company.id), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest_path = base_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(
            _build_manifest(
                db,
                main_company.id,
                branch_company.id,
                generated_files,
                maintenance_summary,
                csv_result,
                xml_result,
            ),
            indent=2,
            ensure_ascii=False,
            default=_json_default,
        ),
        encoding="utf-8",
    )

    sql_dump_path = base_dir / "demo_seed_dump.sql"
    _export_sql_dump(sql_dump_path)

    return DemoSeedResult(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        output_dir=str(base_dir.resolve()),
        company_id=main_company.id,
        branch_company_id=branch_company.id,
        master_username=master_demo.username,
        admin_username=admin_demo.username,
        operator_username=operator_demo.username,
        branch_admin_username=branch_admin.username,
        created_counts={
            "companies": db.query(ProviderCompany).filter(ProviderCompany.cnpj.in_([DEMO_MAIN_CNPJ, DEMO_BRANCH_CNPJ])).count(),
            "users": db.query(User).filter(User.username.in_(["master.demo", "admin.demo", "operador.demo", "admin.filial.demo"])).count(),
            "products_main_company": db.query(Product).filter(Product.empresa_prestadora_id == main_company.id).count(),
            "products_branch_company": db.query(Product).filter(Product.empresa_prestadora_id == branch_company.id).count(),
            "customers": db.query(Customer).filter(Customer.empresa_prestadora_id == main_company.id).count(),
            "contracts": db.query(Contract).filter(Contract.empresa_prestadora_id == main_company.id).count(),
            "work_orders": db.query(WorkOrder).filter(WorkOrder.empresa_prestadora_id == main_company.id).count(),
            "finance_entries": db.query(FinanceEntry).filter(FinanceEntry.empresa_prestadora_id == main_company.id).count(),
            "stock_movements": db.query(StockMovement).filter(StockMovement.empresa_prestadora_id.in_([main_company.id, branch_company.id])).count(),
        },
        files={
            "blueprint_json": str(blueprint_path.resolve()),
            "manifest_json": str(manifest_path.resolve()),
            "sql_dump": str(sql_dump_path.resolve()),
            **{key: str(Path(value).resolve()) for key, value in generated_files.items()},
        },
        identifiers={
            "company_cnpj": DEMO_MAIN_CNPJ,
            "branch_cnpj": DEMO_BRANCH_CNPJ,
            "default_password": DEMO_USER_PASSWORD,
            "receipt_number": receipt.numero,
            "completed_work_order_number": completed_avulsa_os.numero,
            "contract_ids": [active_contract["id"], expiring_contract["id"], expired_contract["id"]],
            "manual_expense_id": manual_expense.id,
            "manual_revenue_id": manual_revenue.id,
        },
    )


def _configure_company_technical_profile(
    db: Session,
    user: User,
    assets_dir: Path,
    *,
    legal_name: str = "Dedetiza Prime Servicos Ambientais Ltda",
    trade_name: str = "Dedetiza Prime",
    cnpj: str = DEMO_MAIN_CNPJ,
    address: str = "Avenida das Nacoes Unidas, 18801 - Vila Almeida - Sao Paulo/SP - CEP 04567-000",
    phone: str = "(11) 3155-4400",
    technical_name: str = "Biologo Renato Tavares",
    registry_number: str = "123456",
    sanitary_number: str = "LS-SP-2026-1001",
    sanitary_expiry: str = "31/12/2026",
    environmental_number: str = "LA-SP-2026-2001",
    environmental_expiry: str = "31/10/2026",
    toxicology_phone: str = "0800-722-6001",
) -> None:
    update_system_settings(
        db,
        SystemSettingsUpdate(
            company=SettingsCompanyUpdate(
                legal_name=legal_name,
                trade_name=trade_name,
                cnpj=cnpj,
                address=address,
                phone=phone,
                technical_responsible_name=technical_name,
                technical_registry_type="CRBio",
                technical_registry_number=registry_number,
                technical_registry_state="SP",
                sanitary_license_number=sanitary_number,
                sanitary_license_expiry=sanitary_expiry,
                environmental_license_number=environmental_number,
                environmental_license_expiry=environmental_expiry,
                toxicology_center_name="Centro de Informacao Toxicologica",
                toxicology_center_phone=toxicology_phone,
            )
        ),
        current_user=user,
    )

    sanitary_pdf = _build_mock_pdf(
        "Licenca Sanitaria Mock",
        [
            f"Empresa: {trade_name}",
            f"Responsavel tecnico: {technical_name}",
            f"Registro: CRBio {registry_number}/SP",
            f"Endereco: {address}",
            f"Numero da Licenca: {sanitary_number}",
            f"Validade: {sanitary_expiry}",
            "Centro de Informacao Toxicologica: Centro de Informacao Toxicologica",
            f"Telefone CIT: {toxicology_phone}",
        ],
    )
    environmental_pdf = _build_mock_pdf(
        "Licenca Ambiental Mock",
        [
            f"Empresa: {trade_name}",
            f"Responsavel tecnico: {technical_name}",
            f"Registro profissional: CRBio {registry_number}/SP",
            f"Endereco da empresa: {address}",
            f"Numero da Licenca: {environmental_number}",
            f"Vencimento: {environmental_expiry}",
            "Centro de Informacao Toxicologica: Centro de Informacao Toxicologica",
            f"Telefone CIT: {toxicology_phone}",
        ],
    )

    sanitary_path = assets_dir / f"sanitary-{user.username}.pdf"
    environmental_path = assets_dir / f"environmental-{user.username}.pdf"
    signature_path = assets_dir / f"signature-{user.username}.png"
    sanitary_path.write_bytes(sanitary_pdf)
    environmental_path.write_bytes(environmental_pdf)
    signature_path.write_bytes(_signature_png_bytes())

    save_company_technical_asset(
        db,
        current_user=user,
        asset_kind="sanitary_license",
        filename=sanitary_path.name,
        content_type="application/pdf",
        content=sanitary_pdf,
    )
    save_company_technical_asset(
        db,
        current_user=user,
        asset_kind="environmental_license",
        filename=environmental_path.name,
        content_type="application/pdf",
        content=environmental_pdf,
    )
    save_company_signature_from_data_url(
        db,
        current_user=user,
        data_url=f"data:image/png;base64,{base64.b64encode(_signature_png_bytes()).decode('ascii')}",
    )


def _generate_document_pack(db: Session, work_order_id: int, receipt_id: int, documents_dir: Path, current_user: User) -> dict[str, str]:
    files = {
        "work_order_pdf": documents_dir / "ordem_servico_demo.pdf",
        "technical_report_pdf": documents_dir / "relatorio_tecnico_demo.pdf",
        "sanitary_certificate_pdf": documents_dir / "certificado_sanitario_demo.pdf",
        "framed_certificate_pdf": documents_dir / "certificado_moldura_demo.pdf",
        "guarantee_certificate_pdf": documents_dir / "garantia_demo.pdf",
        "receipt_pdf": documents_dir / "recibo_demo.pdf",
    }
    files["work_order_pdf"].write_bytes(generate_work_order_pdf(db, work_order_id, current_user=current_user))
    files["technical_report_pdf"].write_bytes(generate_technical_report_pdf(db, work_order_id, current_user=current_user))
    files["sanitary_certificate_pdf"].write_bytes(generate_sanitary_certificate_pdf(db, work_order_id, current_user=current_user))
    files["framed_certificate_pdf"].write_bytes(generate_framed_sanitary_certificate_pdf(db, work_order_id, current_user=current_user))
    files["guarantee_certificate_pdf"].write_bytes(generate_guarantee_certificate_pdf(db, work_order_id, current_user=current_user))
    files["receipt_pdf"].write_bytes(generate_receipt_pdf(db, receipt_id, current_user_id=current_user.id))
    return {key: str(path) for key, path in files.items()}


def _build_manifest(
    db: Session,
    company_id: int,
    branch_company_id: int,
    generated_files: dict[str, str],
    maintenance_summary: dict[str, Any],
    csv_result: Any,
    xml_result: Any,
) -> dict[str, Any]:
    main_company = db.get(ProviderCompany, company_id)
    branch_company = db.get(ProviderCompany, branch_company_id)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "companies": {
            "main": {
                "id": main_company.id,
                "razao_social": main_company.razao_social,
                "nome_fantasia": main_company.nome_fantasia,
                "cnpj": main_company.cnpj,
                "cidade": main_company.cidade,
                "estado": main_company.estado,
            },
            "branch": {
                "id": branch_company.id,
                "razao_social": branch_company.razao_social,
                "nome_fantasia": branch_company.nome_fantasia,
                "cnpj": branch_company.cnpj,
                "empresa_pai_id": branch_company.empresa_pai_id,
            },
        },
        "users": [
            {
                "username": user.username,
                "role": user.role,
                "empresa_prestadora_id": user.empresa_prestadora_id,
            }
            for user in db.execute(
                select(User)
                .where(User.username.in_(["master.demo", "admin.demo", "operador.demo", "admin.filial.demo"]))
                .order_by(User.id.asc())
            ).scalars()
        ],
        "counts": {
            "products": db.query(Product).filter(Product.empresa_prestadora_id.in_([company_id, branch_company_id])).count(),
            "stock_movements": db.query(StockMovement).filter(StockMovement.empresa_prestadora_id.in_([company_id, branch_company_id])).count(),
            "stock_import_logs": db.query(StockImportLog).filter(StockImportLog.empresa_prestadora_id == company_id).count(),
            "customers": db.query(Customer).filter(Customer.empresa_prestadora_id == company_id).count(),
            "contracts": db.query(Contract).filter(Contract.empresa_prestadora_id == company_id).count(),
            "work_orders": db.query(WorkOrder).filter(WorkOrder.empresa_prestadora_id == company_id).count(),
            "appointments": db.query(Appointment).filter(Appointment.empresa_prestadora_id == company_id).count(),
            "finance_entries": db.query(FinanceEntry).filter(FinanceEntry.empresa_prestadora_id == company_id).count(),
            "receipts": db.query(Receipt).filter(Receipt.empresa_prestadora_id == company_id).count(),
        },
        "imports": {
            "csv": json.loads(json.dumps(csv_result, default=_json_default)),
            "xml": json.loads(json.dumps(xml_result, default=_json_default)),
        },
        "contract_maintenance": maintenance_summary,
        "documents": generated_files,
    }


def _build_blueprint_json(company_id: int, branch_company_id: int) -> dict[str, Any]:
    return {
        "tenant": {
            "main_company_id": company_id,
            "branch_company_id": branch_company_id,
            "main_company_cnpj": DEMO_MAIN_CNPJ,
            "branch_company_cnpj": DEMO_BRANCH_CNPJ,
        },
        "credentials": {
            "default_password": DEMO_USER_PASSWORD,
            "users": ["master.demo", "admin.demo", "operador.demo", "admin.filial.demo"],
        },
        "coverage": {
            "modules": [
                "empresas_prestadoras",
                "usuarios",
                "clientes",
                "contratos",
                "produtos",
                "estoque",
                "importacoes_estoque",
                "inventario",
                "transferencias",
                "ordens_servico",
                "agendamentos",
                "financeiro",
                "recibos",
                "documentos_tecnicos",
            ],
            "generated_files": [
                "assinatura png",
                "licenca sanitaria pdf",
                "licenca ambiental pdf",
                "pdfs de os/relatorio/certificados/recibo",
                "sql dump sqlite",
                "manifest json",
            ],
        },
    }


def _build_sample_products_csv() -> bytes:
    return (
        "nome;principio_ativo;grupo_quimico;toxicidade;concentracao;registro_ms;quantidade_entrada;estoque_minimo;custo_total;fornecedor_nome;referencia;data_entrada;categoria_financeira;observacoes;registrar_financeiro\n"
        "Gel Baraticida Prime;Fipronil;Fenilpirazol;Baixa;2%;CSV-001;8.00;2.00;240.00;Fornecedor Prime;CSV-DEMO-001;2026-03-21;Compra de estoque;Entrada inicial demonstracao;true\n"
        "Produto Existente CSV;Fipronil;Fenilpirazol;Media;1%;CSV-EXIST;2.50;0.50;80.00;Fornecedor Prime;CSV-DEMO-002;2026-03-21;Reposicao;Complemento de lote;true\n"
    ).encode("utf-8")


def _build_sample_nfe_xml() -> bytes:
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
            <xNome>Fornecedor XML Demo Ltda</xNome>
            <CNPJ>12345678000100</CNPJ>
          </emit>
          <det nItem="1">
            <prod>
              <cProd>XML-001</cProd>
              <cEAN>7891000003001</cEAN>
              <xProd>Inseticida NF Demo</xProd>
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
              <cEAN>7891000003002</cEAN>
              <xProd>Produto Existente XML</xProd>
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


def _build_mock_pdf(title: str, lines: list[str]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(title)
    y = 800
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, title)
    y -= 30
    pdf.setFont("Helvetica", 11)
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 18
    pdf.save()
    return buffer.getvalue()


def _signature_png_bytes() -> bytes:
    return base64.b64decode(DEMO_SIGNATURE_PNG_BASE64)


def _get_global_master_user(db: Session) -> User:
    user = db.execute(select(User).where(User.role == UserRole.MASTER.value).order_by(User.id.asc())).scalars().first()
    if user is None:
        raise RuntimeError("Nenhum usuario master foi encontrado para gerar a base demonstracao.")
    return user


def _purge_existing_demo_data(db: Session) -> None:
    company_ids = [
        item.id
        for item in db.execute(
            select(ProviderCompany).where(ProviderCompany.cnpj.in_([DEMO_MAIN_CNPJ, DEMO_BRANCH_CNPJ]))
        ).scalars()
    ]
    if not company_ids:
        return

    contract_paths = [
        contract.arquivo_caminho
        for contract in db.execute(select(Contract).where(Contract.empresa_prestadora_id.in_(company_ids))).scalars()
        if contract.arquivo_caminho
    ]
    appointment_ids = list(db.execute(select(Appointment.id).where(Appointment.empresa_prestadora_id.in_(company_ids))).scalars())
    work_order_ids = list(db.execute(select(WorkOrder.id).where(WorkOrder.empresa_prestadora_id.in_(company_ids))).scalars())
    inventory_ids = list(db.execute(select(StockInventorySession.id).where(StockInventorySession.empresa_prestadora_id.in_(company_ids))).scalars())
    receipt_ids = list(db.execute(select(Receipt.id).where(Receipt.empresa_prestadora_id.in_(company_ids))).scalars())

    if appointment_ids:
        db.query(AppointmentHistory).filter(AppointmentHistory.agendamento_id.in_(appointment_ids)).delete(synchronize_session=False)
        db.query(AppointmentWhatsAppLog).filter(AppointmentWhatsAppLog.agendamento_id.in_(appointment_ids)).delete(synchronize_session=False)
    if work_order_ids:
        db.query(WorkOrderPhoto).filter(WorkOrderPhoto.os_id.in_(work_order_ids)).delete(synchronize_session=False)
        db.query(WorkOrderProduct).filter(WorkOrderProduct.os_id.in_(work_order_ids)).delete(synchronize_session=False)
        db.query(WorkOrderPest).filter(WorkOrderPest.os_id.in_(work_order_ids)).delete(synchronize_session=False)
    if inventory_ids:
        db.query(StockInventoryItem).filter(StockInventoryItem.inventario_id.in_(inventory_ids)).delete(synchronize_session=False)
    if receipt_ids:
        db.query(ReceiptHistory).filter(ReceiptHistory.recibo_id.in_(receipt_ids)).delete(synchronize_session=False)

    finance_ids = list(db.execute(select(FinanceEntry.id).where(FinanceEntry.empresa_prestadora_id.in_(company_ids))).scalars())
    if finance_ids:
        db.query(CashLedgerEntry).filter(CashLedgerEntry.finance_entry_id.in_(finance_ids)).delete(synchronize_session=False)

    db.query(Receipt).filter(Receipt.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(FinanceEntry).filter(FinanceEntry.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(Appointment).filter(Appointment.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(WorkOrder).filter(WorkOrder.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(StockInventorySession).filter(StockInventorySession.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(StockLocationBalance).filter(StockLocationBalance.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(StockMovement).filter(StockMovement.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(StockImportLog).filter(StockImportLog.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(StockLocation).filter(StockLocation.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(StockWarehouse).filter(StockWarehouse.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(Contract).filter(Contract.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(Pest).filter(Pest.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(Technician).filter(Technician.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(Product).filter(Product.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(Customer).filter(Customer.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(CompanyTechnicalData).filter(CompanyTechnicalData.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(License).filter(License.empresa_prestadora_id.in_(company_ids)).delete(synchronize_session=False)
    db.query(User).filter(
        User.empresa_prestadora_id.in_(company_ids),
        User.username != get_settings().default_admin_username,
    ).delete(synchronize_session=False)
    db.query(ProviderCompany).filter(ProviderCompany.id.in_(company_ids)).delete(synchronize_session=False)
    db.commit()

    for stored_path in contract_paths:
        try:
            Path(stored_path).unlink(missing_ok=True)
        except OSError:
            continue


def _export_sql_dump(destination: Path) -> None:
    settings = get_settings()
    if not settings.database_url.startswith("sqlite:///"):
        destination.write_text("-- SQL dump automatico disponivel apenas para bancos SQLite neste utilitario.\n", encoding="utf-8")
        return
    database_path = settings.database_url.replace("sqlite:///", "", 1)
    with sqlite3.connect(database_path) as connection:
        dump = "\n".join(connection.iterdump())
    destination.write_text(dump, encoding="utf-8")


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)
