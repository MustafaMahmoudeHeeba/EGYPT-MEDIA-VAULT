from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration for the EGYPT-MEDIA-VAULT pipeline.

    Values are loaded from environment variables and, when available,
    from the root .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "EGYPT-MEDIA-VAULT"
    app_env: str = "development"
    log_level: str = "INFO"

    # Scraping
    request_timeout_seconds: int = Field(default=10, ge=1)
    request_delay_seconds: float = Field(default=1.0, ge=0.0)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_factor: float = Field(default=1.0, ge=0.0)

    # Story matching
    story_similarity_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
    )

    # Azure SQL Database
    azure_sql_server: str
    azure_sql_database: str
    azure_sql_username: str
    azure_sql_password: str

    # Azure Data Lake Storage
    azure_storage_account_name: str = ""
    azure_storage_account_key: str = ""
    azure_storage_container_name: str = "egypt-media-vault"

    @property
    def azure_sql_url(self) -> str:
        """Build the SQLAlchemy Azure SQL connection URL."""
        return (
            "mssql+pyodbc://"
            f"{self.azure_sql_username}:"
            f"{self.azure_sql_password}@"
            f"{self.azure_sql_server}/"
            f"{self.azure_sql_database}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&Encrypt=yes"
            "&TrustServerCertificate=no"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Caching prevents repeatedly parsing environment variables
    throughout the application lifecycle.
    """
    return Settings()


settings = get_settings()