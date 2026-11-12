"""Unit tests for Domain Exceptions & RFC 7807 Exception Handlers (app.core.exceptions)."""

from fastapi import APIRouter
from httpx import AsyncClient

from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    PaymentRequiredException,
    UnauthorizedException,
)
from app.main import app

# Dummy test router to trigger each exception
dummy_router = APIRouter(prefix="/test-exceptions")


@dummy_router.get("/not-found")
async def trigger_not_found() -> None:
    raise NotFoundException("User not found", details={"userId": "123"})


@dummy_router.get("/conflict")
async def trigger_conflict() -> None:
    raise ConflictException("Email already registered")


@dummy_router.get("/unauthorized")
async def trigger_unauthorized() -> None:
    raise UnauthorizedException("Token expired")


@dummy_router.get("/forbidden")
async def trigger_forbidden() -> None:
    raise ForbiddenException("Account suspended")


@dummy_router.get("/payment-required")
async def trigger_payment_required() -> None:
    raise PaymentRequiredException("Wallet balance depleted")


@dummy_router.get("/bad-gateway")
async def trigger_bad_gateway() -> None:
    raise BadGatewayException("Amazon Polly unavailable")


app.include_router(dummy_router)


async def test_not_found_exception_response(async_client: AsyncClient) -> None:
    response = await async_client.get("/test-exceptions/not-found")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["error"]["message"] == "User not found"
    assert payload["error"]["details"] == {"userId": "123"}


async def test_conflict_exception_response(async_client: AsyncClient) -> None:
    response = await async_client.get("/test-exceptions/conflict")
    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "RESOURCE_CONFLICT"
    assert payload["error"]["message"] == "Email already registered"


async def test_unauthorized_exception_response(async_client: AsyncClient) -> None:
    response = await async_client.get("/test-exceptions/unauthorized")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "UNAUTHORIZED"


async def test_forbidden_exception_response(async_client: AsyncClient) -> None:
    response = await async_client.get("/test-exceptions/forbidden")
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "FORBIDDEN"


async def test_payment_required_exception_response(async_client: AsyncClient) -> None:
    response = await async_client.get("/test-exceptions/payment-required")
    assert response.status_code == 402
    payload = response.json()
    assert payload["error"]["code"] == "INSUFFICIENT_FUNDS"


async def test_bad_gateway_exception_response(async_client: AsyncClient) -> None:
    response = await async_client.get("/test-exceptions/bad-gateway")
    assert response.status_code == 502
    payload = response.json()
    assert payload["error"]["code"] == "BAD_GATEWAY"
