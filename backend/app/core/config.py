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
    version: str = "2.4.0"
    environment: str = Field(default="dev", alias="MBOASHIELD_ENV")
    deployment_profile: str = Field(default="demo", alias="DEPLOYMENT_PROFILE")
    country_pack: str = Field(default="cm", alias="COUNTRY_PACK")
    tenant_id: str = Field(default="cm", alias="TENANT_ID")
    tenant_display_name: str = Field(default="Cameroon", alias="TENANT_DISPLAY_NAME")

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

    # NTOC / Phase 7
    ntoc_enabled: bool = Field(default=True, alias="NTOC_ENABLED")
    threat_elevated: int = Field(default=40, alias="THREAT_LEVEL_ELEVATED")
    threat_high: int = Field(default=70, alias="THREAT_LEVEL_HIGH")
    threat_critical: int = Field(default=85, alias="THREAT_LEVEL_CRITICAL")
    notification_webhook_url: str = Field(default="", alias="NOTIFICATION_WEBHOOK_URL")

    # Interoperability / T4
    interop_enabled: bool = Field(default=True, alias="INTEROP_ENABLED")
    webhook_signing_secret: str = Field(default="", alias="WEBHOOK_SIGNING_SECRET")
    webhook_max_retries: int = Field(default=3, alias="WEBHOOK_MAX_RETRIES")

    # Threat intelligence / Phase 8 (compliant sources only)
    intel_enabled: bool = Field(default=True, alias="INTEL_ENABLED")
    intel_egress_allowlist: str = Field(default="*", alias="INTEL_EGRESS_ALLOWLIST")
    intel_ingest_limit: int = Field(default=50, alias="INTEL_INGEST_LIMIT")

    # Evidence vault / Phase 9
    vault_enabled: bool = Field(default=True, alias="VAULT_ENABLED")
    vault_storage: str = Field(default="local", alias="VAULT_STORAGE")
    vault_local_path: str = Field(default="", alias="VAULT_LOCAL_PATH")
    vault_max_bytes: int = Field(default=10_485_760, alias="VAULT_MAX_BYTES")
    vault_retention_days: int = Field(default=365, alias="VAULT_RETENTION_DAYS")
    vault_signing_key: str = Field(default="", alias="VAULT_SIGNING_KEY")
    vault_s3_bucket: str = Field(default="", alias="VAULT_S3_BUCKET")
    vault_s3_region: str = Field(default="us-east-1", alias="VAULT_S3_REGION")
    vault_s3_endpoint_url: str = Field(default="", alias="VAULT_S3_ENDPOINT_URL")
    vault_s3_access_key: str = Field(default="", alias="VAULT_S3_ACCESS_KEY")
    vault_s3_secret_key: str = Field(default="", alias="VAULT_S3_SECRET_KEY")

    # Institution portal / Phase 10
    institution_portal_enabled: bool = Field(default=True, alias="INSTITUTION_PORTAL_ENABLED")

    # Verified government communications / Phase 11
    verified_comms_enabled: bool = Field(default=True, alias="VERIFIED_COMMS_ENABLED")
    announcement_signing_key: str = Field(default="", alias="ANNOUNCEMENT_SIGNING_KEY")
    announcement_signing_kid: str = Field(default="mboashield-announce-v1", alias="ANNOUNCEMENT_SIGNING_KID")
    public_base_url: str = Field(default="", alias="PUBLIC_BASE_URL")

    # Advanced AI / Phase 12
    advanced_ai_enabled: bool = Field(default=True, alias="ADVANCED_AI_ENABLED")
    ai_eval_latency_budget_ms: int = Field(default=2500, alias="AI_EVAL_LATENCY_BUDGET_MS")

    # Enterprise infrastructure / Phase 13
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    workers_enabled: bool = Field(default=False, alias="WORKERS_ENABLED")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="", alias="CELERY_RESULT_BACKEND")

    # Governance / Phase 14
    governance_enabled: bool = Field(default=True, alias="GOVERNANCE_ENABLED")

    # Password policy
    password_min_length: int = Field(default=8, alias="PASSWORD_MIN_LENGTH")
    password_require_upper: bool = Field(default=False, alias="PASSWORD_REQUIRE_UPPER")
    password_require_special: bool = Field(default=False, alias="PASSWORD_REQUIRE_SPECIAL")
    password_reset_ttl_minutes: int = Field(default=30, alias="PASSWORD_RESET_TTL_MINUTES")
    password_reset_return_token: bool = Field(default=False, alias="PASSWORD_RESET_RETURN_TOKEN")

    # MFA policy
    mfa_required_roles: str = Field(default="admin", alias="MFA_REQUIRED_ROLES")
    mfa_enforce: bool = Field(default=False, alias="MFA_ENFORCE")
    trusted_device_days: int = Field(default=30, alias="TRUSTED_DEVICE_DAYS")
    trusted_device_skip_mfa: bool = Field(default=True, alias="TRUSTED_DEVICE_SKIP_MFA")

    # OIDC / OpenID Connect
    oidc_enabled: bool = Field(default=True, alias="OIDC_ENABLED")
    oidc_provider_id: str = Field(default="national-id", alias="OIDC_PROVIDER_ID")
    oidc_provider_name: str = Field(default="National Identity Provider", alias="OIDC_PROVIDER_NAME")
    oidc_issuer: str = Field(default="", alias="OIDC_ISSUER")
    oidc_client_id: str = Field(default="", alias="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(default="", alias="OIDC_CLIENT_SECRET")
    oidc_scopes: str = Field(default="openid profile email", alias="OIDC_SCOPES")
    oidc_redirect_uri: str = Field(
        default="http://127.0.0.1:8000/api/v1/auth/oidc/national-id/callback",
        alias="OIDC_REDIRECT_URI",
    )
    oidc_token_url: str = Field(default="", alias="OIDC_TOKEN_URL")
    oidc_jwks_url: str = Field(default="", alias="OIDC_JWKS_URL")
    oidc_userinfo_url: str = Field(default="", alias="OIDC_USERINFO_URL")
    oidc_default_role: str = Field(default="citizen", alias="OIDC_DEFAULT_ROLE")

    # SAML 2.0 SP
    saml_enabled: bool = Field(default=False, alias="SAML_ENABLED")
    saml_sp_entity_id: str = Field(default="https://mboashield.local/saml/metadata", alias="SAML_SP_ENTITY_ID")
    saml_acs_url: str = Field(
        default="http://127.0.0.1:8000/api/v1/auth/saml/acs",
        alias="SAML_ACS_URL",
    )
    saml_idp_entity_id: str = Field(default="", alias="SAML_IDP_ENTITY_ID")
    saml_idp_sso_url: str = Field(default="", alias="SAML_IDP_SSO_URL")
    saml_idp_x509_cert: str = Field(default="", alias="SAML_IDP_X509_CERT")
    saml_allow_unsigned: bool = Field(default=False, alias="SAML_ALLOW_UNSIGNED")
    saml_default_role: str = Field(default="citizen", alias="SAML_DEFAULT_ROLE")

    # LDAP / Active Directory
    ldap_enabled: bool = Field(default=False, alias="LDAP_ENABLED")
    ldap_server_uri: str = Field(default="", alias="LDAP_SERVER_URI")
    ldap_use_ssl: bool = Field(default=True, alias="LDAP_USE_SSL")
    ldap_bind_dn_template: str = Field(default="", alias="LDAP_BIND_DN_TEMPLATE")
    ldap_user_search_base: str = Field(default="", alias="LDAP_USER_SEARCH_BASE")
    ldap_user_filter_template: str = Field(
        default="(|(uid={username})(sAMAccountName={username})(userPrincipalName={username}))",
        alias="LDAP_USER_FILTER_TEMPLATE",
    )
    ldap_group_attr: str = Field(default="memberOf", alias="LDAP_GROUP_ATTR")
    ldap_email_attr: str = Field(default="mail", alias="LDAP_EMAIL_ATTR")
    ldap_name_attr: str = Field(default="displayName", alias="LDAP_NAME_ATTR")
    ldap_group_role_map: str = Field(default="", alias="LDAP_GROUP_ROLE_MAP")
    ldap_default_role: str = Field(default="citizen", alias="LDAP_DEFAULT_ROLE")

    def resolved_database_url(self) -> str:
        if self.database_url.strip():
            return self.database_url.strip()
        path = Path(self.sqlite_path) if self.sqlite_path.strip() else DEFAULT_SQLITE
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"

    def mfa_roles(self) -> set[str]:
        return {item.strip() for item in self.mfa_required_roles.split(",") if item.strip()}

    def ldap_role_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for part in self.ldap_group_role_map.split(","):
            item = part.strip()
            if not item or "=" not in item:
                continue
            group, role = item.split("=", 1)
            mapping[group.strip().lower()] = role.strip()
        return mapping

    def is_government_profile(self) -> bool:
        return self.deployment_profile.strip().lower() in {"government", "gov", "national"}

    def intel_allowlist_hosts(self) -> set[str] | None:
        raw = self.intel_egress_allowlist.strip()
        if not raw or raw == "*":
            return None
        return {item.strip().lower() for item in raw.split(",") if item.strip()}

    def resolved_celery_broker(self) -> str:
        if self.celery_broker_url.strip():
            return self.celery_broker_url.strip()
        return self.redis_url.strip() or "redis://127.0.0.1:6379/0"

    def resolved_celery_backend(self) -> str:
        if self.celery_result_backend.strip():
            return self.celery_result_backend.strip()
        return self.redis_url.strip() or "redis://127.0.0.1:6379/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


VERSION = get_settings().version
DB_PATH = Path(get_settings().sqlite_path) if get_settings().sqlite_path else DEFAULT_SQLITE
