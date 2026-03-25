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
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get(
    "",
    response_model=List[ProductRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
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
    current_user: User = Depends(require_roles(["master", "admin"])),
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
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> ProductRead:
    return update_product(db, product_id, payload, current_user=current_user)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
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
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> ProductXmlImportResult:
    return import_products_from_invoice_xml(
        db,
        await xml_file.read(),
        create_finance_entry=registrar_financeiro,
        current_user=current_user,
    )


@router.post(
    "/importar-csv",
    response_model=ProductCsvImportResult,
)
async def import_product_csv(
    csv_file: UploadFile = File(...),
    registrar_financeiro: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> ProductCsvImportResult:
    return import_products_from_csv(
        db,
        await csv_file.read(),
        create_finance_entry=registrar_financeiro,
        current_user=current_user,
    )
