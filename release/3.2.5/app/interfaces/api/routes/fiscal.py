from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.fiscal_services import (
    create_simples_config,
    get_cash_flow_summary,
    get_or_refresh_ncm_profile,
    get_simples_nacional_monthly_summary,
    list_simples_configs,
    search_ncm_profiles,
    update_simples_config,
)
from app.application.schemas import (
    FinanceCashFlowSummaryRead,
    NcmTaxProfileRead,
    SimplesNationalConfigCreate,
    SimplesNationalConfigRead,
    SimplesNationalConfigUpdate,
    SimplesNationalMonthlySummaryRead,
)
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/fiscal", tags=["fiscal"])


@router.get(
    "/ncm",
    response_model=List[NcmTaxProfileRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_ncm_profiles(
    query: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> List[NcmTaxProfileRead]:
    return search_ncm_profiles(db, query=query, limit=limit)


@router.get(
    "/ncm/{codigo}",
    response_model=NcmTaxProfileRead,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_ncm_profile(codigo: str, db: Session = Depends(get_db)) -> NcmTaxProfileRead:
    profile = get_or_refresh_ncm_profile(db, codigo)
    if not profile:
        raise BusinessRuleViolation("NCM nao encontrado.")
    return profile


@router.get(
    "/simples",
    response_model=List[SimplesNationalConfigRead],
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def get_simples_configs(db: Session = Depends(get_db)) -> List[SimplesNationalConfigRead]:
    return list_simples_configs(db)


@router.post(
    "/simples",
    response_model=SimplesNationalConfigRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def post_simples_config(payload: SimplesNationalConfigCreate, db: Session = Depends(get_db)) -> SimplesNationalConfigRead:
    return create_simples_config(db, payload)


@router.put(
    "/simples/{config_id}",
    response_model=SimplesNationalConfigRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def put_simples_config(
    config_id: int,
    payload: SimplesNationalConfigUpdate,
    db: Session = Depends(get_db),
) -> SimplesNationalConfigRead:
    return update_simples_config(db, config_id, payload)


@router.get(
    "/simples/resumo/{year}/{month}",
    response_model=SimplesNationalMonthlySummaryRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def get_simples_summary(year: int, month: int, db: Session = Depends(get_db)) -> SimplesNationalMonthlySummaryRead:
    return get_simples_nacional_monthly_summary(db, year, month)


@router.get(
    "/fluxo-caixa/resumo",
    response_model=FinanceCashFlowSummaryRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def get_cash_flow_summary_view(period: str = "monthly", db: Session = Depends(get_db)) -> FinanceCashFlowSummaryRead:
    return get_cash_flow_summary(db, period=period)
