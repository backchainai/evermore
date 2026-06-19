# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Pydantic response schemas for the messages module."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """Single message in a conversation."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class MessageHistoryResponse(BaseModel):
    """Paginated conversation history."""

    model_config = ConfigDict(frozen=True)

    messages: list[MessageResponse]
    count: int


class ClearHistoryResponse(BaseModel):
    """Result of clearing conversation history."""

    model_config = ConfigDict(frozen=True)

    deleted_count: int
    message: str
