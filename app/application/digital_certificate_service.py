from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID, ObjectIdentifier
from sqlalchemy.orm import Session

from app.application.schemas import (
    DigitalCertificateAddressRead,
    DigitalCertificateCompanyRead,
    DigitalCertificateInfoRead,
    DigitalCertificateValidationRead,
)
from app.application.settings_service import _get_or_create_company_technical_data, _get_settings_cipher
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.models import (
    DigitalCertificate,
    DigitalCertificateAudit,
    ProviderCompany,
    User,
)

LOGGER = logging.getLogger(__name__)

ALLOWED_CERTIFICATE_EXTENSIONS = {".pfx", ".p12"}
MAX_CERTIFICATE_SIZE_BYTES = 8 * 1024 * 1024
ICP_BRASIL_CNPJ_OID = ObjectIdentifier("2.16.76.1.3.3")
ICP_BRASIL_IE_OID = ObjectIdentifier("2.16.76.1.3.4")


@dataclass(frozen=True)
class LoadedCertificate:
    private_key: Any
    certificate: x509.Certificate
    additional_certificates: list[x509.Certificate]
    encrypted_file_data: bytes
    encrypted_password: str
    file_sha256: str
    info: DigitalCertificateInfoRead


def get_digital_certificate(db: Session, current_user: User) -> DigitalCertificateInfoRead:
    record = _get_company_certificate(db, current_user)
    if record is None:
        return DigitalCertificateInfoRead()
    return _certificate_record_to_read(record)


def validate_digital_certificate_upload(
    *,
    filename: str,
    content: bytes,
    password: str,
) -> DigitalCertificateValidationRead:
    loaded = _load_certificate_from_upload(filename=filename, content=content, password=password)
    valid = loaded.info.status == "valid"
    message = "Certificado validado com sucesso." if valid else "Certificado lido com alertas."
    return DigitalCertificateValidationRead(valid=valid, message=message, certificate=loaded.info)


def save_digital_certificate(
    db: Session,
    *,
    current_user: User,
    filename: str,
    content_type: str,
    content: bytes,
    password: str,
    apply_company_data: bool = False,
) -> DigitalCertificateInfoRead:
    target_company_id = _resolve_company_id(db, current_user)
    loaded = _load_certificate_from_upload(filename=filename, content=content, password=password)
    now = _utc_now()
    record = db.query(DigitalCertificate).filter(DigitalCertificate.empresa_prestadora_id == target_company_id).first()
    action = "created" if record is None else "replaced"
    if record is None:
        record = DigitalCertificate(empresa_prestadora_id=target_company_id)
        db.add(record)

    _apply_loaded_certificate_to_record(
        record,
        loaded=loaded,
        filename=_clean_filename(filename),
        content_type=content_type or "application/x-pkcs12",
        current_user=current_user,
        now=now,
    )
    db.flush()
    _record_audit(
        db,
        certificate=record,
        current_user=current_user,
        action=action,
        status="success",
        detail=f"Certificado {record.thumbprint or record.serial_number or 'sem thumbprint'} salvo.",
    )
    if apply_company_data:
        apply_certificate_company_data(db, current_user=current_user, commit=False)
    db.commit()
    db.refresh(record)
    LOGGER.info(
        "digital_certificate_saved",
        extra={"company_id": target_company_id, "certificate_id": record.id, "action": action},
    )
    return _certificate_record_to_read(record)


