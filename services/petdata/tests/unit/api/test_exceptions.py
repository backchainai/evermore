"""Unit tests for API exception hierarchy."""

from __future__ import annotations

from petdata.modules.api.exceptions import (
    APIAuthenticationError,
    APIError,
    APINetworkError,
    APIRateLimitError,
    APIResponseParseError,
    APIServerError,
    APIValidationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_all_exceptions_inherit_from_api_error(self):
        """All specific exceptions inherit from APIError."""
        exceptions = [
            APIAuthenticationError,
            APIValidationError,
            APIRateLimitError,
            APIServerError,
            APINetworkError,
            APIResponseParseError,
        ]
        for exc in exceptions:
            assert issubclass(exc, APIError)

    def test_api_error_inherits_from_exception(self):
        """APIError inherits from base Exception."""
        assert issubclass(APIError, Exception)


class TestExceptionChaining:
    """Tests for exception chaining with 'from e'."""

    def test_exception_chains_cause(self):
        """Exceptions support 'raise from' chaining."""
        original = ValueError("original error")
        try:
            raise APIValidationError("validation failed") from original
        except APIValidationError as e:
            assert e.__cause__ is original
            assert str(e.__cause__) == "original error"


class TestAPIServerError:
    """Tests for APIServerError with debugging attributes."""

    def test_server_error_with_status_code(self):
        """APIServerError stores status_code attribute."""
        exc = APIServerError("server error", status_code=500)
        assert exc.status_code == 500

    def test_server_error_with_response_body(self):
        """APIServerError stores response_body attribute."""
        body = '{"error": "internal server error"}'
        exc = APIServerError("server error", response_body=body)
        assert exc.response_body == body

    def test_server_error_with_all_attributes(self):
        """APIServerError stores both status_code and response_body."""
        exc = APIServerError(
            "server error", status_code=502, response_body="gateway error"
        )
        assert exc.status_code == 502
        assert exc.response_body == "gateway error"
        assert str(exc) == "server error"

    def test_server_error_without_optional_attributes(self):
        """APIServerError works without optional attributes."""
        exc = APIServerError("server error")
        assert exc.status_code is None
        assert exc.response_body is None
