"""Unit tests for Security Module: Password Hashing & JWT Token Operations (app.core.security)."""

from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    raw_password = "SuperSecretPassword123!@"
    hashed = hash_password(raw_password)

    # Hash should be a valid bcrypt string ($2b$...)
    assert hashed.startswith("$2b$")
    assert hashed != raw_password

    # Verification
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_access_token_creation_and_decoding() -> None:
    subject = "user-sub-uuid-42"
    claims = {"role": "HOST", "email": "test@example.com"}

    token = create_access_token(subject=subject, claims=claims, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded["sub"] == subject
    assert decoded["role"] == "HOST"
    assert decoded["email"] == "test@example.com"
    assert "exp" in decoded
    assert "iat" in decoded


def test_expired_jwt_token_raises_error() -> None:
    subject = "expired-user"
    token = create_access_token(subject=subject, expires_delta=timedelta(seconds=-10))

    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(token)


def test_invalid_jwt_token_signature_raises_error() -> None:
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("this.is.a.completely.invalid.token")
