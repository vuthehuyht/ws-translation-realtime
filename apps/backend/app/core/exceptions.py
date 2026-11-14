"""Domain Exceptions and Global Exception Handlers.

Defines standardized, RFC 7807 compliant error schemas and FastAPI
middleware exception handlers for consistent API error responses.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application domain exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class NotFoundException(AppException):
    """Resource not found (HTTP 404)."""

    def __init__(
        self, message: str = "Resource not found", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class ConflictException(AppException):
    """Resource conflict or duplicate key (HTTP 409)."""

    def __init__(
        self, message: str = "Resource conflict", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details=details,
        )


class UnauthorizedException(AppException):
    """Authentication failed or token invalid (HTTP 401)."""

    def __init__(
        self, message: str = "Unauthorized", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenException(AppException):
    """Operation forbidden or insufficient permissions (HTTP 403)."""

    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            details=details,
        )


class ValidationException(AppException):
    """Business rule or input validation error (HTTP 422)."""

    def __init__(
        self, message: str = "Validation error", details: dict[str, Any] | list[Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class PaymentRequiredException(AppException):
    """Insufficient wallet balance to proceed (HTTP 402)."""

    def __init__(
        self, message: str = "Insufficient wallet balance", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="INSUFFICIENT_FUNDS",
            details=details,
        )


class BadGatewayException(AppException):
    """Downstream cloud service failure (HTTP 502)."""

    def __init__(
        self, message: str = "Downstream service error", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="BAD_GATEWAY",
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform RFC 7807 JSON error handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters or payload",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )
