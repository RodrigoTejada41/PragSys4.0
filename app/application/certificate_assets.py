from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, Optional

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.infrastructure.models import Technician

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
DEFAULT_TEMPLATE_BASENAMES = (
    "certificado_moldura_oficial",
    "certificado_moldura",
    "modelo_certificado_oficial",
    "modelo_certificado",
    "modelo",
)


def _normalize_path_token(value: Optional[str]) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    return normalized.strip("_")


def _iter_candidate_names(technician: Technician) -> Iterable[str]:
    seen: set[str] = set()
    for raw_value in (
        getattr(technician, "registro", None),
        getattr(technician, "nome", None),
        getattr(technician, "id", None),
    ):
        token = _normalize_path_token(raw_value)
        if token and token not in seen:
            seen.add(token)
            yield token


def _resolve_certificate_model_path_from_dirs(
    official_dir: Path,
    legacy_dir: Optional[Path],
    model_name: Optional[str],
) -> Optional[Path]:
    candidate_names = []
    if model_name:
        candidate_names.append(Path(model_name).stem)
    candidate_names.extend(DEFAULT_TEMPLATE_BASENAMES)

    for base_name in candidate_names:
        for extension in SUPPORTED_IMAGE_EXTENSIONS:
            candidate = official_dir / f"{base_name}{extension}"
            if candidate.exists():
                return candidate

    if legacy_dir:
        for base_name in candidate_names:
            for extension in SUPPORTED_IMAGE_EXTENSIONS:
                candidate = legacy_dir / f"{base_name}{extension}"
                if candidate.exists():
                    logger.warning("Using legacy certificate model path: %s", candidate)
                    return candidate

    return None


def _resolve_signature_path(signatures_dir: Path, candidate_name: str) -> Optional[Path]:
    for extension in SUPPORTED_IMAGE_EXTENSIONS:
        candidate = signatures_dir / f"{candidate_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def _resolve_fallback_signature_path(signatures_dir: Path) -> Optional[Path]:
    fallback_images = [path for extension in SUPPORTED_IMAGE_EXTENSIONS for path in signatures_dir.glob(f"*{extension}")]
    if len(fallback_images) == 1:
        return fallback_images[0]
    return None


def resolve_certificate_model_path(model_name: Optional[str] = None) -> Optional[Path]:
    settings = get_settings()
    official_dir = settings.certificate_models_path
    legacy_dir = settings.legacy_certificate_models_path
    resolved = _resolve_certificate_model_path_from_dirs(
        official_dir,
        legacy_dir,
        model_name,
    )
    logger.info(
        "certificate_model_path_resolved model_name=%s official_dir=%s legacy_dir=%s found=%s",
        model_name or "",
        official_dir,
        legacy_dir,
        resolved,
    )
    return resolved


def require_certificate_model_path(model_name: Optional[str] = None) -> Path:
    template_path = resolve_certificate_model_path(model_name)
    if template_path:
        return template_path
    settings = get_settings()
    raise BusinessRuleViolation(
        "Modelo oficial do certificado nao encontrado. "
        f"Configure um arquivo de template em '{settings.certificate_models_path}'."
    )


def resolve_technical_signature_path(technician: Technician) -> Optional[Path]:
    signatures_dir = get_settings().technical_signatures_path
    for candidate_name in _iter_candidate_names(technician):
        candidate = _resolve_signature_path(signatures_dir, candidate_name)
        if candidate is not None:
            logger.info(
                "technical_signature_resolved technician_id=%s candidate_name=%s path=%s",
                getattr(technician, "id", None),
                candidate_name,
                candidate,
            )
            return candidate
    fallback_image = _resolve_fallback_signature_path(signatures_dir)
    if fallback_image is not None:
        logger.warning("Using fallback technical signature for technician %s", getattr(technician, "id", "?"))
        return fallback_image
    logger.info(
        "technical_signature_missing technician_id=%s searched_dir=%s",
        getattr(technician, "id", None),
        signatures_dir,
    )
    return None


def require_technical_signature_path(technician: Technician) -> Path:
    signature_path = resolve_technical_signature_path(technician)
    if signature_path:
        return signature_path

    signatures_dir = get_settings().technical_signatures_path
    searched_names = ", ".join(f"{name}.*" for name in _iter_candidate_names(technician)) or "assinatura.*"
    raise BusinessRuleViolation(
        "Assinatura tecnica nao encontrada para o tecnico responsavel. "
        f"Adicione o arquivo em '{signatures_dir}' usando um destes nomes: {searched_names}."
    )
