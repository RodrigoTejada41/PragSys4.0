from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class WhatsAppIntegrationConfig:
    enabled: bool
    provider: str
    api_base_url: Optional[str]
    message_api_url: Optional[str]
    api_key: Optional[str]
    auth_token: Optional[str]
    sender_id: Optional[str]
    instance_name: Optional[str]
    status_api_url: Optional[str]
    qr_api_url: Optional[str]
    connect_api_url: Optional[str]
    logout_api_url: Optional[str]
    timeout_seconds: float

    @property
    def is_ready(self) -> bool:
        provider = self.provider.strip().lower()
        if provider == "twilio":
            return bool(self.api_key and self.auth_token and self.sender_id)
        if self.supports_qr:
            return bool(self.api_base_url and (self.instance_name or self.sender_id))
        return bool(self.api_base_url and self.sender_id and (self.auth_token or self.api_key))

    @property
    def supports_qr(self) -> bool:
        provider = self.provider.strip().lower()
        return provider in {"whatsapp_web", "qr_bridge", "evolution"} or bool(
            self.qr_api_url or self.connect_api_url or self.logout_api_url
        )


def _clean_text(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _setting_from_db(db, key: str, fallback: Any) -> Any:
    if db is None:
        return fallback
    from app.application.settings_service import get_setting_value

    return get_setting_value(db, key, fallback)


def load_whatsapp_config(settings: Optional[Settings] = None, db=None) -> WhatsAppIntegrationConfig:
    runtime_settings = settings or get_settings()
    return WhatsAppIntegrationConfig(
        enabled=bool(_setting_from_db(db, "whatsapp_enabled", runtime_settings.whatsapp_enabled)),
        provider=str(_setting_from_db(db, "whatsapp_provider", runtime_settings.whatsapp_provider or "custom") or "custom").strip().lower(),
        api_base_url=_clean_text(_setting_from_db(db, "whatsapp_api_base_url", runtime_settings.whatsapp_api_base_url)),
        message_api_url=_clean_text(_setting_from_db(db, "whatsapp_message_api_url", runtime_settings.whatsapp_message_api_url)),
        api_key=_clean_text(_setting_from_db(db, "whatsapp_api_key", runtime_settings.whatsapp_api_key)),
        auth_token=_clean_text(_setting_from_db(db, "whatsapp_auth_token", runtime_settings.whatsapp_auth_token)),
        sender_id=_clean_text(_setting_from_db(db, "whatsapp_sender_id", runtime_settings.whatsapp_sender_id)),
        instance_name=_clean_text(_setting_from_db(db, "whatsapp_instance_name", runtime_settings.whatsapp_instance_name)),
        status_api_url=_clean_text(_setting_from_db(db, "whatsapp_status_api_url", runtime_settings.whatsapp_status_api_url)),
        qr_api_url=_clean_text(_setting_from_db(db, "whatsapp_qr_api_url", runtime_settings.whatsapp_qr_api_url)),
        connect_api_url=_clean_text(_setting_from_db(db, "whatsapp_connect_api_url", runtime_settings.whatsapp_connect_api_url)),
        logout_api_url=_clean_text(_setting_from_db(db, "whatsapp_logout_api_url", runtime_settings.whatsapp_logout_api_url)),
        timeout_seconds=float(_setting_from_db(db, "whatsapp_timeout_seconds", runtime_settings.whatsapp_timeout_seconds)),
    )
