import json

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.application.google_calendar_service import (
    build_google_oauth_authorization_url,
    get_google_connection_status,
    handle_google_oauth_callback,
    logout_google_calendar,
    sync_appointment_with_google_or_request_oauth,
)
from app.application.schemas import (
    GoogleCalendarAppointmentSyncRead,
    GoogleCalendarConnectionStatusRead,
    GoogleCalendarOAuthStartRead,
)
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.interfaces.api.deps import require_roles

router = APIRouter(prefix="/google-calendar", tags=["google-calendar"])


@router.post(
    "/oauth/start",
    response_model=GoogleCalendarOAuthStartRead,
)
def post_google_oauth_start(
    appointment_id: Optional[int] = None,
    provider_company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> GoogleCalendarOAuthStartRead:
    return GoogleCalendarOAuthStartRead(
        authorization_url=build_google_oauth_authorization_url(
            db,
            current_user.id,
            appointment_id=appointment_id,
            provider_company_id=provider_company_id,
        ),
        message="Abra a autenticacao Google para conectar a conta e concluir a sincronizacao.",
    )


@router.post(
    "/login",
    response_model=GoogleCalendarOAuthStartRead,
)
def post_google_login(
    appointment_id: Optional[int] = None,
    provider_company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> GoogleCalendarOAuthStartRead:
    return post_google_oauth_start(
        appointment_id=appointment_id,
        provider_company_id=provider_company_id,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/status",
    response_model=GoogleCalendarConnectionStatusRead,
)
def get_google_status(
    provider_company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> GoogleCalendarConnectionStatusRead:
    return GoogleCalendarConnectionStatusRead(
        **get_google_connection_status(
            db,
            user_id=current_user.id,
            provider_company_id=provider_company_id,
        )
    )


@router.post(
    "/logout",
    response_model=GoogleCalendarConnectionStatusRead,
)
def post_google_logout(
    provider_company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> GoogleCalendarConnectionStatusRead:
    return GoogleCalendarConnectionStatusRead(
        **logout_google_calendar(
            db,
            user_id=current_user.id,
            provider_company_id=provider_company_id,
        )
    )


@router.post(
    "/appointments/{appointment_id}/sync",
    response_model=GoogleCalendarAppointmentSyncRead,
)
def post_google_sync_or_connect(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["master", "admin", "operador"])),
) -> GoogleCalendarAppointmentSyncRead:
    return GoogleCalendarAppointmentSyncRead(
        **sync_appointment_with_google_or_request_oauth(db, appointment_id, current_user.id)
    )


@router.get(
    "/oauth/callback",
    response_class=HTMLResponse,
)
def get_google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    status = "success"
    try:
        result = handle_google_oauth_callback(db, code, state)
        title = "Google conectado"
        message = result["message"]
    except BusinessRuleViolation as exc:
        status = "error"
        title = "Falha na conexao Google"
        message = exc.message

    payload = {
        "type": "syspragas-google-calendar-oauth",
        "status": status,
        "message": message,
    }
    if status == "success":
        payload["appointmentId"] = result.get("appointment_id")

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f3f5ef;
                color: #1e2a22;
                margin: 0;
                min-height: 100vh;
                display: grid;
                place-items: center;
                padding: 24px;
            }}
            .card {{
                width: min(460px, 100%);
                background: #ffffff;
                border: 1px solid rgba(30, 42, 34, 0.08);
                border-radius: 18px;
                padding: 28px;
                box-shadow: 0 18px 50px rgba(30, 42, 34, 0.12);
            }}
            h1 {{
                margin: 0 0 12px;
                font-size: 1.35rem;
            }}
            p {{
                margin: 0;
                line-height: 1.5;
                color: #51605a;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>{title}</h1>
            <p>{message}</p>
        </div>
        <script>
            const payload = {json.dumps(payload)};
            if (window.opener && window.opener !== window) {{
                window.opener.postMessage(payload, window.location.origin);
            }}
            window.setTimeout(() => window.close(), 1200);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
