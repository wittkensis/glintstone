"""Application settings loaded from .env via pydantic-settings.

Database configuration accepts EITHER `DATABASE_URL` (preferred, the format every
hosted Postgres service emits) OR the discrete `DB_HOST`/`DB_PORT`/`DB_NAME`/
`DB_USER`/`DB_PASSWORD` fallback. `DATABASE_URL` takes precedence when both are set.

Environment selection: `APP_ENV` chooses which `.env.<env>` file to load. The base
`.env` file is always loaded first (if present); env-specific values override it.
"""

import os
from functools import lru_cache
from typing import Optional
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _select_env_files() -> tuple[str, ...]:
    """Pick env files in load order. Later files override earlier ones.

    Always load `.env` first (if present), then `.env.<APP_ENV>` for overrides.
    """
    app_env = os.environ.get("APP_ENV", "local").strip().lower()
    base = ".env"
    overlay = f".env.{app_env}"
    files: list[str] = []
    if os.path.exists(base):
        files.append(base)
    if os.path.exists(overlay):
        files.append(overlay)
    return tuple(files) or (".env",)


class Settings(BaseSettings):
    app_env: str = "local"
    app_debug: bool = True

    database_url: Optional[str] = None

    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "glintstone"
    db_user: str = "glintstone"
    db_password: str = "glintstone"
    db_sslmode: Optional[str] = None

    api_port: int = 8001
    web_port: int = 8002
    marketing_port: int = 8003

    api_url: str = "http://localhost:8001"
    web_url: str = "http://localhost:8002"
    marketing_url: str = "http://localhost:8003"

    image_path: str = "./app-v0.1/database/images"

    storage_backend: str = "local"
    r2_account_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("R2_ACCOUNT_ID", "CLOUDFLARE_ACCOUNT_ID"),
    )
    r2_access_key_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("R2_ACCESS_KEY_ID", "CLOUDFLARE_ACCESS_KEY_ID"),
    )
    r2_secret_access_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "R2_SECRET_ACCESS_KEY", "CLOUDFLARE_SECRET_ACCESS_KEY"
        ),
    )
    r2_bucket: str = Field(
        default="glintstone-assets",
        validation_alias=AliasChoices("R2_BUCKET", "CLOUDFLARE_BUCKET_NAME"),
    )
    r2_s3_endpoint: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("R2_S3_ENDPOINT", "CLOUDFLARE_S3_ENDPOINT_URL"),
    )
    r2_public_base_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "R2_PUBLIC_BASE_URL", "CLOUDFLARE_PUBLIC_BASE_URL"
        ),
    )

    cdli_user_agent: str = "Glintstone/0.1 (academic; +https://app.glintstone.org; contact eric.wittke@gmail.com)"
    cdli_min_request_interval_seconds: float = 5.0
    cdli_crawl_delay_seconds: float = 60.0

    deploy_host: Optional[str] = None
    deploy_user: str = "deploy"
    deploy_remote_dir: str = "/var/www/glintstone"

    model_config = SettingsConfigDict(
        env_file=_select_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _backfill_from_database_url(self) -> "Settings":
        """If DATABASE_URL is set, populate discrete fields from it.

        Keeps both representations in sync so legacy code that reads `db_host`
        etc. continues to work after the DATABASE_URL refactor.
        """
        if not self.database_url:
            return self
        parsed = urlparse(self.database_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError(
                f"DATABASE_URL must use postgres:// or postgresql:// scheme, "
                f"got {parsed.scheme!r}"
            )
        if not parsed.hostname:
            raise ValueError("DATABASE_URL missing hostname")
        self.db_host = parsed.hostname
        self.db_port = parsed.port or 5432
        if parsed.path and len(parsed.path) > 1:
            self.db_name = parsed.path.lstrip("/")
        if parsed.username:
            self.db_user = parsed.username
        if parsed.password:
            self.db_password = parsed.password
        if "sslmode=" in (parsed.query or ""):
            for pair in parsed.query.split("&"):
                if pair.startswith("sslmode="):
                    self.db_sslmode = pair.split("=", 1)[1]
                    break
        return self

    def effective_database_url(self) -> str:
        """Return a DATABASE_URL string, building one from discrete fields if needed."""
        if self.database_url:
            return self.database_url
        auth = f"{self.db_user}:{self.db_password}"
        url = f"postgresql://{auth}@{self.db_host}:{self.db_port}/{self.db_name}"
        if self.db_sslmode:
            url += f"?sslmode={self.db_sslmode}"
        return url

    def psycopg_conninfo(self) -> str:
        """Return a psycopg-style conninfo string for the active connection."""
        parts = [
            f"host={self.db_host}",
            f"port={self.db_port}",
            f"dbname={self.db_name}",
            f"user={self.db_user}",
            f"password={self.db_password}",
        ]
        if self.db_sslmode:
            parts.append(f"sslmode={self.db_sslmode}")
        return " ".join(parts)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Clear the settings cache. Use in tests after mutating env vars."""
    get_settings.cache_clear()