def test_stored_digital_certificate(db: Session, current_user: User) -> DigitalCertificateValidationRead:
    record = _require_company_certificate(db, current_user)
    try:
        loaded = _load_certificate_from_bytes(
            filename=record.filename,
            content=_decrypt_bytes(record.encrypted_file_data),
            password=_decrypt_text(record.encrypted_password),
        )
    except BusinessRuleViolation as exc:
        record.status = "invalid"
        record.last_validation_status = "invalid"
        record.last_validation_error = exc.message
        record.last_validated_at = _utc_now()
        _record_audit(db, certificate=record, current_user=current_user, action="tested", status="failed", detail=exc.message)
        db.commit()
        return DigitalCertificateValidationRead(valid=False, message=exc.message, certificate=_certificate_record_to_read(record))

    now = _utc_now()
    record.status = loaded.info.status
    record.last_validation_status = loaded.info.status
    record.last_validation_error = "; ".join(loaded.info.errors) if loaded.info.errors else None
    record.last_validated_at = now
    _record_audit(
        db,
        certificate=record,
        current_user=current_user,
        action="tested",
        status="success" if loaded.info.status == "valid" else "warning",
        detail="Certificado testado com sucesso." if loaded.info.status == "valid" else "Certificado testado com alertas.",
    )
    db.commit()
    db.refresh(record)
    return DigitalCertificateValidationRead(
        valid=loaded.info.status == "valid",
        message="Certificado central testado com sucesso." if loaded.info.status == "valid" else "Certificado central possui alertas.",
        certificate=_certificate_record_to_read(record),
    )


def remove_digital_certificate(db: Session, current_user: User) -> DigitalCertificateInfoRead:
    record = _require_company_certificate(db, current_user)
    _record_audit(
        db,
        certificate=record,
        current_user=current_user,
        action="removed",
        status="success",
        detail=f"Certificado {record.thumbprint or record.serial_number or record.id} removido.",
    )
    db.delete(record)
    db.commit()
    return DigitalCertificateInfoRead()


def apply_certificate_company_data(
    db: Session,
    *,
    current_user: User,
    commit: bool = True,
) -> DigitalCertificateInfoRead:
    record = _require_company_certificate(db, current_user)
    info = _certificate_record_to_read(record)
    company = info.company
    address = info.address
    technical = _get_or_create_company_technical_data(db, current_user=current_user, create_if_missing=True)
    provider = db.query(ProviderCompany).filter(ProviderCompany.id == record.empresa_prestadora_id).first()

    if company.legal_name:
        technical.legal_name = company.legal_name
        if provider:
            provider.razao_social = company.legal_name
    if company.trade_name:
        technical.trade_name = company.trade_name
        if provider:
            provider.nome_fantasia = company.trade_name
    if company.cnpj:
        technical.cnpj = company.cnpj
        if provider:
            provider.cnpj = _digits_only(company.cnpj) or company.cnpj
    composed_address = _compose_address(address)
    if composed_address:
        technical.address = composed_address
        if provider:
            provider.endereco = composed_address
            provider.bairro = address.district or provider.bairro
            provider.cidade = address.city or provider.cidade
            provider.estado = (address.state or provider.estado or "").upper()[:2] or provider.estado
            provider.cep = address.zip_code or provider.cep

    _record_audit(
        db,
        certificate=record,
        current_user=current_user,
        action="company_applied",
        status="success",
        detail="Dados disponiveis no certificado aplicados ao cadastro da empresa.",
    )
    if commit:
        db.commit()
    return info


def load_central_certificate_material(db: Session) -> Optional[tuple[bytes, bytes]]:
    record = db.query(DigitalCertificate).order_by(DigitalCertificate.updated_at.desc(), DigitalCertificate.id.desc()).first()
    if record is None:
        return None
    try:
        loaded = _load_certificate_from_bytes(
            filename=record.filename,
            content=_decrypt_bytes(record.encrypted_file_data),
            password=_decrypt_text(record.encrypted_password),
            encrypt_payload=False,
        )
    except BusinessRuleViolation as exc:
        record.status = "invalid"
        record.last_validation_status = "invalid"
        record.last_validation_error = exc.message
        record.last_validated_at = _utc_now()
        db.commit()
        raise

    key_pem = loaded.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_pem = loaded.certificate.public_bytes(serialization.Encoding.PEM)
    record.last_used_at = _utc_now()
    record.last_validation_status = loaded.info.status
    record.last_validation_error = "; ".join(loaded.info.errors) if loaded.info.errors else None
    db.commit()
    return key_pem, cert_pem


def has_central_digital_certificate(db: Session) -> bool:
    return db.query(DigitalCertificate.id).first() is not None


