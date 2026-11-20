"""Authenticated User Profile, Preferences, Billing Info, Avatar & Security Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.cookies import clear_refresh_cookies, set_no_store_headers
from app.api.deps import (
    AccessTokenContext,
    get_access_token_context,
    get_current_user,
    get_user_service,
)
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.integrations.s3 import MockS3Client, get_s3_client
from app.models.user import User
from app.schemas.requests.user import (
    MAX_AVATAR_SIZE_BYTES,
    AvatarConfirmRequest,
    AvatarUploadUrlRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    UpdateBillingInfoRequest,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)
from app.schemas.responses.user import (
    AvatarConfirmResponse,
    AvatarUploadUrlResponse,
    ChangePasswordResponse,
    UserMeResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's profile and wallet summary",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserMeResponse:
    """Return profile, translation preferences, VAT billing info, and wallet balance."""
    return await user_service.get_me(current_user.id)


@router.patch(
    "/me/profile",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update basic profile information",
)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserMeResponse:
    """Partially update fullName, phoneNumber, timezone, and bio."""
    return await user_service.update_profile(current_user.id, payload)


@router.patch(
    "/me/preferences",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update default translation languages and preferences",
)
async def update_preferences(
    payload: UpdatePreferencesRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserMeResponse:
    """Update defaultSourceLang, defaultTargetLangs, and UI/VAD preferences."""
    return await user_service.update_preferences(current_user.id, payload)


@router.put(
    "/me/billing-info",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update company and VAT billing information",
)
async def update_billing_info(
    payload: UpdateBillingInfoRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserMeResponse:
    """Replace companyName, taxCode, and companyAddress used on VAT invoices."""
    return await user_service.update_billing_info(current_user.id, payload)


@router.post(
    "/me/avatar/upload-url",
    response_model=AvatarUploadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate presigned S3 upload URL for avatar",
)
async def create_avatar_upload_url(
    payload: AvatarUploadUrlRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AvatarUploadUrlResponse:
    """Return a time-limited S3 PUT URL for direct client-side avatar upload."""
    return await user_service.create_avatar_upload_url(current_user.id, payload)


@router.post(
    "/me/avatar/confirm",
    response_model=AvatarConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm uploaded avatar object and update profile CDN URL",
)
async def confirm_avatar(
    payload: AvatarConfirmRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AvatarConfirmResponse:
    """Verify the avatar exists in S3 and persist its CDN URL on the user profile."""
    return await user_service.confirm_avatar(current_user.id, payload)


@router.put(
    "/me/avatar/mock-upload/{s3_key:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def mock_upload_avatar(
    s3_key: str,
    request: Request,
) -> Response:
    """Accept direct PUT uploads during local/test offline mode using MockS3Client."""
    s3_client = get_s3_client()
    if not isinstance(s3_client, MockS3Client):
        raise NotFoundException("Endpoint is only available in local mock storage mode")

    if not s3_key.startswith("avatars/") or ".." in s3_key or "\\" in s3_key:
        raise ForbiddenException("Invalid mock upload key")

    body = await request.body()
    if not body or len(body) > MAX_AVATAR_SIZE_BYTES:
        raise BadRequestException("Avatar file must be between 1 byte and 2 MB")

    content_type = request.headers.get("content-type", "application/octet-stream")
    await s3_client.upload_bytes(s3_key=s3_key, data=body, content_type=content_type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/me/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Change authenticated user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    token_context: Annotated[AccessTokenContext, Depends(get_access_token_context)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> ChangePasswordResponse:
    """Change the active user's password via Amazon Cognito ChangePassword."""
    return await user_service.change_password(token_context.token, payload)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete account and anonymize personal data (GDPR/PDPA)",
)
async def delete_me(
    payload: DeleteAccountRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    token_context: Annotated[AccessTokenContext, Depends(get_access_token_context)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Delete Cognito identity, revoke all sessions, anonymize PII, and clear auth cookies."""
    _ = payload
    await user_service.delete_account(
        user_id=current_user.id,
        access_token=token_context.token,
        expires_at=token_context.expires_at,
    )
    set_no_store_headers(response)
    clear_refresh_cookies(response)
