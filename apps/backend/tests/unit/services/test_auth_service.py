"""Unit tests for AuthService (app.services.auth_service)."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.integrations.cognito import MockCognitoClient
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.requests import ConfirmRequest, LoginRequest, RegisterRequest
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
    assert login_res.tokens.access_token is not None
    assert login_res.user.email == "host.new@example.com"
    assert login_res.user.full_name == "Nguyễn Văn A"
    assert login_res.user.role == "HOST"


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
