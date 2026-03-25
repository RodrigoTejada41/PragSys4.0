from __future__ import annotations

import json
from typing import Any, Optional, Union
from urllib.parse import urljoin

import httpx

from app.core.config import get_settings
from app.domain.enums import NfeEnvironment


class FocusNfeApiError(Exception):
    def __init__(self, message: str, *, status_code: Optional[int] = None, payload: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


class FocusNfeClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        environment: Optional[Union[NfeEnvironment, str]] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        settings = get_settings()
        resolved_environment = self._normalize_environment(environment or settings.focus_nfe_environment)
        self.api_key = api_key or settings.focus_nfe_api_key
        self.base_url = (base_url or settings.focus_nfe_api_base_url or self._default_base_url(resolved_environment)).rstrip("/")
        self.environment = resolved_environment
        self.timeout_seconds = timeout_seconds or settings.focus_nfe_timeout_seconds

    @staticmethod
    def _normalize_environment(value: Union[NfeEnvironment, str]) -> NfeEnvironment:
        if isinstance(value, NfeEnvironment):
            return value
        return NfeEnvironment(str(value).strip().lower())

    @staticmethod
    def _default_base_url(environment: NfeEnvironment) -> str:
        if environment == NfeEnvironment.PRODUCAO:
            return "https://api.focusnfe.com.br"
        return "https://homologacao.focusnfe.com.br"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def emit_invoice(self, reference: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/v2/nfe?ref={reference}", json=payload)

    def get_invoice(self, reference: str) -> dict[str, Any]:
        return self._request("GET", f"/v2/nfe/{reference}")

    def cancel_invoice(self, reference: str, *, justification: Optional[str] = None) -> dict[str, Any]:
        body = {"justificativa": justification} if justification else None
        return self._request("DELETE", f"/v2/nfe/{reference}", json=body)

    def _request(self, method: str, path: str, *, json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if not self.is_configured():
            raise FocusNfeApiError("Integracao Focus NFe nao configurada.", status_code=None)

        request_url = f"{self.base_url}{path}"
        try:
            with httpx.Client(auth=(self.api_key or "", ""), timeout=self.timeout_seconds) as client:
                response = client.request(method, request_url, json=json)
        except httpx.TimeoutException as exc:
            raise FocusNfeApiError("Tempo limite excedido ao comunicar com a Focus NFe.") from exc
        except httpx.RequestError as exc:
            raise FocusNfeApiError("Falha de rede ao comunicar com a Focus NFe.") from exc

        payload = self._safe_json(response)
        if response.status_code >= 400:
            message = self._extract_error_message(payload) or f"Falha ao comunicar com a Focus NFe (HTTP {response.status_code})."
            raise FocusNfeApiError(message, status_code=response.status_code, payload=payload)
        if payload is None:
            raise FocusNfeApiError("A Focus NFe retornou uma resposta sem JSON valido.", status_code=response.status_code)
        return payload

    @staticmethod
    def _safe_json(response: httpx.Response) -> Optional[dict[str, Any]]:
        try:
            data = response.json()
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else {"data": data}

    @staticmethod
    def _extract_error_message(payload: Optional[dict[str, Any]]) -> Optional[str]:
        if not payload:
            return None
        return payload.get("mensagem") or payload.get("message") or payload.get("erro")

    def resolve_download_url(self, path_or_url: Optional[str]) -> Optional[str]:
        if not path_or_url:
            return None
        if str(path_or_url).startswith("http://") or str(path_or_url).startswith("https://"):
            return path_or_url
        return urljoin(f"{self.base_url}/", str(path_or_url).lstrip("/"))
