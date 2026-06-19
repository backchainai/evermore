# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""User model — mirrors Supabase Auth users."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from retriever.models.base import Base

# Default tenant UUID for single-tenant MVP.
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class User(Base):
    """Application user record, keyed to Supabase Auth uid."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=lambda: DEFAULT_TENANT_ID
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
