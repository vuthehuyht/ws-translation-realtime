"""Authentication and Identity Business Service.

Orchestrates Cognito integration with PostgreSQL User and Wallet repositories.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import jwt
import redis.asyncio as aioredis
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    TooManyRequestsException,
    UnauthorizedException,
)
from app.integrations.cognito import CognitoClient, get_cognito_client
from app.models.user import User, UserProfile
from app.models.wallet import PaymentTransaction, Wallet
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.requests import (
    ConfirmRequest,
    LoginRequest,
    RegisterRequest,
    ResendOtpRequest,
)
from app.schemas.responses import (
    ConfirmResponse,
    LoginResponse,
    RefreshResponse,
    RegisterResponse,
    ResendOtpResponse,
    TokenResponse,
    UserProfileResponse,
)

WELCOME_BONUS_AMOUNT = Decimal("2.0000")
RESEND_OTP_COOLDOWN_SECONDS = 60


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
        """Register user in Cognito without saving to DB until OTP confirmation."""
        normalized_email = request.email.strip().lower()

        # Check for active existing email in local database
        existing_user = await self.user_repo.get_by_email(normalized_email)
        if existing_user and existing_user.status == "ACTIVE":
            raise ConflictException(f"User with email '{normalized_email}' already exists")

        # Call AWS Cognito SignUp (sends OTP via Amazon SES)
        cognito_result = await self.cognito.sign_up(
            email=normalized_email,
            password=request.password,
            full_name=request.full_name,
        )
        user_sub = cognito_result["userSub"]

        # Note: Per TASK-AUTH-01 / FR-101.1, PostgreSQL persistence of users and wallets
        # is deferred until OTP is successfully confirmed in TASK-AUTH-02.
        return RegisterResponse(
            status="CONFIRMATION_REQUIRED",
            email=normalized_email,
            user_sub=user_sub,
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

        wallet = await self.wallet_repo.get_by_host_id(user_sub)
        if not wallet:
            try:
                async with session.begin_nested():
                    wallet = Wallet(
                        host_id=user_sub,
                        balance=WELCOME_BONUS_AMOUNT,
                        currency="USD",
                        auto_degrade_tts=True,
                        auto_topup_enabled=False,
                    )
                    await self.wallet_repo.create(wallet)
            except IntegrityError:
                wallet = await self.wallet_repo.get_by_host_id(user_sub)

        assert wallet is not None  # Guaranteed after insert or concurrent lookup

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
                        currency="USD",
                        status="SUCCEEDED",
                        metadata_json={"reason": "welcome_bonus"},
                        completed_at=datetime.now(UTC),
                    )
                    await self.wallet_repo.create_transaction(welcome_tx)
            except IntegrityError:
                pass

        return ConfirmResponse(
            status=result.get("status", "CONFIRMED"),
            user_sub=user_sub,
            wallet_balance=wallet.balance,
        )

    async def resend_otp(self, request: ResendOtpRequest) -> ResendOtpResponse:
        """Resend confirmation OTP with a 60-second Redis rate limit per email."""
        normalized_email = request.email.strip().lower()
        rate_key = f"email:{normalized_email}:resend_limit"

        if self.redis is not None:
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

        try:
            await self.cognito.resend_confirmation_code(normalized_email)
        except TooManyRequestsException:
            # Preserve the 60s Redis cooldown when Cognito itself throttles the request
            raise
        except Exception:
            if self.redis is not None:
                await self.redis.delete(rate_key)
            raise

        return ResendOtpResponse(
            status="OTP_SENT",
            email=normalized_email,
            retry_after=RESEND_OTP_COOLDOWN_SECONDS,
        )

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
        user = await self.user_repo.get_by_email(normalized_email)
        if not user:
            raise UnauthorizedException(
                f"User with email '{normalized_email}' not found in database"
            )
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
            default_source_lang=profile_data.default_source_lang if profile_data else "vi-VN",
            default_target_langs=profile_data.default_target_langs if profile_data else [],
            timezone=profile_data.timezone if profile_data else "Asia/Ho_Chi_Minh",
        )

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

        user = await self.user_repo.get_by_id(sub)
        if not user:
            raise UnauthorizedException(f"User '{sub}' not found in database")
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
