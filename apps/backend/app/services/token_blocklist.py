"""Redis blocklist for revoked access tokens.

Access tokens are validated locally, so a Cognito revocation alone does not stop a still-valid
JWT from calling this API. The blocklist closes that gap until the token expires naturally.

Redis failures are surfaced as 503 instead of being ignored: if the blocklist cannot be read,
a revoked token could slip through, so the request must fail closed.
"""

import hashlib
import time

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.exceptions import ServiceUnavailableException

REVOKED_TOKEN_KEY_PREFIX = "auth:revoked_token:"  # noqa: S105 - Redis key prefix, not a secret
REVOKED_SESSION_KEY_PREFIX = "auth:revoked_session:"
REVOKED_BEFORE_KEY_PREFIX = "auth:revoked_before:"

# Cognito lets the user pool configure access-token lifetime up to 24h, independent of this
# service's settings, so the markers use the maximum plus clock-skew slack.
MAX_ACCESS_TOKEN_LIFETIME_SECONDS = 24 * 3600 + 60


def _token_key(token: str) -> str:
    # Hash the token so raw credentials are never stored in Redis.
    return REVOKED_TOKEN_KEY_PREFIX + hashlib.sha256(token.encode("utf-8")).hexdigest()


def _store_unavailable() -> ServiceUnavailableException:
    return ServiceUnavailableException("Session store is temporarily unavailable")


async def revoke_access_token(
    redis: aioredis.Redis,
    token: str,
    expires_at: int | None,
) -> None:
    """Block a single access token until it would have expired anyway."""
    if expires_at is None:
        ttl = MAX_ACCESS_TOKEN_LIFETIME_SECONDS
    else:
        ttl = max(expires_at - int(time.time()), 1)
    try:
        await redis.set(_token_key(token), "1", ex=ttl)
    except RedisError as e:
        raise _store_unavailable() from e


async def revoke_session(redis: aioredis.Redis, session_id: str) -> None:
    """Block every access token minted from one login session (Cognito `origin_jti`).

    Cognito's RevokeToken kills all access tokens issued from the refresh token, but this API
    validates JWTs locally, so earlier tokens of the same session must be blocked here too.
    """
    try:
        await redis.set(
            REVOKED_SESSION_KEY_PREFIX + session_id,
            "1",
            ex=MAX_ACCESS_TOKEN_LIFETIME_SECONDS,
        )
    except RedisError as e:
        raise _store_unavailable() from e


async def revoke_all_for_subject(redis: aioredis.Redis, subject: str) -> None:
    """Block every access token issued to the subject up to now (global sign-out)."""
    try:
        await redis.set(
            REVOKED_BEFORE_KEY_PREFIX + subject,
            str(int(time.time())),
            ex=MAX_ACCESS_TOKEN_LIFETIME_SECONDS,
        )
    except RedisError as e:
        raise _store_unavailable() from e


async def is_revoked(
    redis: aioredis.Redis,
    *,
    token: str,
    subject: str,
    issued_at: int | None,
    session_id: str | None = None,
) -> bool:
    """Return True when the token was revoked individually, by session, or by global sign-out."""
    try:
        if await redis.exists(_token_key(token)):
            return True
        if session_id and await redis.exists(REVOKED_SESSION_KEY_PREFIX + session_id):
            return True
        cutoff = await redis.get(REVOKED_BEFORE_KEY_PREFIX + subject)
    except RedisError as e:
        raise _store_unavailable() from e

    if cutoff is None:
        return False
    # `<=` is deliberate: `iat` has one-second resolution, so a token issued in the same second
    # as the sign-out cannot be proven newer. Failing closed beats weakening revocation.
    # A token without `iat` cannot be proven newer at all, so deny it.
    return issued_at is None or issued_at <= int(cutoff)
