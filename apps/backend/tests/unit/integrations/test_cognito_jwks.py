"""Unit tests for Cognito RS256 access-token verification via JWKS."""

import json
import time
from typing import Any

import fakeredis.aioredis
import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.api.deps import get_access_token_context, get_logout_token_context
from app.core.exceptions import ServiceUnavailableException, UnauthorizedException
from app.core.security import create_access_token
from app.integrations import cognito as cognito_module
from app.integrations.cognito import AwsCognitoClient
from app.integrations.cognito_jwks import CognitoJwtVerifier

REGION = "ap-southeast-1"
POOL_ID = "ap-southeast-1_TestPool"
CLIENT_ID = "testclientid"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}"


class _Key:
    """RSA key pair plus its public JWK, as Cognito would publish it."""

    def __init__(self, kid: str) -> None:
        self.kid = kid
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_pem = private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        jwk = json.loads(RSAAlgorithm.to_jwk(private.public_key()))
        jwk.update({"kid": kid, "alg": "RS256", "use": "sig"})
        self.jwk = jwk

    def sign(self, claims: dict[str, Any] | None = None, *, kid: str | None = None) -> str:
        now = int(time.time())
        payload: dict[str, Any] = {
            "sub": "user-sub-1",
            "iss": ISSUER,
            "client_id": CLIENT_ID,
            "token_use": "access",
            "iat": now,
            "exp": now + 3600,
            "origin_jti": "session-1",
        }
        payload.update(claims or {})
        return jwt.encode(
            payload, self.private_pem, algorithm="RS256", headers={"kid": kid or self.kid}
        )


class _Jwks:
    """Mock JWKS endpoint that counts requests and can be switched to fail."""

    def __init__(self, *keys: _Key) -> None:
        self.keys = list(keys)
        self.calls = 0
        self.fail = False

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == f"{ISSUER}/.well-known/jwks.json"
            self.calls += 1
            if self.fail:
                return httpx.Response(503)
            return httpx.Response(200, json={"keys": [k.jwk for k in self.keys]})

        return httpx.MockTransport(handler)


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _verifier(jwks: _Jwks, clock: _Clock | None = None, **kwargs: Any) -> CognitoJwtVerifier:
    return CognitoJwtVerifier(
        region=REGION,
        user_pool_id=POOL_ID,
        client_id=CLIENT_ID,
        transport=jwks.transport(),
        clock=clock or _Clock(),
        **kwargs,
    )


async def test_valid_token_is_verified_and_keys_are_cached() -> None:
    key = _Key("kid-1")
    jwks = _Jwks(key)
    verifier = _verifier(jwks)

    claims = await verifier.verify_access_token(key.sign())
    await verifier.verify_access_token(key.sign())

    assert claims["sub"] == "user-sub-1"
    assert claims["origin_jti"] == "session-1"
    assert jwks.calls == 1


async def test_expired_token_is_rejected_unless_verify_exp_is_disabled() -> None:
    key = _Key("kid-1")
    verifier = _verifier(_Jwks(key))
    expired = key.sign({"exp": int(time.time()) - 60})

    with pytest.raises(ValueError, match="expired"):
        await verifier.verify_access_token(expired)
    # Logout path: still signature-checked, but expiry is tolerated
    assert (await verifier.verify_access_token(expired, verify_exp=False))["sub"] == "user-sub-1"


@pytest.mark.parametrize(
    "claims",
    [
        {"iss": "https://cognito-idp.ap-southeast-1.amazonaws.com/other_Pool"},
        {"client_id": "another-app-client"},
        {"token_use": "id"},
    ],
    ids=["wrong-issuer", "wrong-client", "id-token"],
)
async def test_tokens_with_wrong_claims_are_rejected(claims: dict[str, Any]) -> None:
    key = _Key("kid-1")
    verifier = _verifier(_Jwks(key))

    with pytest.raises(ValueError, match="Invalid token"):
        await verifier.verify_access_token(key.sign(claims))


async def test_token_missing_required_claims_is_rejected() -> None:
    key = _Key("kid-1")
    verifier = _verifier(_Jwks(key))
    payload = {"iss": ISSUER, "client_id": CLIENT_ID, "token_use": "access"}  # no sub / exp
    token = jwt.encode(payload, key.private_pem, algorithm="RS256", headers={"kid": "kid-1"})

    with pytest.raises(ValueError, match="Invalid token"):
        await verifier.verify_access_token(token)


