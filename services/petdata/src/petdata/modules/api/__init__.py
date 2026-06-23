"""SMS API client for petdata data extraction."""

from __future__ import annotations

from petdata.modules.api.auth import CookieAuth
from petdata.modules.api.client import SMSClient
from petdata.modules.api.exceptions import (
    APIAuthenticationError,
    APIError,
    APINetworkError,
    APIRateLimitError,
    APIResponseParseError,
    APIServerError,
    APIValidationError,
)
from petdata.modules.api.parser import (
    parse_animal_response,
    parse_volunteer_note_response,
    parse_walk_record_response,
)

__all__ = [
    "APIAuthenticationError",
    "APIError",
    "APINetworkError",
    "APIRateLimitError",
    "APIResponseParseError",
    "APIServerError",
    "APIValidationError",
    "CookieAuth",
    "SMSClient",
    "parse_animal_response",
    "parse_volunteer_note_response",
    "parse_walk_record_response",
]
