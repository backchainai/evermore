"""Unit tests for SMSClient response size cap enforcement (F6 hardening).

A compromised or misbehaving SMS endpoint could return an oversized payload
that the client would otherwise buffer in full via `response.json()`. These
tests assert the client refuses to parse a response body larger than the
configured `max_response_bytes` cap, raising `APIResponseTooLargeError`
before the JSON parse is attempted.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from petdata.modules.api.client import SMSClient
from petdata.modules.api.exceptions import (
    APIError,
    APIResponseParseError,
    APIResponseTooLargeError,
)


@pytest.fixture
def _mock_cookies(monkeypatch):
    """Set placeholder SMS extraction config (cookies + endpoints) via env."""
    monkeypatch.setenv("PETDATA_COOKIES", "session=test123")
    monkeypatch.setenv("PETDATA_SMS_BASE_URL", "https://sms.example.com/tables")
    monkeypatch.setenv("PETDATA_SMS_TABLE_ANIMALS", "tbl_animals")
    monkeypatch.setenv("PETDATA_SMS_TABLE_VOLUNTEER_NOTES", "tbl_volunteer_notes")
    monkeypatch.setenv("PETDATA_SMS_TABLE_WALK_RECORDS", "tbl_walk_records")


class TestSMSClientResponseSizeCap:
    """Tests that the client rejects oversized response bodies."""

    @respx.mock
    def test_oversized_response_raises_response_too_large_error(
        self, _mock_cookies, monkeypatch, mocker
    ):
        """A response larger than the configured cap raises APIResponseTooLargeError."""
        monkeypatch.setenv("PETDATA_MAX_RESPONSE_BYTES", "50")
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)

        url = "https://sms.example.com/tables/tbl_animals"
        # A normal JSON body comfortably larger than the 50-byte cap.
        big_records = [{"id": f"sms{i}", "Name": "Buddy" * 5} for i in range(20)]
        respx.get(url).mock(return_value=Response(200, json={"records": big_records}))

        with pytest.raises(APIResponseTooLargeError) as exc_info, SMSClient() as client:
            client.fetch_animals(limit=10)

        assert isinstance(exc_info.value, APIError)

    @respx.mock
    def test_small_response_within_default_cap_parses_normally(
        self, _mock_cookies, mocker
    ):
        """A small response under the default cap returns normally."""
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)

        url = "https://sms.example.com/tables/tbl_animals"
        respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with SMSClient() as client:
            result = client.fetch_animals(limit=10)

        assert result == {"records": []}

    @respx.mock
    def test_oversized_non_json_response_raises_size_error_not_parse_error(
        self, _mock_cookies, monkeypatch, mocker
    ):
        """The size cap fires before JSON parsing, even for non-JSON bodies.

        A response that is both larger than the cap AND not valid JSON must
        raise `APIResponseTooLargeError`, not `APIResponseParseError`. If the
        size check ran after `response.json()` (or not at all), this would
        instead surface as a parse error, proving the size check runs first.
        """
        monkeypatch.setenv("PETDATA_MAX_RESPONSE_BYTES", "50")
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)

        url = "https://sms.example.com/tables/tbl_animals"
        # Comfortably larger than the 50-byte cap and not parseable as JSON.
        non_json_body = b"not valid json, just plain text " * 5
        assert len(non_json_body) > 50
        respx.get(url).mock(
            return_value=Response(
                200,
                content=non_json_body,
                headers={"Content-Type": "text/plain"},
            )
        )

        with (
            pytest.raises(
                APIResponseTooLargeError, match="max_response_bytes"
            ) as exc_info,
            SMSClient() as client,
        ):
            client.fetch_animals(limit=10)

        assert not isinstance(exc_info.value, APIResponseParseError)
        assert isinstance(exc_info.value, APIError)


class TestSMSClientResponseSizeCapBoundary:
    """Tests for exact-boundary and Content-Length behavior of the size cap."""

    @staticmethod
    def _json_body_of_exact_length(total_bytes: int) -> bytes:
        """Build a valid JSON body of exactly `total_bytes` bytes.

        Pads a string field with ASCII filler characters (1 byte each) so the
        overall payload length is controlled precisely.
        """
        template = '{{"records": [], "pad": "{pad}"}}'
        overhead = len(template.format(pad="").encode())
        pad_len = total_bytes - overhead
        assert pad_len >= 0, "total_bytes too small for template overhead"
        body = template.format(pad="a" * pad_len).encode()
        assert len(body) == total_bytes
        return body

    @respx.mock
    def test_response_exactly_at_cap_parses_normally(
        self, _mock_cookies, monkeypatch, mocker
    ):
        """A response body of exactly max_response_bytes bytes is accepted."""
        monkeypatch.setenv("PETDATA_MAX_RESPONSE_BYTES", "50")
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)

        url = "https://sms.example.com/tables/tbl_animals"
        body = self._json_body_of_exact_length(50)
        assert len(body) == 50
        respx.get(url).mock(return_value=Response(200, content=body))

        with SMSClient() as client:
            result = client.fetch_animals(limit=10)

        assert result == {"records": [], "pad": "a" * 24}

    @respx.mock
    def test_response_one_byte_over_cap_raises_too_large_error(
        self, _mock_cookies, monkeypatch, mocker
    ):
        """A response body of max_response_bytes + 1 bytes is rejected."""
        monkeypatch.setenv("PETDATA_MAX_RESPONSE_BYTES", "50")
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)

        url = "https://sms.example.com/tables/tbl_animals"
        body = self._json_body_of_exact_length(51)
        assert len(body) == 51
        respx.get(url).mock(return_value=Response(200, content=body))

        with pytest.raises(APIResponseTooLargeError), SMSClient() as client:
            client.fetch_animals(limit=10)

    @respx.mock
    def test_content_length_header_over_cap_raises_even_with_small_body(
        self, _mock_cookies, monkeypatch, mocker
    ):
        """An oversized declared Content-Length triggers the cap.

        The actual buffered body is small (well under the cap), but a
        `Content-Length` header declaring a size over the cap must still
        raise `APIResponseTooLargeError`. respx serves the constructed
        `httpx.Response` back to the client unmodified, so a manually-set
        Content-Length header survives the round trip even though it does
        not match the real body length; this exercises the
        `declared_length` branch in `_get_json` independent of the actual
        response size.
        """
        monkeypatch.setenv("PETDATA_MAX_RESPONSE_BYTES", "100")
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)

        url = "https://sms.example.com/tables/tbl_animals"
        small_body = b'{"records": []}'
        assert len(small_body) < 100
        respx.get(url).mock(
            return_value=Response(
                200,
                content=small_body,
                headers={"Content-Length": "999999"},
            )
        )

        with pytest.raises(APIResponseTooLargeError), SMSClient() as client:
            client.fetch_animals(limit=10)
