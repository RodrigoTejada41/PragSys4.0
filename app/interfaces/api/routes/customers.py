from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import AddressLookupRead, CustomerCnpjLookupRead, CustomerCreate, CustomerRead, CustomerUpdate
from app.application.services import (
    create_customer,
    delete_customer,
    list_customers,
    lookup_address_by_cep,
    lookup_company_by_cnpj,
    update_customer,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get(
    "",
    response_model=List[CustomerRead],
    dependencies=[Depends(require_access(["master", "admin", "operador"], ["customers.view"]))],
)
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["customers.view"])),
) -> List[CustomerRead]:
    return list_customers(db, current_user=current_user)


@router.get(
    "/consultar-cnpj/{cnpj}",
    response_model=CustomerCnpjLookupRead,
    dependencies=[Depends(require_access(["master", "admin", "operador"], ["customers.view"]))],
)
def get_customer_data_by_cnpj(cnpj: str) -> CustomerCnpjLookupRead:
    return lookup_company_by_cnpj(cnpj)


@router.get(
    "/consultar-cep/{cep}",
    response_model=AddressLookupRead,
    dependencies=[Depends(require_access(["master", "admin", "operador"], ["customers.view"]))],
)
def get_customer_address_by_cep(cep: str) -> AddressLookupRead:
    return lookup_address_by_cep(cep)


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def post_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["customers.edit"])),
) -> CustomerRead:
    return create_customer(db, payload, current_user=current_user)


@router.put(
    "/{customer_id}",
    response_model=CustomerRead,
)
def put_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["customers.edit"])),
) -> CustomerRead:
    return update_customer(db, customer_id, payload, current_user=current_user)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin", "operador"], ["customers.edit", "records.delete"])),
) -> Response:
    delete_customer(db, customer_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
