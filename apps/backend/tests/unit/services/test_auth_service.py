"""Unit tests for AuthService (app.services.auth_service)."""

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    ForbiddenException,
    ServiceUnavailableException,
    TooManyRequestsException,
    UnauthorizedException,
)
from app.integrations.cognito import MockCognitoClient
from app.models.user import User, UserProfile
from app.repositories.user_repository import UserRepository, hash_email
from app.repositories.wallet_repository import WalletRepository
from app.schemas.requests import (
    ConfirmRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResendOtpRequest,
)
from app.services.auth_service import (
    FORGOT_PASSWORD_MAX_ATTEMPTS,
    FORGOT_PASSWORD_WINDOW_SECONDS,
    AuthService,
)


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
    assert reg_res.user_sub is None

    # Under TASK-AUTH-01, PostgreSQL is NOT yet populated until OTP confirmation
    user_before_confirm = await user_repo.get_by_email("host.new@example.com")
    assert user_before_confirm is None

    # 2. Duplicate registration raises ConflictException (HTTP 409)
    with pytest.raises(ConflictException):
        await service.register(reg_req)

    # 3. Confirm sign up with OTP (TASK-AUTH-02)
    confirm_req = ConfirmRequest(
        email="host.new@example.com",
        otpCode="123456",
    )
    confirm_res = await service.confirm_sign_up(confirm_req)
    assert confirm_res.status == "CONFIRMED"
    assert confirm_res.model_dump() == {"status": "CONFIRMED"}

    # User in DB should now be ACTIVE, Wallet initialized ($2.00 Welcome Bonus), and Ledger recorded
    user = await user_repo.get_by_email("host.new@example.com")
    assert user is not None
    assert user.status == "ACTIVE"

    wallet = await wallet_repo.get_by_host_id(user.id)
    assert wallet is not None
    assert wallet.balance == Decimal("2.0000")

    welcome_tx = await wallet_repo.get_transaction_by_provider_id(f"welcome_{user.id}")
    assert welcome_tx is not None
    assert welcome_tx.type == "PROMO_CREDIT"
    assert welcome_tx.provider == "SYSTEM"
    assert welcome_tx.amount == Decimal("2.0000")
    assert welcome_tx.status == "SUCCEEDED"

    # Idempotent confirmation with valid code succeeds without double-crediting Welcome Bonus
    second_confirm = await service.confirm_sign_up(confirm_req)
    assert second_confirm.status == "CONFIRMED"
    wallet_after = await wallet_repo.get_by_host_id(user.id)
    assert wallet_after is not None
    assert wallet_after.balance == Decimal("2.0000")

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

    # 1. Unknown email returns uniform OTP_SENT to block email enumeration
    unknown_res = await service.resend_otp(ResendOtpRequest(email="unknown@example.com"))
    assert unknown_res.status == "OTP_SENT"
    assert unknown_res.retry_after == 60

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

    # 4. Confirmed user calling resend_otp also receives uniform OTP_SENT
    await fake_redis.delete("email:resend.test@example.com:resend_limit")
    await service.confirm_sign_up(
        ConfirmRequest(email="resend.test@example.com", otpCode="123456")
    )
    confirmed_res = await service.resend_otp(ResendOtpRequest(email="resend.test@example.com"))
    assert confirmed_res.status == "OTP_SENT"

    await fake_redis.aclose()


async def test_auth_service_resend_otp_redis_outage_and_cognito_error_preservation(
    db_session: AsyncSession,
) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    failing_redis = AsyncMock()
    failing_redis.set.side_effect = RedisConnectionError("Redis down")
    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
        redis_client=failing_redis,
    )

    with pytest.raises(ServiceUnavailableException, match="Rate limit store"):
        await service.resend_otp(ResendOtpRequest(email="anyone@example.com"))

    # When Cognito fails AND Redis cleanup also fails, the Cognito exception must surface.
    cleanup_failing_redis = AsyncMock()
    cleanup_failing_redis.set.return_value = True
    cleanup_failing_redis.delete.side_effect = RedisConnectionError("Redis delete failed")
    mock_cognito.resend_confirmation_code = AsyncMock(  # type: ignore[method-assign]
        side_effect=BadGatewayException("Authentication provider error")
    )
    service_2 = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
        redis_client=cleanup_failing_redis,
    )

    with pytest.raises(BadGatewayException, match="Authentication provider error"):
        await service_2.resend_otp(ResendOtpRequest(email="anyone@example.com"))


