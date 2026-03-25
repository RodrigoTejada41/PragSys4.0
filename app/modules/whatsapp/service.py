from __future__ import annotations

import json
import logging
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
    error_message: Optional[str]
    configured: bool


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
        headers = {"Content-Type": "application/json"}
        if self._config.auth_token:
            headers["Authorization"] = f"Bearer {self._config.auth_token}"
        if self._config.api_key:
            headers["X-API-Key"] = self._config.api_key
        payload = {
            "sender_id": self._config.sender_id,
            "to": destination_phone,
            "message": message,
            "channel": "whatsapp",
        }
        response = httpx.post(
            self._config.api_base_url,
            json=payload,
            headers=headers,
            timeout=self._config.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        external_message_id = body.get("message_id") or body.get("messageId") or body.get("id")
        return WhatsAppSendResult(provider="custom", external_message_id=external_message_id, raw_response=body)


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
    return CustomWhatsAppClient(config)


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
    enabled = config.enabled and get_boolean_setting(db, "whatsapp_enabled", fallback=config.enabled)
    return {
        "enabled": enabled,
        "provider": config.provider,
        "configured": config.is_ready,
        "api_base_url": config.api_base_url,
        "sender_id_configured": bool(config.sender_id),
        "auth_configured": bool(config.auth_token or config.api_key),
    }


def _resolve_status_url(config: WhatsAppIntegrationConfig) -> Optional[str]:
    if config.status_api_url:
        return config.status_api_url
    if config.provider == "custom" and config.api_base_url:
        return f"{config.api_base_url.rstrip('/')}/status"
    return None


def _normalize_connection_status(payload: Optional[dict], config: WhatsAppIntegrationConfig) -> WhatsAppConnectionStatus:
    payload = payload or {}
    instance_name = (
        payload.get("instance_name")
        or payload.get("instance")
        or payload.get("name")
        or config.instance_name
        or config.sender_id
    )
    connected_flag = payload.get("connected")
    raw_status = str(
        payload.get("status")
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
    return WhatsAppConnectionStatus(
        status=status,
        provider=config.provider,
        instance_name=instance_name,
        error_message=compact_error_message(error_message) if error_message else None,
        configured=config.is_ready,
    )


class WhatsAppService:
    @staticmethod
    def get_status() -> WhatsAppConnectionStatus:
        config = load_whatsapp_config()
        instance_name = config.instance_name or config.sender_id

        if not config.enabled:
            return WhatsAppConnectionStatus(
                status="desconectado",
                provider=config.provider,
                instance_name=instance_name,
                error_message="Integracao WhatsApp desabilitada nas configuracoes.",
                configured=False,
            )
        if not config.is_ready:
            return WhatsAppConnectionStatus(
                status="aguardando_conexao",
                provider=config.provider,
                instance_name=instance_name,
                error_message="Configuracao da integracao WhatsApp incompleta.",
                configured=False,
            )

        status_url = _resolve_status_url(config)
        if not status_url:
            return WhatsAppConnectionStatus(
                status="ativo",
                provider=config.provider,
                instance_name=instance_name,
                error_message=None,
                configured=True,
            )

        headers = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
        if config.api_key:
            headers["X-API-Key"] = config.api_key

        try:
            response = httpx.get(status_url, headers=headers, timeout=config.timeout_seconds)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            return _normalize_connection_status(payload, config)
        except httpx.TimeoutException:
            logger.warning("WhatsApp status check timed out for %s", status_url)
            return WhatsAppConnectionStatus(
                status="erro",
                provider=config.provider,
                instance_name=instance_name,
                error_message="Timeout ao consultar o status da conexao WhatsApp.",
                configured=True,
            )
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("WhatsApp status check failed: %s", exc)
            return WhatsAppConnectionStatus(
                status="erro",
                provider=config.provider,
                instance_name=instance_name,
                error_message=compact_error_message(str(exc)) or "Falha ao consultar o status da conexao WhatsApp.",
                configured=True,
            )


def send_whatsapp_message(destination_phone: str, message: str) -> WhatsAppSendResult:
    config = load_whatsapp_config()
    client = _build_client(config)
    return client.send_message(destination_phone, message)


def enviar_mensagem_whatsapp(numero: str, mensagem: str) -> WhatsAppSendResult:
    return send_whatsapp_message(numero, mensagem)


def get_whatsapp_connection_status(db: Session) -> dict:
    status = WhatsAppService.get_status().__dict__
    if not get_boolean_setting(db, "whatsapp_enabled", fallback=load_whatsapp_config().enabled):
        status["status"] = "desconectado"
        status["configured"] = False
        status["error_message"] = "Integracao WhatsApp desabilitada nas configuracoes do sistema."
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
        if not get_boolean_setting(db, "whatsapp_enabled", fallback=config.enabled):
            raise BusinessRuleViolation("Integracao WhatsApp desabilitada nas configuracoes do sistema.")
        if not config.enabled:
            raise BusinessRuleViolation("Integracao WhatsApp desabilitada nas configuracoes do sistema.")
        if not config.is_ready:
            raise BusinessRuleViolation("Configuracao da integracao WhatsApp incompleta.")
        result = send_whatsapp_message(normalized_phone, rendered_message)
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
