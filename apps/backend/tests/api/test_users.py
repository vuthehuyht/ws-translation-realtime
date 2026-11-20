"""Integration Tests for User Profile, Preferences, Billing Info, Avatar, and Security API."""

import pytest
from httpx import AsyncClient

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
