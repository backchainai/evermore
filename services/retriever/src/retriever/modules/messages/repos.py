# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Message repository — async persistence for conversation history."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import CursorResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.models.message import Message

logger = structlog.get_logger(__name__)


class MessageRepository:
    """Async repository for conversation messages.

    Handles saving, retrieving, and clearing messages scoped
    to a user within a tenant.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_message(
        self,
        user_id: uuid.UUID,
        role: str,
        content: str,
        tenant_id: uuid.UUID,
    ) -> Message:
        """Persist a new conversation message.

        Args:
            user_id: Owner of the message.
            role: Message role — must be ``"user"`` or ``"assistant"``.
            content: Message body text.
            tenant_id: Tenant scope.

        Returns:
            The persisted Message instance.

        Raises:
            ValueError: If *role* is not ``"user"`` or ``"assistant"``.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role!r}. Must be 'user' or 'assistant'.")

        message = Message(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            content=content,
        )

        async with self._session_factory() as session:
            session.add(message)
            await session.commit()
            await session.refresh(message)

        logger.debug(
            "message.saved",
            message_id=str(message.id),
            user_id=str(user_id),
            role=role,
            content_length=len(content),
        )

        return message

    async def get_recent_messages(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[Message]:
        """Return the most recent messages in chronological order.

        Fetches the *limit* newest messages (DESC), then reverses to
        chronological order (oldest first) for conversation context.

        Args:
            user_id: Owner of the messages.
            tenant_id: Tenant scope.
            limit: Maximum number of messages to return.

        Returns:
            Messages sorted oldest-first.
        """
        stmt = (
            select(Message)
            .where(Message.user_id == user_id, Message.tenant_id == tenant_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            rows = list(result.scalars().all())

        # Reverse to chronological order (oldest first).
        rows.reverse()

        logger.debug(
            "messages.retrieved",
            user_id=str(user_id),
            count=len(rows),
            limit=limit,
        )

        return rows

    async def clear_messages(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> int:
        """Delete all messages for a user within a tenant.

        Args:
            user_id: Owner of the messages.
            tenant_id: Tenant scope.

        Returns:
            Number of messages deleted.
        """
        stmt = delete(Message).where(
            Message.user_id == user_id,
            Message.tenant_id == tenant_id,
        )

        async with self._session_factory() as session:
            cursor: CursorResult[tuple[()]] = await session.execute(stmt)  # type: ignore[assignment]
            await session.commit()
            deleted: int = cursor.rowcount

        if deleted > 0:
            logger.info(
                "messages.cleared",
                user_id=str(user_id),
                count=deleted,
            )

        return deleted
