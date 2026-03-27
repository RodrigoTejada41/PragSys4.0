import base64
import hashlib
import json
import logging
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.application.schemas import (
    SettingsContractsRead,
    SettingsDatabaseRead,
    SettingsEmailRead,
    SettingsEnvironmentRead,
    SettingsIntegrationsRead,
    SettingsSystemRead,
    SystemSettingsRead,
    SystemSettingsUpdate,
)
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.models import SystemSetting, User

LOGGER = logging.getLogger(__name__)
SENSITIVE_SETTINGS = {"smtp_password"}
ENCRYPTED_SETTING_PREFIX = "enc:v1:"


DEFAULT_SETTINGS: dict[str, Any] = {
    "google_calendar_enabled": False,
    "whatsapp_enabled": False,
    "whatsapp_auto_send": True,
    "whatsapp_default_message": "Ola {nome_cliente}, tudo bem?\n\nSeu agendamento foi confirmado com sucesso!\n\nData: {data}\nHora: {hora}\nTecnico: {tecnico}\nServico: {servico}\n\nQualquer duvida estamos a disposicao.",
    "contract_alert_days": 15,
    "contract_email_enabled": False,
    "contract_storage_dir": "uploads/contratos",
    "smtp_host": None,
    "smtp_port": 587,
    "smtp_username": None,
    "smtp_password": None,
    "smtp_use_tls": True,
    "smtp_use_ssl": False,
    "smtp_sender_email": None,
    "smtp_sender_name": None,
    "database_backup_dir": "backups/database",
    "multiempresa_enabled": True,
    "operation_mode": "local",
    "notifications_enabled": True,
    "appointment_default_google_sync": False,
}

RUNTIME_FALLBACK_KEYS = {
    "google_calendar_enabled",
    "whatsapp_enabled",
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "smtp_use_tls",
    "smtp_use_ssl",
    "smtp_sender_email",
    "smtp_sender_name",
}


def _serialize_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def _deserialize_value(value: str) -> Any:
    return json.loads(value)


