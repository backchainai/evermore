"""Unit tests for SMSClient redirect handling (outbound-egress safety).

A static Cookie auth header combined with `follow_redirects=True` would let a
3xx response from the SMS host steer the client to an arbitrary host while
still carrying the session cookie. These tests assert redirects are disabled:
a redirect response surfaces as a loud `APIServerError` instead of being
silently followed to an attacker-controlled origin.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from petdata.modules.api.client import SMSClient
from petdata.modules.api.exceptions import APIServerError


@pytest.fixture
def _mock_cookies(monkeypatch):
    """Set placeholder SMS extraction config (cookies + endpoints) via env."""
    monkeypatch.setenv("PETDATA_COOKIES", "session=test123")
    monkeypatch.setenv("PETDATA_SMS_BASE_URL", "https://sms.example.com/tables")
    monkeypatch.setenv("PETDATA_SMS_TABLE_ANIMALS", "tbl_animals")
    monkeypatch.setenv("PETDATA_SMS_TABLE_VOLUNTEER_NOTES", "tbl_volunteer_notes")
    monkeypatch.setenv("PETDATA_SMS_TABLE_WALK_RECORDS", "tbl_walk_records")


class TestSMSClientRedirectSafety:
    """Tests that the client refuses to follow cross-origin redirects."""

    @respx.mock
    def test_redirect_is_not_followed_to_cross_origin_host(self, _mock_cookies, mocker):
        """A 3xx from the SMS host raises APIServerError; evil host untouched."""
        mocker.patch.object(SMSClient, "_enforce_rate_limit", return_value=None)
        url = "https://sms.example.com/tables/tbl_animals"
        evil_url = "https://evil.example.net/steal"

        respx.get(url).mock(return_value=Response(302, headers={"Location": evil_url}))
        evil_route = respx.get(evil_url).mock(
            return_value=Response(200, json={"records": []})
        )

        with pytest.raises(APIServerError), SMSClient() as client:
            client.fetch_animals(limit=10)

        assert not evil_route.called

    @respx.mock
    def test_client_has_redirects_disabled(self, _mock_cookies):
        """The underlying httpx.Client is constructed with follow_redirects=False."""
        with SMSClient() as client:
            assert client._client is not None
            assert client._client.follow_redirects is False
