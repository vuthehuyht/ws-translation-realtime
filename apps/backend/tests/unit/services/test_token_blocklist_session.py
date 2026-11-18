"""Unit tests for session-level revocation in the Redis token blocklist."""

import time

import fakeredis.aioredis

from app.services import token_blocklist


async def test_revoke_session_blocks_every_token_of_that_session_only() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    now = int(time.time())

    await token_blocklist.revoke_session(redis, "session-a")

    assert await token_blocklist.is_revoked(
        redis, token="any", subject="u1", issued_at=now, session_id="session-a"
    )
    assert not await token_blocklist.is_revoked(
        redis, token="any", subject="u1", issued_at=now, session_id="session-b"
    )
    # Tokens without a session id are unaffected by session markers
    assert not await token_blocklist.is_revoked(
        redis, token="any", subject="u1", issued_at=now, session_id=None
    )
    assert await redis.ttl(token_blocklist.REVOKED_SESSION_KEY_PREFIX + "session-a") > 24 * 3600
