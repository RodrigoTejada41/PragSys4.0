from typing import List

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.application.receipt_services import (
    create_receipt,
    delete_receipt,
    generate_receipt_pdf,
    get_receipt,
    list_receipts,
    preview_receipt,
    update_receipt,
)
from app.application.schemas import ReceiptCreate, ReceiptPreviewRead, ReceiptRead, ReceiptUpdate
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/recibos", tags=["recibos"])


@router.get(
    "",
    response_model=List[ReceiptRead],
)
def get_receipts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.view"])),
) -> List[ReceiptRead]:
    return list_receipts(db)


@router.get(
    "/{receipt_id}",
    response_model=ReceiptRead,
)
def get_receipt_by_id(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.view"])),
) -> ReceiptRead:
    return get_receipt(db, receipt_id)


@router.post(
    "/preview",
    response_model=ReceiptPreviewRead,
)
def post_receipt_preview(
    payload: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.manage"])),
) -> ReceiptPreviewRead:
    return preview_receipt(db, payload)


@router.post(
    "",
    response_model=ReceiptRead,
    status_code=status.HTTP_201_CREATED,
)
def post_receipt(
    payload: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.manage"])),
) -> ReceiptRead:
    return create_receipt(db, payload, current_user_id=current_user.id)


@router.put(
    "/{receipt_id}",
    response_model=ReceiptRead,
)
def put_receipt(
    receipt_id: int,
    payload: ReceiptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.manage"])),
) -> ReceiptRead:
    return update_receipt(db, receipt_id, payload, current_user_id=current_user.id)


@router.delete(
    "/{receipt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.manage", "records.delete"])),
) -> Response:
    delete_receipt(db, receipt_id, current_user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{receipt_id}/pdf",
)
def get_receipt_pdf(
    receipt_id: int,
    download: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_access(["master", "admin"], ["finance.view"])),
) -> Response:
    pdf_bytes = generate_receipt_pdf(db, receipt_id, current_user_id=current_user.id)
    disposition = "attachment" if download else "inline"
    headers = {
        "Content-Disposition": f'{disposition}; filename="recibo-{receipt_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