def _get_settings_cipher() -> Fernet:
    settings = get_settings()
    secret_source = settings.settings_encryption_key or settings.jwt_secret
    digest = hashlib.sha256(secret_source.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_setting_value(value: Any) -> str:
    payload = _serialize_value(value).encode("utf-8")
    token = _get_settings_cipher().encrypt(payload).decode("utf-8")
    return f"{ENCRYPTED_SETTING_PREFIX}{token}"


def _decrypt_setting_value(value: str) -> Any:
    if not value.startswith(ENCRYPTED_SETTING_PREFIX):
        return _deserialize_value(value)
    token = value[len(ENCRYPTED_SETTING_PREFIX):].encode("utf-8")
    try:
        decrypted = _get_settings_cipher().decrypt(token).decode("utf-8")
    except InvalidToken as exc:
        LOGGER.exception("system_setting_decryption_failed")
        raise BusinessRuleViolation(
            "Nao foi possivel descriptografar uma configuracao sensivel. Verifique SETTINGS_ENCRYPTION_KEY/JWT_SECRET."
        ) from exc
    return _deserialize_value(decrypted)


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
    if key in SENSITIVE_SETTINGS:
        return _decrypt_setting_value(setting.value)
    return _deserialize_value(setting.value)


def get_boolean_setting(db: Session, key: str, fallback: bool = False) -> bool:
    value = get_setting_value(db, key, default=fallback)
    return bool(value)


def set_setting_value(db: Session, key: str, value: Any, updated_by_user_id: Optional[int] = None) -> SystemSetting:
    serialized_value = _encrypt_setting_value(value) if key in SENSITIVE_SETTINGS and value is not None else _serialize_value(value)
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting is None:
        setting = SystemSetting(key=key, value=serialized_value)
        db.add(setting)
    else:
        setting.value = serialized_value
    setting.updated_by_user_id = updated_by_user_id
    return setting


def update_system_settings(db: Session, payload: SystemSettingsUpdate, current_user: User) -> SystemSettingsRead:
    updates: dict[str, Any] = {}
    if payload.integrations:
        updates.update({key: value for key, value in payload.integrations.model_dump().items() if value is not None})
    if payload.contracts:
        updates.update(
            {
                f"contract_{key}": value
                for key, value in payload.contracts.model_dump().items()
                if value is not None
            }
        )
    if payload.system:
        updates.update({key: value for key, value in payload.system.model_dump().items() if value is not None})
    if payload.email:
        email_payload = payload.email.model_dump()
        for key, value in email_payload.items():
            if value is None:
                continue
            if key == "smtp_password" and value == "":
                continue
            updates[key] = value
    if payload.database:
        database_payload = payload.database.model_dump()
        for key, value in database_payload.items():
            if value is None:
                continue
            updates[f"database_{key}"] = value

    if "operation_mode" in updates and updates["operation_mode"] not in {"local", "rede"}:
        raise BusinessRuleViolation("O modo de operacao deve ser 'local' ou 'rede'.")
    if "contract_storage_dir" in updates and not str(updates["contract_storage_dir"]).strip():
        raise BusinessRuleViolation("O diretorio de contratos nao pode ficar vazio.")
    if "database_backup_dir" in updates and not str(updates["database_backup_dir"]).strip():
        raise BusinessRuleViolation("O diretorio de backup do banco nao pode ficar vazio.")

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
        contracts=SettingsContractsRead(
            alert_days=int(get_setting_value(db, "contract_alert_days", DEFAULT_SETTINGS["contract_alert_days"])),
            email_enabled=get_boolean_setting(db, "contract_email_enabled", fallback=False),
            storage_dir=str(get_setting_value(db, "contract_storage_dir", DEFAULT_SETTINGS["contract_storage_dir"])),
        ),
        system=SettingsSystemRead(
            multiempresa_enabled=get_boolean_setting(db, "multiempresa_enabled", fallback=True),
            operation_mode=str(get_setting_value(db, "operation_mode", "local")),
            notifications_enabled=get_boolean_setting(db, "notifications_enabled", fallback=True),
            appointment_default_google_sync=get_boolean_setting(db, "appointment_default_google_sync", fallback=False),
        ),
        email=SettingsEmailRead(
            smtp_host=_clean_optional_setting_text(get_setting_value(db, "smtp_host", settings.smtp_host)),
            smtp_port=int(get_setting_value(db, "smtp_port", settings.smtp_port)),
            smtp_username=_clean_optional_setting_text(get_setting_value(db, "smtp_username", settings.smtp_username)),
            smtp_use_tls=bool(get_setting_value(db, "smtp_use_tls", settings.smtp_use_tls)),
            smtp_use_ssl=bool(get_setting_value(db, "smtp_use_ssl", settings.smtp_use_ssl)),
            smtp_sender_email=_clean_optional_setting_text(get_setting_value(db, "smtp_sender_email", settings.smtp_sender_email)),
            smtp_sender_name=_clean_optional_setting_text(get_setting_value(db, "smtp_sender_name", settings.smtp_sender_name)),
            smtp_password_configured=bool(_clean_optional_setting_text(get_setting_value(db, "smtp_password", settings.smtp_password))),
        ),
        database=SettingsDatabaseRead(
            backup_dir=str(get_setting_value(db, "database_backup_dir", DEFAULT_SETTINGS["database_backup_dir"])),
            engine="sqlite" if settings.database_url.startswith("sqlite") else settings.database_url.split(":", 1)[0],
            database_file_name=_extract_database_file_name(settings.database_url),
        ),
        environment=SettingsEnvironmentRead(
            database_url_masked=_mask_database_url(settings.database_url),
            app_host=settings.app_host,
            app_port=settings.app_port,
            allow_remote_access=settings.allow_remote_access,
        ),
    )


def _clean_optional_setting_text(value: Any) -> Optional[str]:
    cleaned = str(value or "").strip()
    return cleaned or None


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


def _extract_database_file_name(database_url: str) -> Optional[str]:
    if not database_url.startswith("sqlite"):
        return None
    database_path = database_url.split("///", 1)[-1].strip()
    if not database_path or database_path == ":memory:":
        return None
    normalized = database_path.replace("\\", "/")
    return normalized.rsplit("/", 1)[-1]
