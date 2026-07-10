from contextlib import asynccontextmanager
import secrets

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.application.services import ensure_license_allows_access
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.core.logging import configure_logging
from app.core.security import verify_password
from app.application.contract_scheduler import contract_scheduler
from app.infrastructure.db import get_db, init_db
from app.infrastructure.models import User
from app.interfaces.api.routes import (
    assistant,
    appointments,
    auth,
    contracts,
    customers,
    fiscal,
    finance,
    google_calendar,
    licenses,
    nfe,
    orchestrator,
    pests,
    products,
    provider_companies,
    receipts,
    settings as system_settings,
    technicians,
    users,
    whatsapp,
    work_orders,
)
from app.modules.sefaz_nfe import routes as sefaz_nfe_routes
from app.interfaces.web.routes import STATIC_DIR, router as web_router

settings = get_settings()
configure_logging()
docs_security = HTTPBasic(auto_error=False)


def _security_policy_for_path(path: str, nonce: str) -> str:
    script_src = f"'self' 'nonce-{nonce}'"
    if path.rstrip("/") == "/docs":
        script_src = "'self' 'unsafe-inline'"
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src {script_src}",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
        ]
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.contract_scheduler_enabled:
        contract_scheduler.start()
    yield
    if settings.contract_scheduler_enabled:
        contract_scheduler.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce
    response = await call_next(request)
    response.headers.setdefault("Content-Security-Policy", _security_policy_for_path(request.url.path, nonce))
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(_: Request, exc: BusinessRuleViolation) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url=f"{settings.normalized_base_path}/app")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _get_docs_master_user(
    credentials: HTTPBasicCredentials = Depends(docs_security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacao obrigatoria.",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = db.query(User).filter(User.username == credentials.username, User.is_active.is_(True)).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas.",
            headers={"WWW-Authenticate": "Basic"},
        )

    if user.role != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A documentacao da API esta disponivel apenas para usuarios MASTER.",
        )

    try:
        ensure_license_allows_access(db, user)
    except BusinessRuleViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        ) from exc

    return user


@app.get("/openapi.json", include_in_schema=False)
def openapi_schema(_: User = Depends(_get_docs_master_user)) -> dict:
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )


@app.get("/docs", include_in_schema=False)
def swagger_docs(_: User = Depends(_get_docs_master_user)):
    return get_swagger_ui_html(
        openapi_url=f"{settings.normalized_base_path}/openapi.json",
        title=f"{settings.app_name} - API Docs",
    )


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(assistant.router, prefix=settings.api_v1_prefix)
app.include_router(contracts.router, prefix=settings.api_v1_prefix)
app.include_router(customers.router, prefix=settings.api_v1_prefix)
app.include_router(products.router, prefix=settings.api_v1_prefix)
app.include_router(pests.router, prefix=settings.api_v1_prefix)
app.include_router(technicians.router, prefix=settings.api_v1_prefix)
app.include_router(receipts.router, prefix=settings.api_v1_prefix)
app.include_router(finance.router, prefix=settings.api_v1_prefix)
app.include_router(fiscal.router, prefix=settings.api_v1_prefix)
app.include_router(nfe.router, prefix=settings.api_v1_prefix)
app.include_router(orchestrator.router, prefix=settings.api_v1_prefix)
app.include_router(sefaz_nfe_routes.router, prefix=settings.api_v1_prefix)
app.include_router(work_orders.router, prefix=settings.api_v1_prefix)
app.include_router(appointments.router, prefix=settings.api_v1_prefix)
app.include_router(google_calendar.router, prefix=settings.api_v1_prefix)
app.include_router(whatsapp.router, prefix=settings.api_v1_prefix)
app.include_router(system_settings.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(licenses.router, prefix=settings.api_v1_prefix)
app.include_router(provider_companies.router, prefix=settings.api_v1_prefix)
app.include_router(web_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
