"""Authentication and Identity Business Service.

Orchestrates Cognito integration with PostgreSQL User and Wallet repositories.
"""

import logging
import math
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import jwt
import redis.asyncio as aioredis
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
    TooManyRequestsException,
    UnauthorizedException,
    ValidationException,
)
from app.integrations.cognito import CognitoClient, get_cognito_client
from app.models.user import User, UserProfile
from app.models.wallet import PaymentTransaction, Wallet
from app.repositories.user_repository import UserRepository, hash_email
from app.repositories.wallet_repository import WalletRepository
from app.schemas.requests import (
    ConfirmRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
)
from app.schemas.responses import (
    ConfirmResponse,
    ForgotPasswordResponse,
    LoginResponse,
    RefreshResponse,
    RegisterResponse,
    ResendOtpResponse,
    ResetPasswordResponse,
    TokenResponse,
    UserProfileResponse,
)
from app.services import token_blocklist

WELCOME_BONUS_AMOUNT = Decimal("200.0000")  # Credits
RESEND_OTP_COOLDOWN_SECONDS = 60
FORGOT_PASSWORD_MAX_ATTEMPTS = 3
FORGOT_PASSWORD_WINDOW_SECONDS = 900
RESET_PASSWORD_MAX_FAILED_ATTEMPTS = 5
RESET_PASSWORD_WINDOW_SECONDS = 900
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LoginResult:
    """Public login payload plus the refresh token that must only be set as an HttpOnly cookie."""

    response: LoginResponse
    refresh_token: str


@dataclass(frozen=True, slots=True)
class RefreshResult:
    """Public refresh payload plus the rotated refresh token (None if Cognito did not rotate)."""

    response: RefreshResponse
    refresh_token: str | None


