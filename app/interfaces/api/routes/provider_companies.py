from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import CustomerCnpjLookupRead, ProviderCompanyCreate, ProviderCompanyRead, ProviderCompanyUpdate
from app.application.services import (
    create_provider_company,
    delete_provider_company,
    get_provider_company,
    list_provider_companies,
    lookup_company_by_cnpj,
    update_provider_company,
)
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/empresas-prestadoras", tags=["empresas-prestadoras"])


@router.get(
    "",
    response_model=List[ProviderCompanyRead],
    dependencies=[Depends(require_roles(["master"]))],
)
def get_provider_companies(db: Session = Depends(get_db)) -> List[ProviderCompanyRead]:
    return list_provider_companies(db)


@router.get(
    "/consultar-cnpj/{cnpj}",
    response_model=CustomerCnpjLookupRead,
    dependencies=[Depends(require_roles(["master"]))],
)
def get_provider_company_by_cnpj(cnpj: str) -> CustomerCnpjLookupRead:
    return lookup_company_by_cnpj(cnpj)


@router.post(
    "",
    response_model=ProviderCompanyRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master"]))],
)
def post_provider_company(payload: ProviderCompanyCreate, db: Session = Depends(get_db)) -> ProviderCompanyRead:
    company = create_provider_company(db, payload)
    db.commit()
    return get_provider_company(db, company.id)


@router.put(
    "/{provider_company_id}",
    response_model=ProviderCompanyRead,
    dependencies=[Depends(require_roles(["master"]))],
)
def put_provider_company(
    provider_company_id: int,
    payload: ProviderCompanyUpdate,
    db: Session = Depends(get_db),
) -> ProviderCompanyRead:
    return update_provider_company(db, provider_company_id, payload)


@router.delete(
    "/{provider_company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["master"]))],
)
def remove_provider_company(provider_company_id: int, db: Session = Depends(get_db)) -> Response:
    delete_provider_company(db, provider_company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
