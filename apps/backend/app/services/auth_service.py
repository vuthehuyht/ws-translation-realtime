"""Authentication and Identity Business Service.

Orchestrates Cognito integration with PostgreSQL User and Wallet repositories.
"""

from decimal import Decimal

from app.core.exceptions import ConflictException, UnauthorizedException
from app.integrations.cognito import CognitoClient, get_cognito_client
from app.models.user import User, UserProfile
from app.models.wallet import Wallet
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.requests import (
    ConfirmRequest,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.responses import (
    LoginResponse,
    RegisterResponse,
    TokenResponse,
    UserProfileResponse,
)


class AuthService:
    """Service encapsulating user registration, confirmation, and login workflows."""

    def __init__(
        self,
        user_repo: UserRepository,
        wallet_repo: WalletRepository,
        cognito_client: CognitoClient | None = None,
    ) -> None:
        self.user_repo = user_repo
        self.wallet_repo = wallet_repo
        self.cognito = cognito_client or get_cognito_client()

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

    async def confirm_sign_up(self, request: ConfirmRequest) -> dict[str, str]:
        """Confirm user registration with verification code and initialize PostgreSQL records."""
        normalized_email = request.email.strip().lower()
        result = await self.cognito.confirm_sign_up(
            email=normalized_email,
            confirmation_code=request.confirmation_code,
        )
        user_info = await self.cognito.get_user_info(normalized_email)
        user_sub = result.get("sub") or user_info["sub"]
        full_name = user_info.get("name") or normalized_email.split("@")[0]

        # Atomic PostgreSQL initialization (TASK-AUTH-02)
        user = await self.user_repo.get_by_id(user_sub)
        if not user:
            user = User(
                id=user_sub,
                email=normalized_email,
                role="HOST",
                status="ACTIVE",
            )
            profile = UserProfile(
                user_id=user_sub,
                full_name=full_name,
                default_source_lang="vi-VN",
                default_target_langs=["en-US"],
            )
            await self.user_repo.create_user_with_profile(user=user, profile=profile)

            # Initialize default Wallet ($0.00)
            wallet = Wallet(
                host_id=user_sub,
                balance=Decimal("0.0000"),
                currency="USD",
                auto_degrade_tts=True,
                auto_topup_enabled=False,
            )
            await self.wallet_repo.create(wallet)
        else:
            user.status = "ACTIVE"
            await self.user_repo.update(user)

        return {"status": result.get("status", "CONFIRMED")}

    async def login(self, request: LoginRequest) -> LoginResponse:
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

        profile_data = user.profile
        return LoginResponse(
            tokens=TokenResponse(
                access_token=auth_tokens["accessToken"],
                id_token=auth_tokens["idToken"],
                refresh_token=auth_tokens["refreshToken"],
                expires_in=auth_tokens.get("expiresIn", 3600),
            ),
            user=UserProfileResponse(
                id=user.id,
                email=user.email,
                role=user.role,
                status=user.status,
                full_name=profile_data.full_name if profile_data else None,
                default_source_lang=profile_data.default_source_lang if profile_data else "vi-VN",
                default_target_langs=profile_data.default_target_langs if profile_data else [],
                timezone=profile_data.timezone if profile_data else "Asia/Ho_Chi_Minh",
            ),
        )
