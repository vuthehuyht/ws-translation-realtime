from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["local", "test", "staging", "production"] = "local"
    app_name: str = "ws-translation-backend"
    log_level: str = "INFO"
    aws_region: str = "ap-southeast-1"
    redis_url: str = "redis://localhost:6379/0"
    dynamodb_endpoint_url: str | None = None
    s3_bucket_name: str = "ws-translation-media-local"
    cdn_base_url: str = "http://localhost:8000/media"
    jwt_secret_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
