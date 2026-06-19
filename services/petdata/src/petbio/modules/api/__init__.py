"""Adalo API client for petbio data extraction."""

from __future__ import annotations

from petbio.modules.api.auth import CookieAuth
from petbio.modules.api.client import AdaloClient
from petbio.modules.api.exceptions import (
    APIAuthenticationError,
    APIError,
    APINetworkError,
    APIRateLimitError,
    APIResponseParseError,
    APIServerError,
    APIValidationError,
)
from petbio.modules.api.parser import (
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
    "AdaloClient",
    "CookieAuth",
    "parse_animal_response",
    "parse_volunteer_note_response",
    "parse_walk_record_response",
]
