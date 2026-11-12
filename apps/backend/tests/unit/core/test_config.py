"""Unit tests for Application Configuration Module (app.core.config)."""

import os
from unittest import mock

from app.core.config import Settings, get_settings


def test_default_settings_instantiation() -> None:
    settings = get_settings()
    assert settings.app_name == "ws-translation-backend"
    assert settings.env == "local"
    assert settings.app.is_local is True
    assert "localhost" in settings.database_url
    assert "redis://" in settings.redis.url


def test_nested_domain_properties() -> None:
    settings = get_settings()

    # App
    assert settings.app.name == settings.app_name
    assert settings.app.env == settings.env
    assert "http://localhost:3000" in settings.app.cors_origins

    # Database
    assert settings.db.url == settings.database_url
    assert settings.db.pool_size == 10

    # Redis
    assert settings.redis.url == settings.redis_url

    # Cognito
    assert settings.cognito.user_pool_id == settings.cognito_user_pool_id
    assert settings.cognito.client_id == settings.cognito_client_id

    # S3
    assert settings.s3.bucket_name == settings.s3_bucket_name
    assert settings.s3.cdn_base_url == settings.cdn_base_url

    # Security
    assert settings.security.jwt_secret_key == settings.jwt_secret_key
    assert settings.security.jwt_algorithm == "HS256"

    # AI
    assert settings.ai.transcribe_language_code == "en-US"
    assert settings.ai.translate_default_target == "vi"
    assert settings.ai.polly_neural_engine == "neural"


def test_custom_environment_variable_override() -> None:
    with mock.patch.dict(
        os.environ,
        {
            "ENV": "staging",
            "APP_NAME": "custom-translation-api",
            "DATABASE_URL": "postgresql+asyncpg://user:pass@db:5432/testdb",
            "REDIS_URL": "redis://cache:6379/1",
        },
    ):
        custom_settings = Settings()
        assert custom_settings.env == "staging"
        assert custom_settings.app.is_local is False
        assert custom_settings.app_name == "custom-translation-api"
        assert custom_settings.database_url == "postgresql+asyncpg://user:pass@db:5432/testdb"
        assert custom_settings.redis.url == "redis://cache:6379/1"
