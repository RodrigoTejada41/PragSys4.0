from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote, urlencode

import httpx
import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.models import ProviderCompany, User

GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _get_company_for_user(db: Session, user_id: Optional[int]) -> Optional[ProviderCompany]:
    if user_id is None:
        return db.query(ProviderCompany).order_by(ProviderCompany.id.asc()).first()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessRuleViolation("Usuario responsavel pela integracao Google nao encontrado.")

    if user.empresa_prestadora_id:
        company = db.query(ProviderCompany).filter(ProviderCompany.id == user.empresa_prestadora_id).first()
        if company:
            return company

    return db.query(ProviderCompany).order_by(ProviderCompany.id.asc()).first()


def _get_company_for_context(
    db: Session,
    user_id: Optional[int],
    provider_company_id: Optional[int] = None,
) -> Optional[ProviderCompany]:
    if provider_company_id is not None:
        return db.query(ProviderCompany).filter(ProviderCompany.id == provider_company_id).first()
    return _get_company_for_user(db, user_id)


def _get_company_or_fail(
    db: Session,
    user_id: Optional[int],
    provider_company_id: Optional[int] = None,
) -> ProviderCompany:
    company = _get_company_for_context(db, user_id, provider_company_id=provider_company_id)
    if not company:
        raise BusinessRuleViolation("Nao existe empresa prestadora disponivel para vincular a integracao Google.")
    return company


def _resolve_calendar_id(company: Optional[ProviderCompany]) -> str:
    settings = get_settings()
    return (
        (company.google_calendar_id if company else None)
        or settings.google_calendar_id
        or "primary"
    )


def _oauth_is_configured() -> bool:
    settings = get_settings()
    return bool(
        settings.google_oauth_client_id
        and settings.google_oauth_client_secret
        and settings.google_oauth_redirect_uri
    )


