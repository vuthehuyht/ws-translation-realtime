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


async def test_auth_service_full_registration_and_login_lifecycle(db_session: AsyncSession) -> None:
    user_repo = UserRepository(session=db_session)
    wallet_repo = WalletRepository(session=db_session)
    mock_cognito = MockCognitoClient()

    service = AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        cognito_client=mock_cognito,
    )

    # 1. Register new host
    reg_req = RegisterRequest(
        email="host.new@example.com",
        password="SuperPassword123@",
        full_name="Nguyễn Văn A",
        role="HOST",
    )
    reg_res = await service.register(reg_req)
    assert reg_res.email == "host.new@example.com"
    assert reg_res.status == "PENDING_CONFIRMATION"

    # Verify wallet was initialized with $0.00
    wallet = await wallet_repo.get_by_host_id(reg_res.user_id)
    assert wallet is not None
    assert wallet.balance == Decimal("0.0000")

    # 2. Duplicate registration should fail
    with pytest.raises(ConflictException, match="already exists"):
        await service.register(reg_req)

    # 3. Confirm sign up
    confirm_req = ConfirmRequest(
        email="host.new@example.com",
        confirmation_code="123456",
    )
    confirm_res = await service.confirm_sign_up(confirm_req)
    assert confirm_res["status"] == "CONFIRMED"

    # User in DB should now be ACTIVE
    user = await user_repo.get_by_id(reg_res.user_id)
    assert user is not None
    assert user.status == "ACTIVE"

    # 4. Login
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
            full_name="Tester",
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
