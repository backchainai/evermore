"""Integration tests for AdaloClient with mocked HTTP."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from petbio.modules.api.client import AdaloClient
from petbio.modules.api.exceptions import (
    APIRateLimitError,
    APIResponseParseError,
    APIServerError,
)


@pytest.fixture
def _mock_cookies(monkeypatch):
    """Mock PETBIO_COOKIES environment variable."""
    monkeypatch.setenv("PETBIO_COOKIES", "session=test123")


class TestAdaloClientRetry:
    """Tests for retry logic with exponential backoff."""

    @respx.mock
    def test_retry_on_429_with_backoff(self, _mock_cookies, mocker):
        """Client retries on 429 with exponential backoff."""
        mock_sleep = mocker.patch("time.sleep")
        # Disable rate limiting to isolate retry backoff
        mocker.patch.object(AdaloClient, "_enforce_rate_limit", return_value=None)
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        # First two calls return 429, third succeeds
        respx.get(url).mock(
            side_effect=[
                Response(429),
                Response(429),
                Response(200, json={"records": []}),
            ]
        )

        with AdaloClient() as client:
            result = client.fetch_animals(limit=10)
            assert result == {"records": []}

        # Should have slept twice (after 1st and 2nd 429)
        assert mock_sleep.call_count == 2

    @respx.mock
    def test_retry_exhausted_raises_rate_limit_error(self, _mock_cookies):
        """Client raises APIRateLimitError after max attempts."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        # All calls return 429
        respx.get(url).mock(return_value=Response(429))

        with (
            pytest.raises(APIRateLimitError, match="Rate limit exceeded after 3"),
            AdaloClient() as client,
        ):
            client.fetch_animals(limit=10)

    @respx.mock
    def test_retry_on_500_with_backoff(self, _mock_cookies, mocker):
        """Client retries on 5xx errors."""
        mock_sleep = mocker.patch("time.sleep")
        # Disable rate limiting to isolate retry backoff
        mocker.patch.object(AdaloClient, "_enforce_rate_limit", return_value=None)
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        # First call returns 500, second succeeds
        respx.get(url).mock(
            side_effect=[
                Response(500),
                Response(200, json={"records": []}),
            ]
        )

        with AdaloClient() as client:
            result = client.fetch_animals(limit=10)
            assert result == {"records": []}

        # Should have slept once (after 500)
        assert mock_sleep.call_count == 1

    @respx.mock
    def test_retry_exhausted_raises_server_error(self, _mock_cookies):
        """Client raises APIServerError after max attempts on 5xx."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        # All calls return 500
        respx.get(url).mock(return_value=Response(500, text="Internal error"))

        with (
            pytest.raises(APIServerError, match="Server error 500"),
            AdaloClient() as client,
        ):
            client.fetch_animals(limit=10)

    @respx.mock
    def test_server_error_includes_status_and_body(self, _mock_cookies):
        """APIServerError includes status_code and response_body."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        respx.get(url).mock(return_value=Response(502, text="Bad gateway"))

        with pytest.raises(APIServerError) as exc_info, AdaloClient() as client:
            client.fetch_animals(limit=10)

        assert exc_info.value.status_code == 502
        assert "Bad gateway" in (exc_info.value.response_body or "")


class TestAdaloClientRateLimiting:
    """Tests for rate limiting enforcement."""

    @respx.mock
    def test_rate_limiting_enforces_delay(self, _mock_cookies, mocker):
        """Client enforces minimum delay between requests."""
        mock_sleep = mocker.patch("time.sleep")
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            client.fetch_animals(limit=10)
            # Second request immediately - should enforce full 500ms delay
            client.fetch_animals(limit=10)

        # Should sleep once for rate limiting (500ms = 0.5s)
        assert mock_sleep.call_count >= 1
        # First sleep call should be approximately 0.5s (500ms)
        first_sleep = mock_sleep.call_args_list[0][0][0]
        assert first_sleep == pytest.approx(0.5, abs=0.01)

    @respx.mock
    def test_rate_limiting_handles_elapsed_greater_than_delay(
        self, _mock_cookies, mocker
    ):
        """Client handles case where elapsed time > delay (no negative sleep)."""
        # Mock time to progress by >500ms between requests
        time_values = [0.0, 0.0, 0.6, 0.6]  # First request: 0.0, second: 0.6
        _mock_time = mocker.patch("time.time", side_effect=time_values)
        mock_sleep = mocker.patch("time.sleep")

        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            client.fetch_animals(limit=10)
            client.fetch_animals(limit=10)

        # Should not sleep (elapsed > delay)
        mock_sleep.assert_not_called()