def _build_oauth_state(user_id: int, company_id: int, appointment_id: Optional[int] = None) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "company_id": company_id,
        "appointment_id": appointment_id,
        "purpose": "google_calendar_oauth",
        "nonce": secrets.token_urlsafe(18),
        "exp": _now_utc() + timedelta(minutes=15),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_oauth_state(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception as exc:  # pragma: no cover - jwt exceptions vary
        raise BusinessRuleViolation("O retorno da autenticacao Google expirou ou e invalido.") from exc
    if payload.get("purpose") != "google_calendar_oauth":
        raise BusinessRuleViolation("O retorno da autenticacao Google nao corresponde a uma solicitacao valida.")
    return payload


def build_google_oauth_authorization_url(
    db: Session,
    user_id: int,
    appointment_id: Optional[int] = None,
    provider_company_id: Optional[int] = None,
) -> str:
    if not _oauth_is_configured():
        raise BusinessRuleViolation(
            "OAuth do Google nao configurado. Defina GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET e GOOGLE_OAUTH_REDIRECT_URI."
        )

    settings = get_settings()
    company = _get_company_or_fail(db, user_id, provider_company_id=provider_company_id)
    state = _build_oauth_state(user_id, company.id, appointment_id)
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": settings.google_oauth_scopes,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


def _exchange_code_for_tokens(code: str) -> dict:
    settings = get_settings()
    if not _oauth_is_configured():
        raise BusinessRuleViolation(
            "OAuth do Google nao configurado. Defina GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET e GOOGLE_OAUTH_REDIRECT_URI."
        )

    payload = {
        "code": code,
        "client_id": settings.google_oauth_client_id,
        "client_secret": settings.google_oauth_client_secret,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        response = httpx.post(GOOGLE_OAUTH_TOKEN_URL, data=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
        raise BusinessRuleViolation(f"Falha ao trocar o codigo de autorizacao do Google: {detail}") from exc


def _fetch_google_account_email(access_token: str) -> Optional[str]:
    try:
        response = httpx.get(
            GOOGLE_OAUTH_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("email")
    except httpx.HTTPError:
        return None


def _apply_company_token_payload(company: ProviderCompany, payload: dict) -> None:
    access_token = payload.get("access_token")
    if not access_token:
        raise BusinessRuleViolation("O Google nao retornou um access token valido.")

    expires_in = int(payload.get("expires_in") or 3600)
    company.google_access_token = access_token
    if payload.get("refresh_token"):
        company.google_refresh_token = payload["refresh_token"]
    company.google_calendar_id = company.google_calendar_id or get_settings().google_calendar_id or "primary"
    company.google_token_expires_at = _now_utc() + timedelta(seconds=max(expires_in - 60, 60))
    company.google_connected_at = _now_utc()
    company.google_account_email = _fetch_google_account_email(access_token) or company.google_account_email


def _clear_company_google_session(company: ProviderCompany) -> None:
    company.google_access_token = None
    company.google_refresh_token = None
    company.google_token_expires_at = None
    company.google_connected_at = None
    company.google_account_email = None
    company.google_calendar_id = get_settings().google_calendar_id or "primary"


def handle_google_oauth_callback(db: Session, code: str, state_token: str) -> dict:
    payload = _decode_oauth_state(state_token)
    user_id = int(payload["sub"])
    company = db.query(ProviderCompany).filter(ProviderCompany.id == int(payload["company_id"])).first()
    if not company:
        raise BusinessRuleViolation("Empresa prestadora da integracao Google nao encontrada.")

    tokens = _exchange_code_for_tokens(code)
    _apply_company_token_payload(company, tokens)
    db.commit()

    appointment_id = payload.get("appointment_id")
    sync_message = "Conta Google conectada com sucesso."
    if appointment_id:
        from app.application.scheduling_services import sync_appointment_google_event

        try:
            appointment = sync_appointment_google_event(db, int(appointment_id), current_user_id=user_id)
            sync_message = f"Conta Google conectada e agendamento #{appointment.id} sincronizado com sucesso."
        except BusinessRuleViolation as exc:
            sync_message = f"Conta Google conectada, mas a sincronizacao do agendamento falhou: {exc.message}"

    return {
        "message": sync_message,
        "appointment_id": appointment_id,
        "company_id": company.id,
        "company_name": company.nome_fantasia or company.razao_social,
        "company_email": company.google_account_email,
    }


def _refresh_company_access_token(company: ProviderCompany) -> None:
    settings = get_settings()
    if not company.google_refresh_token:
        raise BusinessRuleViolation("A conexao com Google Agenda expirou e nao possui refresh token. Conecte a conta novamente.")
    if not _oauth_is_configured():
        raise BusinessRuleViolation(
            "OAuth do Google nao configurado. Defina GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET e GOOGLE_OAUTH_REDIRECT_URI."
        )

    payload = {
        "client_id": settings.google_oauth_client_id,
        "client_secret": settings.google_oauth_client_secret,
        "refresh_token": company.google_refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        response = httpx.post(GOOGLE_OAUTH_TOKEN_URL, data=payload, timeout=20)
        response.raise_for_status()
        refreshed = response.json()
    except httpx.HTTPError as exc:
        detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
        raise BusinessRuleViolation(f"Falha ao atualizar a sessao do Google Agenda: {detail}") from exc

    refreshed["refresh_token"] = refreshed.get("refresh_token") or company.google_refresh_token
    _apply_company_token_payload(company, refreshed)


def _get_runtime_google_credentials(db: Session, user_id: Optional[int]) -> tuple[str, str]:
    company = _get_company_for_context(db, user_id)
    if company and (company.google_access_token or company.google_refresh_token):
        if (
            not company.google_access_token
            or not company.google_token_expires_at
            or company.google_token_expires_at <= _now_utc()
        ):
            _refresh_company_access_token(company)
            db.commit()
        return _resolve_calendar_id(company), company.google_access_token

    settings = get_settings()
    if settings.google_calendar_enabled and settings.google_calendar_access_token:
        return settings.google_calendar_id or "primary", settings.google_calendar_access_token

    raise BusinessRuleViolation(
        "Nenhuma conta Google conectada para esta operacao. Conecte uma conta Google antes de sincronizar."
    )


def google_calendar_request(
    db: Session,
    user_id: Optional[int],
    method: str,
    path: str,
    payload: Optional[dict] = None,
) -> tuple[dict | None, str]:
    calendar_id, access_token = _get_runtime_google_credentials(db, user_id)
    url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.request(method, url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
        raise BusinessRuleViolation(f"Falha ao sincronizar com Google Agenda: {detail}") from exc
    content = response.json() if response.content else None
    return content, calendar_id


def sync_appointment_with_google_or_request_oauth(db: Session, appointment_id: int, current_user_id: int) -> dict:
    from app.application.scheduling_services import get_appointment, sync_appointment_google_event

    appointment = get_appointment(db, appointment_id)
    if not appointment.sincronizar_google:
        raise BusinessRuleViolation(
            "Ative a sincronizacao com Google Agenda neste agendamento antes de usar a sincronizacao manual."
        )

    try:
        synced = sync_appointment_google_event(db, appointment_id, current_user_id=current_user_id)
        return {
            "mode": "synced",
            "message": "Agendamento sincronizado com Google Agenda.",
            "authorization_url": None,
            "appointment": synced,
        }
    except BusinessRuleViolation as exc:
        if not _oauth_is_configured():
            raise
        authorization_url = build_google_oauth_authorization_url(db, current_user_id, appointment_id=appointment_id)
        return {
            "mode": "oauth_required",
            "message": f"{exc.message} Abra a autenticacao Google para concluir a sincronizacao.",
            "authorization_url": authorization_url,
            "appointment": None,
        }


def get_google_connection_status(
    db: Session,
    *,
    user_id: Optional[int] = None,
    provider_company_id: Optional[int] = None,
) -> dict:
    company = _get_company_for_context(db, user_id, provider_company_id=provider_company_id)
    if not company:
        settings = get_settings()
        if settings.google_calendar_enabled and settings.google_calendar_access_token:
            return {
                "status": "ativo",
                "message": "Configuracao global de Google Agenda ativa.",
                "company_id": 0,
                "company_name": "Configuracao global",
                "account_email": None,
                "calendar_id": settings.google_calendar_id or "primary",
            }
        raise BusinessRuleViolation("Nao existe empresa prestadora disponivel para verificar a conexao Google.")

    if company.google_refresh_token or company.google_access_token:
        status = "ativo"
        message = "Conta Google conectada para sincronizacao de agenda."
    elif _oauth_is_configured():
        status = "aguardando_conexao"
        message = "Nenhuma conta Google conectada. Inicie a autenticacao para vincular uma conta."
    else:
        status = "desconectado"
        message = "OAuth do Google ainda nao foi configurado."

    return {
        "status": status,
        "message": message,
        "company_id": company.id,
        "company_name": company.nome_fantasia or company.razao_social,
        "account_email": company.google_account_email,
        "calendar_id": _resolve_calendar_id(company),
    }


def logout_google_calendar(
    db: Session,
    *,
    user_id: Optional[int] = None,
    provider_company_id: Optional[int] = None,
) -> dict:
    company = _get_company_or_fail(db, user_id, provider_company_id=provider_company_id)
    _clear_company_google_session(company)
    db.commit()
    return {
        "status": "desconectado",
        "message": "Conta Google desconectada com sucesso. Voce ja pode conectar outra conta.",
        "company_id": company.id,
        "company_name": company.nome_fantasia or company.razao_social,
        "account_email": None,
        "calendar_id": _resolve_calendar_id(company),
    }
