# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI routes for conversation history."""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from retriever.infrastructure.database.session import _get_factory
from retriever.models.user import DEFAULT_TENANT_ID
from retriever.modules.auth import AuthUser, require_auth
from retriever.modules.messages.repos import MessageRepository
from retriever.modules.messages.schemas import (
    ClearHistoryResponse,
    MessageHistoryResponse,
    MessageResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["messages"])


def get_message_repository() -> MessageRepository:
    """Build a MessageRepository from the shared session factory."""
    return MessageRepository(_get_factory())


@router.get("/history", response_model=MessageHistoryResponse)
async def get_history(
    user: Annotated[AuthUser, Depends(require_auth)],
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> MessageHistoryResponse:
    """Return recent conversation history for the authenticated user."""
    try:
        user_id = uuid.UUID(user.sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID in token",
        ) from exc

    messages = await repo.get_recent_messages(
        user_id=user_id,
        tenant_id=DEFAULT_TENANT_ID,
    )

    return MessageHistoryResponse(
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
        count=len(messages),
    )


@router.delete("/history", response_model=ClearHistoryResponse)
async def clear_history(
    user: Annotated[AuthUser, Depends(require_auth)],
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> ClearHistoryResponse:
    """Clear all conversation history for the authenticated user."""
    try:
        user_id = uuid.UUID(user.sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID in token",
        ) from exc

    deleted = await repo.clear_messages(
        user_id=user_id,
        tenant_id=DEFAULT_TENANT_ID,
    )

    logger.info("history.cleared", user_id=user.sub, deleted_count=deleted)

    return ClearHistoryResponse(
        deleted_count=deleted,
        message=f"Cleared {deleted} message(s).",
    )
