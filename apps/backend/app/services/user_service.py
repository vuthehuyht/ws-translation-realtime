"""User Profile, Preferences, Billing Info, Avatar, and Security Service."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as aioredis

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
)
from app.integrations.cognito import get_cognito_client
from app.integrations.s3 import get_s3_client
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository, hash_email
from app.schemas.requests.user import (
    MAX_AVATAR_SIZE_BYTES,
    AvatarConfirmRequest,
    AvatarUploadUrlRequest,
    ChangePasswordRequest,
    UpdateBillingInfoRequest,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)
from app.schemas.responses.user import (
    AvatarConfirmResponse,
    AvatarUploadUrlResponse,
    ChangePasswordResponse,
    UserMeResponse,
    WalletSummaryResponse,
)
from app.services import token_blocklist

logger = logging.getLogger(__name__)

MIME_TO_EXTENSION: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

AVATAR_UPLOAD_TTL_SECONDS = 900  # 15 minutes
RE_REGISTRATION_COOLDOWN_DAYS = 7


class UserService:
    """Business logic for authenticated user profile management and password changes."""

    def __init__(
        self,
        user_repo: UserRepository,
        room_repo: RoomRepository | None = None,
        redis_client: aioredis.Redis | None = None,
    ) -> None:
        self.user_repo = user_repo
        self.room_repo = room_repo
        self.redis = redis_client

    @staticmethod
    def _build_user_me_response(user: User) -> UserMeResponse:
        """Map eager-loaded User, UserProfile, and Wallet entities into UserMeResponse."""
        profile = user.profile
        if profile is None:
            raise NotFoundException("User profile not found")

        wallet_summary = (
            WalletSummaryResponse(
                balance=user.wallet.balance,
                currency=user.wallet.currency,
                auto_degrade_tts=user.wallet.auto_degrade_tts,
                auto_topup_enabled=user.wallet.auto_topup_enabled,
            )
            if user.wallet is not None
            else None
        )

        return UserMeResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            status=user.status,
            full_name=profile.full_name,
            phone_number=profile.phone_number,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            timezone=profile.timezone,
            default_source_lang=profile.default_source_lang,
            default_target_langs=list(profile.default_target_langs or []),
            company_name=profile.company_name,
            tax_code=profile.tax_code,
            company_address=profile.company_address,
            preferences=dict(profile.preferences or {}),
            wallet=wallet_summary,
        )

    async def get_me(self, user_id: str) -> UserMeResponse:
        """Return the authenticated user's profile and embedded wallet summary."""
        user = await self.user_repo.get_by_id(
            user_id, include_profile=True, include_wallet=True
        )
        if not user:
            raise NotFoundException("User not found")
        return self._build_user_me_response(user)

    async def update_profile(
        self,
        user_id: str,
        payload: UpdateProfileRequest,
    ) -> UserMeResponse:
        """Partially update basic user profile attributes."""
        updates: dict[str, Any] = {}
        if "full_name" in payload.model_fields_set and payload.full_name is not None:
            updates["full_name"] = payload.full_name
        if "phone_number" in payload.model_fields_set:
            updates["phone_number"] = payload.phone_number
        if "timezone" in payload.model_fields_set and payload.timezone is not None:
            updates["timezone"] = payload.timezone
        if "bio" in payload.model_fields_set:
            updates["bio"] = payload.bio

        if updates:
            updated = await self.user_repo.update_profile(user_id, **updates)
            if not updated:
                raise NotFoundException("User profile not found")
            await self.user_repo.session.commit()

        return await self.get_me(user_id)

    async def update_preferences(
        self,
        user_id: str,
        payload: UpdatePreferencesRequest,
    ) -> UserMeResponse:
        """Update default translation languages and merged UI/VAD preferences."""
        user = await self.user_repo.get_by_id(
            user_id, include_profile=True, include_wallet=True
        )
        if not user or not user.profile:
            raise NotFoundException("User profile not found")

        updates: dict[str, Any] = {}
        if (
            "default_source_lang" in payload.model_fields_set
            and payload.default_source_lang is not None
        ):
            updates["default_source_lang"] = payload.default_source_lang
        if (
            "default_target_langs" in payload.model_fields_set
            and payload.default_target_langs is not None
        ):
            updates["default_target_langs"] = payload.default_target_langs
        if "preferences" in payload.model_fields_set and payload.preferences is not None:
            merged_preferences = {**(user.profile.preferences or {}), **payload.preferences}
            updates["preferences"] = merged_preferences

        if updates:
            await self.user_repo.update_profile(user_id, **updates)
            await self.user_repo.session.commit()

        return await self.get_me(user_id)

    async def update_billing_info(
        self,
        user_id: str,
        payload: UpdateBillingInfoRequest,
    ) -> UserMeResponse:
        """Replace company and VAT billing information on the user's profile."""
        updated = await self.user_repo.update_profile(
            user_id,
            company_name=payload.company_name,
            tax_code=payload.tax_code,
            company_address=payload.company_address,
        )
        if not updated:
            raise NotFoundException("User profile not found")
        await self.user_repo.session.commit()
        return await self.get_me(user_id)

    async def create_avatar_upload_url(
        self,
        user_id: str,
        payload: AvatarUploadUrlRequest,
    ) -> AvatarUploadUrlResponse:
        """Generate a scoped S3 presigned PUT URL for direct avatar upload."""
        ext = MIME_TO_EXTENSION[payload.file_type]
        s3_key = f"avatars/{user_id}/{uuid.uuid4()}.{ext}"
        presigned = await get_s3_client().generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=payload.file_type,
            max_size_bytes=MAX_AVATAR_SIZE_BYTES,
            expires_in=AVATAR_UPLOAD_TTL_SECONDS,
        )
        return AvatarUploadUrlResponse(**presigned)

    async def confirm_avatar(
        self,
        user_id: str,
        payload: AvatarConfirmRequest,
    ) -> AvatarConfirmResponse:
        """Verify the uploaded avatar exists in S3 under the user's prefix and save CDN URL."""
        expected_prefix = f"avatars/{user_id}/"
        s3_key = payload.s3_key.strip()
        # Prevent cross-user key binding (IDOR) and path traversal segments.
        if (
            not s3_key.startswith(expected_prefix)
            or ".." in s3_key
            or "\\" in s3_key
            or len(s3_key) <= len(expected_prefix)
        ):
            raise ForbiddenException("Avatar key does not belong to the authenticated user")

        s3_client = get_s3_client()
        exists = await s3_client.object_exists(s3_key)
        if not exists:
            raise BadRequestException("Uploaded avatar object was not found in storage")

        cdn_url = s3_client.build_cdn_url(s3_key)
        updated = await self.user_repo.update_profile(user_id, avatar_url=cdn_url)
        if not updated:
            raise NotFoundException("User profile not found")
        await self.user_repo.session.commit()

        return AvatarConfirmResponse(avatar_url=cdn_url, s3_key=s3_key)

    async def change_password(
        self,
        access_token: str,
        payload: ChangePasswordRequest,
    ) -> ChangePasswordResponse:
        """Change the authenticated user's password via Amazon Cognito."""
        await get_cognito_client().change_password(
            access_token=access_token,
            previous_password=payload.old_password,
            proposed_password=payload.new_password,
        )
        return ChangePasswordResponse()

    async def delete_account(
        self,
        *,
        user_id: str,
        access_token: str,
        expires_at: int | None,
    ) -> None:
        """Permanently delete Cognito identity, anonymize PII, and record 7-day cooldown.

        Financial ledgers (payment_transactions, usage_ledger) remain intact under the
        anonymized user row for tax/accounting compliance (FR-107).
        """
        # Fail closed if the room repository dependency was not wired; irreversible deletion
        # must never bypass active-session protection.
        if self.room_repo is None:
            raise ServiceUnavailableException("Room state store is temporarily unavailable")

        user = await self.user_repo.get_by_id(
            user_id,
            include_profile=True,
            include_wallet=True,
            for_update=True,
        )
        if not user:
            raise NotFoundException("User not found")

        if await self.room_repo.has_active_rooms(user_id):
            raise ConflictException(
                "Cannot delete account while you have active translation rooms. "
                "Please end all active rooms first."
            )

        email_hash = hash_email(user.email)
        now = datetime.now(UTC)
        re_register_allowed_at = now + timedelta(days=RE_REGISTRATION_COOLDOWN_DAYS)

        # Stage and flush PostgreSQL changes BEFORE the irreversible Cognito deletion so any
        # DB error or constraint violation aborts cleanly without touching Cognito.
        # Anonymize first so an explicit write transaction is active before the upsert savepoint.
        await self.user_repo.anonymize_user_account(user)
        await self.user_repo.upsert_deleted_account_record(
            email_hash=email_hash,
            deleted_at=now,
            re_register_allowed_at=re_register_allowed_at,
        )

        try:
            await get_cognito_client().delete_user(access_token=access_token)
        except Exception:
            await self.user_repo.session.rollback()
            raise

        try:
            await self.user_repo.session.commit()
        except Exception:
            logger.critical(
                "PostgreSQL commit failed AFTER Cognito delete_user succeeded for user %s; "
                "manual PII anonymization reconciliation required",
                user_id,
            )
            raise

        # Immediately revoke existing JWTs in Redis. If Redis is briefly unreachable after DB
        # commit, get_current_user still rejects the DELETED account on PostgreSQL.
        if self.redis is not None:
            try:
                await token_blocklist.revoke_all_for_subject(self.redis, user_id)
                await token_blocklist.revoke_access_token(self.redis, access_token, expires_at)
            except ServiceUnavailableException as exc:
                logger.error(
                    "Failed to revoke tokens in Redis after deleting user %s: %s",
                    user_id,
                    exc,
                )

        # Best-effort cleanup of uploaded avatar objects in S3.
        try:
            await get_s3_client().delete_prefix(f"avatars/{user_id}/")
        except Exception as exc:
            logger.warning("Failed to delete S3 avatars for deleted user %s: %s", user_id, exc)
