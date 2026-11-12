"""Unit tests for S3 Storage Integration (app.integrations.s3)."""

from app.integrations.s3 import get_s3_client


async def test_s3_presigned_urls_and_upload() -> None:
    s3 = get_s3_client()
    s3_key = "avatars/user-123/avatar.png"

    # 1. Generate presigned upload URL
    upload_data = await s3.generate_presigned_upload_url(
        s3_key=s3_key,
        content_type="image/png",
        max_size_bytes=2097152,
    )
    assert upload_data["s3Key"] == s3_key
    assert "uploadUrl" in upload_data
    assert upload_data["maxSizeBytes"] == 2097152

    # 2. Object does not exist initially
    assert await s3.object_exists(s3_key) is False

    # 3. Upload bytes directly
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    cdn_url = await s3.upload_bytes(s3_key, image_bytes, content_type="image/png")
    assert s3_key in cdn_url
    assert await s3.object_exists(s3_key) is True

    # 4. Generate presigned download URL
    download_url = await s3.generate_presigned_download_url(s3_key, expires_in=1800)
    assert s3_key in download_url
    assert "expires=1800" in download_url
