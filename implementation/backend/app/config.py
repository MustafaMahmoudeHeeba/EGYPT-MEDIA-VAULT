
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root:
# EGYPT-MEDIA-VAULT/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """FastAPI application configuration."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "EGYPT-MEDIA-VAULT API"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"

    azure_sql_server: str
    azure_sql_database: str
    azure_sql_username: str
    azure_sql_password: str

    sql_pool_size: int = Field(default=5, ge=1)
    sql_max_overflow: int = Field(default=10, ge=0)
    sql_pool_recycle: int = Field(default=1800, ge=60)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
