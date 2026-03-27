from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.application.schemas import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate
from app.application.services import (
    add_work_order_photos,
    create_work_order,
    delete_work_order_photo,
    delete_work_order,
    generate_framed_sanitary_certificate_pdf,
    generate_guarantee_certificate_pdf_bundle,
    generate_work_order_pdf,
    generate_sanitary_certificate_pdf,
    generate_technical_report_pdf,
    get_work_order_photo_content,
    list_work_orders,
    mark_work_order_as_completed,
    reopen_work_order,
    settle_work_order,
    update_work_order,
)
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/os", tags=["ordens-de-servico"])


@router.get(
    "",
    response_model=List[WorkOrderRead],
)
def get_work_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> List[WorkOrderRead]:
    return list_work_orders(db, current_user=current_user)


@router.post(
    "",
    response_model=WorkOrderRead,
)
def post_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WorkOrderRead:
    return create_work_order(db, payload, current_user_id=current_user.id)


@router.put(
    "/{work_order_id}",
    response_model=WorkOrderRead,
)
def put_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WorkOrderRead:
    return update_work_order(db, work_order_id, payload, current_user_id=current_user.id)


@router.post(
    "/{work_order_id}/efetuar",
    response_model=WorkOrderRead,
)
def complete_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WorkOrderRead:
    return mark_work_order_as_completed(db, work_order_id, current_user_id=current_user.id)


@router.post(
    "/{work_order_id}/baixar",
    response_model=WorkOrderRead,
)
def settle_work_order_route(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin"])),
) -> WorkOrderRead:
    return settle_work_order(db, work_order_id, current_user_id=current_user.id)


@router.post(
    "/{work_order_id}/reabrir",
    response_model=WorkOrderRead,
)
def reopen_work_order_route(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WorkOrderRead:
    return reopen_work_order(db, work_order_id, current_user_id=current_user.id)


@router.post(
    "/{work_order_id}/fotos",
    response_model=WorkOrderRead,
)
def upload_work_order_photos(
    work_order_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WorkOrderRead:
    payload = [(file.filename, file.content_type or "", file.file.read()) for file in files]
    return add_work_order_photos(db, work_order_id, payload, current_user=current_user)


@router.delete(
    "/{work_order_id}/fotos/{photo_id}",
    response_model=WorkOrderRead,
)
def remove_work_order_photo(
    work_order_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> WorkOrderRead:
    return delete_work_order_photo(db, work_order_id, photo_id, current_user=current_user)


@router.get(
    "/fotos/{photo_id}",
)
def get_work_order_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    filename, content_type, image_data = get_work_order_photo_content(db, photo_id, current_user=current_user)
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
    }
    return Response(content=image_data, media_type=content_type, headers=headers)


@router.delete(
    "/{work_order_id}",
    status_code=204,
)
def remove_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    delete_work_order(db, work_order_id, current_user=current_user)
    return Response(status_code=204)


@router.get(
    "/{work_order_id}/pdf",
)
def get_work_order_pdf(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    pdf_bytes = generate_work_order_pdf(db, work_order_id, current_user=current_user)
    headers = {
        "Content-Disposition": f'inline; filename="os-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/relatorio-tecnico.pdf",
)
def get_technical_report_pdf(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    pdf_bytes = generate_technical_report_pdf(db, work_order_id, current_user=current_user)
    headers = {
        "Content-Disposition": f'inline; filename="relatorio-tecnico-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/certificado-sanitario.pdf",
)
def get_sanitary_certificate_pdf(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    pdf_bytes = generate_sanitary_certificate_pdf(db, work_order_id, current_user=current_user)
    headers = {
        "Content-Disposition": f'inline; filename="certificado-sanitario-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/certificado-garantia.pdf",
)
def get_guarantee_certificate_pdf(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    pdf_bytes, filename = generate_guarantee_certificate_pdf_bundle(db, work_order_id, current_user=current_user)
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get(
    "/{work_order_id}/certificado-moldura.pdf",
)
def get_framed_sanitary_certificate_pdf(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> Response:
    pdf_bytes = generate_framed_sanitary_certificate_pdf(db, work_order_id, current_user=current_user)
    headers = {
        "Content-Disposition": f'inline; filename="certificado-moldura-{work_order_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
