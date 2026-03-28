from typing import List

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.application.schemas import (
    ProductCsvImportResult,
    ProductCreate,
    ProductRead,
    ProviderCompanyRead,
    StockBalanceCreate,
    StockCodeLookupRead,
    StockImportLogRead,
    StockInventoryCountCreate,
    StockInventoryFinalizeCreate,
    StockInventorySessionCreate,
    StockInventorySessionRead,
    StockLabelRequest,
    StockLocationCreate,
    StockLocationRead,
    StockLocationUpdate,
    StockMovementCreate,
    StockMovementRead,
    StockPositionRead,
    StockTransferCreate,
    StockWarehouseCreate,
    StockWarehouseRead,
    StockWarehouseUpdate,
    ProductUpdate,
    ProductXmlImportResult,
)
from app.application.services import (
    create_product,
    create_stock_balance,
    create_stock_inventory_session,
    create_stock_location,
    create_stock_movement,
    create_stock_transfer,
    create_stock_warehouse,
    delete_product,
    finalize_stock_inventory_session,
    generate_stock_labels_pdf,
    import_products_from_csv,
    import_products_from_invoice_xml,
    import_products_from_xlsx,
    list_stock_inventory_sessions,
    list_stock_locations,
    list_products,
    list_stock_companies,
    list_stock_import_logs,
    list_stock_movements,
    list_stock_positions,
    list_stock_warehouses,
    lookup_product_by_stock_code,
    register_stock_inventory_count,
    update_product,
    update_stock_location,
    update_stock_warehouse,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get(
    "/estoque/empresas",
    response_model=List[ProviderCompanyRead],
)
def get_stock_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[ProviderCompanyRead]:
    return list_stock_companies(db, current_user=current_user)


@router.get(
    "/estoque",
    response_model=List[StockPositionRead],
)
def get_stock_positions(
    empresa_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[StockPositionRead]:
    return list_stock_positions(db, current_user=current_user, company_id=empresa_id)


@router.get(
    "/estoque/movimentacoes",
    response_model=List[StockMovementRead],
)
def get_stock_movements(
    empresa_id: int | None = None,
    produto_id: int | None = None,
    tipo_movimento: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[StockMovementRead]:
    return list_stock_movements(
        db,
        current_user=current_user,
        company_id=empresa_id,
        product_id=produto_id,
        movement_type=tipo_movimento,
    )


@router.post(
    "/estoque/movimentacoes",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
)
def post_stock_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.move"])),
) -> StockMovementRead:
    return create_stock_movement(db, payload, current_user=current_user)


@router.get(
    "",
    response_model=List[ProductRead],
)
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[ProductRead]:
    return list_products(db, current_user=current_user)


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def post_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> ProductRead:
    return create_product(db, payload, current_user=current_user)


@router.put(
    "/{product_id}",
    response_model=ProductRead,
)
def put_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> ProductRead:
    return update_product(db, product_id, payload, current_user=current_user)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage", "records.delete"])),
) -> Response:
    delete_product(db, product_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/importar-xml",
    response_model=ProductXmlImportResult,
)
async def import_product_xml(
    xml_file: UploadFile = File(...),
    registrar_financeiro: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> ProductXmlImportResult:
    return import_products_from_invoice_xml(
        db,
        await xml_file.read(),
        create_finance_entry=registrar_financeiro,
        current_user=current_user,
        original_filename=xml_file.filename or "estoque.xml",
    )


@router.post(
    "/importar-csv",
    response_model=ProductCsvImportResult,
)
async def import_product_csv(
    csv_file: UploadFile = File(...),
    registrar_financeiro: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> ProductCsvImportResult:
    return import_products_from_csv(
        db,
        await csv_file.read(),
        create_finance_entry=registrar_financeiro,
        current_user=current_user,
        original_filename=csv_file.filename or "estoque.csv",
    )


@router.post(
    "/importar-xlsx",
    response_model=ProductCsvImportResult,
)
async def import_product_xlsx(
    xlsx_file: UploadFile = File(...),
    registrar_financeiro: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> ProductCsvImportResult:
    return import_products_from_xlsx(
        db,
        await xlsx_file.read(),
        create_finance_entry=registrar_financeiro,
        current_user=current_user,
        original_filename=xlsx_file.filename or "estoque.xlsx",
    )


@router.post(
    "/estoque/balanco",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
)
def post_stock_balance(
    payload: StockBalanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.move"])),
) -> StockMovementRead:
    return create_stock_balance(db, payload, current_user=current_user)


@router.post(
    "/estoque/transferencias",
    response_model=List[StockMovementRead],
    status_code=status.HTTP_201_CREATED,
)
def post_stock_transfer(
    payload: StockTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.move"])),
) -> List[StockMovementRead]:
    return create_stock_transfer(db, payload, current_user=current_user)


@router.get(
    "/estoque/importacoes",
    response_model=List[StockImportLogRead],
)
def get_stock_import_logs(
    empresa_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.view"])),
) -> List[StockImportLogRead]:
    return list_stock_import_logs(db, current_user=current_user, company_id=empresa_id)


@router.get(
    "/estoque/armazens",
    response_model=List[StockWarehouseRead],
)
def get_stock_warehouses(
    empresa_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[StockWarehouseRead]:
    return list_stock_warehouses(db, current_user=current_user, company_id=empresa_id)


@router.post(
    "/estoque/armazens",
    response_model=StockWarehouseRead,
    status_code=status.HTTP_201_CREATED,
)
def post_stock_warehouse(
    payload: StockWarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> StockWarehouseRead:
    return create_stock_warehouse(db, payload, current_user=current_user)


@router.put(
    "/estoque/armazens/{warehouse_id}",
    response_model=StockWarehouseRead,
)
def put_stock_warehouse(
    warehouse_id: int,
    payload: StockWarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> StockWarehouseRead:
    return update_stock_warehouse(db, warehouse_id, payload, current_user=current_user)


@router.get(
    "/estoque/locais",
    response_model=List[StockLocationRead],
)
def get_stock_locations(
    empresa_id: int | None = None,
    armazem_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[StockLocationRead]:
    return list_stock_locations(db, current_user=current_user, company_id=empresa_id, warehouse_id=armazem_id)


@router.post(
    "/estoque/locais",
    response_model=StockLocationRead,
    status_code=status.HTTP_201_CREATED,
)
def post_stock_location(
    payload: StockLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> StockLocationRead:
    return create_stock_location(db, payload, current_user=current_user)


@router.put(
    "/estoque/locais/{location_id}",
    response_model=StockLocationRead,
)
def put_stock_location(
    location_id: int,
    payload: StockLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.manage"])),
) -> StockLocationRead:
    return update_stock_location(db, location_id, payload, current_user=current_user)


@router.get(
    "/estoque/buscar-por-codigo/{codigo}",
    response_model=StockCodeLookupRead,
)
def get_stock_code_lookup(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> StockCodeLookupRead:
    return lookup_product_by_stock_code(db, codigo, current_user=current_user)


@router.get(
    "/estoque/inventarios",
    response_model=List[StockInventorySessionRead],
)
def get_stock_inventories(
    empresa_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"], ["stock.view"])),
) -> List[StockInventorySessionRead]:
    return list_stock_inventory_sessions(db, current_user=current_user, company_id=empresa_id)


@router.post(
    "/estoque/inventarios",
    response_model=StockInventorySessionRead,
    status_code=status.HTTP_201_CREATED,
)
def post_stock_inventory(
    payload: StockInventorySessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.move"])),
) -> StockInventorySessionRead:
    return create_stock_inventory_session(db, payload, current_user=current_user)


@router.post(
    "/estoque/inventarios/{inventory_id}/contagens",
    response_model=StockInventorySessionRead,
)
def post_stock_inventory_count(
    inventory_id: int,
    payload: StockInventoryCountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.move"])),
) -> StockInventorySessionRead:
    return register_stock_inventory_count(db, inventory_id, payload, current_user=current_user)


@router.post(
    "/estoque/inventarios/{inventory_id}/finalizar",
    response_model=StockInventorySessionRead,
)
def post_stock_inventory_finalize(
    inventory_id: int,
    payload: StockInventoryFinalizeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.move"])),
) -> StockInventorySessionRead:
    return finalize_stock_inventory_session(db, inventory_id, payload, current_user=current_user)


@router.post(
    "/estoque/etiquetas/pdf",
)
def post_stock_labels_pdf(
    payload: StockLabelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "gestor_estoque"], ["stock.view"])),
) -> Response:
    pdf_bytes = generate_stock_labels_pdf(db, payload, current_user=current_user)
    return Response(content=pdf_bytes, media_type="application/pdf")
