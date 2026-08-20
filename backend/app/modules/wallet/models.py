import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class WalletTransactionType(enum.StrEnum):
    deposit = "deposit"
    purchase = "purchase"
    refund = "refund"
    admin_credit = "admin_credit"
    admin_debit = "admin_debit"


# Transaction types that increase the balance vs. decrease it — the single
# source of truth for the ledger's arithmetic direction.
CREDIT_TYPES = {
    WalletTransactionType.deposit,
    WalletTransactionType.refund,
    WalletTransactionType.admin_credit,
}
DEBIT_TYPES = {WalletTransactionType.purchase, WalletTransactionType.admin_debit}


class Wallet(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False, default=0)


class WalletTransaction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "wallet_transactions"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[WalletTransactionType] = mapped_column(
        Enum(WalletTransactionType, name="wallet_transaction_type", native_enum=True),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