def _load_certificate_from_upload(*, filename: str, content: bytes, password: str) -> LoadedCertificate:
    _validate_upload(filename, content, password)
    return _load_certificate_from_bytes(filename=filename, content=content, password=password)


def _load_certificate_from_bytes(
    *,
    filename: str,
    content: bytes,
    password: str,
    encrypt_payload: bool = True,
) -> LoadedCertificate:
    try:
        private_key, certificate, additional = pkcs12.load_key_and_certificates(
            content,
            password.encode("utf-8"),
        )
    except Exception as exc:
        raise BusinessRuleViolation("Nao foi possivel abrir o certificado. Verifique arquivo e senha.") from exc

    if private_key is None or certificate is None:
        raise BusinessRuleViolation("O certificado A1 nao contem chave privada utilizavel.")

    info = _build_certificate_info(filename, certificate, list(additional or []))
    return LoadedCertificate(
        private_key=private_key,
        certificate=certificate,
        additional_certificates=list(additional or []),
        encrypted_file_data=_encrypt_bytes(content) if encrypt_payload else b"",
        encrypted_password=_encrypt_text(password) if encrypt_payload else "",
        file_sha256=hashlib.sha256(content).hexdigest(),
        info=info,
    )


def _build_certificate_info(
    filename: str,
    certificate: x509.Certificate,
    additional_certificates: list[x509.Certificate],
) -> DigitalCertificateInfoRead:
    now = datetime.now(timezone.utc)
    valid_from = _cert_datetime(certificate, "not_valid_before_utc", "not_valid_before")
    valid_to = _cert_datetime(certificate, "not_valid_after_utc", "not_valid_after")
    days = (valid_to.date() - now.date()).days if valid_to else None
    errors: list[str] = []
    alerts: list[str] = []
    if valid_from and now < valid_from:
        errors.append("Certificado ainda nao esta dentro do periodo de validade.")
    if valid_to and now > valid_to:
        errors.append("Certificado vencido.")
    if days is not None:
        if days < 0:
            alerts.append("Certificado vencido.")
        elif days <= 7:
            alerts.append("Certificado vence em ate 7 dias.")
        elif days <= 15:
            alerts.append("Certificado vence em ate 15 dias.")
        elif days <= 30:
            alerts.append("Certificado vence em ate 30 dias.")
        elif days <= 60:
            alerts.append("Certificado vence em ate 60 dias.")
    chain_status = "present" if additional_certificates else "not_provided"
    if not additional_certificates:
        alerts.append("Cadeia intermediaria nao esta embutida no arquivo PFX/P12.")

    company = _extract_company_info(certificate)
    status = "valid" if not errors else "invalid"
    return DigitalCertificateInfoRead(
        configured=True,
        status=status,
        certificate_type="A1",
        filename=_clean_filename(filename),
        serial_number=format(certificate.serial_number, "x").upper(),
        authority=_name_attr(certificate.issuer, NameOID.COMMON_NAME) or _name_attr(certificate.issuer, NameOID.ORGANIZATION_NAME),
        issuer=_name_to_text(certificate.issuer),
        subject=_name_to_text(certificate.subject),
        valid_from=_as_naive_utc(valid_from),
        valid_to=_as_naive_utc(valid_to),
        days_until_expiration=days,
        thumbprint=certificate.fingerprint(hashes.SHA1()).hex().upper(),
        signature_algorithm=getattr(certificate.signature_hash_algorithm, "name", None),
        chain_status=chain_status,
        company=company,
        address=_extract_address_info(certificate),
        alerts=alerts,
        errors=errors,
    )


