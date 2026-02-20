"""Application settings loaded from .env via pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    app_debug: bool = True

    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "glintstone"
    db_user: str = "glintstone"
    db_password: str = "glintstone"

    api_port: int = 8001
    web_port: int = 8002
    marketing_port: int = 8003

    api_url: str = "http://localhost:8001"
    web_url: str = "http://localhost:8002"
    marketing_url: str = "http://localhost:8003"

    image_path: str = "./app-v0.1/database/images"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
