from typing import List

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.application.schemas import (
    ProductCreate,
    ProductCsvImportResult,
    ProductRead,
    ProductUpdate,
    ProductXmlImportResult,
)
from app.application.services import (
    create_product,
    delete_product,
    import_products_from_csv,
    import_products_from_invoice_xml,
    list_products,
    update_product,
)
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get(
    "",
    response_model=List[ProductRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_products(db: Session = Depends(get_db)) -> List[ProductRead]:
    return list_products(db)


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def post_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    return create_product(db, payload)


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def put_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> ProductRead:
    return update_product(db, product_id, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def remove_product(product_id: int, db: Session = Depends(get_db)) -> Response:
    delete_product(db, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/importar-xml",
    response_model=ProductXmlImportResult,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
async def import_product_xml(
    xml_file: UploadFile = File(...),
    registrar_financeiro: bool = True,
    db: Session = Depends(get_db),
) -> ProductXmlImportResult:
    return import_products_from_invoice_xml(
        db,
        await xml_file.read(),
        create_finance_entry=registrar_financeiro,
    )


@router.post(
    "/importar-csv",
    response_model=ProductCsvImportResult,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
async def import_product_csv(
    csv_file: UploadFile = File(...),
    registrar_financeiro: bool = True,
    db: Session = Depends(get_db),
) -> ProductCsvImportResult:
    return import_products_from_csv(
        db,
        await csv_file.read(),
        create_finance_entry=registrar_financeiro,
    )
