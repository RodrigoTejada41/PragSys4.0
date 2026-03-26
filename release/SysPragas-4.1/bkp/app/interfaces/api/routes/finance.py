from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import (
    CashLedgerEntryRead,
    FinanceDashboardRead,
    FinanceEntryCreate,
    FinanceEntryRead,
    FinanceEntryUpdate,
    FinancePaymentRequest,
)
from app.application.services import (
    create_finance_entry,
    delete_finance_entry,
    get_finance_dashboard,
    list_cash_ledger_entries,
    list_finance_entries,
    mark_finance_entry_as_paid,
    update_finance_entry,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/financeiro", tags=["financeiro"])


@router.get(
    "",
    response_model=List[FinanceEntryRead],
)
def get_finance_entries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    cliente_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    tipo: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> List[FinanceEntryRead]:
    return list_finance_entries(
        db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        cliente_id=cliente_id,
        status_filter=status_filter,
        tipo=tipo,
        search=search,
    )


@router.get(
    "/dashboard",
    response_model=FinanceDashboardRead,
)
def get_finance_dashboard_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> FinanceDashboardRead:
    return get_finance_dashboard(db, current_user=current_user)


@router.get(
    "/caixa",
    response_model=List[CashLedgerEntryRead],
)
def get_cash_ledger_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> List[CashLedgerEntryRead]:
    return list_cash_ledger_entries(db, current_user=current_user)


@router.post(
    "",
    response_model=FinanceEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def post_finance_entry(
    payload: FinanceEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> FinanceEntryRead:
    return create_finance_entry(db, payload, current_user=current_user)


@router.put(
    "/{finance_entry_id}",
    response_model=FinanceEntryRead,
)
def put_finance_entry(
    finance_entry_id: int,
    payload: FinanceEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> FinanceEntryRead:
    return update_finance_entry(db, finance_entry_id, payload, current_user=current_user)


@router.post(
    "/{finance_entry_id}/pagar",
    response_model=FinanceEntryRead,
)
def pay_finance_entry(
    finance_entry_id: int,
    payload: Optional[FinancePaymentRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> FinanceEntryRead:
    return mark_finance_entry_as_paid(db, finance_entry_id, payload, current_user=current_user)


@router.delete(
    "/{finance_entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_finance_entry(
    finance_entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> Response:
    delete_finance_entry(db, finance_entry_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
