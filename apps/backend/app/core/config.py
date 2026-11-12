"""Application Configuration & Dynamic Environment Settings.

Provides structured, nested domain configuration sub-models loaded via
Pydantic Settings with cascading .env file resolution.
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentType = Literal["local", "test", "dev", "staging", "production"]


def _resolve_env_files() -> tuple[str, ...]:
    """Resolve cascading environment files in priority order without failing if absent."""
    current_env = os.getenv("ENV", "local")
    candidates = [
        ".env",
        f".env.{current_env}",
        ".env.local",
    ]
    if custom_env_file := os.getenv("ENV_FILE"):
        candidates.append(custom_env_file)
    return tuple(dict.fromkeys(candidates))


# -----------------------------------------------------------------------------
# Nested Domain Sub-models
# -----------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Core FastAPI runtime metadata and security origins."""

    env: EnvironmentType = "local"
    name: str = "ws-translation-backend"
    project_name: str = "ws-translation"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_local(self) -> bool:
        """Check whether runtime is purely local or test."""
        return self.env in ("local", "test")


class DatabaseConfig(BaseModel):
    """PostgreSQL 16 Async Connection Pool settings."""

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/translation_db",
        description="Asyncpg database URL connection string",
    )
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False


class RedisConfig(BaseModel):
    """ElastiCache Redis / EC2 standalone connection parameters."""

    url: str = "redis://localhost:6379/0"


class CognitoConfig(BaseModel):
    """Amazon Cognito User Pool & App Client configuration."""

    user_pool_id: str = "ap-southeast-1_local"
    client_id: str = "local_client_id"


class S3Config(BaseModel):
    """Amazon S3 Media Bucket and CloudFront CDN distribution."""

    bucket_name: str = "ws-translation-local-media"
    cdn_base_url: str = "http://localhost:8000/media"


class AppSyncConfig(BaseModel):
    """AWS AppSync Realtime WebSocket and Events API settings."""

    endpoint_url: str | None = None
    api_key: str | None = None


class AIServicesConfig(BaseModel):
    """AWS AI Pipeline configurations (Transcribe, Translate, Polly, Bedrock)."""

    transcribe_language_code: str = "en-US"
    translate_default_target: str = "vi"
    polly_voice_id: str = "Joanna"
    polly_neural_engine: str = "neural"
    bedrock_model_id: str = "anthropic.claude-3-5-haiku-20241022-v1:0"


class SecurityConfig(BaseModel):
    """Cryptographic secrets and authentication parameters."""

    jwt_secret_key: str = "default-insecure-dev-jwt-secret-key-32chars-min!"  # noqa: S105
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30


# -----------------------------------------------------------------------------
# Root Settings Class with Dynamic Fallback & Backward Compatibility
# -----------------------------------------------------------------------------


class Settings(BaseSettings):
    """Root application configuration loaded from environment variables & env files."""

    model_config = SettingsConfigDict(
        env_file=_resolve_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    env: EnvironmentType = "local"
    app_name: str = "ws-translation-backend"
    project_name: str = "ws-translation"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    # AWS General
    aws_region: str = "ap-southeast-1"
    aws_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # Database & Cache
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/translation_db"
    redis_url: str = "redis://localhost:6379/0"

    # Cognito
    cognito_user_pool_id: str = "ap-southeast-1_local"
    cognito_client_id: str = "local_client_id"

    # S3 & CDN
    s3_bucket_name: str = "ws-translation-local-media"
    cdn_base_url: str = "http://localhost:8000/media"

    # AppSync
    appsync_endpoint_url: str | None = None
    appsync_api_key: str | None = None

    # Security
    jwt_secret_key: str = "default-insecure-dev-jwt-secret-key-32chars-min!"  # noqa: S105
    jwt_algorithm: str = "HS256"

    # Domain models
    @property
    def app(self) -> AppConfig:
        return AppConfig(
            env=self.env,
            name=self.app_name,
            project_name=self.project_name,
            log_level=self.log_level,
            cors_origins=self.cors_origins,
        )

    @property
    def db(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.database_url,
            echo=self.env in ("local", "test"),
        )

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(url=self.redis_url)

    @property
    def cognito(self) -> CognitoConfig:
        return CognitoConfig(
            user_pool_id=self.cognito_user_pool_id,
            client_id=self.cognito_client_id,
        )

    @property
    def s3(self) -> S3Config:
        return S3Config(
            bucket_name=self.s3_bucket_name,
            cdn_base_url=self.cdn_base_url,
        )

    @property
    def appsync(self) -> AppSyncConfig:
        return AppSyncConfig(
            endpoint_url=self.appsync_endpoint_url,
            api_key=self.appsync_api_key,
        )

    @property
    def security(self) -> SecurityConfig:
        return SecurityConfig(
            jwt_secret_key=self.jwt_secret_key,
            jwt_algorithm=self.jwt_algorithm,
        )

    @property
    def ai(self) -> AIServicesConfig:
        return AIServicesConfig()


@lru_cache
def get_settings() -> Settings:
    """Singleton getter for application configuration."""
    return Settings()
