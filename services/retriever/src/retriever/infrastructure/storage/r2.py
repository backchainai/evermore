# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Cloudflare R2 storage backend backed by the boto3 S3-compatible client.

R2 speaks the S3 API, so boto3's S3 client works against it unchanged. boto3's
calls are synchronous, so each one is offloaded to a worker thread to keep the
async interface non-blocking. boto3 is imported lazily inside ``build_r2_storage``
so this module imports without boto3 installed and offline unit tests never need
it; an injected client (see ``R2Storage.__init__``) is enough to exercise it.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

from retriever.infrastructure.storage.exceptions import (
    ObjectNotFoundError,
    StorageConfigError,
)

if TYPE_CHECKING:
    from retriever.config import Settings
    from retriever.infrastructure.storage.protocol import S3Client

# S3 error code that means "the object is not there" on the get path.
# get_object raises ClientError with code "NoSuchKey" for a missing key; "404"
# only comes from head_object (never called here) and "NoSuchBucket" is a
# misconfiguration, not a per-object not-found, so neither belongs here.
_NOT_FOUND_CODES = frozenset({"NoSuchKey"})


class R2Storage:
    """StorageBackend implementation wrapping an injected boto3 S3 client.

    The client and the ``ClientError`` type are injected so the backend can be
    tested against a hand-written double with no boto3 dependency. Use
    ``build_r2_storage`` to construct a production instance from settings.
    """

    def __init__(
        self,
        client: S3Client,
        *,
        bucket: str,
        client_error: type[Exception],
    ) -> None:
        """Initialize the backend.

        Args:
            client: An S3-compatible client (boto3 client or test double).
            bucket: The R2 bucket name to operate against.
            client_error: The exception type raised by the client on API errors
                (botocore's ``ClientError`` in production); inspected to map a
                missing object onto ``ObjectNotFoundError``.
        """
        self._client = client
        self._bucket = bucket
        self._client_error = client_error

    def _is_not_found(self, exc: Exception) -> bool:
        """Return True if ``exc`` is a client error for a missing object."""
        if not isinstance(exc, self._client_error):
            return False
        response = getattr(exc, "response", None)
        if not isinstance(response, dict):
            return False
        code = response.get("Error", {}).get("Code")
        return code in _NOT_FOUND_CODES

    async def put(
        self, key: str, data: bytes, *, content_type: str | None = None
    ) -> None:
        """Store ``data`` under ``key`` in the bucket."""
        kwargs: dict[str, Any] = {"Bucket": self._bucket, "Key": key, "Body": data}
        if content_type is not None:
            kwargs["ContentType"] = content_type
        await asyncio.to_thread(self._client.put_object, **kwargs)

    async def get(self, key: str) -> bytes:
        """Return the bytes stored under ``key``.

        Raises:
            ObjectNotFoundError: If no object exists for ``key``.
        """
        try:
            response = await asyncio.to_thread(
                self._client.get_object, Bucket=self._bucket, Key=key
            )
        except Exception as exc:
            if self._is_not_found(exc):
                raise ObjectNotFoundError(key) from exc
            raise
        body = response["Body"]
        data: bytes = await asyncio.to_thread(body.read)
        return data

    async def delete(self, key: str) -> None:
        """Delete the object stored under ``key``.

        Idempotent: S3/R2 ``delete_object`` returns HTTP 200 for a missing key
        and does not raise, so deleting a missing key is a no-op. Genuine client
        errors (e.g. permissions) propagate unchanged.
        """
        await asyncio.to_thread(
            self._client.delete_object, Bucket=self._bucket, Key=key
        )

    async def url(self, key: str, *, expires_in: int = 3600) -> str:
        """Return a presigned GET URL for ``key``."""
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


def build_r2_storage(settings: Settings) -> R2Storage:
    """Construct an R2Storage from application settings.

    boto3 is imported lazily here so the module imports without boto3 installed
    and offline unit tests never need it.

    Args:
        settings: Application settings supplying the R2 endpoint, credentials,
            and bucket name.

    Returns:
        An R2Storage pointed at the configured R2 bucket.

    Raises:
        StorageConfigError: If boto3 is not installed or required config is empty.
    """
    bucket = settings.r2_bucket
    access_key = settings.r2_access_key_id.get_secret_value()
    secret_key = settings.r2_secret_access_key.get_secret_value()
    missing = [
        name
        for name, value in (
            ("R2_BUCKET", bucket),
            ("R2_ACCESS_KEY_ID", access_key),
            ("R2_SECRET_ACCESS_KEY", secret_key),
        )
        if not value
    ]
    if missing:
        raise StorageConfigError(
            f"R2 storage is not configured: missing {', '.join(missing)}."
        )

    try:
        endpoint = settings.r2_endpoint
    except ValueError as exc:
        raise StorageConfigError(str(exc)) from exc

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError as exc:
        raise StorageConfigError(
            "boto3 is required for R2 storage. Install it with 'uv add boto3'."
        ) from exc

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )
    return R2Storage(
        cast("S3Client", client),
        bucket=bucket,
        client_error=ClientError,
    )