async def test_forged_signature_with_known_kid_is_rejected() -> None:
    real, attacker = _Key("kid-1"), _Key("kid-1")  # attacker reuses the public kid
    verifier = _verifier(_Jwks(real))

    with pytest.raises(ValueError, match="Invalid token"):
        await verifier.verify_access_token(attacker.sign())


async def test_algorithm_confusion_attacks_are_rejected() -> None:
    key = _Key("kid-1")
    verifier = _verifier(_Jwks(key))
    now = int(time.time())
    claims = {
        "sub": "x", "iss": ISSUER, "client_id": CLIENT_ID,
        "token_use": "access", "exp": now + 600,
    }

    hs256 = jwt.encode(
        claims, "shared-secret-32-bytes-long-xxxxxxxx", "HS256", headers={"kid": "kid-1"}
    )
    none_alg = jwt.encode(claims, None, algorithm="none", headers={"kid": "kid-1"})

    for token in (hs256, none_alg, "not-a-jwt", key.sign() + "tampered"):
        with pytest.raises(ValueError, match="Invalid token"):
            await verifier.verify_access_token(token)


async def test_unknown_kid_is_rejected_without_refetch_storm() -> None:
    key = _Key("kid-1")
    jwks = _Jwks(key)
    clock = _Clock()
    verifier = _verifier(jwks, clock)
    await verifier.verify_access_token(key.sign())
    assert jwks.calls == 1

    stranger = _Key("kid-unknown")
    for _ in range(5):
        with pytest.raises(ValueError, match="Invalid token"):
            await verifier.verify_access_token(stranger.sign())
    # Forged key ids right after a fetch must not trigger new downloads
    assert jwks.calls == 1


async def test_key_rotation_is_picked_up_after_the_refetch_interval() -> None:
    old, new = _Key("kid-old"), _Key("kid-new")
    jwks = _Jwks(old)
    clock = _Clock()
    verifier = _verifier(jwks, clock, min_refetch_interval_seconds=30.0)
    await verifier.verify_access_token(old.sign())

    jwks.keys = [old, new]
    clock.now += 31.0
    claims = await verifier.verify_access_token(new.sign())

    assert claims["sub"] == "user-sub-1"
    assert jwks.calls == 2


async def test_jwks_outage_fails_closed_without_cache_and_serves_stale_with_cache() -> None:
    key = _Key("kid-1")
    jwks = _Jwks(key)
    clock = _Clock()
    verifier = _verifier(jwks, clock, cache_ttl_seconds=100.0, min_refetch_interval_seconds=10.0)

    # No cache yet and Cognito unreachable -> 503, not 401
    jwks.fail = True
    with pytest.raises(ServiceUnavailableException):
        await verifier.verify_access_token(key.sign())
    # Failing endpoint is not hammered on every request
    calls_after_first_failure = jwks.calls
    with pytest.raises(ServiceUnavailableException):
        await verifier.verify_access_token(key.sign())
    assert jwks.calls == calls_after_first_failure

    # Once healthy, keys load; after the TTL expires an outage falls back to the stale keys
    jwks.fail = False
    clock.now += 20.0
    await verifier.verify_access_token(key.sign())
    jwks.fail = True
    clock.now += 500.0
    assert (await verifier.verify_access_token(key.sign()))["sub"] == "user-sub-1"


async def test_aws_client_and_auth_dependencies_use_the_jwks_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = _Key("kid-1")
    verifier = _verifier(_Jwks(key))
    client = AwsCognitoClient(
        user_pool_id=POOL_ID, client_id=CLIENT_ID, region=REGION, jwt_verifier=verifier
    )
    monkeypatch.setattr(cognito_module, "_cognito_instance", client)
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    context = await get_access_token_context(redis, f"Bearer {key.sign()}")
    assert context.subject == "user-sub-1"
    assert context.session_id == "session-1"

    # A locally signed HS256 token (valid in offline mode) must be rejected in AWS mode
    with pytest.raises(UnauthorizedException):
        await get_access_token_context(redis, f"Bearer {create_access_token('user-sub-1')}")

    # Logout tolerates expiry only
    expired = key.sign({"exp": int(time.time()) - 60})
    with pytest.raises(UnauthorizedException, match="expired"):
        await get_access_token_context(redis, f"Bearer {expired}")
    assert (await get_logout_token_context(redis, f"Bearer {expired}")).subject == "user-sub-1"
