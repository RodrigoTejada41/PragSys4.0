from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.application.schemas import NfeCancelRequest, NfeInvoiceCreate, NfeInvoiceRead, NfeInvoiceUpdate, SefazDirectReadinessRead
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles
from app.modules.sefaz_nfe.services import (
    cancel_direct_nfe,
    get_direct_nfe_status,
    get_direct_sefaz_readiness,
    issue_direct_nfe,
    update_direct_nfe_local,
)

router = APIRouter(prefix="/nfe/sefaz", tags=["nfe-sefaz"])


@router.get(
    "/readiness",
    response_model=SefazDirectReadinessRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def get_sefaz_readiness() -> SefazDirectReadinessRead:
    return get_direct_sefaz_readiness()


@router.post(
    "",
    response_model=NfeInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def post_direct_nfe(payload: NfeInvoiceCreate, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return issue_direct_nfe(db, payload)


@router.get(
    "/{nfe_id}",
    response_model=NfeInvoiceRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def get_direct_nfe(nfe_id: int, sync: bool = True, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return get_direct_nfe_status(db, nfe_id, sync_with_sefaz=sync)


@router.put(
    "/{nfe_id}",
    response_model=NfeInvoiceRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def put_direct_nfe(nfe_id: int, payload: NfeInvoiceUpdate, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return update_direct_nfe_local(db, nfe_id, payload)


@router.delete(
    "/{nfe_id}",
    response_model=NfeInvoiceRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def delete_direct_nfe(
    nfe_id: int,
    payload: Optional[NfeCancelRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> NfeInvoiceRead:
    return cancel_direct_nfe(db, nfe_id, payload)
