"""Cloudflare R2 (S3-compatible) object storage for user photos.

Only object KEYS are stored in the database; the image bytes live in R2. boto3 is
imported lazily so the app still boots when the dependency or R2 config is absent -
the photo endpoints then fail loudly with a clear error (CLAUDE.md rule #12).
"""
from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageNotConfigured(RuntimeError):
    pass


def _client():
    if not settings.r2_configured:
        raise StorageNotConfigured("R2 is not configured (set R2_* in .env).")
    try:
        import boto3
    except ImportError as e:  # pragma: no cover
        raise StorageNotConfigured("boto3 is not installed; add it to requirements and pip install.") from e
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_bytes(data: bytes, key: str, content_type: str) -> str:
    """Upload bytes to R2 under `key`; returns the key. Synchronous - call via to_thread."""
    _client().put_object(Bucket=settings.R2_BUCKET, Key=key, Body=data, ContentType=content_type)
    return key


def delete_object(key: str) -> None:
    _client().delete_object(Bucket=settings.R2_BUCKET, Key=key)


def presigned_url(key: str, expires_in: int = 3600) -> str:
    """Time-limited GET URL so the client can fetch a private object."""
    return _client().generate_presigned_url(
        "get_object", Params={"Bucket": settings.R2_BUCKET, "Key": key}, ExpiresIn=expires_in
    )
