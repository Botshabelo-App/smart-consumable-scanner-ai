from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Smart Consumable Scanner AI API"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite:///./scanner.db"
    ai_service_url: str = "http://localhost:8000"
    fallback_to_sqlite: bool = True
    cors_origins: List[str] = ["*"]
    access_token_expire_minutes: int = 60 * 24  # 1 day


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