class AuthService:
    """Service encapsulating user registration, confirmation, and login workflows."""

    def __init__(
        self,
        user_repo: UserRepository,
        wallet_repo: WalletRepository,
        cognito_client: CognitoClient | None = None,
        redis_client: aioredis.Redis | None = None,
    ) -> None:
        self.user_repo = user_repo
        self.wallet_repo = wallet_repo
        self.cognito = cognito_client or get_cognito_client()
        self.redis = redis_client

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """Register a new user in Cognito and reject duplicate or cooldown-locked emails."""
        normalized_email = request.email.strip().lower()

        existing_user = await self.user_repo.get_by_email(normalized_email)
        if existing_user and existing_user.status == "ACTIVE":
            raise ConflictException("An account with this email already exists")

        deleted_record = await self.user_repo.get_deleted_account_by_email_hash(
            hash_email(normalized_email)
        )
        if deleted_record is not None:
            now = datetime.now(UTC)
            re_register_at = (
                deleted_record.re_register_allowed_at.replace(tzinfo=UTC)
                if deleted_record.re_register_allowed_at.tzinfo is None
                else deleted_record.re_register_allowed_at
            )
            if now < re_register_at:
                retry_after_seconds = max(1, math.ceil((re_register_at - now).total_seconds()))
                raise ForbiddenException(
                    message=(
                        "This email was recently deleted and cannot be re-registered "
                        "for 7 days."
                    ),
                    error_code="ACCOUNT_RE_REGISTRATION_COOLDOWN",
                    details={
                        "reRegisterAllowedAt": re_register_at.isoformat(),
                        "retryAfterSeconds": retry_after_seconds,
                    },
                )

        await self.cognito.sign_up(
            email=normalized_email,
            password=request.password,
            full_name=request.full_name,
        )

        # Note: Per TASK-AUTH-01 / FR-101.1, PostgreSQL persistence of users and wallets
        # is deferred until OTP is successfully confirmed in TASK-AUTH-02.
        return RegisterResponse(
            status="CONFIRMATION_REQUIRED",
            email=normalized_email,
        )

    async def confirm_sign_up(self, request: ConfirmRequest) -> ConfirmResponse:
        """Confirm user registration with verification code and initialize PostgreSQL records."""
        normalized_email = request.email.strip().lower()
        result = await self.cognito.confirm_sign_up(
            email=normalized_email,
            confirmation_code=request.confirmation_code,
        )
        user_sub = result.get("sub")
        full_name = result.get("name")
        if not user_sub or full_name is None:
            user_info = await self.cognito.get_user_info(normalized_email)
            user_sub = user_sub or user_info["sub"]
            full_name = user_info.get("name") or normalized_email.split("@")[0]
        else:
            full_name = full_name or normalized_email.split("@")[0]

        session = self.user_repo.session

        # Idempotent ACID initialization across users, user_profiles, wallets, and ledger.
        # Savepoints guard against concurrent duplicate confirm requests under READ COMMITTED.
        user = await self.user_repo.get_by_id(user_sub)
        if not user:
            try:
                async with session.begin_nested():
                    user = User(
                        id=user_sub,
                        email=normalized_email,
                        role="HOST",
                        status="ACTIVE",
                    )
                    profile = UserProfile(
                        user_id=user_sub,
                        full_name=full_name,
                        timezone="Asia/Ho_Chi_Minh",
                        default_source_lang="vi-VN",
                        default_target_langs=["en-US"],
                    )
                    await self.user_repo.create_user_with_profile(user=user, profile=profile)
            except IntegrityError:
                user = await self.user_repo.get_by_id(user_sub)
        elif user.status != "ACTIVE":
            user.status = "ACTIVE"
            await self.user_repo.update(user)

        # Re-registered emails that previously deleted their account do not receive
        # new-account welcome benefits (welcome credit bonus).
        prior_deleted_record = await self.user_repo.get_deleted_account_by_email_hash(
            hash_email(normalized_email)
        )
        eligible_for_welcome_bonus = prior_deleted_record is None
        initial_balance = WELCOME_BONUS_AMOUNT if eligible_for_welcome_bonus else Decimal("0.0000")

        wallet = await self.wallet_repo.get_by_host_id(user_sub)
        if not wallet:
            try:
                async with session.begin_nested():
                    wallet = Wallet(
                        host_id=user_sub,
                        balance=initial_balance,
                        auto_degrade_tts=True,
                        auto_topup_enabled=False,
                    )
                    await self.wallet_repo.create(wallet)
            except IntegrityError:
                wallet = await self.wallet_repo.get_by_host_id(user_sub)

        assert wallet is not None  # Guaranteed after insert or concurrent lookup

        if eligible_for_welcome_bonus:
            welcome_tx_id = f"welcome_{user_sub}"
            existing_tx = await self.wallet_repo.get_transaction_by_provider_id(welcome_tx_id)
            if not existing_tx:
                try:
                    async with session.begin_nested():
                        welcome_tx = PaymentTransaction(
                            host_id=user_sub,
                            transaction_id=welcome_tx_id,
                            type="PROMO_CREDIT",
                            provider="SYSTEM",
                            amount=WELCOME_BONUS_AMOUNT,
                            status="SUCCEEDED",
                            metadata_json={"reason": "welcome_bonus"},
                            completed_at=datetime.now(UTC),
                        )
                        await self.wallet_repo.create_transaction(welcome_tx)
                except IntegrityError:
                    pass

        return ConfirmResponse(
            status=result.get("status", "CONFIRMED"),
        )

    async def resend_otp(self, request: ResendOtpRequest) -> ResendOtpResponse:
        """Resend confirmation OTP with a 60-second Redis rate limit per email."""
        normalized_email = request.email.strip().lower()
        rate_key = f"email:{normalized_email}:resend_limit"

        if self.redis is not None:
            try:
                acquired = await self.redis.set(
                    rate_key, "1", ex=RESEND_OTP_COOLDOWN_SECONDS, nx=True
                )
                if not acquired:
                    ttl = await self.redis.ttl(rate_key)
                    retry_after = ttl if ttl > 0 else RESEND_OTP_COOLDOWN_SECONDS
                    raise TooManyRequestsException(
                        f"Please wait {retry_after} seconds before requesting another OTP",
                        details={"retryAfter": retry_after},
                    )
            except RedisError as exc:
                raise ServiceUnavailableException(
                    "Rate limit store is temporarily unavailable"
                ) from exc

        try:
            await self.cognito.resend_confirmation_code(normalized_email)
        except (NotFoundException, ConflictException):
            # Return the same 200 response for unknown or already-confirmed emails to block
            # account enumeration while preserving the 60s cooldown against abuse.
            return ResendOtpResponse(
                status="OTP_SENT",
                email=normalized_email,
                retry_after=RESEND_OTP_COOLDOWN_SECONDS,
            )
        except TooManyRequestsException:
            # Preserve the 60s Redis cooldown when Cognito itself throttles the request
            raise
        except Exception:
            if self.redis is not None:
                try:
                    await self.redis.delete(rate_key)
                except RedisError as redis_exc:
                    # Never mask the original Cognito error when Redis cleanup also fails.
                    logger.warning("Failed to roll back resend_otp cooldown key: %s", redis_exc)
            raise

        return ResendOtpResponse(
            status="OTP_SENT",
            email=normalized_email,
            retry_after=RESEND_OTP_COOLDOWN_SECONDS,
        )

    async def forgot_password(self, request: ForgotPasswordRequest) -> ForgotPasswordResponse:
        """Initiate password reset OTP with a 3-per-15-minute sliding-window Redis rate limit."""
        normalized_email = request.email.strip().lower()
        if self.redis is None:
            raise ServiceUnavailableException("Rate limit store is temporarily unavailable")

        rate_key = f"email:{normalized_email}:forgot_password_attempts"
        now = time.time()
        window_start = now - FORGOT_PASSWORD_WINDOW_SECONDS
        member = f"{now:.6f}:{uuid.uuid4().hex}"

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(rate_key, "-inf", window_start)
                pipe.zadd(rate_key, {member: now})
                pipe.zcard(rate_key)
                pipe.zrange(rate_key, 0, 0, withscores=True)
                pipe.expire(rate_key, FORGOT_PASSWORD_WINDOW_SECONDS)
                _, _, attempt_count, oldest_entries, _ = await pipe.execute()

            if int(attempt_count) > FORGOT_PASSWORD_MAX_ATTEMPTS:
                # Remove the rejected request so spam does not pollute the sliding window.
                await self.redis.zrem(rate_key, member)
                if oldest_entries:
                    oldest_ts = float(oldest_entries[0][1])
                    retry_after = min(
                        FORGOT_PASSWORD_WINDOW_SECONDS,
                        max(1, math.ceil(oldest_ts + FORGOT_PASSWORD_WINDOW_SECONDS - now)),
                    )
                else:
                    retry_after = FORGOT_PASSWORD_WINDOW_SECONDS
                raise TooManyRequestsException(
                    "Too many password reset requests. "
                    f"Please wait {retry_after} seconds before trying again.",
                    details={"retryAfter": retry_after},
                )
        except RedisError as exc:
            raise ServiceUnavailableException(
                "Rate limit store is temporarily unavailable"
            ) from exc

        try:
            # Block suspended or non-active accounts from triggering reset emails while keeping
            # the response identical to active accounts to prevent account enumeration.
            user = await self.user_repo.get_by_email(normalized_email)
            if user is not None and user.status != "ACTIVE":
                return ForgotPasswordResponse(email=normalized_email)

            await self.cognito.forgot_password(normalized_email)
        except (NotFoundException, ConflictException):
            return ForgotPasswordResponse(email=normalized_email)
        except TooManyRequestsException:
            # Preserve the consumed Redis slot when Cognito itself throttles the request.
            raise
        except Exception:
            try:
                await self.redis.zrem(rate_key, member)
            except RedisError as redis_exc:
                # Never mask the original provider/DB error when Redis cleanup also fails.
                logger.warning(
                    "Failed to roll back forgot_password rate-limit entry: %s", redis_exc
                )
            raise

        return ForgotPasswordResponse(email=normalized_email)

    async def reset_password(self, request: ResetPasswordRequest) -> ResetPasswordResponse:
        """Confirm password reset with OTP and revoke all existing sessions across devices."""
        normalized_email = request.email.strip().lower()
        if self.redis is None:
            raise ServiceUnavailableException("Rate limit store is temporarily unavailable")

        # A 6-digit OTP has only 10^6 possibilities, so cap wrong guesses per email on top of
        # Cognito's own throttling.
        failure_key = f"email:{normalized_email}:reset_password_failures"
        await self._ensure_reset_attempts_allowed(failure_key)

        # Block suspended or non-active accounts with the same error as an invalid OTP
        # to avoid revealing account status.
        user = await self.user_repo.get_by_email(normalized_email)
        if user is not None and user.status != "ACTIVE":
            raise ValidationException("Invalid or expired reset code")

        try:
            await self.cognito.confirm_forgot_password(
                email=normalized_email,
                confirmation_code=request.otp_code,
                new_password=request.new_password,
            )
        except ValidationException:
            await self._record_reset_failure(failure_key)
            raise

        try:
            await self.redis.delete(failure_key)
        except RedisError as exc:
            logger.warning("Failed to clear reset_password failure counter: %s", exc)

        # Password is now updated in Cognito; revoke old sessions best-effort so a transient
        # revocation failure never misleads the caller into thinking the reset failed.
        # Only swallow the known provider error, and log at error level because old sessions
        # may still be alive.
        try:
            await self.cognito.admin_global_sign_out(normalized_email)
        except BadGatewayException as exc:
            logger.error(
                "Post-reset Cognito global sign-out failed; refresh tokens may remain valid: %s",
                exc,
            )

        if user is not None:
            try:
                await token_blocklist.revoke_all_for_subject(self.redis, user.id)
            except RedisError as exc:
                logger.error("Post-reset Redis token revocation failed: %s", exc)

        return ResetPasswordResponse()

    async def _ensure_reset_attempts_allowed(self, failure_key: str) -> None:
        """Reject further OTP guesses once the per-email failure budget is exhausted."""
        assert self.redis is not None
        try:
            raw_count = await self.redis.get(failure_key)
            if raw_count is not None and int(raw_count) >= RESET_PASSWORD_MAX_FAILED_ATTEMPTS:
                ttl = await self.redis.ttl(failure_key)
                retry_after = ttl if ttl > 0 else RESET_PASSWORD_WINDOW_SECONDS
                raise TooManyRequestsException(
                    "Too many failed password reset attempts. "
                    f"Please wait {retry_after} seconds before trying again.",
                    details={"retryAfter": retry_after},
                )
        except RedisError as exc:
            raise ServiceUnavailableException(
                "Rate limit store is temporarily unavailable"
            ) from exc

    async def _record_reset_failure(self, failure_key: str) -> None:
        """Count a failed OTP confirmation; window starts at the first failure."""
        assert self.redis is not None
        try:
            count = await self.redis.incr(failure_key)
            if int(count) == 1:
                await self.redis.expire(failure_key, RESET_PASSWORD_WINDOW_SECONDS)
        except RedisError as exc:
            # Never mask the original validation error when Redis is down; log only.
            logger.warning("Failed to record reset_password failure: %s", exc)

    @staticmethod
    def _ensure_active(user: User) -> None:
        """Default-deny: only ACTIVE accounts may obtain or renew a session."""
        if user.status == "SUSPENDED":
            raise ForbiddenException("Account is suspended")
        if user.status != "ACTIVE":
            raise ForbiddenException("Account is not active")

    async def login(self, request: LoginRequest) -> LoginResult:
        """Authenticate user against Cognito and retrieve profile details from database."""
        normalized_email = request.email.strip().lower()

        # Authenticate via Cognito
        auth_tokens = await self.cognito.authenticate(
            email=normalized_email,
            password=request.password,
        )

        # Retrieve user and profile from database
        user = await self.user_repo.get_by_email(normalized_email, include_profile=True)
        if not user:
            raise UnauthorizedException("Incorrect username or password")
        self._ensure_active(user)

        return LoginResult(
            response=LoginResponse(
                tokens=TokenResponse(
                    access_token=auth_tokens["accessToken"],
                    id_token=auth_tokens["idToken"],
                    expires_in=auth_tokens.get("expiresIn", 3600),
                ),
                user=self._build_user_profile(user),
            ),
            refresh_token=auth_tokens["refreshToken"],
        )

    @staticmethod
    def _build_user_profile(user: User) -> UserProfileResponse:
        """Map User ORM entity and optional profile relation into UserProfileResponse."""
        profile_data = user.profile
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            status=user.status,
            full_name=profile_data.full_name if profile_data else None,
            avatar_url=profile_data.avatar_url if profile_data else None,
            default_source_lang=profile_data.default_source_lang if profile_data else "vi-VN",
            default_target_langs=profile_data.default_target_langs if profile_data else [],
            timezone=profile_data.timezone if profile_data else "Asia/Ho_Chi_Minh",
        )

    async def logout(
        self,
        *,
        access_token: str,
        subject: str,
        expires_at: int | None,
        refresh_token: str | None,
        global_sign_out: bool,
        session_id: str | None = None,
    ) -> None:
        """Revoke the session at Cognito, then block the access token locally.

        Cognito goes first so a Cognito outage leaves the session intact and the client can
        retry. An UnauthorizedException from Cognito means the token is already dead, which is
        the desired end state, so the call stays idempotent.
        """
        if self.redis is None:
            # Without the blocklist a 204 would claim a revocation that is not enforced.
            raise ServiceUnavailableException("Session store is not configured")

        if global_sign_out and expires_at is not None and expires_at <= int(time.time()):
            # GlobalSignOut needs a live access token; the client must refresh and retry
            # instead of us silently skipping the Cognito half of a global sign-out.
            raise UnauthorizedException("Access token expired; refresh and retry global sign-out")

        try:
            if global_sign_out:
                await self.cognito.global_sign_out(access_token)
            elif refresh_token:
                await self.cognito.revoke_token(refresh_token)
        except UnauthorizedException:
            pass

        # Access tokens are validated locally, so Cognito revocation alone would not stop them.
        if global_sign_out:
            await token_blocklist.revoke_all_for_subject(self.redis, subject)
        else:
            await token_blocklist.revoke_access_token(self.redis, access_token, expires_at)
            if session_id:
                # Earlier unexpired access tokens of the same session must die with it.
                await token_blocklist.revoke_session(self.redis, session_id)

    async def refresh_session(self, refresh_token: str) -> RefreshResult:
        """Refresh access and ID tokens via Cognito while enforcing account status."""
        normalized_token = refresh_token.strip()
        if not normalized_token:
            raise UnauthorizedException("Missing refresh token")

        refreshed = await self.cognito.refresh_tokens(normalized_token)

        # Decode unverified claims solely to read sub because the token was just
        # received directly over TLS from Cognito InitiateAuth.
        sub: str | None = None
        for token_key in ("idToken", "accessToken"):
            raw_jwt = refreshed.get(token_key)
            if not raw_jwt:
                continue
            try:
                claims = jwt.decode(raw_jwt, options={"verify_signature": False})
                candidate = claims.get("sub")
                if isinstance(candidate, str) and candidate:
                    sub = candidate
                    break
            except jwt.PyJWTError:
                continue

        if not sub:
            raise UnauthorizedException("Refreshed token missing subject identifier")

        user = await self.user_repo.get_by_id(sub, include_profile=True)
        if not user:
            raise UnauthorizedException("Session is invalid")
        self._ensure_active(user)

        return RefreshResult(
            response=RefreshResponse(
                tokens=TokenResponse(
                    access_token=refreshed["accessToken"],
                    id_token=refreshed["idToken"],
                    expires_in=refreshed.get("expiresIn", 3600),
                ),
                user=self._build_user_profile(user),
            ),
            refresh_token=refreshed.get("refreshToken"),
        )
