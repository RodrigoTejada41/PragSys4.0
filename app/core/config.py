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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
