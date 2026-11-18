"""Cognito access-token verification against the user pool's public JWKS (RS256).

Cognito signs access tokens with an asymmetric key, so this API must verify them with the pool's
public keys instead of a shared secret. Keys are fetched with an async HTTP client (no blocking
I/O in the event loop), cached, and refreshed when Cognito rotates them.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import httpx
import jwt

from app.core.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)

JWKS_CACHE_TTL_SECONDS = 3600.0
# Unknown `kid` values trigger a refetch to pick up key rotation; this floor stops a client from
# forcing a JWKS download on every request by sending random key ids.
JWKS_MIN_REFETCH_INTERVAL_SECONDS = 30.0
JWKS_FETCH_TIMEOUT_SECONDS = 5.0
# Only RS256 is accepted: allowing the algorithm named in the token header would enable
# algorithm-confusion attacks (e.g. HS256 signed with the public key, or "none").
ALLOWED_ALGORITHMS = ["RS256"]


class CognitoJwtVerifier:
    """Verify Cognito-issued access tokens (signature, issuer, token_use, client_id, expiry)."""

    def __init__(
        self,
        *,
        region: str,
        user_pool_id: str,
        client_id: str,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
        cache_ttl_seconds: float = JWKS_CACHE_TTL_SECONDS,
        min_refetch_interval_seconds: float = JWKS_MIN_REFETCH_INTERVAL_SECONDS,
    ) -> None:
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self.jwks_url = f"{self.issuer}/.well-known/jwks.json"
        self.client_id = client_id
        self._transport = transport
        self._clock = clock
        self._cache_ttl = cache_ttl_seconds
        self._min_refetch_interval = min_refetch_interval_seconds
        self._keys: dict[str, dict[str, Any]] = {}
        self._fetched_at: float | None = None
        self._last_failure_at: float | None = None
        self._lock = asyncio.Lock()

    async def verify_access_token(self, token: str, *, verify_exp: bool = True) -> dict[str, Any]:
        """Return the verified claims, or raise ValueError for any invalid token.

        `verify_exp=False` is only for logout; the signature, issuer and client are still checked.
        """
        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as e:
            raise ValueError("Invalid token signature or claims") from e

        kid = header.get("kid")
        if header.get("alg") not in ALLOWED_ALGORITHMS or not isinstance(kid, str):
            raise ValueError("Invalid token signature or claims")

        jwk = await self._get_jwk(kid)
        try:
            claims = jwt.decode(
                token,
                jwt.PyJWK(jwk).key,
                algorithms=ALLOWED_ALGORITHMS,
                issuer=self.issuer,
                # Access tokens carry `client_id` instead of `aud`, which is checked below.
                options={
                    "verify_exp": verify_exp,
                    "verify_aud": False,
                    "require": ["exp", "iss", "sub"],
                },
            )
        except jwt.ExpiredSignatureError as e:
            raise ValueError("Token has expired") from e
        except (jwt.InvalidTokenError, jwt.PyJWKError) as e:
            raise ValueError("Invalid token signature or claims") from e

        # An ID token or a token minted for another app client must not authenticate API calls.
        if claims.get("token_use") != "access" or claims.get("client_id") != self.client_id:
            raise ValueError("Invalid token signature or claims")
        return dict(claims)

    async def _get_jwk(self, kid: str) -> dict[str, Any]:
        async with self._lock:
            now = self._clock()
            cache_fresh = self._fetched_at is not None and now - self._fetched_at < self._cache_ttl
            if cache_fresh and kid in self._keys:
                return self._keys[kid]

            if cache_fresh and now - (self._fetched_at or 0.0) < self._min_refetch_interval:
                # Unknown kid right after a fetch: treat as a forged key id, do not refetch.
                raise ValueError("Invalid token signature or claims")

            failed_recently = (
                self._last_failure_at is not None
                and now - self._last_failure_at < self._min_refetch_interval
            )
            if failed_recently:
                # Do not hammer a failing JWKS endpoint; serve stale keys if we still have them.
                if kid in self._keys:
                    return self._keys[kid]
                raise ServiceUnavailableException("Token verification is temporarily unavailable")

            try:
                await self._refresh_keys(now)
            except ServiceUnavailableException:
                self._last_failure_at = now
                # Keep serving from a stale cache during an outage; fail only when it lacks the key.
                if kid not in self._keys:
                    raise
            if kid not in self._keys:
                raise ValueError("Invalid token signature or claims")
            return self._keys[kid]

    async def _refresh_keys(self, now: float) -> None:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=JWKS_FETCH_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                keys = response.json()["keys"]
                fetched = {str(key["kid"]): key for key in keys}
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as e:
            logger.error("Cognito JWKS fetch failed: %s", e)
            raise ServiceUnavailableException(
                "Token verification is temporarily unavailable"
            ) from e

        self._keys = fetched
        self._fetched_at = now
        self._last_failure_at = None
