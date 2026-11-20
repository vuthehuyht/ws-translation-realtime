"""Unit tests for S3 Storage Integration (app.integrations.s3)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import BadGatewayException
from app.integrations.s3 import AwsS3Client, get_s3_client


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


async def test_mock_s3_delete_prefix_only_deletes_matching_prefix() -> None:
    s3 = get_s3_client()
    await s3.upload_bytes("avatars/user-1/a.png", b"aaa", content_type="image/png")
    await s3.upload_bytes("avatars/user-1/b.png", b"bbb", content_type="image/png")
    await s3.upload_bytes("avatars/user-2/c.png", b"ccc", content_type="image/png")

    deleted = await s3.delete_prefix("avatars/user-1/")

    assert deleted == 2
    assert await s3.object_exists("avatars/user-1/a.png") is False
    assert await s3.object_exists("avatars/user-1/b.png") is False
    assert await s3.object_exists("avatars/user-2/c.png") is True

    with pytest.raises(ValueError, match="non-empty"):
        await s3.delete_prefix("")
    with pytest.raises(ValueError, match="non-empty"):
        await s3.delete_prefix("///")


async def test_aws_s3_delete_prefix_paginates_handles_partial_errors_and_client_error() -> None:
    mock_boto = AsyncMock()
    mock_boto.list_objects_v2.side_effect = [
        {
            "Contents": [{"Key": "avatars/u1/1.png"}, {"Key": "avatars/u1/2.png"}],
            "IsTruncated": True,
            "NextContinuationToken": "tok-2",
        },
        {
            "Contents": [{"Key": "avatars/u1/3.png"}],
            "IsTruncated": False,
        },
    ]
    mock_boto.delete_objects.side_effect = [
        {"Errors": [{"Key": "avatars/u1/2.png", "Code": "AccessDenied"}]},
        {"Errors": []},
    ]

    s3 = AwsS3Client(bucket_name="live-bucket", region="ap-southeast-1")
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_boto)
    ctx.__aexit__ = AsyncMock(return_value=False)
    s3.session = MagicMock()
    s3.session.client.return_value = ctx

    with pytest.raises(ValueError, match="non-empty"):
        await s3.delete_prefix("/")

    deleted = await s3.delete_prefix("avatars/u1/")

    # 3 attempted minus 1 reported error = 2 successfully deleted
    assert deleted == 2
    assert mock_boto.delete_objects.await_count == 2

    mock_boto.list_objects_v2.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Denied"}},
        "ListObjectsV2",
    )
    with pytest.raises(BadGatewayException, match="Storage service error"):
        await s3.delete_prefix("avatars/u1/")
