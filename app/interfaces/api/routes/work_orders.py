from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.application.schemas import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate
from app.application.services import (
    create_work_order,
    delete_work_order,
    generate_framed_sanitary_certificate_pdf,
    generate_work_order_pdf,
    generate_sanitary_certificate_pdf,
    generate_technical_report_pdf,
    list_work_orders,
    mark_work_order_as_completed,
    settle_work_order,
    update_work_order,
)
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/os", tags=["ordens-de-servico"])


@router.get(
    "",
    response_model=List[WorkOrderRead],
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_work_orders(db: Session = Depends(get_db)) -> List[WorkOrderRead]:
    return list_work_orders(db)


@router.post(
    "",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def post_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)) -> WorkOrderRead:
    return create_work_order(db, payload)


@router.put(
    "/{work_order_id}",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def put_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    db: Session = Depends(get_db),
) -> WorkOrderRead:
    return update_work_order(db, work_order_id, payload)


@router.post(
    "/{work_order_id}/efetuar",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def complete_work_order(work_order_id: int, db: Session = Depends(get_db)) -> WorkOrderRead:
    return mark_work_order_as_completed(db, work_order_id)


@router.post(
    "/{work_order_id}/baixar",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_roles(["master", "admin"]))],
)
def settle_work_order_route(work_order_id: int, db: Session = Depends(get_db)) -> WorkOrderRead:
    return settle_work_order(db, work_order_id)


@router.delete(
    "/{work_order_id}",
    status_code=204,
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def remove_work_order(work_order_id: int, db: Session = Depends(get_db)) -> Response:
    delete_work_order(db, work_order_id)
    return Response(status_code=204)


@router.get(
    "/{work_order_id}/pdf",
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_work_order_pdf(work_order_id: int, db: Session = Depends(get_db)) -> Response:
    pdf_bytes = generate_work_order_pdf(db, work_order_id)
    headers = {
        "Content-Disposition": f'inline; filename="os-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/relatorio-tecnico.pdf",
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_technical_report_pdf(work_order_id: int, db: Session = Depends(get_db)) -> Response:
    pdf_bytes = generate_technical_report_pdf(db, work_order_id)
    headers = {
        "Content-Disposition": f'inline; filename="relatorio-tecnico-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/certificado-sanitario.pdf",
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_sanitary_certificate_pdf(work_order_id: int, db: Session = Depends(get_db)) -> Response:
    pdf_bytes = generate_sanitary_certificate_pdf(db, work_order_id)
    headers = {
        "Content-Disposition": f'inline; filename="certificado-sanitario-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/certificado-moldura.pdf",
    dependencies=[Depends(require_roles(["master", "admin", "operador"]))],
)
def get_framed_sanitary_certificate_pdf(work_order_id: int, db: Session = Depends(get_db)) -> Response:
    pdf_bytes = generate_framed_sanitary_certificate_pdf(db, work_order_id)
    headers = {
        "Content-Disposition": f'inline; filename="certificado-moldura-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
