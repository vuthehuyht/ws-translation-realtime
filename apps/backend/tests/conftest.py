"""Pytest Test Configuration and Fixtures.

Provides in-memory SQLite async database engine, isolated session management,
mock service resets, and async HTTP test client.
"""

from collections.abc import AsyncGenerator, AsyncIterator

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_redis
from app.core.db import get_db
from app.integrations.appsync import MockAppSyncClient, set_appsync_client
from app.integrations.cognito import MockCognitoClient, set_cognito_client
from app.integrations.s3 import MockS3Client, set_s3_client
from app.main import app
from app.models.base import Base

# In-memory SQLite Async Engine for fast, 100% offline unit & integration testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_test_database_and_mocks() -> AsyncGenerator[None, None]:
    """Create all schema tables in memory before each test and reset mock state."""
    # Reset mock external clients
    set_cognito_client(MockCognitoClient())
    set_s3_client(MockS3Client())
    set_appsync_client(MockAppSyncClient())

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated AsyncSession bound to the in-memory SQLite test database."""
    async with TestSessionFactory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Yield an AsyncClient with get_db and get_redis overridden for isolated offline tests."""
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis() -> fakeredis.aioredis.FakeRedis:
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await fake_redis.aclose()
    app.dependency_overrides.clear()
