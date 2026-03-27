import base64
import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.application.schemas import (
    SettingsCompanyRead,
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
from app.infrastructure.models import CompanyTechnicalData, ProviderCompany

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

    if payload.company:
        _update_company_technical_data(db, payload.company, current_user)

    db.commit()
    return get_system_settings(db, current_user)


def get_system_settings(db: Session, current_user: Optional[User] = None) -> SystemSettingsRead:
    settings = get_settings()
    ensure_system_settings_seed(db)
    company_settings = _read_company_technical_data(db, current_user)
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
        company=company_settings,
    )


def get_document_company_settings(db: Session, provider_company_id: Optional[int] = None):
    settings = _read_company_technical_data(db, company_id=provider_company_id)
    record = _get_or_create_company_technical_data(db, company_id=provider_company_id, create_if_missing=True)
    return SimpleNamespace(
        company_legal_name=settings.legal_name,
        company_trade_name=settings.trade_name,
        company_cnpj=settings.cnpj,
        company_address=settings.address,
        company_phone=settings.phone,
        technical_responsible_name=settings.technical_responsible_name,
        technical_responsible_registry=settings.technical_responsible_registry,
        technical_registry_type=settings.technical_registry_type,
        technical_registry_number=settings.technical_registry_number,
        technical_registry_state=settings.technical_registry_state,
        sanitary_license_number=settings.sanitary_license_number,
        sanitary_license_expiry=settings.sanitary_license_expiry,
        environmental_license_number=settings.environmental_license_number,
        environmental_license_expiry=settings.environmental_license_expiry,
        toxicology_center_name=settings.toxicology_center_name,
        toxicology_center_phone=settings.toxicology_center_phone,
        sanitary_license_filename=settings.sanitary_license_file.filename,
        environmental_license_filename=settings.environmental_license_file.filename,
        signature_filename=settings.technical_signature.filename,
        sanitary_license_content_type=settings.sanitary_license_file.content_type,
        environmental_license_content_type=settings.environmental_license_file.content_type,
        signature_content_type=settings.technical_signature.content_type,
        sanitary_license_data=getattr(record, "sanitary_license_data", None),
        environmental_license_data=getattr(record, "environmental_license_data", None),
        technical_signature_data=getattr(record, "signature_data", None),
    )


def get_company_technical_asset_content(
    db: Session,
    *,
    current_user: User,
    asset_kind: str,
) -> tuple[str, str, bytes]:
    record = _get_or_create_company_technical_data(db, current_user=current_user, create_if_missing=False)
    if record is None:
        raise BusinessRuleViolation("Nenhum dado tecnico institucional foi cadastrado para esta empresa.")

    asset_map = {
        "sanitary_license": (
            record.sanitary_license_filename,
            record.sanitary_license_content_type,
            record.sanitary_license_data,
        ),
        "environmental_license": (
            record.environmental_license_filename,
            record.environmental_license_content_type,
            record.environmental_license_data,
        ),
        "signature": (
            record.signature_filename,
            record.signature_content_type,
            record.signature_data,
        ),
    }
    if asset_kind not in asset_map:
        raise BusinessRuleViolation("Ativo tecnico solicitado e invalido.")
    filename, content_type, content = asset_map[asset_kind]
    if not filename or not content:
        raise BusinessRuleViolation("Nenhum arquivo foi cadastrado para este ativo tecnico.")
    return filename, content_type or "application/octet-stream", content


def save_company_technical_asset(
    db: Session,
    *,
    current_user: User,
    asset_kind: str,
    filename: str,
    content_type: str,
    content: bytes,
    signature_source: Optional[str] = None,
) -> SettingsCompanyRead:
    record = _get_or_create_company_technical_data(db, current_user=current_user, create_if_missing=True)
    _validate_company_asset(asset_kind=asset_kind, filename=filename, content_type=content_type, content=content)
    normalized_filename = _normalize_uploaded_filename(filename, fallback=_asset_fallback_filename(asset_kind, content_type))
    normalized_type = _normalize_content_type(content_type)
    uploaded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if asset_kind == "sanitary_license":
        record.sanitary_license_filename = normalized_filename
        record.sanitary_license_content_type = normalized_type
        record.sanitary_license_data = content
        record.sanitary_license_uploaded_at = uploaded_at
    elif asset_kind == "environmental_license":
        record.environmental_license_filename = normalized_filename
        record.environmental_license_content_type = normalized_type
        record.environmental_license_data = content
        record.environmental_license_uploaded_at = uploaded_at
    elif asset_kind == "signature":
        record.signature_filename = normalized_filename
        record.signature_content_type = normalized_type
        record.signature_data = content
        record.signature_uploaded_at = uploaded_at
        record.signature_source = signature_source or "upload"
    else:
        raise BusinessRuleViolation("Tipo de ativo tecnico invalido.")

    if normalized_type == "application/pdf":
        extracted_fields = _extract_regulatory_fields_from_pdf(content)
        _apply_extracted_regulatory_fields(record, extracted_fields, asset_kind=asset_kind)

    db.add(record)
    db.commit()
    return _read_company_technical_data(db, current_user)


