from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.application.contracts_service import (
    create_contract,
    delete_contract,
    get_contract,
    get_contract_dashboard,
    get_contract_file_content,
    list_contracts,
    list_customer_contracts,
    run_contract_maintenance,
    update_contract,
)
from app.application.schemas import ContractCreate, ContractDashboardRead, ContractMaintenanceRead, ContractRead, ContractUpdate
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(tags=["contratos"])


def _contract_create_from_form(
    nome: str = Form(...),
    data_inicio: str = Form(...),
    data_vencimento: str = Form(...),
    observacoes: Optional[str] = Form(default=None),
) -> ContractCreate:
    return ContractCreate(
        nome=nome,
        data_inicio=data_inicio,
        data_vencimento=data_vencimento,
        observacoes=observacoes,
    )


def _contract_update_from_form(
    nome: str = Form(...),
    data_inicio: str = Form(...),
    data_vencimento: str = Form(...),
    observacoes: Optional[str] = Form(default=None),
) -> ContractUpdate:
    return ContractUpdate(
        nome=nome,
        data_inicio=data_inicio,
        data_vencimento=data_vencimento,
        observacoes=observacoes,
    )


@router.get(
    "/clientes/{customer_id}/contratos",
    response_model=List[ContractRead],
)
def get_customer_contracts(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> List[ContractRead]:
    return list_customer_contracts(db, customer_id, current_user=current_user)


@router.post(
    "/clientes/{customer_id}/contratos",
    response_model=ContractRead,
)
def post_customer_contract(
    customer_id: int,
    payload: ContractCreate = Depends(_contract_create_from_form),
    arquivo: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> ContractRead:
    file_payload = None
    if arquivo is not None:
        file_payload = (arquivo.filename or "contrato", arquivo.content_type or "", arquivo.file.read())
    return create_contract(db, customer_id, payload, file_payload=file_payload, current_user=current_user)


@router.get(
    "/contratos",
    response_model=List[ContractRead],
)
def get_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> List[ContractRead]:
    return list_contracts(db, current_user=current_user)


@router.get(
    "/contratos/dashboard",
    response_model=ContractDashboardRead,
)
def get_contracts_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> ContractDashboardRead:
    return get_contract_dashboard(db, current_user=current_user)


@router.get(
    "/contratos/{contract_id}",
    response_model=ContractRead,
)
def get_contract_by_id(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> ContractRead:
    return get_contract(db, contract_id, current_user=current_user)


@router.put(
    "/contratos/{contract_id}",
    response_model=ContractRead,
)
def put_contract(
    contract_id: int,
    payload: ContractUpdate = Depends(_contract_update_from_form),
    arquivo: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> ContractRead:
    file_payload = None
    if arquivo is not None and arquivo.filename:
        file_payload = (arquivo.filename, arquivo.content_type or "", arquivo.file.read())
    return update_contract(db, contract_id, payload, file_payload=file_payload, current_user=current_user)


@router.delete(
    "/contratos/{contract_id}",
    status_code=204,
)
def remove_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    delete_contract(db, contract_id, current_user=current_user)
    return Response(status_code=204)


@router.get("/contratos/{contract_id}/arquivo")
def get_contract_file(
    contract_id: int,
    download: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    filename, content_type, content = get_contract_file_content(db, contract_id, current_user=current_user)
    disposition = "attachment" if download else "inline"
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@router.post(
    "/contratos/rotina/sincronizar",
    response_model=ContractMaintenanceRead,
)
def post_contract_maintenance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> ContractMaintenanceRead:
    return run_contract_maintenance(db, current_user=current_user)
