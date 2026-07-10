from pathlib import Path
import sys

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

router = APIRouter(tags=["web"])

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _BASE_DIR = Path(sys._MEIPASS) / "app" / "interfaces" / "web"
else:
    _BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = _BASE_DIR / "static"
TEMPLATES_DIR = _BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#0f766e"/>
<path d="M18 34c0-9 6-16 14-16s14 7 14 16-6 16-14 16-14-7-14-16Z" fill="#ecfeff"/>
<path d="M24 34h16M32 20v28M22 26l20 16M42 26 22 42" stroke="#0f766e" stroke-width="4" stroke-linecap="round"/>
</svg>"""

NAV_ITEMS = [
    {"kind": "header", "label": "Painel", "classes": ""},
    {"view": "dashboard", "label": "Dashboard", "icon": "fas fa-tachometer-alt", "classes": ""},
    {"kind": "header", "label": "Cadastros", "classes": ""},
    {"view": "clientes", "label": "Clientes", "icon": "fas fa-address-book", "classes": ""},
    {"view": "produtos", "label": "Produtos", "icon": "fas fa-box-open", "classes": "stock-only"},
    {"view": "estoque", "label": "Estoque", "icon": "fas fa-warehouse", "classes": "stock-only"},
    {"view": "estoque-importacoes", "label": "Importacoes", "icon": "fas fa-file-import", "classes": "stock-only"},
    {"view": "estoque-estrutura", "label": "Armazens e locais", "icon": "fas fa-layer-group", "classes": "stock-only"},
    {"view": "estoque-balanco", "label": "Balanco", "icon": "fas fa-clipboard-check", "classes": "stock-only"},
    {"view": "estoque-inventario", "label": "Inventario", "icon": "fas fa-qrcode", "classes": "stock-only"},
    {"view": "estoque-etiquetas", "label": "Etiquetas", "icon": "fas fa-tags", "classes": "stock-only"},
    {"view": "estoque-transferencias", "label": "Transferencias", "icon": "fas fa-exchange-alt", "classes": "stock-only"},
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
    settings = get_settings()
    app_js_version = str(int((STATIC_DIR / "app.js").stat().st_mtime))
    return templates.TemplateResponse(
        request=request,
        name="pages/app.html",
        context={
            "nav_items": NAV_ITEMS,
            "app_js_version": app_js_version,
            "base_path": settings.normalized_base_path,
            "csp_nonce": getattr(request.state, "csp_nonce", ""),
        },
    )


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")
