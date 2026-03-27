from pathlib import Path
import sys

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["web"])

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _BASE_DIR = Path(sys._MEIPASS) / "app" / "interfaces" / "web"
else:
    _BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = _BASE_DIR / "static"
TEMPLATES_DIR = _BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

NAV_ITEMS = [
    {"kind": "header", "label": "Painel", "classes": ""},
    {"view": "dashboard", "label": "Dashboard", "icon": "fas fa-tachometer-alt", "classes": ""},
    {"kind": "header", "label": "Cadastros", "classes": ""},
    {"view": "clientes", "label": "Clientes", "icon": "fas fa-address-book", "classes": ""},
    {"view": "produtos", "label": "Produtos", "icon": "fas fa-box-open", "classes": ""},
    {"view": "pragas", "label": "Pragas", "icon": "fas fa-bug", "classes": ""},
    {"view": "tecnicos", "label": "Tecnicos", "icon": "fas fa-user-cog", "classes": ""},
    {"kind": "header", "label": "Operacao", "classes": ""},
    {"view": "ordens-nova", "label": "Nova OS", "icon": "fas fa-plus-square", "classes": ""},
    {"view": "ordens-cadastradas", "label": "Ordens", "icon": "fas fa-clipboard-list", "classes": ""},
    {"view": "agenda-novo", "label": "Novo agendamento", "icon": "fas fa-calendar-plus", "classes": ""},
    {"view": "agenda-operacional", "label": "Agenda", "icon": "fas fa-calendar-check", "classes": ""},
    {"kind": "header", "label": "Financeiro", "classes": "finance-only"},
    {"view": "financeiro-lancamentos", "label": "Contas", "icon": "fas fa-wallet", "classes": "finance-only"},
    {"view": "financeiro-recibos", "label": "Recibos", "icon": "fas fa-receipt", "classes": "finance-only"},
    {"view": "financeiro-nfe", "label": "NF-e", "icon": "fas fa-file-invoice-dollar", "classes": "finance-only"},
    {"view": "financeiro-caixa", "label": "Fluxo de caixa", "icon": "fas fa-cash-register", "classes": "finance-only"},
    {"view": "financeiro-relatorios", "label": "Relatorios", "icon": "fas fa-chart-bar", "classes": "finance-only"},
    {"kind": "header", "label": "Configuracoes", "classes": "admin-only hidden"},
    {"view": "configuracoes", "label": "Config. do sistema", "icon": "fas fa-sliders-h", "classes": "admin-only hidden"},
    {"kind": "header", "label": "Administracao", "classes": "admin-only hidden"},
    {"view": "empresas", "label": "Empresas", "icon": "fas fa-building", "classes": "master-only hidden"},
    {"view": "usuarios", "label": "Usuarios", "icon": "fas fa-users", "classes": "admin-only hidden"},
    {"view": "licencas", "label": "Licencas", "icon": "fas fa-id-card-alt", "classes": "master-only hidden"},
]


@router.get("/app", response_class=HTMLResponse)
def web_app(request: Request) -> HTMLResponse:
    app_js_version = str(int((STATIC_DIR / "app.js").stat().st_mtime))
    return templates.TemplateResponse(
        request=request,
        name="pages/app.html",
        context={
            "nav_items": NAV_ITEMS,
            "app_js_version": app_js_version,
        },
    )
