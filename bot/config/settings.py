"""Bot configuration settings."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Bot settings
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: str = Field("", alias="ADMIN_IDS")

    # Database settings
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: str = Field("prediction_bot", alias="DB_NAME")
    db_user: str = Field("prediction_bot", alias="DB_USER")
    db_password: str = Field("prediction_bot_password", alias="DB_PASSWORD")

    # Scheduler settings
    scheduler_timezone: str = Field("Europe/Moscow", alias="SCHEDULER_TIMEZONE")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def admin_ids_list(self) -> List[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_ids:
            return []
        return [int(id_.strip()) for id_ in self.admin_ids.split(",") if id_.strip()]

    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
