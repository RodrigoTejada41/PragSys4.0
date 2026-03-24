from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class WhatsAppIntegrationConfig:
    enabled: bool
    provider: str
    api_base_url: Optional[str]
    api_key: Optional[str]
    auth_token: Optional[str]
    sender_id: Optional[str]
    timeout_seconds: float

    @property
    def is_ready(self) -> bool:
        if not self.enabled:
            return False
        provider = self.provider.strip().lower()
        if provider == "twilio":
            return bool(self.api_key and self.auth_token and self.sender_id)
        return bool(self.api_base_url and self.sender_id and (self.auth_token or self.api_key))


def load_whatsapp_config(settings: Optional[Settings] = None) -> WhatsAppIntegrationConfig:
    runtime_settings = settings or get_settings()
    return WhatsAppIntegrationConfig(
        enabled=runtime_settings.whatsapp_enabled,
        provider=str(runtime_settings.whatsapp_provider or "custom").strip().lower(),
        api_base_url=(runtime_settings.whatsapp_api_base_url or "").strip() or None,
        api_key=(runtime_settings.whatsapp_api_key or "").strip() or None,
        auth_token=(runtime_settings.whatsapp_auth_token or "").strip() or None,
        sender_id=(runtime_settings.whatsapp_sender_id or "").strip() or None,
        timeout_seconds=runtime_settings.whatsapp_timeout_seconds,
    )

