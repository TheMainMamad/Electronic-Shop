import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TicketStatus(enum.StrEnum):
    open = "open"
    waiting_for_support = "waiting_for_support"
    waiting_for_customer = "waiting_for_customer"
    closed = "closed"


class TicketPriority(enum.StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class TicketMessageAuthorRole(enum.StrEnum):
    customer = "customer"
    support = "support"
    system = "system"


class Ticket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=True), nullable=False, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", native_enum=True),
        nullable=False,
        default=TicketPriority.normal,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_response_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    messages: Mapped[list["TicketMessage"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", lazy="noload"
    )


class TicketMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_role: Mapped[TicketMessageAuthorRole] = mapped_column(
        Enum(TicketMessageAuthorRole, name="ticket_message_author_role", native_enum=True),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="messages")