async def test_auth_service_suspended_user_login_fails(db_session: AsyncSession) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
    )

    await service.register(
        RegisterRequest(
            email="suspended@example.com",
            password="ValidPassword123@",
            fullName="Suspended Host",
        )
    )
    await service.confirm_sign_up(
        ConfirmRequest(email="suspended@example.com", otpCode="123456")
    )

    user = await user_repo.get_by_email("suspended@example.com")
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

    with pytest.raises(UnauthorizedException, match="Incorrect username or password"):
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

    await service.register(
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
    db_user = await user_repo.get_by_email("refresh.svc@example.com")
    assert db_user is not None

    # 1. Valid refresh returns new access/id tokens and user profile
    refreshed = await service.refresh_session(login_res.refresh_token)
    assert refreshed.response.tokens.access_token
    assert refreshed.response.tokens.id_token
    assert refreshed.refresh_token is None
    assert refreshed.response.tokens.expires_in == 3600
    assert refreshed.response.user.id == db_user.id
    assert refreshed.response.user.email == "refresh.svc@example.com"

    # 2. Blank refresh token raises UnauthorizedException
    with pytest.raises(UnauthorizedException, match="Missing refresh token"):
        await service.refresh_session("   ")

    # 3. Suspended user cannot refresh session
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


async def test_logout_requires_session_store(db_session: AsyncSession) -> None:
    service = AuthService(
        user_repo=UserRepository(session=db_session),
        wallet_repo=WalletRepository(session=db_session),
        cognito_client=MockCognitoClient(),
        redis_client=None,
    )

    # Returning success without a blocklist would claim a revocation that is not enforced.
    with pytest.raises(ServiceUnavailableException):
        await service.logout(
            access_token="t",
            subject="u1",
            expires_at=None,
            refresh_token="r",
            global_sign_out=False,
        )


async def _make_forgot_service(
    db_session: AsyncSession,
    *,
    redis_client: fakeredis.aioredis.FakeRedis | None = None,
    cognito_client: MockCognitoClient | None = None,
) -> tuple[AuthService, MockCognitoClient]:
    cognito = cognito_client or MockCognitoClient()
    service = AuthService(
        user_repo=UserRepository(db_session),
        wallet_repo=WalletRepository(db_session),
        cognito_client=cognito,
        redis_client=redis_client,
    )
    return service, cognito


async def _seed_user(
    db_session: AsyncSession,
    cognito: MockCognitoClient,
    *,
    email: str,
    status: str = "ACTIVE",
    confirmed: bool = True,
) -> User:
    sign_up_res = await cognito.sign_up(email=email, password="Password123@", full_name="Host User")
    if confirmed:
        await cognito.confirm_sign_up(email=email, confirmation_code="123456")
    user = User(id=sign_up_res["userSub"], email=email, role="HOST", status=status)
    profile = UserProfile(user_id=user.id, full_name="Host User")
    await UserRepository(db_session).create_user_with_profile(user=user, profile=profile)
    return user


async def test_forgot_password_active_user_succeeds_and_records_redis_slot(
    db_session: AsyncSession,
) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service, cognito = await _make_forgot_service(db_session, redis_client=redis)
    await _seed_user(db_session, cognito, email="active@example.com", status="ACTIVE")

    res = await service.forgot_password(ForgotPasswordRequest(email="  Active@Example.COM  "))

    assert res.status == "OTP_SENT"
    assert res.email == "active@example.com"
    assert cognito.users["active@example.com"].reset_code == "123456"
    rate_key = "email:active@example.com:forgot_password_attempts"
    assert await redis.zcard(rate_key) == 1
    assert 0 < await redis.ttl(rate_key) <= FORGOT_PASSWORD_WINDOW_SECONDS
    await redis.aclose()


async def test_forgot_password_anti_enumeration_unknown_and_unconfirmed_emails(
    db_session: AsyncSession,
) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service, cognito = await _make_forgot_service(db_session, redis_client=redis)
    await cognito.sign_up(email="unconfirmed@example.com", password="Password123@", full_name="U")

    unknown_res = await service.forgot_password(ForgotPasswordRequest(email="ghost@example.com"))
    unconfirmed_res = await service.forgot_password(
        ForgotPasswordRequest(email="unconfirmed@example.com")
    )

    assert unknown_res.status == "OTP_SENT"
    assert unknown_res.email == "ghost@example.com"
    assert unconfirmed_res.status == "OTP_SENT"
    assert unconfirmed_res.email == "unconfirmed@example.com"
    assert await redis.zcard("email:ghost@example.com:forgot_password_attempts") == 1
    assert await redis.zcard("email:unconfirmed@example.com:forgot_password_attempts") == 1
    await redis.aclose()


async def test_forgot_password_suspended_user_skips_cognito_and_returns_uniform_response(
    db_session: AsyncSession,
) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service, cognito = await _make_forgot_service(db_session, redis_client=redis)
    await _seed_user(db_session, cognito, email="suspended@example.com", status="SUSPENDED")
    cognito.forgot_password = AsyncMock(side_effect=AssertionError("Cognito must not be called"))

    res = await service.forgot_password(ForgotPasswordRequest(email="suspended@example.com"))

    assert res.status == "OTP_SENT"
    assert res.email == "suspended@example.com"
    assert await redis.zcard("email:suspended@example.com:forgot_password_attempts") == 1
    await redis.aclose()


async def test_forgot_password_sliding_window_rate_limit_blocks_4th_attempt_and_recovers(
    db_session: AsyncSession,
) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service, cognito = await _make_forgot_service(db_session, redis_client=redis)
    await _seed_user(db_session, cognito, email="limit@example.com", status="ACTIVE")
    await _seed_user(db_session, cognito, email="other@example.com", status="ACTIVE")

    # First 3 requests within 15 minutes succeed (mixed casing shares same key)
    for variant in ("limit@example.com", "LIMIT@example.com", "  Limit@Example.Com "):
        res = await service.forgot_password(ForgotPasswordRequest(email=variant))
        assert res.status == "OTP_SENT"

    # 4th request is rejected with 429 and accurate retryAfter without polluting ZSET
    rate_key = "email:limit@example.com:forgot_password_attempts"
    with pytest.raises(TooManyRequestsException) as exc_info:
        await service.forgot_password(ForgotPasswordRequest(email="limit@example.com"))

    retry_after = exc_info.value.details["retryAfter"]
    assert isinstance(retry_after, int)
    assert 1 <= retry_after <= FORGOT_PASSWORD_WINDOW_SECONDS
    assert await redis.zcard(rate_key) == FORGOT_PASSWORD_MAX_ATTEMPTS

    # Other emails remain unaffected
    other_res = await service.forgot_password(ForgotPasswordRequest(email="other@example.com"))
    assert other_res.status == "OTP_SENT"

    # Simulate oldest timestamp expiring past the 900s sliding window
    oldest = await redis.zrange(rate_key, 0, 0)
    await redis.zadd(rate_key, {oldest[0]: time.time() - FORGOT_PASSWORD_WINDOW_SECONDS - 5})

    recovered = await service.forgot_password(ForgotPasswordRequest(email="limit@example.com"))
    assert recovered.status == "OTP_SENT"
    assert await redis.zcard(rate_key) == FORGOT_PASSWORD_MAX_ATTEMPTS
    await redis.aclose()


async def test_forgot_password_fails_closed_when_redis_missing_or_down(
    db_session: AsyncSession,
) -> None:
    service_no_redis, cognito = await _make_forgot_service(db_session, redis_client=None)
    cognito.forgot_password = AsyncMock(side_effect=AssertionError("Cognito must not be called"))

    with pytest.raises(ServiceUnavailableException):
        await service_no_redis.forgot_password(ForgotPasswordRequest(email="host@example.com"))

    broken_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    broken_redis.pipeline = lambda *args, **kwargs: (_ for _ in ()).throw(
        RedisConnectionError("Redis offline")
    )
    service_broken, _ = await _make_forgot_service(db_session, redis_client=broken_redis)

    with pytest.raises(ServiceUnavailableException):
        await service_broken.forgot_password(ForgotPasswordRequest(email="host@example.com"))
    await broken_redis.aclose()


async def test_forgot_password_preserves_slot_on_cognito_throttle_and_rolls_back_on_5xx(
    db_session: AsyncSession,
) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service, cognito = await _make_forgot_service(db_session, redis_client=redis)
    await _seed_user(db_session, cognito, email="err@example.com", status="ACTIVE")
    rate_key = "email:err@example.com:forgot_password_attempts"

    # DB lookup failure also rolls back the Redis slot so the user does not lose an attempt
    original_get_by_email = service.user_repo.get_by_email
    service.user_repo.get_by_email = AsyncMock(side_effect=RuntimeError("DB timeout"))
    with pytest.raises(RuntimeError, match="DB timeout"):
        await service.forgot_password(ForgotPasswordRequest(email="err@example.com"))
    assert await redis.zcard(rate_key) == 0
    service.user_repo.get_by_email = original_get_by_email

    # Cognito 5xx rolls back the Redis slot so the user does not lose an attempt
    cognito.forgot_password = AsyncMock(side_effect=BadGatewayException("Provider down"))
    with pytest.raises(BadGatewayException):
        await service.forgot_password(ForgotPasswordRequest(email="err@example.com"))
    assert await redis.zcard(rate_key) == 0

    # Cognito 429 preserves the Redis slot
    cognito.forgot_password = AsyncMock(side_effect=TooManyRequestsException("Throttled"))
    with pytest.raises(TooManyRequestsException):
        await service.forgot_password(ForgotPasswordRequest(email="err@example.com"))
    assert await redis.zcard(rate_key) == 1

    # Rollback Redis failure must never mask the original BadGatewayException
    cognito.forgot_password = AsyncMock(side_effect=BadGatewayException("Provider down"))
    redis.zrem = AsyncMock(side_effect=RedisConnectionError("Cleanup failed"))
    with pytest.raises(BadGatewayException, match="Provider down"):
        await service.forgot_password(ForgotPasswordRequest(email="err@example.com"))
    await redis.aclose()


async def test_auth_service_register_blocks_deleted_email_during_7_day_cooldown(
    db_session: AsyncSession,
) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()
    mock_cognito.sign_up = AsyncMock(  # type: ignore[method-assign]
        side_effect=AssertionError("Cognito sign_up must not be called during cooldown")
    )
    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
    )

    now = datetime.now(UTC)
    allowed_at = now + timedelta(days=5)
    await user_repo.upsert_deleted_account_record(
        email_hash=hash_email("cooldown@example.com"),
        deleted_at=now - timedelta(days=2),
        re_register_allowed_at=allowed_at,
    )

    with pytest.raises(ForbiddenException) as exc_info:
        await service.register(
            RegisterRequest(
                email="  COOLDOWN@Example.COM ",
                password="SuperPassword123@",
                fullName="Returning Host",
            )
        )

    assert exc_info.value.error_code == "ACCOUNT_RE_REGISTRATION_COOLDOWN"
    assert exc_info.value.details["reRegisterAllowedAt"] == allowed_at.isoformat()
    assert exc_info.value.details["retryAfterSeconds"] > 0


async def test_auth_service_confirm_withholds_welcome_bonus_after_cooldown_expires(
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

    email = "returning.host@example.com"
    now = datetime.now(UTC)
    await user_repo.upsert_deleted_account_record(
        email_hash=hash_email(email),
        deleted_at=now - timedelta(days=8),
        re_register_allowed_at=now - timedelta(days=1),
    )

    reg_res = await service.register(
        RegisterRequest(
            email=email,
            password="SuperPassword123@",
            fullName="Returning Host",
        )
    )
    assert reg_res.status == "CONFIRMATION_REQUIRED"

    confirm_res = await service.confirm_sign_up(
        ConfirmRequest(email=email, otpCode="123456")
    )
    assert confirm_res.status == "CONFIRMED"

    user = await user_repo.get_by_email(email)
    assert user is not None
    wallet = await wallet_repo.get_by_host_id(user.id)
    assert wallet is not None
    assert wallet.balance == Decimal("0.0000")
    assert await wallet_repo.get_transaction_by_provider_id(f"welcome_{user.id}") is None
