"""Tests for the R2-backed storage interface."""

from __future__ import annotations

from typing import Any

import pytest

from retriever.config import Settings
from retriever.infrastructure.storage import (
    InMemoryStorage,
    ObjectNotFoundError,
    R2Storage,
    StorageConfigError,
    build_r2_storage,
)

# --- InMemoryStorage --------------------------------------------------------


async def test_in_memory_round_trip() -> None:
    """put then get returns the same bytes."""
    storage = InMemoryStorage()
    await storage.put("a/b.txt", b"hello", content_type="text/plain")
    assert await storage.get("a/b.txt") == b"hello"


async def test_in_memory_get_missing_raises() -> None:
    """get of a missing key raises ObjectNotFoundError."""
    storage = InMemoryStorage()
    with pytest.raises(ObjectNotFoundError):
        await storage.get("nope")


async def test_in_memory_delete_missing_is_noop() -> None:
    """delete of a missing key is a silent no-op (idempotent)."""
    storage = InMemoryStorage()
    await storage.delete("nope")


async def test_in_memory_delete_then_get_raises() -> None:
    """get after delete raises ObjectNotFoundError."""
    storage = InMemoryStorage()
    await storage.put("k", b"v")
    await storage.delete("k")
    with pytest.raises(ObjectNotFoundError):
        await storage.get("k")


async def test_in_memory_url_is_deterministic_string() -> None:
    """url returns a deterministic fake URL string."""
    storage = InMemoryStorage()
    await storage.put("k", b"v")
    url = await storage.url("k")
    assert isinstance(url, str)
    assert url == "memory://k"


# --- R2Storage against a hand-written fake S3 client ------------------------


class _FakeClientError(Exception):
    """Stand-in for botocore.exceptions.ClientError in tests."""

    def __init__(self, code: str) -> None:
        self.response = {"Error": {"Code": code}}
        super().__init__(code)


class _FakeS3Client:
    """A minimal in-process test double for the boto3 S3 client.

    Records calls and stores objects in a dict; never touches the network.
    """

    def __init__(self, *, missing: bool = False) -> None:
        self.objects: dict[str, bytes] = {}
        self.missing = missing
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("put_object", kwargs))
        self.objects[kwargs["Key"]] = kwargs["Body"]
        return {}

    def get_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("get_object", kwargs))
        if self.missing or kwargs["Key"] not in self.objects:
            raise _FakeClientError("NoSuchKey")
        body = _FakeStreamingBody(self.objects[kwargs["Key"]])
        return {"Body": body}

    def delete_object(self, **kwargs: Any) -> dict[str, Any]:
        # S3/R2 delete is idempotent: deleting a missing key returns HTTP 200
        # and does not raise NoSuchKey.
        self.calls.append(("delete_object", kwargs))
        self.objects.pop(kwargs["Key"], None)
        return {}

    def generate_presigned_url(
        self, operation: str, *, Params: dict[str, Any], ExpiresIn: int
    ) -> str:
        self.calls.append(
            (
                "generate_presigned_url",
                {"operation": operation, "Params": Params, "ExpiresIn": ExpiresIn},
            )
        )
        return f"https://signed.example/{Params['Key']}?exp={ExpiresIn}"


class _FakeStreamingBody:
    """Mimics botocore's StreamingBody.read()."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


def _r2(client: _FakeS3Client) -> R2Storage:
    return R2Storage(client, bucket="test-bucket", client_error=_FakeClientError)


async def test_r2_put_delegates() -> None:
    """put forwards bucket, key, body, and content type to the client."""
    client = _FakeS3Client()
    storage = _r2(client)
    await storage.put("k", b"data", content_type="application/pdf")
    name, kwargs = client.calls[-1]
    assert name == "put_object"
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Key"] == "k"
    assert kwargs["Body"] == b"data"
    assert kwargs["ContentType"] == "application/pdf"


async def test_r2_get_round_trip() -> None:
    """get returns the bytes stored via put."""
    client = _FakeS3Client()
    storage = _r2(client)
    await storage.put("k", b"data")
    assert await storage.get("k") == b"data"


async def test_r2_get_missing_maps_to_object_not_found() -> None:
    """A NoSuchKey client error maps to ObjectNotFoundError."""
    client = _FakeS3Client(missing=True)
    storage = _r2(client)
    with pytest.raises(ObjectNotFoundError):
        await storage.get("k")


async def test_r2_get_missing_bucket_propagates_client_error() -> None:
    """A NoSuchBucket error is a misconfiguration, not a per-object not-found."""
    client = _FakeS3Client()

    def _raise(**_: Any) -> dict[str, Any]:
        raise _FakeClientError("NoSuchBucket")

    client.get_object = _raise  # type: ignore[method-assign]
    storage = _r2(client)
    with pytest.raises(_FakeClientError):
        await storage.get("k")


async def test_r2_delete_delegates() -> None:
    """delete forwards bucket and key to the client."""
    client = _FakeS3Client()
    storage = _r2(client)
    await storage.put("k", b"data")
    await storage.delete("k")
    name, kwargs = client.calls[-1]
    assert name == "delete_object"
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Key"] == "k"
    assert "k" not in client.objects


async def test_r2_delete_missing_is_noop() -> None:
    """delete of a missing key is a silent no-op (S3 delete is idempotent)."""
    client = _FakeS3Client(missing=True)
    storage = _r2(client)
    await storage.delete("k")
    name, _ = client.calls[-1]
    assert name == "delete_object"


async def test_r2_delete_propagates_client_error() -> None:
    """A non-not-found client error from delete propagates unchanged."""
    client = _FakeS3Client()

    def _raise(**_: Any) -> dict[str, Any]:
        raise _FakeClientError("AccessDenied")

    client.delete_object = _raise  # type: ignore[method-assign]
    storage = _r2(client)
    with pytest.raises(_FakeClientError):
        await storage.delete("k")


async def test_r2_url_delegates() -> None:
    """url returns the presigned URL from the client with the given expiry."""
    client = _FakeS3Client()
    storage = _r2(client)
    url = await storage.url("k", expires_in=120)
    assert url == "https://signed.example/k?exp=120"
    name, kwargs = client.calls[-1]
    assert name == "generate_presigned_url"
    assert kwargs["operation"] == "get_object"
    assert kwargs["Params"] == {"Bucket": "test-bucket", "Key": "k"}
    assert kwargs["ExpiresIn"] == 120


# --- Config -----------------------------------------------------------------


def test_r2_endpoint_from_explicit_url() -> None:
    """r2_endpoint prefers the explicit endpoint URL."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        r2_endpoint_url="https://custom.example",
        r2_account_id="acct",
    )
    assert settings.r2_endpoint == "https://custom.example"


def test_r2_endpoint_from_account_id() -> None:
    """r2_endpoint falls back to the account-id form when no URL is set."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        r2_endpoint_url="",
        r2_account_id="acct",
    )
    assert settings.r2_endpoint == "https://acct.r2.cloudflarestorage.com"


def test_r2_endpoint_raises_when_unconfigured() -> None:
    """r2_endpoint raises when neither URL nor account id is set."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        r2_endpoint_url="",
        r2_account_id="",
    )
    with pytest.raises(ValueError, match="No R2 endpoint"):
        _ = settings.r2_endpoint


# --- build_r2_storage -------------------------------------------------------


def test_build_r2_storage_raises_when_config_empty() -> None:
    """build_r2_storage raises StorageConfigError when required config is empty."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        r2_account_id="acct",
        r2_bucket="",
    )
    with pytest.raises(StorageConfigError):
        build_r2_storage(settings)
