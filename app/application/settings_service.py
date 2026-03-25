import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.application.schemas import (
    SettingsEnvironmentRead,
    SettingsIntegrationsRead,
    SettingsSystemRead,
    SystemSettingsRead,
    SystemSettingsUpdate,
)
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.models import SystemSetting, User


DEFAULT_SETTINGS: dict[str, Any] = {
    "google_calendar_enabled": False,
    "whatsapp_enabled": False,
    "whatsapp_auto_send": True,
    "whatsapp_default_message": "Seu agendamento foi confirmado com sucesso.",
    "multiempresa_enabled": True,
    "operation_mode": "local",
    "notifications_enabled": True,
    "appointment_default_google_sync": False,
}

RUNTIME_FALLBACK_KEYS = {
    "google_calendar_enabled",
    "whatsapp_enabled",
}


def _serialize_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def _deserialize_value(value: str) -> Any:
    return json.loads(value)


def ensure_system_settings_seed(db: Session) -> None:
    changed = False
    for key, default_value in DEFAULT_SETTINGS.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting is None:
            db.add(SystemSetting(key=key, value=_serialize_value(default_value)))
            changed = True
    if changed:
        db.commit()


def get_setting_value(db: Session, key: str, default: Any = None) -> Any:
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting is None:
        if key in DEFAULT_SETTINGS:
            return DEFAULT_SETTINGS[key]
        return default
    if key in RUNTIME_FALLBACK_KEYS and setting.updated_by_user_id is None:
        if default is not None:
            return default
        if key in DEFAULT_SETTINGS:
            return DEFAULT_SETTINGS[key]
    return _deserialize_value(setting.value)


def get_boolean_setting(db: Session, key: str, fallback: bool = False) -> bool:
    value = get_setting_value(db, key, default=fallback)
    return bool(value)


def set_setting_value(db: Session, key: str, value: Any, updated_by_user_id: Optional[int] = None) -> SystemSetting:
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting is None:
        setting = SystemSetting(key=key, value=_serialize_value(value))
        db.add(setting)
    else:
        setting.value = _serialize_value(value)
    setting.updated_by_user_id = updated_by_user_id
    return setting


def update_system_settings(db: Session, payload: SystemSettingsUpdate, current_user: User) -> SystemSettingsRead:
    updates: dict[str, Any] = {}
    if payload.integrations:
        updates.update({key: value for key, value in payload.integrations.model_dump().items() if value is not None})
    if payload.system:
        updates.update({key: value for key, value in payload.system.model_dump().items() if value is not None})

    if "operation_mode" in updates and updates["operation_mode"] not in {"local", "rede"}:
        raise BusinessRuleViolation("O modo de operacao deve ser 'local' ou 'rede'.")

    for key, value in updates.items():
        set_setting_value(db, key, value, updated_by_user_id=current_user.id)

    db.commit()
    return get_system_settings(db)


def get_system_settings(db: Session) -> SystemSettingsRead:
    settings = get_settings()
    ensure_system_settings_seed(db)
    return SystemSettingsRead(
        integrations=SettingsIntegrationsRead(
            google_calendar_enabled=get_boolean_setting(db, "google_calendar_enabled", fallback=settings.google_calendar_enabled),
            whatsapp_enabled=get_boolean_setting(db, "whatsapp_enabled", fallback=settings.whatsapp_enabled),
            whatsapp_auto_send=get_boolean_setting(db, "whatsapp_auto_send", fallback=True),
            whatsapp_default_message=str(get_setting_value(db, "whatsapp_default_message", DEFAULT_SETTINGS["whatsapp_default_message"])),
        ),
        system=SettingsSystemRead(
            multiempresa_enabled=get_boolean_setting(db, "multiempresa_enabled", fallback=True),
            operation_mode=str(get_setting_value(db, "operation_mode", "local")),
            notifications_enabled=get_boolean_setting(db, "notifications_enabled", fallback=True),
            appointment_default_google_sync=get_boolean_setting(db, "appointment_default_google_sync", fallback=False),
        ),
        environment=SettingsEnvironmentRead(
            database_url_masked=_mask_database_url(settings.database_url),
            app_host=settings.app_host,
            app_port=settings.app_port,
            allow_remote_access=settings.allow_remote_access,
        ),
    )


def _mask_database_url(database_url: str) -> str:
    if "@" not in database_url:
        return database_url
    left, right = database_url.rsplit("@", 1)
    if "://" not in left:
        return f"***@{right}"
    prefix, credentials = left.split("://", 1)
    if ":" not in credentials:
        return f"{prefix}://***@{right}"
    username, _ = credentials.split(":", 1)
    return f"{prefix}://{username}:***@{right}"
