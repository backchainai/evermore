# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Pydantic response schemas for the documents module."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Single document metadata."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    filename: str
    title: str
    file_type: str
    file_size_bytes: int
    is_indexed: bool
    created_at: datetime
    description: str | None


class DocumentListResponse(BaseModel):
    """List of documents with total count."""

    model_config = ConfigDict(frozen=True)

    documents: list[DocumentResponse]
    count: int


class DocumentUploadResponse(BaseModel):
    """Result of uploading and indexing a document."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    filename: str
    title: str
    chunks_created: int
    message: str


class DocumentDeleteResponse(BaseModel):
    """Result of deleting a document."""

    model_config = ConfigDict(frozen=True)

    message: str
