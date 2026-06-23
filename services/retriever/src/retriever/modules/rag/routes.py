# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI routes for the RAG ask endpoint."""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from retriever.config import get_settings
from retriever.models.user import DEFAULT_TENANT_ID
from retriever.modules.auth import AuthUser, require_auth
from retriever.modules.messages.repos import MessageRepository
from retriever.modules.rag.dependencies import get_message_repository, get_rag_service
from retriever.modules.rag.schemas import ChunkWithScore, RAGResponse
from retriever.modules.rag.service import RAGService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["rag"])


class AskRequest(BaseModel):
    """Request body for the ask endpoint."""

    model_config = ConfigDict(frozen=True)

    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    """Response from the RAG ask endpoint."""

    model_config = ConfigDict(frozen=True)

    answer: str
    chunks_used: list[ChunkWithScore]
    confidence_level: str
    confidence_score: float
    blocked: bool = False
    blocked_reason: str | None = None


def _to_ask_response(rag_response: RAGResponse) -> AskResponse:
    """Convert internal RAGResponse to API AskResponse.

    Args:
        rag_response: Internal RAG pipeline response.

    Returns:
        API response model.
    """
    return AskResponse(
        answer=rag_response.answer,
        chunks_used=rag_response.chunks_used,
        confidence_level=rag_response.confidence_level,
        confidence_score=rag_response.confidence_score,
        blocked=rag_response.blocked,
        blocked_reason=rag_response.blocked_reason,
    )


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    user: Annotated[AuthUser, Depends(require_auth)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> AskResponse:
    """Answer a question using RAG with conversation history.

    Loads recent conversation history, runs the RAG pipeline, and
    persists both the user question and assistant response.
    """
    try:
        user_id = uuid.UUID(user.sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID in token",
        ) from exc

    settings = get_settings()

    # Load recent conversation history
    recent_messages = await message_repo.get_recent_messages(
        user_id=user_id,
        tenant_id=DEFAULT_TENANT_ID,
        limit=settings.conversation_max_messages,
    )

    # Format as list[dict[str, str]] for the RAG service
    conversation_history: list[dict[str, str]] = [
        {"role": msg.role, "content": msg.content} for msg in recent_messages
    ]

    # Run RAG pipeline
    rag_response: RAGResponse = await rag_service.ask(
        question=body.question,
        conversation_history=conversation_history if conversation_history else None,
    )

    logger.info(
        "ask.completed",
        user_id=user.sub,
        question_length=len(body.question),
        answer_length=len(rag_response.answer),
        confidence_level=rag_response.confidence_level,
        blocked=rag_response.blocked,
    )

    # Save user message and assistant response
    await message_repo.save_message(
        user_id=user_id,
        role="user",
        content=body.question,
        tenant_id=DEFAULT_TENANT_ID,
    )
    await message_repo.save_message(
        user_id=user_id,
        role="assistant",
        content=rag_response.answer,
        tenant_id=DEFAULT_TENANT_ID,
    )

    return _to_ask_response(rag_response)
