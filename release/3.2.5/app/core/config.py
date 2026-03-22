from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SysPragas API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./syspragas.db"
    jwt_secret: str = "<SECRET>"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    default_admin_username: str = "admin"
    default_admin_password: str = "syspragas123"
    default_admin_name: str = "Administrador"
    company_name: str = "SysPragas"
    company_legal_name: str = "SysPragas Servicos de Controle de Pragas"
    company_trade_name: str = "SysPragas"
    company_address: str = "Endereco da empresa nao configurado"
    company_phone: str = "Telefone da empresa nao configurado"
    company_logo_path: Optional[str] = None
    sanitary_license_number: str = "Licenca sanitaria nao configurada"
    sanitary_license_expiry: str = "Validade nao configurada"
    environmental_license_number: str = "Licenca ambiental nao configurada"
    environmental_license_expiry: str = "Validade nao configurada"
    toxicology_center_phone: str = "0800 nao configurado"
    technical_responsible_name: str = "Responsavel tecnico nao configurado"
    technical_responsible_registry: str = "Registro profissional nao configurado"
    company_cnpj: Optional[str] = None
    company_timezone: str = "America/Sao_Paulo"
    google_calendar_enabled: bool = False
    google_calendar_id: Optional[str] = None
    google_calendar_access_token: Optional[str] = None
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None
    google_oauth_redirect_uri: Optional[str] = None
    google_oauth_scopes: str = "https://www.googleapis.com/auth/calendar.events openid email profile"
    ncm_external_source_url: Optional[str] = None
    ncm_external_source_token: Optional[str] = None
    focus_nfe_api_base_url: Optional[str] = None
    focus_nfe_api_key: Optional[str] = None
    focus_nfe_environment: str = "homologacao"
    focus_nfe_timeout_seconds: float = 30.0
    focus_nfe_webhook_secret: Optional[str] = None
    nfe_provider: str = "focus_nfe"
    sefaz_nfe_uf: Optional[str] = None
    sefaz_nfe_serie: int = 1
    sefaz_nfe_certificate_path: Optional[str] = None
    sefaz_nfe_certificate_password: Optional[str] = None
    sefaz_nfe_xsd_dir: Optional[str] = None
    sefaz_nfe_ws_urls_json: Optional[str] = None
    sefaz_nfe_verify_tls: bool = True
    company_ie: Optional[str] = None
    company_im: Optional[str] = None
    company_cnae: Optional[str] = None
    company_crt: str = "1"
    company_street: Optional[str] = None
    company_number: Optional[str] = None
    company_district: Optional[str] = None
    company_city: Optional[str] = None
    company_city_code: Optional[str] = None
    company_state: Optional[str] = None
    company_state_code: Optional[str] = None
    company_zip_code: Optional[str] = None
    simples_nacional_default_aliquota: float = 6.0
    simples_nacional_default_anexo: str = "III"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