def _apply_loaded_certificate_to_record(
    record: DigitalCertificate,
    *,
    loaded: LoadedCertificate,
    filename: str,
    content_type: str,
    current_user: User,
    now: datetime,
) -> None:
    info = loaded.info
    record.filename = filename
    record.content_type = content_type
    record.encrypted_file_data = loaded.encrypted_file_data
    record.encrypted_password = loaded.encrypted_password
    record.file_sha256 = loaded.file_sha256
    record.certificate_type = info.certificate_type or "A1"
    record.serial_number = info.serial_number
    record.thumbprint = info.thumbprint
    record.subject = info.subject
    record.issuer = info.issuer
    record.authority = info.authority
    record.signature_algorithm = info.signature_algorithm
    record.valid_from = info.valid_from
    record.valid_to = info.valid_to
    record.company_info_json = json.dumps(info.company.model_dump(), ensure_ascii=True)
    record.address_info_json = json.dumps(info.address.model_dump(), ensure_ascii=True)
    record.chain_status = info.chain_status
    record.status = info.status
    record.last_validation_status = info.status
    record.last_validation_error = "; ".join(info.errors) if info.errors else None
    record.last_validated_at = now
    record.updated_by_user_id = current_user.id


def _certificate_record_to_read(record: DigitalCertificate) -> DigitalCertificateInfoRead:
    company = DigitalCertificateCompanyRead(**_json_dict(record.company_info_json))
    address = DigitalCertificateAddressRead(**_json_dict(record.address_info_json))
    days = (record.valid_to.date() - _utc_now().date()).days if record.valid_to else None
    alerts = _expiration_alerts(days)
    if record.chain_status == "not_provided":
        alerts.append("Cadeia intermediaria nao esta embutida no arquivo PFX/P12.")
    errors = [record.last_validation_error] if record.last_validation_error else []
    return DigitalCertificateInfoRead(
        configured=True,
        status=record.status,
        certificate_type=record.certificate_type,
        filename=record.filename,
        serial_number=record.serial_number,
        authority=record.authority,
        issuer=record.issuer,
        subject=record.subject,
        valid_from=record.valid_from,
        valid_to=record.valid_to,
        days_until_expiration=days,
        thumbprint=record.thumbprint,
        signature_algorithm=record.signature_algorithm,
        chain_status=record.chain_status,
        company=company,
        address=address,
        last_used_at=record.last_used_at,
        last_validated_at=record.last_validated_at,
        alerts=alerts,
        errors=errors,
    )


def _expiration_alerts(days: Optional[int]) -> list[str]:
    if days is None:
        return []
    if days < 0:
        return ["Certificado vencido."]
    for threshold in (7, 15, 30, 60):
        if days <= threshold:
            return [f"Certificado vence em ate {threshold} dias."]
    return []


def _extract_company_info(certificate: x509.Certificate) -> DigitalCertificateCompanyRead:
    subject = certificate.subject
    cn = _name_attr(subject, NameOID.COMMON_NAME)
    organization = _name_attr(subject, NameOID.ORGANIZATION_NAME)
    cnpj = _name_attr(subject, ICP_BRASIL_CNPJ_OID) or _find_cnpj(_name_to_text(subject))
    legal_name = organization or _strip_identifier_from_name(cn)
    return DigitalCertificateCompanyRead(
        legal_name=legal_name,
        trade_name=_name_attr(subject, NameOID.ORGANIZATIONAL_UNIT_NAME),
        cnpj=cnpj,
        state_registration=_name_attr(subject, ICP_BRASIL_IE_OID),
        municipal_registration=None,
    )


def _extract_address_info(certificate: x509.Certificate) -> DigitalCertificateAddressRead:
    subject = certificate.subject
    return DigitalCertificateAddressRead(
        street=_name_attr(subject, NameOID.STREET_ADDRESS),
        city=_name_attr(subject, NameOID.LOCALITY_NAME),
        state=_name_attr(subject, NameOID.STATE_OR_PROVINCE_NAME),
        zip_code=_name_attr(subject, NameOID.POSTAL_CODE),
    )


def _name_attr(name: x509.Name, oid: ObjectIdentifier) -> Optional[str]:
    values = [attribute.value for attribute in name.get_attributes_for_oid(oid) if str(attribute.value).strip()]
    return str(values[0]).strip() if values else None


def _name_to_text(name: x509.Name) -> str:
    return ", ".join(f"{attribute.oid._name}={attribute.value}" for attribute in name)


