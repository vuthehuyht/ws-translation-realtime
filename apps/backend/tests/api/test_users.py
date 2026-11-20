"""Integration Tests for User Profile, Preferences, Billing Info, Avatar, and Security API."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.s3 import get_s3_client
from app.models.room import Room
from app.models.user import DeletedAccountRecord, User
from app.models.wallet import PaymentTransaction
from app.repositories.user_repository import hash_email

pytestmark = pytest.mark.asyncio


async def _register_confirm_and_login(
    async_client: AsyncClient,
    *,
    email: str = "profile.host@example.com",
    password: str = "ValidPass123!",  # noqa: S107
    full_name: str = "Host User",
) -> dict[str, str]:
    """Create a confirmed host user and return auth headers + user id."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "fullName": full_name},
    )
    assert reg.status_code == 201

    confirm = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": email, "otpCode": "123456"},
    )
    assert confirm.status_code == 200

    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    body = login.json()
    return {
        "access_token": body["tokens"]["accessToken"],
        "user_id": body["user"]["id"],
    }


async def test_get_me_requires_authentication(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_me_returns_profile_and_wallet(async_client: AsyncClient) -> None:
    auth = await _register_confirm_and_login(async_client)
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {auth['access_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == auth["user_id"]
    assert data["email"] == "profile.host@example.com"
    assert data["fullName"] == "Host User"
    assert data["timezone"] == "Asia/Ho_Chi_Minh"
    assert data["defaultSourceLang"] == "vi-VN"
    assert data["defaultTargetLangs"] == ["en-US"]
    assert data["wallet"] is not None
    assert data["wallet"]["currency"] == "USD"
    assert float(data["wallet"]["balance"]) == 2.0


async def test_update_profile_basic_fields_and_validation(async_client: AsyncClient) -> None:
    auth = await _register_confirm_and_login(async_client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # Valid update
    response = await async_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={
            "fullName": "Nguyen Van Minh",
            "phoneNumber": "+84 901 234 567",
            "timezone": "Asia/Tokyo",
            "bio": "Conference host and interpreter.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fullName"] == "Nguyen Van Minh"
    assert data["phoneNumber"] == "+84901234567"
    assert data["timezone"] == "Asia/Tokyo"
    assert data["bio"] == "Conference host and interpreter."

    # Invalid phone number (not E.164)
    bad_phone = await async_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={"phoneNumber": "0901234567"},
    )
    assert bad_phone.status_code == 422

    # Invalid timezone
    bad_tz = await async_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={"timezone": "Mars/Olympus_Mons"},
    )
    assert bad_tz.status_code == 422


async def test_update_preferences_and_merge_json(async_client: AsyncClient) -> None:
    auth = await _register_confirm_and_login(async_client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    response = await async_client.patch(
        "/api/v1/users/me/preferences",
        headers=headers,
        json={
            "defaultSourceLang": "en-US",
            "defaultTargetLangs": ["vi-VN", "ja-JP", "vi-VN"],
            "preferences": {
                "vadSensitivity": "high",
                "subtitleMode": "bilingual",
                "uiLanguage": "vi",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["defaultSourceLang"] == "en-US"
    # Deduplicated while preserving order
    assert data["defaultTargetLangs"] == ["vi-VN", "ja-JP"]
    assert data["preferences"] == {
        "vadSensitivity": "high",
        "subtitleMode": "bilingual",
        "uiLanguage": "vi",
    }

    # Partial preferences update preserves previous keys
    response2 = await async_client.patch(
        "/api/v1/users/me/preferences",
        headers=headers,
        json={"preferences": {"subtitleMode": "target_only"}},
    )
    assert response2.status_code == 200
    assert response2.json()["preferences"] == {
        "vadSensitivity": "high",
        "subtitleMode": "target_only",
        "uiLanguage": "vi",
    }

    # Unsupported language fails validation
    bad_lang = await async_client.patch(
        "/api/v1/users/me/preferences",
        headers=headers,
        json={"defaultSourceLang": "xx-XX"},
    )
    assert bad_lang.status_code == 422


async def test_update_billing_info_vat_validation(async_client: AsyncClient) -> None:
    auth = await _register_confirm_and_login(async_client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    response = await async_client.put(
        "/api/v1/users/me/billing-info",
        headers=headers,
        json={
            "companyName": "VoiceBridge Vietnam JSC",
            "taxCode": "0101234567-001",
            "companyAddress": "District 1, Ho Chi Minh City",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["companyName"] == "VoiceBridge Vietnam JSC"
    assert data["taxCode"] == "0101234567-001"
    assert data["companyAddress"] == "District 1, Ho Chi Minh City"

    # Invalid tax code (too short)
    bad_tax = await async_client.put(
        "/api/v1/users/me/billing-info",
        headers=headers,
        json={"taxCode": "12345"},
    )
    assert bad_tax.status_code == 422


async def test_avatar_upload_and_confirm_flow(async_client: AsyncClient) -> None:
    auth = await _register_confirm_and_login(async_client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # 1. Request presigned upload URL
    upload_resp = await async_client.post(
        "/api/v1/users/me/avatar/upload-url",
        headers=headers,
        json={
            "fileName": "portrait.png",
            "fileType": "image/png",
            "fileSizeBytes": 1024,
        },
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    s3_key = upload_data["s3Key"]
    assert s3_key.startswith(f"avatars/{auth['user_id']}/")
    assert s3_key.endswith(".png")

    # Confirming before upload returns 400
    premature_confirm = await async_client.post(
        "/api/v1/users/me/avatar/confirm",
        headers=headers,
        json={"s3Key": s3_key},
    )
    assert premature_confirm.status_code == 400

    # 2. Upload bytes to mock presigned URL
    put_resp = await async_client.put(
        upload_data["uploadUrl"],
        content=b"\x89PNG\r\n\x1a\nfake-image-bytes",
        headers={"Content-Type": "image/png"},
    )
    assert put_resp.status_code == 204

    # 3. Confirm avatar
    confirm_resp = await async_client.post(
        "/api/v1/users/me/avatar/confirm",
        headers=headers,
        json={"s3Key": s3_key},
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["s3Key"] == s3_key
    assert confirm_data["avatarUrl"].endswith(s3_key)

    # Verify persisted on GET /users/me
    me = await async_client.get("/api/v1/users/me", headers=headers)
    assert me.json()["avatarUrl"] == confirm_data["avatarUrl"]

    # Cross-user key (IDOR) is rejected with 403
    idor_resp = await async_client.post(
        "/api/v1/users/me/avatar/confirm",
        headers=headers,
        json={"s3Key": "avatars/another-user/hack.png"},
    )
    assert idor_resp.status_code == 403

    # Oversized file (>2MB) fails validation
    oversized = await async_client.post(
        "/api/v1/users/me/avatar/upload-url",
        headers=headers,
        json={
            "fileName": "huge.jpg",
            "fileType": "image/jpeg",
            "fileSizeBytes": 2_097_153,
        },
    )
    assert oversized.status_code == 422


async def test_change_password_success_and_wrong_old_password(async_client: AsyncClient) -> None:
    auth = await _register_confirm_and_login(
        async_client,
        email="pw.host@example.com",
        password="OldPassword123!",
    )
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # Wrong current password -> 400
    wrong_old = await async_client.post(
        "/api/v1/users/me/change-password",
        headers=headers,
        json={
            "oldPassword": "WrongPassword123!",
            "newPassword": "NewPassword456@",
        },
    )
    assert wrong_old.status_code == 400

    # Same password -> 422
    same_pw = await async_client.post(
        "/api/v1/users/me/change-password",
        headers=headers,
        json={
            "oldPassword": "OldPassword123!",
            "newPassword": "OldPassword123!",
        },
    )
    assert same_pw.status_code == 422

    # Valid password change -> 200
    changed = await async_client.post(
        "/api/v1/users/me/change-password",
        headers=headers,
        json={
            "oldPassword": "OldPassword123!",
            "newPassword": "NewPassword456@",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["status"] == "PASSWORD_CHANGED"

    # Old password no longer logs in; new password succeeds
    old_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "pw.host@example.com", "password": "OldPassword123!"},
    )
    assert old_login.status_code == 401

    new_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "pw.host@example.com", "password": "NewPassword456@"},
    )
    assert new_login.status_code == 200


async def test_delete_me_validation_and_active_room_guard(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Unauthenticated request -> 401
    unauth = await async_client.request(
        "DELETE",
        "/api/v1/users/me",
        json={"confirmation": "DELETE"},
    )
    assert unauth.status_code == 401

    auth = await _register_confirm_and_login(
        async_client,
        email="active.room.host@example.com",
    )
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # Wrong confirmation string -> 422
    bad_confirm = await async_client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=headers,
        json={"confirmation": "NOPE"},
    )
    assert bad_confirm.status_code == 422

    # Active room owned by user blocks deletion with 409 Conflict
    room = Room(
        id="room-active-1",
        host_id=auth["user_id"],
        title="Live Event",
        source_language="vi-VN",
        target_languages=["en-US"],
        status="ACTIVE",
        host_token_hash="hashed-token",
    )
    db_session.add(room)
    await db_session.commit()

    conflict = await async_client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "RESOURCE_CONFLICT"


async def test_delete_me_gdpr_anonymization_cooldown_and_no_welcome_bonus_on_reregister(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = "gdpr.host@example.com"
    password = "ValidPass123!"  # noqa: S105
    auth = await _register_confirm_and_login(
        async_client,
        email=email,
        password=password,
        full_name="GDPR Host",
    )
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    first_user_id = auth["user_id"]

    # Populate profile PII, billing info, and upload an avatar to S3
    await async_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={"phoneNumber": "+84901234567", "bio": "Private bio"},
    )
    await async_client.put(
        "/api/v1/users/me/billing-info",
        headers=headers,
        json={
            "companyName": "Secret Corp",
            "taxCode": "0101234567",
            "companyAddress": "HCMC",
        },
    )
    upload_resp = await async_client.post(
        "/api/v1/users/me/avatar/upload-url",
        headers=headers,
        json={"fileName": "me.png", "fileType": "image/png", "fileSizeBytes": 256},
    )
    s3_key = upload_resp.json()["s3Key"]
    await async_client.put(
        upload_resp.json()["uploadUrl"],
        content=b"\x89PNG\r\n\x1a\nbytes",
        headers={"Content-Type": "image/png"},
    )
    await async_client.post(
        "/api/v1/users/me/avatar/confirm",
        headers=headers,
        json={"s3Key": s3_key},
    )
    assert await get_s3_client().object_exists(s3_key) is True

    # 1. Delete account -> 204, no-store headers, cookies cleared
    delete_resp = await async_client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert delete_resp.status_code == 204
    assert delete_resp.headers.get("cache-control") == "no-store"
    set_cookie_header = " ".join(delete_resp.headers.get_list("set-cookie"))
    assert "ws_refresh_token=" in set_cookie_header

    # 2. Existing JWT is immediately revoked in Redis, login & refresh fail
    after_me = await async_client.get("/api/v1/users/me", headers=headers)
    assert after_me.status_code == 401

    after_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert after_login.status_code == 401

    # 3. Verify DB anonymization preserved financial ledger and scrubbed PII
    db_session.expire_all()
    anonymized_user = (
        await db_session.execute(select(User).where(User.id == first_user_id))
    ).scalar_one()
    assert anonymized_user.status == "DELETED"
    assert anonymized_user.email == f"deleted_{first_user_id}@anonymized.invalid"

    await db_session.refresh(anonymized_user, attribute_names=["profile", "wallet"])
    assert anonymized_user.profile.full_name == "Deleted User"
    assert anonymized_user.profile.phone_number is None
    assert anonymized_user.profile.bio is None
    assert anonymized_user.profile.avatar_url is None
    assert anonymized_user.profile.company_name is None
    assert anonymized_user.profile.tax_code is None
    assert anonymized_user.profile.company_address is None
    assert anonymized_user.wallet.auto_topup_enabled is False

    # Financial ledger remains intact under the anonymized user id
    txs = (
        (
            await db_session.execute(
                select(PaymentTransaction).where(PaymentTransaction.host_id == first_user_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(txs) == 1
    assert txs[0].type == "PROMO_CREDIT"

    # Avatar deleted from S3
    assert await get_s3_client().object_exists(s3_key) is False

    # 4. DeletedAccountRecord created with hashed email and 7-day cooldown
    deleted_record = (
        await db_session.execute(
            select(DeletedAccountRecord).where(DeletedAccountRecord.email_hash == hash_email(email))
        )
    ).scalar_one()
    assert deleted_record.deletion_count == 1

    # 5. Re-registration within 7 days is rejected with 403 ACCOUNT_RE_REGISTRATION_COOLDOWN
    early_reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "fullName": "Returning Host"},
    )
    assert early_reg.status_code == 403
    early_err = early_reg.json()["error"]
    assert early_err["code"] == "ACCOUNT_RE_REGISTRATION_COOLDOWN"
    assert "reRegisterAllowedAt" in early_err["details"]
    assert early_err["details"]["retryAfterSeconds"] > 0

    # 6. Simulate 7 days elapsed -> re-registration succeeds WITHOUT new-account welcome bonus
    deleted_record.re_register_allowed_at = datetime.now(UTC) - timedelta(seconds=10)
    await db_session.commit()

    returning_auth = await _register_confirm_and_login(
        async_client,
        email=email,
        password=password,
        full_name="Returning Host",
    )
    returning_headers = {"Authorization": f"Bearer {returning_auth['access_token']}"}
    returning_me = await async_client.get("/api/v1/users/me", headers=returning_headers)
    assert returning_me.status_code == 200
    assert Decimal(returning_me.json()["wallet"]["balance"]) == Decimal("0.0000")

    returning_txs = (
        (
            await db_session.execute(
                select(PaymentTransaction).where(
                    PaymentTransaction.host_id == returning_auth["user_id"]
                )
            )
        )
        .scalars()
        .all()
    )
    assert returning_txs == []

    # 7. Deleting the re-registered account increments deletion_count via upsert
    second_delete = await async_client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=returning_headers,
        json={"confirmation": "DELETE"},
    )
    assert second_delete.status_code == 204
    db_session.expire_all()
    updated_record = (
        await db_session.execute(
            select(DeletedAccountRecord).where(DeletedAccountRecord.email_hash == hash_email(email))
        )
    ).scalar_one()
    assert updated_record.deletion_count == 2
