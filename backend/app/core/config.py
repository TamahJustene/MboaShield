from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
DEFAULT_SQLITE = ROOT / "storage" / "mboashield.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MboaShield"
    version: str = "0.9.0"
    environment: str = Field(default="dev", alias="MBOASHIELD_ENV")

    database_url: str = Field(default="", alias="DATABASE_URL")
    sqlite_path: str = Field(default="", alias="MBOASHIELD_DB_PATH")

    jwt_secret: str = Field(default="change-me-in-production-mboashield", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    auth_enforce: bool = Field(default=False, alias="AUTH_ENFORCE")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    trusted_hosts: str = Field(default="*", alias="TRUSTED_HOSTS")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    # OIDC / OpenID Connect readiness
    oidc_provider_id: str = Field(default="national-id", alias="OIDC_PROVIDER_ID")
    oidc_provider_name: str = Field(default="National Identity Provider", alias="OIDC_PROVIDER_NAME")
    oidc_issuer: str = Field(default="", alias="OIDC_ISSUER")
    oidc_client_id: str = Field(default="", alias="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(default="", alias="OIDC_CLIENT_SECRET")
    oidc_scopes: str = Field(default="openid profile email", alias="OIDC_SCOPES")
    oidc_redirect_uri: str = Field(default="http://127.0.0.1:8000/api/v1/auth/oidc/national-id/callback", alias="OIDC_REDIRECT_URI")

    # MFA policy
    mfa_required_roles: str = Field(default="admin", alias="MFA_REQUIRED_ROLES")

    def resolved_database_url(self) -> str:
        if self.database_url.strip():
            return self.database_url.strip()
        path = Path(self.sqlite_path) if self.sqlite_path.strip() else DEFAULT_SQLITE
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"

    def mfa_roles(self) -> set[str]:
        return {item.strip() for item in self.mfa_required_roles.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


VERSION = get_settings().version
DB_PATH = Path(get_settings().sqlite_path) if get_settings().sqlite_path else DEFAULT_SQLITE
