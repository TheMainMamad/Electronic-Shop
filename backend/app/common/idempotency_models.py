import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class IdempotencyStatus(enum.StrEnum):
    pending = "pending"
    completed = "completed"


class IdempotencyKey(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "operation", "key", name="uq_idempotency_user_operation_key"),
    )

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[IdempotencyStatus] = mapped_column(
        Enum(IdempotencyStatus, name="idempotency_status", native_enum=True),
        nullable=False,
        default=IdempotencyStatus.pending,
    )
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