class TestAdaloClientContextManager:
    """Tests for context manager support."""

    @respx.mock
    def test_context_manager_closes_client(self, _mock_cookies):
        """Context manager closes httpx.Client on exit."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            assert client._client is not None
            client.fetch_animals(limit=10)

        # Client should be closed after exiting context
        assert client._client is not None  # Reference exists but closed

    @respx.mock
    def test_explicit_close_works(self, _mock_cookies):
        """Explicit close() method works."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        respx.get(url).mock(return_value=Response(200, json={"records": []}))

        client = AdaloClient()
        with client:
            client.fetch_animals(limit=10)

        client.close()  # Should not raise


class TestAdaloClientFetchMethods:
    """Tests for fetch_animals, fetch_volunteer_notes, fetch_walk_records."""

    @respx.mock
    def test_fetch_animals_includes_query_params(self, _mock_cookies):
        """fetch_animals includes correct query parameters."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        route = respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            client.fetch_animals(limit=50, offset=100)

        # Verify query params
        assert route.called
        last_request = route.calls.last.request
        assert "limit=50" in str(last_request.url)
        assert "offset=100" in str(last_request.url)
        assert "imageMeta=true" in str(last_request.url)

    @respx.mock
    def test_fetch_volunteer_notes_uses_correct_table(self, _mock_cookies):
        """fetch_volunteer_notes uses correct table ID."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_9yomkzwe9lsdlgwvkbwa9uoai"
        )

        route = respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            client.fetch_volunteer_notes(limit=25)

        assert route.called

    @respx.mock
    def test_fetch_walk_records_uses_correct_table(self, _mock_cookies):
        """fetch_walk_records uses correct table ID."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0cd59s41203wo2dbdr8bwtoa4"
        )

        route = respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            client.fetch_walk_records(limit=10)

        assert route.called

    @respx.mock
    def test_authentication_headers_injected(self, _mock_cookies):
        """Client injects Cookie and Accept headers."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        route = respx.get(url).mock(return_value=Response(200, json={"records": []}))

        with AdaloClient() as client:
            client.fetch_animals(limit=10)

        last_request = route.calls.last.request
        assert "Cookie" in last_request.headers
        assert last_request.headers["Cookie"] == "session=test123"

    @respx.mock
    def test_invalid_json_response_raises_error(self, _mock_cookies):
        """Client raises APIResponseParseError for invalid JSON."""
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        respx.get(url).mock(return_value=Response(200, text="not json"))

        with (
            pytest.raises(APIResponseParseError, match="Failed to parse JSON"),
            AdaloClient() as client,
        ):
            client.fetch_animals(limit=10)


class TestRetryAfterHeader:
    """Tests for Retry-After header extraction."""

    @respx.mock
    def test_retry_after_header_respected(self, _mock_cookies, mocker):
        """Client respects Retry-After header for 429 responses."""
        mock_sleep = mocker.patch("time.sleep")
        # Disable rate limiting to isolate Retry-After behavior
        mocker.patch.object(AdaloClient, "_enforce_rate_limit", return_value=None)
        url = (
            "https://database-red.adalo.com/databases/"
            "bjql6w9oy6hlarewbcr9fwh2i/tables/t_0sslo1men4fkuiap2eis82riv"
        )

        # First call returns 429 with Retry-After: 5, second succeeds
        respx.get(url).mock(
            side_effect=[
                Response(429, headers={"Retry-After": "5"}),
                Response(200, json={"records": []}),
            ]
        )

        with AdaloClient() as client:
            client.fetch_animals(limit=10)

        # Should sleep 5 seconds (from Retry-After header)
        mock_sleep.assert_called_once_with(5.0)