def save_company_signature_from_data_url(
    db: Session,
    *,
    current_user: User,
    data_url: str,
) -> SettingsCompanyRead:
    if not str(data_url or "").startswith("data:image/png;base64,"):
        raise BusinessRuleViolation("A assinatura desenhada deve ser enviada como imagem PNG valida.")
    try:
        content = base64.b64decode(data_url.split(",", 1)[1], validate=True)
    except (ValueError, IndexError) as exc:
        raise BusinessRuleViolation("Nao foi possivel processar a assinatura desenhada.") from exc
    return save_company_technical_asset(
        db,
        current_user=current_user,
        asset_kind="signature",
        filename="assinatura-desenhada.png",
        content_type="image/png",
        content=content,
        signature_source="drawn",
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


def _read_company_technical_data(
    db: Session,
    current_user: Optional[User] = None,
    company_id: Optional[int] = None,
) -> SettingsCompanyRead:
    settings = get_settings()
    record = _get_or_create_company_technical_data(
        db,
        current_user=current_user,
        company_id=company_id,
        create_if_missing=True,
    )
    registry = _compose_registry_label(
        record.technical_registry_type,
        record.technical_registry_number,
        record.technical_registry_state,
    )
    return SettingsCompanyRead(
        legal_name=record.legal_name or settings.company_legal_name,
        trade_name=record.trade_name or record.legal_name or settings.company_trade_name,
        cnpj=_clean_optional_setting_text(record.cnpj or settings.company_cnpj),
        address=record.address or settings.company_address,
        phone=_clean_optional_setting_text(record.phone or settings.company_phone),
        technical_responsible_name=record.technical_responsible_name or settings.technical_responsible_name,
        technical_registry_type=record.technical_registry_type or "CRBio",
        technical_registry_number=record.technical_registry_number or "",
        technical_registry_state=record.technical_registry_state or "SP",
        technical_responsible_registry=registry,
        sanitary_license_number=record.sanitary_license_number or settings.sanitary_license_number,
        sanitary_license_expiry=_clean_optional_setting_text(record.sanitary_license_expiry or settings.sanitary_license_expiry),
        environmental_license_number=record.environmental_license_number or settings.environmental_license_number,
        environmental_license_expiry=_clean_optional_setting_text(
            record.environmental_license_expiry or settings.environmental_license_expiry
        ),
        toxicology_center_name=record.toxicology_center_name or "Centro de Informacao Toxicologica",
        toxicology_center_phone=record.toxicology_center_phone or settings.toxicology_center_phone,
        sanitary_license_file=_build_asset_read(
            record.sanitary_license_filename,
            record.sanitary_license_content_type,
            record.sanitary_license_data,
            record.sanitary_license_uploaded_at,
        ),
        environmental_license_file=_build_asset_read(
            record.environmental_license_filename,
            record.environmental_license_content_type,
            record.environmental_license_data,
            record.environmental_license_uploaded_at,
        ),
        technical_signature=_build_asset_read(
            record.signature_filename,
            record.signature_content_type,
            record.signature_data,
            record.signature_uploaded_at,
        ),
    )


def _update_company_technical_data(db: Session, payload, current_user: User) -> None:
    record = _get_or_create_company_technical_data(db, current_user=current_user, create_if_missing=True)
    registry_type, registry_number, registry_state = _normalize_registry_payload(payload)
    updates = {
        "legal_name": payload.legal_name,
        "trade_name": payload.trade_name,
        "cnpj": payload.cnpj,
        "address": payload.address,
        "phone": payload.phone,
        "technical_responsible_name": payload.technical_responsible_name,
        "technical_registry_type": registry_type,
        "technical_registry_number": registry_number,
        "technical_registry_state": registry_state,
        "sanitary_license_number": payload.sanitary_license_number,
        "sanitary_license_expiry": payload.sanitary_license_expiry,
        "environmental_license_number": payload.environmental_license_number,
        "environmental_license_expiry": payload.environmental_license_expiry,
        "toxicology_center_name": payload.toxicology_center_name,
        "toxicology_center_phone": payload.toxicology_center_phone,
    }
    for field_name, raw_value in updates.items():
        if raw_value is None:
            continue
        setattr(record, field_name, str(raw_value).strip())

    for field_name in (
        "legal_name",
        "trade_name",
        "address",
        "technical_responsible_name",
        "technical_registry_type",
        "technical_registry_number",
        "technical_registry_state",
        "sanitary_license_number",
        "environmental_license_number",
        "toxicology_center_name",
        "toxicology_center_phone",
    ):
        if not str(getattr(record, field_name, "") or "").strip():
            raise BusinessRuleViolation("Os dados tecnicos obrigatorios da empresa nao podem ficar vazios.")

    record.technical_registry_state = record.technical_registry_state.upper()
    db.add(record)


def _get_or_create_company_technical_data(
    db: Session,
    *,
    current_user: Optional[User] = None,
    company_id: Optional[int] = None,
    create_if_missing: bool,
) -> Optional[CompanyTechnicalData]:
    target_company_id = company_id or getattr(current_user, "empresa_prestadora_id", None)
    if target_company_id is None:
        company = db.query(ProviderCompany).order_by(ProviderCompany.id.asc()).first()
        target_company_id = getattr(company, "id", None)
    if target_company_id is None:
        raise BusinessRuleViolation("Cadastre uma empresa prestadora antes de configurar os dados tecnicos institucionais.")

    record = db.query(CompanyTechnicalData).filter(CompanyTechnicalData.empresa_prestadora_id == target_company_id).first()
    if record or not create_if_missing:
        return record

    settings = get_settings()
    record = CompanyTechnicalData(
        empresa_prestadora_id=target_company_id,
        legal_name=settings.company_legal_name,
        trade_name=settings.company_trade_name or settings.company_legal_name,
        cnpj=settings.company_cnpj,
        address=settings.company_address,
        phone=settings.company_phone,
        technical_responsible_name=settings.technical_responsible_name,
        technical_registry_type=_infer_registry_type(settings.technical_responsible_registry),
        technical_registry_number=_infer_registry_number(settings.technical_responsible_registry),
        technical_registry_state="SP",
        sanitary_license_number=settings.sanitary_license_number,
        sanitary_license_expiry=settings.sanitary_license_expiry,
        environmental_license_number=settings.environmental_license_number,
        environmental_license_expiry=settings.environmental_license_expiry,
        toxicology_center_name="Centro de Informacao Toxicologica",
        toxicology_center_phone=settings.toxicology_center_phone,
    )
    db.add(record)
    db.flush()
    return record


def _normalize_registry_payload(payload) -> tuple[Optional[str], Optional[str], Optional[str]]:
    registry_type = payload.technical_registry_type
    registry_number = payload.technical_registry_number
    registry_state = payload.technical_registry_state
    combined = str(payload.technical_responsible_registry or "").strip()
    if combined and (not registry_type or not registry_number):
        registry_type = registry_type or _infer_registry_type(combined)
        registry_number = registry_number or _infer_registry_number(combined)
    if registry_state:
        registry_state = str(registry_state).strip().upper()
    return registry_type, registry_number, registry_state


def _infer_registry_type(registry_label: Optional[str]) -> str:
    parts = str(registry_label or "").strip().split()
    return parts[0] if parts else "CRBio"


def _infer_registry_number(registry_label: Optional[str]) -> str:
    parts = str(registry_label or "").strip().split(maxsplit=1)
    if len(parts) <= 1:
        return ""
    number = parts[1].strip()
    if "/" in number:
        number = number.split("/", 1)[0].strip()
    return number


def _infer_registry_state(registry_label: Optional[str]) -> Optional[str]:
    match = re.search(r"/\s*([A-Za-z]{2})\b", str(registry_label or ""))
    if match:
        return match.group(1).upper()
    return None


def _compose_registry_label(registry_type: Optional[str], registry_number: Optional[str], registry_state: Optional[str]) -> str:
    parts = [str(registry_type or "").strip(), str(registry_number or "").strip()]
    if registry_state:
        parts.append(str(registry_state or "").strip().upper())
    return " / ".join(part for part in [f"{parts[0]} {parts[1]}".strip(), parts[2] if len(parts) > 2 else ""] if part).strip()


def _build_asset_read(filename: Optional[str], content_type: Optional[str], content: Optional[bytes], uploaded_at: Optional[datetime]):
    return {
        "has_file": bool(filename and content),
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(content) if content else None,
        "uploaded_at": uploaded_at.isoformat() if uploaded_at else None,
    }


def _validate_company_asset(*, asset_kind: str, filename: str, content_type: str, content: bytes) -> None:
    if not content:
        raise BusinessRuleViolation("Selecione um arquivo valido antes de salvar.")
    normalized_type = _normalize_content_type(content_type)
    extension = (filename or "").lower().rsplit(".", 1)[-1] if "." in (filename or "") else ""
    allowed_types = {
        "sanitary_license": {"application/pdf", "image/png", "image/jpeg", "image/jpg"},
        "environmental_license": {"application/pdf", "image/png", "image/jpeg", "image/jpg"},
        "signature": {"image/png", "image/jpeg", "image/jpg"},
    }
    max_size = 4 * 1024 * 1024 if asset_kind != "signature" else 2 * 1024 * 1024
    if normalized_type not in allowed_types.get(asset_kind, set()):
        raise BusinessRuleViolation("Formato de arquivo nao permitido para este ativo tecnico.")
    if len(content) > max_size:
        raise BusinessRuleViolation("O arquivo excede o limite permitido para upload.")
    if asset_kind == "signature" and extension not in {"png", "jpg", "jpeg"}:
        raise BusinessRuleViolation("A assinatura deve ser enviada em PNG ou JPG.")


def _normalize_uploaded_filename(filename: str, fallback: str) -> str:
    cleaned = "".join(ch for ch in str(filename or "").strip() if ch.isalnum() or ch in {".", "-", "_"})
    return cleaned or fallback


def _asset_fallback_filename(asset_kind: str, content_type: str) -> str:
    extension_map = {
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
    }
    return f"{asset_kind}{extension_map.get(_normalize_content_type(content_type), '.bin')}"


def _normalize_content_type(content_type: Optional[str]) -> str:
    return str(content_type or "application/octet-stream").strip().lower()


def _extract_regulatory_fields_from_pdf(content: bytes) -> dict[str, str]:
    try:
        reader = PdfReader(BytesIO(content))
    except Exception:
        LOGGER.warning("technical_pdf_parse_failed")
        return {}

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            continue
    raw_text = "\n".join(pages_text)
    if not raw_text.strip():
        return {}

    cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines() if line.strip()]
    searchable_lines = [(_normalize_pdf_search_text(line), line) for line in cleaned_lines]
    searchable_text = "\n".join(normalized for normalized, _ in searchable_lines)

    extracted: dict[str, str] = {}
    extracted_name = _extract_pdf_line_value(
        searchable_lines,
        [
            r"responsavel tecnico\s*[:\-]\s*(.+)",
            r"resp\.?\s*tecnico\s*[:\-]\s*(.+)",
        ],
    )
    if extracted_name:
        extracted["technical_responsible_name"] = extracted_name

    registry_label = _extract_pdf_line_value(
        searchable_lines,
        [
            r"registro profissional\s*[:\-]\s*(.+)",
            r"conselho profissional\s*[:\-]\s*(.+)",
            r"registro\s*[:\-]\s*(.+)",
            r"(crbio|crea|crq|crm|crmv|cro)\s*(?:n[o0.\-]*\s*)?[:\-]?\s*([a-z0-9./-]+(?:\s*/\s*[a-z]{2})?)",
        ],
    )
    if registry_label:
        extracted["technical_registry_raw"] = registry_label

    address = _extract_pdf_line_value(
        searchable_lines,
        [
            r"endereco(?: da empresa)?\s*[:\-]\s*(.+)",
            r"endereco completo\s*[:\-]\s*(.+)",
        ],
    )
    if address:
        extracted["address"] = address

    company_name = _extract_pdf_line_value(
        searchable_lines,
        [
            r"razao social\s*[:\-]\s*(.+)",
            r"empresa\s*[:\-]\s*(.+)",
        ],
    )
    if company_name:
        extracted["legal_name"] = company_name

    cnpj = _extract_pdf_inline_value(raw_text, [r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"])
    if cnpj:
        extracted["cnpj"] = cnpj

    sanitary_number = _extract_pdf_line_value(
        searchable_lines,
        [
            r"licenca sanitaria\s*(?:n[o0.\-]*\s*)?[:\-]\s*([a-z0-9./-]+)",
            r"alvara sanitario\s*[:\-]\s*([a-z0-9./-]+)",
            r"numero da licenca\s*[:\-]\s*([a-z0-9./-]+)",
        ],
    )
    if sanitary_number:
        extracted["sanitary_license_number"] = sanitary_number.upper()

    environmental_number = _extract_pdf_line_value(
        searchable_lines,
        [
            r"licenca ambiental\s*(?:n[o0.\-]*\s*)?[:\-]\s*([a-z0-9./-]+)",
            r"licenca de operacao\s*[:\-]\s*([a-z0-9./-]+)",
            r"numero da licenca ambiental\s*[:\-]\s*([a-z0-9./-]+)",
            r"numero da licenca\s*[:\-]\s*([a-z0-9./-]+)",
        ],
    )
    if environmental_number:
        extracted["environmental_license_number"] = environmental_number.upper()

    cit_name = _extract_pdf_line_value(
        searchable_lines,
        [
            r"(centro de informacao toxicologica)\s*[:\-]?\s*(?:telefone|fone|contato)?",
            r"(ceatox[^\n:]*)\s*[:\-]?\s*(?:telefone|fone|contato)?",
        ],
    )
    if cit_name:
        extracted["toxicology_center_name"] = cit_name

    cit_phone = _extract_pdf_line_value(
        searchable_lines,
        [
            r"centro de informacao toxicologica\s*[:\-]?\s*(.+)",
            r"\bcit\s*[:\-]\s*(.+)",
            r"telefone cit\s*[:\-]\s*(.+)",
            r"ceatox[^\n:]*\s*[:\-]\s*(.+)",
        ],
    )
    phone_match = _extract_pdf_inline_value(
        cit_phone or raw_text or searchable_text,
        [
            r"0800[\s\-]?\d{3}[\s\-]?\d{4}",
            r"\(?\d{2}\)?\s?\d{4,5}[\s\-]?\d{4}",
        ],
    )
    if phone_match:
        extracted["toxicology_center_phone"] = phone_match

    return extracted


def _normalize_pdf_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value).strip().lower()


def _extract_pdf_line_value(lines: list[tuple[str, str]], patterns: list[str]) -> Optional[str]:
    for pattern in patterns:
        compiled = re.compile(pattern, flags=re.IGNORECASE)
        for normalized_line, original_line in lines:
            match = compiled.search(normalized_line)
            if not match:
                continue
            groups = [group for group in match.groups() if group]
            value = " ".join(groups).strip() if groups else original_line.strip()
            if not value:
                continue
            if ":" in original_line:
                right = original_line.split(":", 1)[1].strip()
                if right:
                    return right
            if " - " in original_line:
                right = original_line.split(" - ", 1)[1].strip()
                if right:
                    return right
            return value
    return None


def _extract_pdf_inline_value(text: str, patterns: list[str]) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _apply_extracted_regulatory_fields(record: CompanyTechnicalData, extracted_fields: dict[str, str], *, asset_kind: str) -> None:
    if not extracted_fields:
        return

    field_map = {
        "technical_responsible_name": "technical_responsible_name",
        "address": "address",
        "legal_name": "legal_name",
        "cnpj": "cnpj",
        "toxicology_center_name": "toxicology_center_name",
        "toxicology_center_phone": "toxicology_center_phone",
    }
    for source_key, target_attr in field_map.items():
        value = extracted_fields.get(source_key)
        if value:
            setattr(record, target_attr, value)

    registry_label = extracted_fields.get("technical_registry_raw")
    if registry_label:
        record.technical_registry_type = _infer_registry_type(registry_label)
        record.technical_registry_number = _infer_registry_number(registry_label)
        inferred_state = _infer_registry_state(registry_label)
        if inferred_state:
            record.technical_registry_state = inferred_state

    if asset_kind == "sanitary_license" and extracted_fields.get("sanitary_license_number"):
        record.sanitary_license_number = extracted_fields["sanitary_license_number"]
    if asset_kind == "environmental_license" and extracted_fields.get("environmental_license_number"):
        record.environmental_license_number = extracted_fields["environmental_license_number"]
