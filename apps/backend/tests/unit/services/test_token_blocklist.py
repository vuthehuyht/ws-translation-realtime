"""Unit tests for the Redis access-token blocklist."""

import time

import fakeredis.aioredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.exceptions import ServiceUnavailableException
from app.services import token_blocklist


async def test_revoke_access_token_blocks_only_that_token() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    now = int(time.time())

    await token_blocklist.revoke_access_token(redis, "token-a", now + 600)

    assert await token_blocklist.is_revoked(redis, token="token-a", subject="u1", issued_at=now)
    assert not await token_blocklist.is_revoked(redis, token="token-b", subject="u1", issued_at=now)

    keys = await redis.keys("*")
    # Raw tokens must never be stored in Redis, and the entry must expire with the token
    assert all("token-a" not in key for key in keys)
    assert 0 < await redis.ttl(keys[0]) <= 600


async def test_revoke_access_token_with_past_expiry_still_gets_a_positive_ttl() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    # Expired tokens can still be revoked during logout; Redis rejects a TTL of 0 or less.
    await token_blocklist.revoke_access_token(redis, "expired", int(time.time()) - 500)

    assert await redis.exists(next(iter(await redis.keys("*")))) == 1


async def test_revoke_all_for_subject_blocks_older_tokens_only() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    now = int(time.time())

    await token_blocklist.revoke_all_for_subject(redis, "u1")

    assert await token_blocklist.is_revoked(redis, token="t", subject="u1", issued_at=now - 10)
    # Tokens without iat cannot be proven newer, so they are denied too
    assert await token_blocklist.is_revoked(redis, token="t", subject="u1", issued_at=None)
    assert not await token_blocklist.is_revoked(redis, token="t", subject="u1", issued_at=now + 5)
    # Other users are unaffected
    assert not await token_blocklist.is_revoked(redis, token="t", subject="u2", issued_at=now - 10)

    # The marker must outlive the longest possible Cognito access-token lifetime (24h)
    ttl = await redis.ttl(token_blocklist.REVOKED_BEFORE_KEY_PREFIX + "u1")
    assert ttl > 24 * 3600


async def test_redis_failures_fail_closed_with_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    async def broken(*_args: object, **_kwargs: object) -> None:
        raise RedisConnectionError("redis down")

    monkeypatch.setattr(redis, "exists", broken)
    monkeypatch.setattr(redis, "set", broken)

    with pytest.raises(ServiceUnavailableException):
        await token_blocklist.is_revoked(redis, token="t", subject="u1", issued_at=1)
    with pytest.raises(ServiceUnavailableException):
        await token_blocklist.revoke_access_token(redis, "t", None)
    with pytest.raises(ServiceUnavailableException):
        await token_blocklist.revoke_all_for_subject(redis, "u1")
