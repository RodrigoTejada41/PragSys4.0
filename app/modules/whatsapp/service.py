from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, Protocol, Union

import httpx
from sqlalchemy.orm import Session, joinedload

from app.application.settings_service import get_boolean_setting, get_setting_value
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.models import Appointment, AppointmentHistory
from app.modules.whatsapp.config import WhatsAppIntegrationConfig, load_whatsapp_config
from app.modules.whatsapp.repository import create_appointment_whatsapp_log
from app.modules.whatsapp.utils import (
    DEFAULT_APPOINTMENT_WHATSAPP_TEMPLATE,
    build_appointment_whatsapp_message,
    compact_error_message,
    normalize_whatsapp_phone,
)

logger = logging.getLogger(__name__)
QR_RETRY_INTERVAL_SECONDS = 1.0
QR_MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class WhatsAppSendResult:
    provider: str
    external_message_id: Optional[str]
    raw_response: Optional[Union[dict, str]]


@dataclass(frozen=True)
class WhatsAppConnectionStatus:
    status: str
    provider: str
    instance_name: Optional[str]
    connected_phone: Optional[str]
    error_message: Optional[str]
    configured: bool
    supports_qr: bool
    session_persistent: bool


@dataclass(frozen=True)
class WhatsAppQrSessionStatus:
    status: str
    provider: str
    instance_name: Optional[str]
    qr_code: Optional[str]
    qr_image_data_url: Optional[str]
    pairing_code: Optional[str]
    expires_at: Optional[str]
    message: Optional[str]
    error_message: Optional[str]


class WhatsAppProviderClient(Protocol):
    def send_message(self, destination_phone: str, message: str) -> WhatsAppSendResult:
        ...


class MetaCloudApiClient:
    def __init__(self, config: WhatsAppIntegrationConfig):
        self._config = config

    def send_message(self, destination_phone: str, message: str) -> WhatsAppSendResult:
        endpoint = f"{self._config.api_base_url.rstrip('/')}/{self._config.sender_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._config.auth_token or self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": destination_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        body = response.json()
        external_message_id = None
        if isinstance(body.get("messages"), list) and body["messages"]:
            external_message_id = body["messages"][0].get("id")
        return WhatsAppSendResult(provider="meta_cloud_api", external_message_id=external_message_id, raw_response=body)


