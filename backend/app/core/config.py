from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production", "test"] = "development"
    debug: bool = False

    database_url: PostgresDsn
    redis_url: RedisDsn

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    csrf_secret_key: str = Field(min_length=32)

    cors_allow_origins_raw: str = Field(default="", alias="CORS_ALLOW_ORIGINS")

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""

    zarinpal_merchant_id: str = ""
    zarinpal_sandbox: bool = True
    zarinpal_callback_url: str = ""

    storage_root: str = "/data/uploads"
    max_upload_size_mb: int = 5

    openapi_enabled: bool = True

    # Cookies are Secure-by-default in production. Override only for a
    # deployment that's deliberately running production behavior without TLS
    # yet (e.g. a bare-IP staging box before a domain/cert exists) — never
    # use this to relax a real, publicly reachable production deployment.
    cookie_secure_override: bool | None = Field(default=None, alias="COOKIE_SECURE")

    @property
    def cors_allow_origins(self) -> list[str]:
        origins = self.cors_allow_origins_raw.split(",")
        return [origin.strip() for origin in origins if origin.strip()]

    @property
    def cookie_secure(self) -> bool:
        if self.cookie_secure_override is not None:
            return self.cookie_secure_override
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