def _find_cnpj(value: str) -> Optional[str]:
    for match in re.finditer(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", value or ""):
        digits = _digits_only(match.group(0))
        if len(digits) == 14:
            return digits
    return None


def _strip_identifier_from_name(value: Optional[str]) -> Optional[str]:
    cleaned = str(value or "").strip()
    if not cleaned:
        return None
    if ":" in cleaned and _find_cnpj(cleaned):
        return cleaned.rsplit(":", 1)[0].strip() or cleaned
    return cleaned


def _validate_upload(filename: str, content: bytes, password: str) -> None:
    cleaned_name = _clean_filename(filename)
    suffix = "." + cleaned_name.rsplit(".", 1)[-1].lower() if "." in cleaned_name else ""
    if suffix not in ALLOWED_CERTIFICATE_EXTENSIONS:
        raise BusinessRuleViolation("Envie um certificado A1 nos formatos .pfx ou .p12.")
    if not content:
        raise BusinessRuleViolation("O arquivo do certificado esta vazio.")
    if len(content) > MAX_CERTIFICATE_SIZE_BYTES:
        raise BusinessRuleViolation("O certificado excede o tamanho maximo permitido de 8 MB.")
    if not password:
        raise BusinessRuleViolation("Informe a senha do certificado para validar o arquivo.")


def _clean_filename(filename: str) -> str:
    cleaned = str(filename or "certificado.pfx").replace("\\", "/").rsplit("/", 1)[-1].strip()
    return cleaned or "certificado.pfx"


def _encrypt_bytes(value: bytes) -> bytes:
    return _get_settings_cipher().encrypt(value)


def _decrypt_bytes(value: bytes) -> bytes:
    try:
        return _get_settings_cipher().decrypt(value)
    except Exception as exc:
        raise BusinessRuleViolation("Nao foi possivel descriptografar o certificado digital central.") from exc


def _encrypt_text(value: str) -> str:
    return _get_settings_cipher().encrypt(value.encode("utf-8")).decode("utf-8")


def _decrypt_text(value: str) -> str:
    try:
        return _get_settings_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise BusinessRuleViolation("Nao foi possivel descriptografar a senha do certificado digital central.") from exc


def _cert_datetime(certificate: x509.Certificate, utc_attr: str, fallback_attr: str) -> Optional[datetime]:
    value = getattr(certificate, utc_attr, None) or getattr(certificate, fallback_attr, None)
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _as_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _digits_only(value: Optional[str]) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _compose_address(address: DigitalCertificateAddressRead) -> Optional[str]:
    parts = [
        address.street,
        address.number,
        address.complement,
        address.district,
        address.city,
        address.state,
        address.zip_code,
    ]
    return " - ".join(str(part).strip() for part in parts if str(part or "").strip()) or None


def _json_dict(value: Optional[str]) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_company_id(db: Session, current_user: User) -> int:
    if current_user.empresa_prestadora_id:
        return current_user.empresa_prestadora_id
    company = db.query(ProviderCompany).order_by(ProviderCompany.id.asc()).first()
    if not company:
        raise BusinessRuleViolation("Cadastre uma empresa prestadora antes de configurar o certificado digital.")
    return company.id


def _get_company_certificate(db: Session, current_user: User) -> Optional[DigitalCertificate]:
    return db.query(DigitalCertificate).filter(DigitalCertificate.empresa_prestadora_id == _resolve_company_id(db, current_user)).first()


def _require_company_certificate(db: Session, current_user: User) -> DigitalCertificate:
    record = _get_company_certificate(db, current_user)
    if record is None:
        raise BusinessRuleViolation("Nenhum certificado digital central foi cadastrado para esta empresa.")
    return record


def _record_audit(
    db: Session,
    *,
    certificate: Optional[DigitalCertificate],
    current_user: Optional[User],
    action: str,
    status: str,
    detail: Optional[str] = None,
) -> None:
    db.add(
        DigitalCertificateAudit(
            certificate_id=getattr(certificate, "id", None),
            empresa_prestadora_id=getattr(certificate, "empresa_prestadora_id", None),
            user_id=getattr(current_user, "id", None),
            action=action,
            status=status,
            detail=detail,
        )
    )
