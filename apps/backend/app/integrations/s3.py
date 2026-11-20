"""S3 Integration: Amazon S3 Presigned URLs & Permanent Storage.

Wraps presigned upload/download URLs, object existence verification, and asset uploads
with automatic offline mock support for local and test environments.
"""

import logging
import os
from typing import Any

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.exceptions import BadGatewayException

logger = logging.getLogger(__name__)


class S3Client:
    """Interface for Amazon S3 asset operations."""

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        content_type: str,
        max_size_bytes: int = 2097152,
        expires_in: int = 900,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def generate_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError

    async def object_exists(self, s3_key: str) -> bool:
        raise NotImplementedError

    async def upload_bytes(
        self,
        s3_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        raise NotImplementedError

    def build_cdn_url(self, s3_key: str) -> str:
        """Build the public CDN URL for an uploaded S3 object key."""
        settings = get_settings()
        base = settings.s3.cdn_base_url.rstrip("/")
        return f"{base}/{s3_key.lstrip('/')}"


class MockS3Client(S3Client):
    """In-memory offline mock for local development and pytest suites."""

    def __init__(self) -> None:
        self.storage: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        content_type: str,
        max_size_bytes: int = 2097152,
        expires_in: int = 900,
    ) -> dict[str, Any]:
        settings = get_settings()
        logger.info("Generated mock presigned upload URL for: %s", s3_key)
        return {
            "uploadUrl": f"/api/v1/users/me/avatar/mock-upload/{s3_key}",
            "s3Key": s3_key,
            "fields": {"Content-Type": content_type, "bucket": settings.s3.bucket_name},
            "expiresIn": expires_in,
            "maxSizeBytes": max_size_bytes,
        }

    async def generate_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        return f"{self.build_cdn_url(s3_key)}?expires={expires_in}"

    async def object_exists(self, s3_key: str) -> bool:
        return s3_key in self.storage

    async def upload_bytes(
        self,
        s3_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self.storage[s3_key] = data
        self.content_types[s3_key] = content_type
        logger.info("Mock S3 uploaded %d bytes to %s", len(data), s3_key)
        return self.build_cdn_url(s3_key)


class AwsS3Client(S3Client):
    """Production Amazon S3 client using aioboto3."""

    def __init__(
        self,
        bucket_name: str,
        region: str = "ap-southeast-1",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        self.bucket_name = bucket_name
        self.region = region
        # Regional S3 endpoint avoids 307 redirects that break browser CORS preflight on PUT.
        self.endpoint_url = endpoint_url or f"https://s3.{region}.amazonaws.com"
        self._boto_config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        )
        session_kwargs: dict[str, str] = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key
            if aws_session_token:
                session_kwargs["aws_session_token"] = aws_session_token
        self.session = aioboto3.Session(**session_kwargs)

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        content_type: str,
        max_size_bytes: int = 2097152,
        expires_in: int = 900,
    ) -> dict[str, Any]:
        async with self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            config=self._boto_config,
        ) as client:
            try:
                upload_url = await client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": s3_key,
                        "ContentType": content_type,
                    },
                    ExpiresIn=expires_in,
                )
            except ClientError as e:
                logger.error("S3 generate_presigned_url failed for %s: %s", s3_key, e)
                raise BadGatewayException("Storage service error") from e

        return {
            "uploadUrl": upload_url,
            "s3Key": s3_key,
            "fields": {"Content-Type": content_type, "bucket": self.bucket_name},
            "expiresIn": expires_in,
            "maxSizeBytes": max_size_bytes,
        }

    async def generate_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        async with self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            config=self._boto_config,
        ) as client:
            try:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError as e:
                logger.error("S3 generate_presigned_download_url failed for %s: %s", s3_key, e)
                raise BadGatewayException("Storage service error") from e

    async def object_exists(self, s3_key: str) -> bool:
        async with self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            config=self._boto_config,
        ) as client:
            try:
                await client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
            except ClientError as e:
                error_code = str(e.response.get("Error", {}).get("Code", ""))
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    return False
                logger.error("S3 head_object failed for %s: %s", s3_key, e)
                raise BadGatewayException("Storage service error") from e

    async def upload_bytes(
        self,
        s3_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        async with self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            config=self._boto_config,
        ) as client:
            try:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=data,
                    ContentType=content_type,
                )
            except ClientError as e:
                logger.error("S3 put_object failed for %s: %s", s3_key, e)
                raise BadGatewayException("Storage service error") from e
        return self.build_cdn_url(s3_key)


_s3_instance: S3Client | None = None


def _has_live_s3_config(bucket_name: str) -> bool:
    """Return True when S3 bucket name is a non-placeholder live bucket."""
    return (
        bool(bucket_name)
        and not bucket_name.endswith("-local-media")
        and not bucket_name.startswith("dummy")
    )


def get_s3_client() -> S3Client:
    """Retrieve singleton S3Client instance (returns MockS3Client for local/test)."""
    global _s3_instance
    if _s3_instance is None:
        settings = get_settings()
        has_live = _has_live_s3_config(settings.s3.bucket_name)
        if not settings.app.is_local or (settings.env != "test" and has_live):
            _s3_instance = AwsS3Client(
                bucket_name=settings.s3.bucket_name,
                region=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                endpoint_url=settings.aws_endpoint_url,
            )
        else:
            _s3_instance = MockS3Client()
    return _s3_instance


def set_s3_client(client: S3Client) -> None:
    """Explicitly override S3 client for test dependency injection."""
    global _s3_instance
    _s3_instance = client
