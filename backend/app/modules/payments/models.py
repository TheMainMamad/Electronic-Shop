import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class PaymentStatus(enum.StrEnum):
    initiated = "initiated"
    pending = "pending"
    verified = "verified"
    failed = "failed"


class Payment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    gateway: Mapped[str] = mapped_column(String(30), nullable=False, default="zarinpal")
    authority: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", native_enum=True),
        nullable=False,
        default=PaymentStatus.initiated,
    )
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_gateway_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
