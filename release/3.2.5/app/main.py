from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.db import init_db
from app.interfaces.api.routes import (
    appointments,
    auth,
    customers,
    fiscal,
    finance,
    google_calendar,
    licenses,
    nfe,
    pests,
    products,
    provider_companies,
    technicians,
    users,
    work_orders,
)
from app.modules.sefaz_nfe import routes as sefaz_nfe_routes
from app.interfaces.web.routes import STATIC_DIR, router as web_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="3.2.5", lifespan=lifespan)
init_db()


@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(_: Request, exc: BusinessRuleViolation) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(customers.router, prefix=settings.api_v1_prefix)
app.include_router(products.router, prefix=settings.api_v1_prefix)
app.include_router(pests.router, prefix=settings.api_v1_prefix)
app.include_router(technicians.router, prefix=settings.api_v1_prefix)
app.include_router(finance.router, prefix=settings.api_v1_prefix)
app.include_router(fiscal.router, prefix=settings.api_v1_prefix)
app.include_router(nfe.router, prefix=settings.api_v1_prefix)
app.include_router(sefaz_nfe_routes.router, prefix=settings.api_v1_prefix)
app.include_router(work_orders.router, prefix=settings.api_v1_prefix)
app.include_router(appointments.router, prefix=settings.api_v1_prefix)
app.include_router(google_calendar.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(licenses.router, prefix=settings.api_v1_prefix)
app.include_router(provider_companies.router, prefix=settings.api_v1_prefix)
app.include_router(web_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
