"""Unit tests for AuthService (app.services.auth_service)."""

from decimal import Decimal

import fakeredis.aioredis
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
)
from app.integrations.cognito import MockCognitoClient
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.requests import ConfirmRequest, LoginRequest, RegisterRequest, ResendOtpRequest
from app.services.auth_service import AuthService


async def test_auth_service_registration_and_confirmation_lifecycle(
    db_session: AsyncSession,
) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
    )

    # 1. Register new host (TASK-AUTH-01)
    reg_req = RegisterRequest(
        email="host.new@example.com",
        password="SuperPassword123@",
        fullName="Nguyễn Văn A",
        role="HOST",
    )
    reg_res = await service.register(reg_req)
    assert reg_res.email == "host.new@example.com"
    assert reg_res.status == "CONFIRMATION_REQUIRED"
    assert len(reg_res.user_sub) > 10

    # Under TASK-AUTH-01, PostgreSQL is NOT yet populated until OTP confirmation
    user_before_confirm = await user_repo.get_by_id(reg_res.user_sub)
    assert user_before_confirm is None

    # 2. Duplicate registration in Cognito raises ConflictException (HTTP 409)
    with pytest.raises(ConflictException, match="already exists"):
        await service.register(reg_req)

    # 3. Confirm sign up with OTP (TASK-AUTH-02)
    confirm_req = ConfirmRequest(
        email="host.new@example.com",
        otpCode="123456",
    )
    confirm_res = await service.confirm_sign_up(confirm_req)
    assert confirm_res.status == "CONFIRMED"
    assert confirm_res.wallet_balance == Decimal("2.0000")

    # User in DB should now be ACTIVE, Wallet initialized ($2.00 Welcome Bonus), and Ledger recorded
    user = await user_repo.get_by_id(reg_res.user_sub)
    assert user is not None
    assert user.status == "ACTIVE"

    wallet = await wallet_repo.get_by_host_id(reg_res.user_sub)
    assert wallet is not None
    assert wallet.balance == Decimal("2.0000")

    welcome_tx = await wallet_repo.get_transaction_by_provider_id(f"welcome_{reg_res.user_sub}")
    assert welcome_tx is not None
    assert welcome_tx.type == "PROMO_CREDIT"
    assert welcome_tx.provider == "SYSTEM"
    assert welcome_tx.amount == Decimal("2.0000")
    assert welcome_tx.status == "SUCCEEDED"

    # Idempotent second confirmation must not fail or double-credit Welcome Bonus
    second_confirm = await service.confirm_sign_up(confirm_req)
    assert second_confirm.status == "CONFIRMED"
    assert second_confirm.wallet_balance == Decimal("2.0000")

    # 4. Login after confirmation
    login_req = LoginRequest(
        email="host.new@example.com",
        password="SuperPassword123@",
    )
    login_res = await service.login(login_req)
    assert login_res.response.tokens.access_token is not None
    assert login_res.response.tokens.id_token != login_res.response.tokens.access_token
    assert login_res.refresh_token
    assert login_res.response.user.email == "host.new@example.com"
    assert login_res.response.user.full_name == "Nguyễn Văn A"
    assert login_res.response.user.role == "HOST"
    # The public payload must never carry the refresh token.
    assert "refreshToken" not in login_res.response.model_dump(by_alias=True)["tokens"]


async def test_auth_service_login_with_wrong_password_fails(db_session: AsyncSession) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    service = AuthService(user_repo=user_repo, wallet_repo=wallet_repo, cognito_client=mock_cognito)

    # Register & confirm
    await service.register(
        RegisterRequest(
            email="login.test@example.com",
            password="CorrectPassword123@",
            fullName="Tester",
        )
    )
    await service.confirm_sign_up(
        ConfirmRequest(
            email="login.test@example.com",
            confirmation_code="123456",
        )
    )

    # Login with wrong password
    with pytest.raises(UnauthorizedException, match="Incorrect username or password"):
        await service.login(
            LoginRequest(
                email="login.test@example.com",
                password="WrongPassword123@",
            )
        )


