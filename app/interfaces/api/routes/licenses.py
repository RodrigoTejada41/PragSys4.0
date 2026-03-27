from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.schemas import LicenseCreate, LicenseRead, LicenseUpdate
from app.application.services import create_license, delete_license, list_licenses, update_license
from app.infrastructure.db import get_db
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/licencas", tags=["licencas"])


@router.get(
    "",
    response_model=List[LicenseRead],
    dependencies=[Depends(require_access(["master"], ["licenses.manage"]))],
)
def get_licenses(db: Session = Depends(get_db)) -> List[LicenseRead]:
    return list_licenses(db)


@router.post(
    "",
    response_model=LicenseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_access(["master"], ["licenses.manage"]))],
)
def post_license(payload: LicenseCreate, db: Session = Depends(get_db)) -> LicenseRead:
    return create_license(db, payload)


@router.put(
    "/{license_id}",
    response_model=LicenseRead,
    dependencies=[Depends(require_access(["master"], ["licenses.manage"]))],
)
def put_license(license_id: int, payload: LicenseUpdate, db: Session = Depends(get_db)) -> LicenseRead:
    return update_license(db, license_id, payload)


@router.delete(
    "/{license_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_access(["master"], ["licenses.manage"]))],
)
def remove_license(license_id: int, db: Session = Depends(get_db)) -> Response:
    delete_license(db, license_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
