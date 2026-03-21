from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import CustomerCreate, CustomerRead, CustomerUpdate
from app.application.services import (
    create_customer,
    delete_customer,
    list_customers,
    update_customer,
)
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get(
    "",
    response_model=List[CustomerRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_customers(db: Session = Depends(get_db)) -> List[CustomerRead]:
    return list_customers(db)


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def post_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> CustomerRead:
    return create_customer(db, payload)


@router.put(
    "/{customer_id}",
    response_model=CustomerRead,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def put_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)) -> CustomerRead:
    return update_customer(db, customer_id, payload)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def remove_customer(customer_id: int, db: Session = Depends(get_db)) -> Response:
    delete_customer(db, customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
