"""Synchronous HTTP client for Adalo API with rate limiting and retry logic."""

from __future__ import annotations

import random
import time
from typing import Any

import httpx

from petdata.config import get_settings
from petdata.modules.api.auth import CookieAuth
from petdata.modules.api.exceptions import (
    APINetworkError,
    APIRateLimitError,
    APIResponseParseError,
    APIServerError,
)


class AdaloClient:
    """Synchronous HTTP client for Adalo API with rate limiting and retry.

    Features:
    - Cookie-based authentication
    - Rate limiting with configurable delay (default 500ms)
    - Exponential backoff retry for 429/5xx/network errors
    - Automatic JSON response parsing
    - Context manager support for resource cleanup

    Important: Not thread-safe - use one client instance per thread.

    Usage:
        >>> with AdaloClient() as client:
        ...     animals = client.fetch_animals(limit=100)
    """

    def __init__(self) -> None:
        """Initialize Adalo API client.

        Note: httpx.Client is created in __enter__ for proper resource management.
        """
        self._settings = get_settings()
        self._auth = CookieAuth()
        self._client: httpx.Client | None = None
        self._last_request_time: float = 0.0

    def __enter__(self) -> AdaloClient:
        """Context manager entry - creates httpx.Client."""
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                self._settings.api_timeout_seconds,
                connect=10.0,
            ),
            headers=self._auth.get_headers(),
            follow_redirects=True,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - closes httpx.Client."""
        if self._client:
            self._client.close()

    def close(self) -> None:
        """Explicitly close the HTTP client.

        Prefer using context manager (`with AdaloClient() as client`)
        for automatic cleanup.
        """
        if self._client:
            self._client.close()

    def _enforce_rate_limit(self) -> None:
        """Sleep to enforce minimum delay between requests.

        Handles case where elapsed time exceeds delay (no negative sleep).
        """
        if self._last_request_time == 0.0:
            self._last_request_time = time.time()
            return

        elapsed_ms = (time.time() - self._last_request_time) * 1000
        if elapsed_ms < self._settings.request_delay_ms:
            delay_s = (self._settings.request_delay_ms - elapsed_ms) / 1000
            time.sleep(delay_s)

        self._last_request_time = time.time()

    def _calculate_retry_delay(
        self, attempt: int, response: httpx.Response | None
    ) -> float:
        """Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current retry attempt (1-indexed).
            response: HTTP response if available (for Retry-After header).

        Returns:
            Delay in seconds, capped at retry_max_delay_ms.
        """
        # Check Retry-After header for 429 responses
        if response and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                return min(
                    float(retry_after),
                    self._settings.retry_max_delay_ms / 1000,
                )

        # Exponential backoff with jitter
        base_delay = (self._settings.retry_backoff_factor**attempt) * 1.0
        jitter = random.uniform(0, 0.5)  # nosec B311  # 0-500ms jitter, not crypto
        return min(base_delay + jitter, self._settings.retry_max_delay_ms / 1000)

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute HTTP request with exponential backoff retry.

        Retries on:
        - 429 (rate limit)
        - 5xx (server errors)
        - Network errors (connection, timeout)

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Full request URL.
            **kwargs: Additional arguments for httpx request.

        Returns:
            Successful HTTP response.

        Raises:
            APIRateLimitError: If rate limit exceeded after all retries.
            APIServerError: If server error persists after all retries.
            APINetworkError: If network error persists after all retries.
        """
        if not self._client:
            msg = "Client not initialized. Use 'with AdaloClient() as client:' syntax"
            raise RuntimeError(msg)

        last_exception: Exception | None = None

        for attempt in range(1, self._settings.retry_max_attempts + 1):
            try:
                self._enforce_rate_limit()
                response = self._client.request(method, url, **kwargs)

                # Check for retriable HTTP errors
                if response.status_code == 429:
                    if attempt == self._settings.retry_max_attempts:
                        msg = f"Rate limit exceeded after {attempt} attempts"
                        raise APIRateLimitError(msg)

                    delay = self._calculate_retry_delay(attempt, response)
                    time.sleep(delay)
                    continue

                if response.status_code >= 500:
                    if attempt == self._settings.retry_max_attempts:
                        msg = (
                            f"Server error {response.status_code} "
                            f"after {attempt} attempts"
                        )
                        raise APIServerError(
                            msg,
                            status_code=response.status_code,
                            response_body=response.text[:1000],  # Limit body size
                        )

                    delay = self._calculate_retry_delay(attempt, None)
                    time.sleep(delay)
                    continue

                # Success or non-retriable error
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Non-retriable HTTP errors (4xx except 429)
                if e.response.status_code < 500 and e.response.status_code != 429:
                    msg = (
                        f"HTTP {e.response.status_code} error: {e.response.text[:500]}"
                    )
                    raise APIServerError(
                        msg,
                        status_code=e.response.status_code,
                        response_body=e.response.text[:1000],
                    ) from e
                # Retriable errors handled above
                raise

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt == self._settings.retry_max_attempts:
                    msg = f"Network error after {attempt} attempts"
                    raise APINetworkError(msg) from e

                delay = self._calculate_retry_delay(attempt, None)
                time.sleep(delay)
                continue

        # Should never reach here, but satisfy type checker
        msg = f"Request failed after {self._settings.retry_max_attempts} attempts"
        raise APINetworkError(msg) from last_exception

    def _get_json(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute GET request and parse JSON response.

        Args:
            url: Request URL.
            params: Query parameters.

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            APIResponseParseError: If response is not valid JSON.
        """
        response = self._request_with_retry("GET", url, params=params)

        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            msg = f"Failed to parse JSON response: {e}"
            raise APIResponseParseError(msg) from e

    def fetch_animals(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch animal records from Adalo.

        Args:
            limit: Maximum records to return (default 100).
            offset: Record offset for pagination (default 0).

        Returns:
            Raw JSON response from Adalo API with {"records": [...]} structure.

        Raises:
            APINetworkError: If request fails after retries.
            APIResponseParseError: If response is not valid JSON.
            APIRateLimitError: If rate limit exceeded after retries.
            APIServerError: If server error persists after retries.
        """
        url = f"{self._settings.adalo_base_url}/{self._settings.adalo_table_animals}"
        params = {
            "limit": limit,
            "offset": offset,
            "imageMeta": "true",
            "evaluateBindings": "true",
        }
        return self._get_json(url, params)

    def fetch_volunteer_notes(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch volunteer note records from Adalo.

        Args:
            limit: Maximum records to return (default 100).
            offset: Record offset for pagination (default 0).

        Returns:
            Raw JSON response from Adalo API with {"records": [...]} structure.

        Raises:
            APINetworkError: If request fails after retries.
            APIResponseParseError: If response is not valid JSON.
            APIRateLimitError: If rate limit exceeded after retries.
            APIServerError: If server error persists after retries.
        """
        url = (
            f"{self._settings.adalo_base_url}/"
            f"{self._settings.adalo_table_volunteer_notes}"
        )
        params = {
            "limit": limit,
            "offset": offset,
        }
        return self._get_json(url, params)

    def fetch_walk_records(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch walk record data from Adalo.

        Args:
            limit: Maximum records to return (default 100).
            offset: Record offset for pagination (default 0).

        Returns:
            Raw JSON response from Adalo API with {"records": [...]} structure.

        Raises:
            APINetworkError: If request fails after retries.
            APIResponseParseError: If response is not valid JSON.
            APIRateLimitError: If rate limit exceeded after retries.
            APIServerError: If server error persists after retries.
        """
        url = (
            f"{self._settings.adalo_base_url}/{self._settings.adalo_table_walk_records}"
        )
        params = {
            "limit": limit,
            "offset": offset,
        }
        return self._get_json(url, params)
