from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["web"])

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

NAV_ITEMS = [
    {"view": "dashboard", "label": "Dashboard", "icon": "fas fa-chart-line", "classes": ""},
    {"view": "clientes", "label": "Clientes", "icon": "fas fa-building", "classes": ""},
    {"view": "produtos", "label": "Produtos", "icon": "fas fa-flask", "classes": ""},
    {"view": "pragas", "label": "Pragas", "icon": "fas fa-spider", "classes": ""},
    {"view": "tecnicos", "label": "Tecnicos", "icon": "fas fa-user-cog", "classes": ""},
    {"view": "ordens", "label": "Ordens de servico", "icon": "fas fa-file-signature", "classes": ""},
    {"view": "financeiro", "label": "Financeiro", "icon": "fas fa-wallet", "classes": "finance-only"},
    {"view": "usuarios", "label": "Usuarios", "icon": "fas fa-users-cog", "classes": "master-only hidden"},
    {"view": "licencas", "label": "Licencas", "icon": "fas fa-id-card-alt", "classes": "master-only hidden"},
]


@router.get("/app", response_class=HTMLResponse)
def web_app(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/app.html",
        context={"nav_items": NAV_ITEMS},
    )