class TwilioWhatsAppClient:
    def __init__(self, config: WhatsAppIntegrationConfig):
        self._config = config

    def send_message(self, destination_phone: str, message: str) -> WhatsAppSendResult:
        endpoint = (
            self._config.api_base_url.rstrip("/")
            if self._config.api_base_url
            else f"https://api.twilio.com/2010-04-01/Accounts/{self._config.api_key}/Messages.json"
        )
        payload = {
            "To": f"whatsapp:+{destination_phone}",
            "From": self._config.sender_id,
            "Body": message,
        }
        response = httpx.post(
            endpoint,
            data=payload,
            auth=(self._config.api_key or "", self._config.auth_token or ""),
            timeout=self._config.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        return WhatsAppSendResult(provider="twilio", external_message_id=body.get("sid"), raw_response=body)


class CustomWhatsAppClient:
    def __init__(self, config: WhatsAppIntegrationConfig):
        self._config = config

    def send_message(self, destination_phone: str, message: str) -> WhatsAppSendResult:
        headers = _build_auth_headers(self._config)
        headers["Content-Type"] = "application/json"
        payload = {
            "sender_id": self._config.sender_id,
            "instance_name": self._config.instance_name,
            "instance": self._config.instance_name,
            "to": destination_phone,
            "number": destination_phone,
            "message": message,
            "text": message,
            "channel": "whatsapp",
        }
        response = httpx.post(
            _resolve_message_url(self._config),
            json=payload,
            headers=headers,
            timeout=self._config.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        external_message_id = body.get("message_id") or body.get("messageId") or body.get("id")
        return WhatsAppSendResult(provider="custom", external_message_id=external_message_id, raw_response=body)


class EvolutionWhatsAppClient:
    def __init__(self, config: WhatsAppIntegrationConfig):
        self._config = config

    def send_message(self, destination_phone: str, message: str) -> WhatsAppSendResult:
        endpoint = _resolve_message_url(self._config)
        headers = _build_auth_headers(self._config)
        headers["Content-Type"] = "application/json"
        payload = {
            "number": destination_phone,
            "text": message,
        }
        response = httpx.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=self._config.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json() if response.content else {}
        external_message_id = (
            body.get("key", {}).get("id")
            or body.get("response", {}).get("key", {}).get("id")
            or body.get("message", {}).get("key", {}).get("id")
            or body.get("id")
        )
        return WhatsAppSendResult(provider="evolution", external_message_id=external_message_id, raw_response=body)


def _appointment_query(db: Session):
    from app.infrastructure.models import AppointmentWhatsAppLog, Customer, Technician, User, WorkOrder

    return db.query(Appointment).options(
        joinedload(Appointment.cliente),
        joinedload(Appointment.tecnico),
        joinedload(Appointment.ordem_servico),
        joinedload(Appointment.usuario_responsavel),
        joinedload(Appointment.usuario_ultima_atualizacao),
        joinedload(Appointment.whatsapp_logs).joinedload(AppointmentWhatsAppLog.usuario),
    )


def _get_appointment_or_fail(db: Session, appointment_id: int) -> Appointment:
    appointment = _appointment_query(db).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise BusinessRuleViolation("Agendamento nao encontrado para envio via WhatsApp.")
    return appointment


def _build_client(config: WhatsAppIntegrationConfig) -> WhatsAppProviderClient:
    provider = config.provider.strip().lower()
    if provider == "meta_cloud_api":
        return MetaCloudApiClient(config)
    if provider == "twilio":
        return TwilioWhatsAppClient(config)
    if provider == "evolution":
        return EvolutionWhatsAppClient(config)
    return CustomWhatsAppClient(config)


def _build_auth_headers(config: WhatsAppIntegrationConfig) -> dict[str, str]:
    headers = {}
    if config.auth_token:
        headers["Authorization"] = f"Bearer {config.auth_token}"
    if config.api_key:
        headers["X-API-Key"] = config.api_key
        headers["apikey"] = config.api_key
    return headers


def _resolve_message_url(config: WhatsAppIntegrationConfig) -> str:
    if config.message_api_url:
        return config.message_api_url
    provider = config.provider.strip().lower()
    if provider == "evolution" and config.api_base_url and config.instance_name:
        return f"{config.api_base_url.rstrip('/')}/message/sendText/{config.instance_name}"
    if config.api_base_url:
        return config.api_base_url
    raise BusinessRuleViolation("Configure o endpoint de envio do WhatsApp antes de disparar mensagens.")


def _resolve_qr_url(config: WhatsAppIntegrationConfig) -> Optional[str]:
    if config.qr_api_url:
        return config.qr_api_url
    if config.provider == "evolution" and config.api_base_url and config.instance_name:
        return f"{config.api_base_url.rstrip('/')}/instance/connect/{config.instance_name}"
    if config.supports_qr and config.api_base_url:
        return f"{config.api_base_url.rstrip('/')}/session/qr"
    return None


def _resolve_status_url(config: WhatsAppIntegrationConfig) -> Optional[str]:
    if config.status_api_url:
        return config.status_api_url
    if config.provider == "evolution" and config.api_base_url and config.instance_name:
        return f"{config.api_base_url.rstrip('/')}/instance/connectionState/{config.instance_name}"
    if config.provider == "custom" and config.api_base_url:
        return f"{config.api_base_url.rstrip('/')}/status"
    return None


def _parse_json_response(response: httpx.Response) -> dict:
    return response.json() if response.content else {}


def _extract_qr_session_payload(payload: dict, config: WhatsAppIntegrationConfig) -> WhatsAppQrSessionStatus:
    qr_code = (
        payload.get("qr_code")
        or payload.get("qr")
        or payload.get("code")
        or payload.get("qrcode")
    )
    qr_image = (
        payload.get("qr_image_data_url")
        or payload.get("qr_image")
        or payload.get("image")
        or payload.get("base64")
    )
    if qr_image and not str(qr_image).startswith("data:image"):
        qr_image = f"data:image/png;base64,{qr_image}"
    pairing_code = payload.get("pairingCode") or payload.get("pairing_code")
    status = payload.get("status") or ("aguardando_conexao" if qr_code or qr_image else "erro")
    return WhatsAppQrSessionStatus(
        status=str(status),
        provider=config.provider,
        instance_name=payload.get("instance_name") or payload.get("instance", {}).get("instanceName") or config.instance_name or config.sender_id,
        qr_code=qr_code,
        qr_image_data_url=qr_image,
        pairing_code=pairing_code,
        expires_at=payload.get("expires_at") or payload.get("ttl"),
        message=payload.get("message") or "Leia o QR Code com o WhatsApp para conectar esta sessao.",
        error_message=payload.get("error"),
    )


def _should_retry_qr_session(status: WhatsAppQrSessionStatus) -> bool:
    normalized = str(status.status or "").strip().lower()
    message = str(status.message or "").strip().lower()
    error_message = str(status.error_message or "").strip().lower()
    expired_tokens = ("expired", "expirado", "qr_expired", "time out", "timeout")
    if status.qr_code or status.qr_image_data_url:
        return False
    if normalized in {"open", "ativo"}:
        return False
    if any(token in message for token in expired_tokens) or any(token in error_message for token in expired_tokens):
        return True
    return normalized in {"connecting", "aguardando_conexao", "pending", "qr", "closed", "desconectado", "erro", "qr_expired"}


def _request_qr_payload(
    config: WhatsAppIntegrationConfig,
    *,
    regenerate: bool,
) -> WhatsAppQrSessionStatus:
    headers = _build_auth_headers(config)
    session_payload = {
        "instance_name": config.instance_name,
        "sender_id": config.sender_id,
    }
    qr_url = _resolve_qr_url(config)
    if not qr_url:
        raise BusinessRuleViolation("Nao foi possivel determinar o endpoint de QR Code do conector WhatsApp.")

    request_kwargs = {"headers": headers, "timeout": config.timeout_seconds}
    if config.provider == "evolution":
        params = {}
        if regenerate:
            params["regenerate"] = "1"
        response = httpx.get(qr_url, params=params, **request_kwargs)
    else:
        params = dict(session_payload)
        if regenerate:
            params["regenerate"] = "1"
        response = httpx.get(qr_url, params=params, **request_kwargs)
    response.raise_for_status()
    payload = _parse_json_response(response)
    return _extract_qr_session_payload(payload, config)


def _connect_qr_session(config: WhatsAppIntegrationConfig, *, regenerate: bool) -> None:
    connect_url = _resolve_connect_url(config)
    if not connect_url:
        return
    headers = _build_auth_headers(config)
    payload = {
        "instance_name": config.instance_name,
        "sender_id": config.sender_id,
    }
    if regenerate:
        payload["regenerate"] = True
    response = httpx.post(connect_url, json=payload, headers=headers, timeout=config.timeout_seconds)
    response.raise_for_status()


def _resolve_connect_url(config: WhatsAppIntegrationConfig) -> Optional[str]:
    if config.connect_api_url:
        return config.connect_api_url
    if config.provider == "evolution":
        return None
    if config.supports_qr and config.api_base_url:
        return f"{config.api_base_url.rstrip('/')}/session/connect"
    return None


def _resolve_logout_url(config: WhatsAppIntegrationConfig) -> Optional[str]:
    if config.logout_api_url:
        return config.logout_api_url
    if config.provider == "evolution" and config.api_base_url and config.instance_name:
        return f"{config.api_base_url.rstrip('/')}/instance/logout/{config.instance_name}"
    if config.supports_qr and config.api_base_url:
        return f"{config.api_base_url.rstrip('/')}/session/logout"
    return None


def _serialize_external_response(payload: Optional[Union[dict, str]]) -> Optional[str]:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, ensure_ascii=True)


def _append_history(
    db: Session,
    appointment: Appointment,
    *,
    user_id: Optional[int],
    action: str,
    details: str,
) -> None:
    db.add(
        AppointmentHistory(
            agendamento_id=appointment.id,
            usuario_id=user_id,
            acao=action,
            detalhes=compact_error_message(details),
        )
    )


def get_whatsapp_configuration_status(db: Session) -> dict:
    config = load_whatsapp_config()
    enabled = get_boolean_setting(db, "whatsapp_enabled", fallback=config.enabled)
    return {
        "enabled": enabled,
        "provider": config.provider,
        "configured": config.is_ready,
        "api_base_url": config.api_base_url,
        "sender_id_configured": bool(config.sender_id),
        "auth_configured": bool(config.auth_token or config.api_key),
        "supports_qr": config.supports_qr,
    }


def _normalize_connection_status(payload: Optional[dict], config: WhatsAppIntegrationConfig) -> WhatsAppConnectionStatus:
    payload = payload or {}
    instance_payload = payload.get("instance") if isinstance(payload.get("instance"), dict) else {}
    instance_name = (
        instance_payload.get("instanceName")
        or instance_payload.get("instance")
        or payload.get("instance_name")
        or (payload.get("instance") if isinstance(payload.get("instance"), str) else None)
        or payload.get("name")
        or config.instance_name
        or config.sender_id
    )
    connected_flag = payload.get("connected")
    raw_status = str(
        instance_payload.get("state")
        or payload.get("status")
        or payload.get("state")
        or payload.get("connection_status")
        or ""
    ).strip().lower()

    if connected_flag is True or raw_status in {"ativo", "active", "connected", "open", "ready"}:
        status = "ativo"
    elif connected_flag is False or raw_status in {"desconectado", "disconnected", "closed", "logout"}:
        status = "desconectado"
    elif raw_status in {"aguardando", "aguardando_conexao", "pending", "connecting", "qr", "awaiting_connection"}:
        status = "aguardando_conexao"
    else:
        status = "ativo" if config.is_ready else "aguardando_conexao"

    error_message = payload.get("error") or payload.get("message") or None
    connected_phone = (
        instance_payload.get("ownerJid")
        or instance_payload.get("profileName")
        or payload.get("phone")
        or payload.get("wid")
        or payload.get("session_phone")
        or payload.get("me")
        or payload.get("account")
    )
    return WhatsAppConnectionStatus(
        status=status,
        provider=config.provider,
        instance_name=instance_name,
        connected_phone=compact_error_message(str(connected_phone)) if connected_phone else None,
        error_message=compact_error_message(error_message) if error_message else None,
        configured=config.is_ready,
        supports_qr=config.supports_qr,
        session_persistent=config.supports_qr,
    )


class WhatsAppService:
    @staticmethod
    def get_status(*, enabled_override: Optional[bool] = None) -> WhatsAppConnectionStatus:
        config = load_whatsapp_config()
        instance_name = config.instance_name or config.sender_id
        effective_enabled = config.enabled if enabled_override is None else enabled_override

        if not effective_enabled:
            return WhatsAppConnectionStatus(
                status="desconectado",
                provider=config.provider,
                instance_name=instance_name,
                connected_phone=None,
                error_message="Integracao WhatsApp desabilitada nas configuracoes.",
                configured=False,
                supports_qr=config.supports_qr,
                session_persistent=config.supports_qr,
            )
        if not config.is_ready:
            return WhatsAppConnectionStatus(
                status="aguardando_conexao",
                provider=config.provider,
                instance_name=instance_name,
                connected_phone=None,
                error_message="Configuracao da integracao WhatsApp incompleta.",
                configured=False,
                supports_qr=config.supports_qr,
                session_persistent=config.supports_qr,
            )

        status_url = _resolve_status_url(config)
        if not status_url:
            return WhatsAppConnectionStatus(
                status="ativo",
                provider=config.provider,
                instance_name=instance_name,
                connected_phone=None,
                error_message=None,
                configured=True,
                supports_qr=config.supports_qr,
                session_persistent=config.supports_qr,
            )

        headers = _build_auth_headers(config)

        try:
            response = httpx.get(status_url, headers=headers, timeout=config.timeout_seconds)
            response.raise_for_status()
            payload = _parse_json_response(response)
            logger.info("WhatsApp status resolved provider=%s status_url=%s payload=%s", config.provider, status_url, payload)
            return _normalize_connection_status(payload, config)
        except httpx.TimeoutException:
            logger.warning("WhatsApp status check timed out for %s", status_url)
            return WhatsAppConnectionStatus(
                status="erro",
                provider=config.provider,
                instance_name=instance_name,
                connected_phone=None,
                error_message="Timeout ao consultar o status da conexao WhatsApp.",
                configured=True,
                supports_qr=config.supports_qr,
                session_persistent=config.supports_qr,
            )
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("WhatsApp status check failed: %s", exc)
            return WhatsAppConnectionStatus(
                status="erro",
                provider=config.provider,
                instance_name=instance_name,
                connected_phone=None,
                error_message=compact_error_message(str(exc)) or "Falha ao consultar o status da conexao WhatsApp.",
                configured=True,
                supports_qr=config.supports_qr,
                session_persistent=config.supports_qr,
            )


def send_whatsapp_message(destination_phone: str, message: str) -> WhatsAppSendResult:
    config = load_whatsapp_config()
    client = _build_client(config)
    return client.send_message(destination_phone, message)


def enviar_mensagem_whatsapp(numero: str, mensagem: str) -> WhatsAppSendResult:
    return send_whatsapp_message(numero, mensagem)


def get_whatsapp_connection_status(db: Session) -> dict:
    enabled = get_boolean_setting(db, "whatsapp_enabled", fallback=load_whatsapp_config().enabled)
    status = WhatsAppService.get_status(enabled_override=enabled).__dict__
    if not enabled:
        status["status"] = "desconectado"
        status["configured"] = False
        status["error_message"] = "Integracao WhatsApp desabilitada nas configuracoes do sistema."
    return status


def request_whatsapp_qr_session(db: Session) -> dict:
    config = load_whatsapp_config()
    if not get_boolean_setting(db, "whatsapp_enabled", fallback=config.enabled):
        raise BusinessRuleViolation("Ative o WhatsApp nas configuracoes do sistema antes de conectar via QR.")
    if not config.supports_qr:
        raise BusinessRuleViolation("O provedor atual nao suporta autenticacao por QR Code.")
    if not config.api_base_url:
        raise BusinessRuleViolation("Configure a URL base do conector WhatsApp Web para gerar o QR Code.")

    logger.info("WhatsApp QR requested provider=%s instance=%s", config.provider, config.instance_name or config.sender_id)
    try:
        _connect_qr_session(config, regenerate=False)
        qr_status = _request_qr_payload(config, regenerate=False)
        for attempt in range(2, QR_MAX_ATTEMPTS + 1):
            if not _should_retry_qr_session(qr_status):
                break
            logger.info(
                "WhatsApp QR retry scheduled provider=%s instance=%s attempt=%s status=%s",
                config.provider,
                config.instance_name or config.sender_id,
                attempt,
                qr_status.status,
            )
            time.sleep(QR_RETRY_INTERVAL_SECONDS)
            qr_status = _request_qr_payload(config, regenerate=True)
    except httpx.TimeoutException as exc:
        raise BusinessRuleViolation("Timeout ao solicitar o QR Code do WhatsApp.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
        raise BusinessRuleViolation(f"Falha ao obter QR Code do WhatsApp: {compact_error_message(detail)}") from exc
    logger.info(
        "WhatsApp QR resolved provider=%s instance=%s status=%s has_qr=%s",
        config.provider,
        qr_status.instance_name,
        qr_status.status,
        bool(qr_status.qr_code or qr_status.qr_image_data_url),
    )
    return qr_status.__dict__


def logout_whatsapp_session(db: Session) -> dict:
    config = load_whatsapp_config()
    if not config.supports_qr:
        raise BusinessRuleViolation("O provedor atual nao suporta logout de sessao por QR Code.")
    logout_url = _resolve_logout_url(config)
    if not logout_url:
        raise BusinessRuleViolation("Nao foi possivel determinar o endpoint de logout do conector WhatsApp.")

    headers = _build_auth_headers(config)
    payload = {
        "instance_name": config.instance_name,
        "sender_id": config.sender_id,
    }
    try:
        if config.provider == "evolution":
            response = httpx.delete(logout_url, headers=headers, timeout=config.timeout_seconds)
        else:
            response = httpx.post(logout_url, json=payload, headers=headers, timeout=config.timeout_seconds)
        response.raise_for_status()
        logger.info("WhatsApp session logout completed provider=%s instance=%s", config.provider, config.instance_name)
    except httpx.TimeoutException as exc:
        raise BusinessRuleViolation("Timeout ao encerrar a sessao do WhatsApp.") from exc
    except httpx.HTTPError as exc:
        detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
        raise BusinessRuleViolation(f"Falha ao desconectar a sessao do WhatsApp: {compact_error_message(detail)}") from exc

    status = get_whatsapp_connection_status(db)
    status["status"] = "desconectado"
    status["error_message"] = "Sessao WhatsApp desconectada. Gere um novo QR Code para reconectar."
    return status


def send_appointment_whatsapp_message(
    db: Session,
    appointment_id: int,
    *,
    current_user_id: Optional[int] = None,
    automatic: bool = False,
    raise_on_error: bool = False,
):
    appointment = _get_appointment_or_fail(db, appointment_id)
    config = load_whatsapp_config()
    destination_phone = appointment.telefone or ""
    rendered_message = ""

    def _resolve_error_message(exc: Exception) -> str:
        if isinstance(exc, BusinessRuleViolation):
            return exc.message
        if isinstance(exc, httpx.TimeoutException):
            return "API do WhatsApp indisponivel por timeout."
        if isinstance(exc, httpx.ConnectError):
            return "Erro de conexao com a API do WhatsApp."
        if isinstance(exc, httpx.HTTPStatusError):
            response_text = exc.response.text if exc.response is not None else str(exc)
            return f"Falha da API do WhatsApp: {response_text}"
        if isinstance(exc, httpx.RequestError):
            return "Falha de comunicacao com a API do WhatsApp."
        return str(exc)

    try:
        template = str(get_setting_value(db, "whatsapp_default_message", DEFAULT_APPOINTMENT_WHATSAPP_TEMPLATE) or "").strip()
        rendered_message = build_appointment_whatsapp_message(appointment, template=template)
        normalized_phone = normalize_whatsapp_phone(destination_phone)
        logger.info(
            "WhatsApp send requested appointment_id=%s automatic=%s provider=%s destination=%s",
            appointment.id,
            automatic,
            config.provider,
            normalized_phone,
        )
        if not get_boolean_setting(db, "whatsapp_enabled", fallback=config.enabled):
            raise BusinessRuleViolation("Integracao WhatsApp desabilitada nas configuracoes do sistema.")
        if not config.enabled:
            raise BusinessRuleViolation("Integracao WhatsApp desabilitada nas configuracoes do sistema.")
        if not config.is_ready:
            raise BusinessRuleViolation("Configuracao da integracao WhatsApp incompleta.")
        result = send_whatsapp_message(normalized_phone, rendered_message)
        logger.info(
            "WhatsApp send succeeded appointment_id=%s automatic=%s provider=%s destination=%s external_message_id=%s",
            appointment.id,
            automatic,
            result.provider,
            normalized_phone,
            result.external_message_id,
        )
        create_appointment_whatsapp_log(
            db,
            appointment_id=appointment.id,
            user_id=current_user_id,
            provider=result.provider,
            status="enviado",
            destination_phone=normalized_phone,
            message=rendered_message,
            automatic=automatic,
            external_message_id=result.external_message_id,
            external_response=_serialize_external_response(result.raw_response),
        )
        _append_history(
            db,
            appointment,
            user_id=current_user_id,
            action="whatsapp_send",
            details=f"Mensagem de WhatsApp enviada com sucesso para {normalized_phone}.",
        )
        db.commit()
    except (BusinessRuleViolation, httpx.HTTPError, httpx.InvalidURL, ValueError) as exc:
        error_message = _resolve_error_message(exc)
        normalized_phone = "".join(char for char in destination_phone if char.isdigit()) or destination_phone or "-"
        logger.warning(
            "WhatsApp send failed appointment_id=%s automatic=%s provider=%s destination=%s error=%s",
            appointment.id,
            automatic,
            config.provider,
            normalized_phone,
            compact_error_message(error_message),
        )
        create_appointment_whatsapp_log(
            db,
            appointment_id=appointment.id,
            user_id=current_user_id,
            provider=config.provider,
            status="falha",
            destination_phone=normalized_phone,
            message=rendered_message or "Mensagem nao gerada por falha de validacao.",
            automatic=automatic,
            error_message=compact_error_message(error_message),
        )
        _append_history(
            db,
            appointment,
            user_id=current_user_id,
            action="whatsapp_send_fail",
            details=f"Falha no envio de WhatsApp: {compact_error_message(error_message)}",
        )
        db.commit()
        if raise_on_error:
            raise BusinessRuleViolation(compact_error_message(error_message) or "Falha ao enviar WhatsApp.")

    db.expire_all()
    from app.application.scheduling_services import get_appointment

    return get_appointment(db, appointment.id)