async def test_auth_service_resend_otp_and_rate_limit(db_session: AsyncSession) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
        redis_client=fake_redis,
    )

    # 1. Unknown email raises NotFoundException and does NOT lock out rate limit
    with pytest.raises(NotFoundException, match="not found"):
        await service.resend_otp(ResendOtpRequest(email="unknown@example.com"))
    assert await fake_redis.get("email:unknown@example.com:resend_limit") is None

    # 2. Register user, resend succeeds and sets 60s Redis cooldown
    await service.register(
        RegisterRequest(
            email="resend.test@example.com",
            password="ValidPassword123@",
            fullName="Resend Tester",
        )
    )
    resend_res = await service.resend_otp(ResendOtpRequest(email="resend.test@example.com"))
    assert resend_res.status == "OTP_SENT"
    assert resend_res.retry_after == 60

    # 3. Immediate second resend raises TooManyRequestsException (429)
    with pytest.raises(TooManyRequestsException, match="wait"):
        await service.resend_otp(ResendOtpRequest(email="resend.test@example.com"))

    # 4. Confirmed user calling resend_otp raises ConflictException (409)
    await fake_redis.delete("email:resend.test@example.com:resend_limit")
    await service.confirm_sign_up(
        ConfirmRequest(email="resend.test@example.com", otpCode="123456")
    )
    with pytest.raises(ConflictException, match="already confirmed"):
        await service.resend_otp(ResendOtpRequest(email="resend.test@example.com"))

    await fake_redis.aclose()


async def test_auth_service_suspended_user_login_fails(db_session: AsyncSession) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
    )

    reg_res = await service.register(
        RegisterRequest(
            email="suspended@example.com",
            password="ValidPassword123@",
            fullName="Suspended Host",
        )
    )
    await service.confirm_sign_up(
        ConfirmRequest(email="suspended@example.com", otpCode="123456")
    )

    user = await user_repo.get_by_id(reg_res.user_sub)
    assert user is not None
    user.status = "SUSPENDED"
    await user_repo.update(user)

    with pytest.raises(ForbiddenException, match="suspended"):
        await service.login(
            LoginRequest(
                email="suspended@example.com",
                password="ValidPassword123@",
            )
        )


async def test_auth_service_login_fails_when_user_missing_in_db(
    db_session: AsyncSession,
) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
    )

    await mock_cognito.sign_up(
        email="orphan@example.com",
        password="ValidPassword123@",
        full_name="Orphan User",
    )
    await mock_cognito.confirm_sign_up(
        email="orphan@example.com",
        confirmation_code="123456",
    )

    with pytest.raises(UnauthorizedException, match="not found in database"):
        await service.login(
            LoginRequest(
                email="orphan@example.com",
                password="ValidPassword123@",
            )
        )


async def test_auth_service_refresh_session_success_and_guards(
    db_session: AsyncSession,
) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()
    service = AuthService(user_repo=user_repo, wallet_repo=wallet_repo, cognito_client=mock_cognito)

    reg_res = await service.register(
        RegisterRequest(
            email="refresh.svc@example.com",
            password="ValidPassword123@",
            fullName="Refresh Host",
        )
    )
    await service.confirm_sign_up(
        ConfirmRequest(email="refresh.svc@example.com", otpCode="123456")
    )
    login_res = await service.login(
        LoginRequest(email="refresh.svc@example.com", password="ValidPassword123@")
    )

    # 1. Valid refresh returns new access/id tokens and user profile
    refreshed = await service.refresh_session(login_res.refresh_token)
    assert refreshed.response.tokens.access_token
    assert refreshed.response.tokens.id_token
    assert refreshed.refresh_token is None
    assert refreshed.response.tokens.expires_in == 3600
    assert refreshed.response.user.id == reg_res.user_sub
    assert refreshed.response.user.email == "refresh.svc@example.com"

    # 2. Blank refresh token raises UnauthorizedException
    with pytest.raises(UnauthorizedException, match="Missing refresh token"):
        await service.refresh_session("   ")

    # 3. Suspended user cannot refresh session
    db_user = await user_repo.get_by_id(reg_res.user_sub)
    assert db_user is not None
    db_user.status = "SUSPENDED"
    await user_repo.update(db_user)

    with pytest.raises(ForbiddenException, match="suspended"):
        await service.refresh_session(login_res.refresh_token)

    # 4. Any non-ACTIVE status is denied by default (login and refresh)
    db_user.status = "PENDING"
    await user_repo.update(db_user)

    with pytest.raises(ForbiddenException, match="not active"):
        await service.refresh_session(login_res.refresh_token)
    with pytest.raises(ForbiddenException, match="not active"):
        await service.login(
            LoginRequest(email="refresh.svc@example.com", password="ValidPassword123@")
        )


async def test_auth_service_refresh_rejects_token_without_subject(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()
    service = AuthService(user_repo=user_repo, wallet_repo=wallet_repo, cognito_client=mock_cognito)

    async def malformed_refresh(_token: str) -> dict[str, object]:
        return {
            "accessToken": "not-a-jwt",
            "idToken": "also-not-a-jwt",
            "refreshToken": None,
            "expiresIn": 3600,
        }

    monkeypatch.setattr(mock_cognito, "refresh_tokens", malformed_refresh)

    with pytest.raises(UnauthorizedException, match="missing subject"):
        await service.refresh_session("mock_refresh_anything")
