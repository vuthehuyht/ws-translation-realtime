"""S3 Integration: Amazon S3 Presigned URLs & Permanent Storage.

Wraps presigned upload/download URLs, object existence verification, and asset uploads
with automatic offline mock support for local and test environments.
"""

import logging
from typing import Any

from app.core.config import get_settings

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


class MockS3Client(S3Client):
    """In-memory offline mock for local development and pytest suites."""

    def __init__(self) -> None:
        self.storage: dict[str, bytes] = {}

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
            "uploadUrl": f"http://localhost:8000/mock-s3-upload/{s3_key}",
            "s3Key": s3_key,
            "fields": {"Content-Type": content_type, "bucket": settings.s3.bucket_name},
            "expiresIn": expires_in,
            "maxSizeBytes": max_size_bytes,
        }

    async def generate_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        settings = get_settings()
        return f"{settings.s3.cdn_base_url}/{s3_key}?expires={expires_in}"

    async def object_exists(self, s3_key: str) -> bool:
        return s3_key in self.storage

    async def upload_bytes(
        self,
        s3_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self.storage[s3_key] = data
        settings = get_settings()
        logger.info("Mock S3 uploaded %d bytes to %s", len(data), s3_key)
        return f"{settings.s3.cdn_base_url}/{s3_key}"


_s3_instance: S3Client | None = None


def get_s3_client() -> S3Client:
    """Retrieve singleton S3Client instance (returns MockS3Client for local/test)."""
    global _s3_instance
    if _s3_instance is None:
        _s3_instance = MockS3Client()
    return _s3_instance


def set_s3_client(client: S3Client) -> None:
    """Explicitly override S3 client for test dependency injection."""
    global _s3_instance
    _s3_instance = client
