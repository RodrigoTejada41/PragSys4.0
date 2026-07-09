from datetime import date
from typing import List, Optional

from xml.etree import ElementTree as ET

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application.fiscal_services import delete_nfe_invoice
from app.application.nfe_danfe_service import NfeDanfeUnavailableError, generate_invoice_nfe_danfe_pdf
from app.application.nfe_integration_service import (
    cancel_nfe,
    get_nfe_status,
    issue_nfe,
    list_nfe_with_integration,
    process_nfe_webhook,
    update_nfe_local,
)
from app.application.schemas import (
    NfeCancelRequest,
    NfeDanfePdfRead,
    NfeInvoiceCreate,
    NfeInvoiceRead,
    NfeInvoiceUpdate,
    NfeWebhookEvent,
)
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/nfe", tags=["nfe"])


@router.get(
    "",
    response_model=List[NfeInvoiceRead],
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.view"]))],
)
def get_nfe_invoices(
    cliente_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[NfeInvoiceRead]:
    return list_nfe_with_integration(
        db,
        customer_id=cliente_id,
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
        search=search,
    )


@router.post(
    "",
    response_model=NfeInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.manage"]))],
)
def post_nfe_invoice(payload: NfeInvoiceCreate, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return issue_nfe(db, payload)


@router.get(
    "/{nfe_id}",
    response_model=NfeInvoiceRead,
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.view"]))],
)
def get_nfe_invoice(nfe_id: int, sync: bool = True, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return get_nfe_status(db, nfe_id, sync_with_provider=sync)


@router.get(
    "/{nfe_id}/danfe/pdf",
    response_model=NfeDanfePdfRead,
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.view"]))],
)
def get_nfe_danfe_pdf(nfe_id: int, db: Session = Depends(get_db)) -> NfeDanfePdfRead:
    try:
        result = generate_invoice_nfe_danfe_pdf(db, nfe_id)
    except NfeDanfeUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ET.ParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="XML NF-e invalido.") from exc
    return NfeDanfePdfRead(
        id=nfe_id,
        access_key=result.access_key,
        filename=result.filename,
        pdf_base64=result.pdf_base64,
    )


@router.put(
    "/{nfe_id}",
    response_model=NfeInvoiceRead,
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.manage"]))],
)
def put_nfe_invoice(nfe_id: int, payload: NfeInvoiceUpdate, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return update_nfe_local(db, nfe_id, payload)


@router.delete(
    "/{nfe_id}",
    response_model=NfeInvoiceRead,
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.manage"]))],
)
def remove_nfe_invoice(
    nfe_id: int,
    payload: Optional[NfeCancelRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> NfeInvoiceRead:
    return cancel_nfe(db, nfe_id, payload)


@router.delete(
    "/{nfe_id}/hard-delete",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_access(["master", "admin"], ["fiscal.manage", "records.delete"]))],
)
def hard_remove_nfe_invoice(nfe_id: int, db: Session = Depends(get_db)) -> Response:
    delete_nfe_invoice(db, nfe_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/webhooks/focus",
    response_model=NfeInvoiceRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_focus_nfe_webhook(payload: NfeWebhookEvent, db: Session = Depends(get_db)) -> NfeInvoiceRead:
    return process_nfe_webhook(db, payload)
