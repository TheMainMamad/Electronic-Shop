import uuid
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError
from app.modules.wallet.models import CREDIT_TYPES, Wallet, WalletTransaction, WalletTransactionType
from app.modules.wallet.repository import WalletRepository


class WalletService:
    """Every balance mutation happens under SELECT ... FOR UPDATE on the
    wallet row plus a ledger insert in the same transaction — the balance
    column is a maintained cache of the ledger sum, never touched on its
    own (see docs/architecture.md §9)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WalletRepository(session)

    async def get_or_create(self, user_id: uuid.UUID) -> Wallet:
        wallet = await self.repo.get_by_user_id(user_id)
        if wallet is not None:
            return wallet

        # Two concurrent first-time operations for the same user (e.g. two
        # parallel deposits) can both reach here and both try to create the
        # wallet. A plain INSERT would raise IntegrityError on the loser —
        # and recovering from that would require session.rollback(), which
        # expires every other object already loaded in this request's
        # session (see the idempotency guard for that exact failure mode).
        # ON CONFLICT DO NOTHING sidesteps the race without ever raising.
        await self.session.execute(
            pg_insert(Wallet)
            .values(user_id=user_id, balance=Decimal(0))
            .on_conflict_do_nothing(index_elements=[Wallet.user_id])
        )
        wallet = await self.repo.get_by_user_id(user_id)
        assert wallet is not None
        return wallet

    async def _apply(
        self,
        user_id: uuid.UUID,
        *,
        type_: WalletTransactionType,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
        note: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> WalletTransaction:
        await self.get_or_create(user_id)
        wallet = await self.repo.lock_by_user_id(user_id)
        assert wallet is not None

        signed_amount = amount if type_ in CREDIT_TYPES else -amount
        new_balance = wallet.balance + signed_amount
        if new_balance < 0:
            raise ConflictError("موجودی کیف پول کافی نیست.")

        wallet.balance = new_balance
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            type=type_,
            amount=amount,
            balance_after=new_balance,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
            actor_id=actor_id,
        )
        self.repo.add_transaction(transaction)
        await self.session.flush()
        return transaction

    async def deposit(self, user_id: uuid.UUID, amount: Decimal) -> WalletTransaction:
        return await self._apply(
            user_id,
            type_=WalletTransactionType.deposit,
            amount=amount,
            note="افزایش موجودی کیف پول",
        )

    async def refund_order(
        self, user_id: uuid.UUID, amount: Decimal, order_id: uuid.UUID, *, actor_id: uuid.UUID
    ) -> WalletTransaction:
        return await self._apply(
            user_id,
            type_=WalletTransactionType.refund,
            amount=amount,
            reference_type="order",
            reference_id=order_id,
            note="بازپرداخت سفارش",
            actor_id=actor_id,
        )

    async def admin_credit(
        self, user_id: uuid.UUID, amount: Decimal, reason: str, *, actor_id: uuid.UUID
    ) -> WalletTransaction:
        return await self._apply(
            user_id,
            type_=WalletTransactionType.admin_credit,
            amount=amount,
            note=reason,
            actor_id=actor_id,
        )

    async def admin_debit(
        self, user_id: uuid.UUID, amount: Decimal, reason: str, *, actor_id: uuid.UUID
    ) -> WalletTransaction:
        return await self._apply(
            user_id,
            type_=WalletTransactionType.admin_debit,
            amount=amount,
            note=reason,
            actor_id=actor_id,
        )

    async def get_wallet_or_404(self, user_id: uuid.UUID) -> Wallet:
        wallet = await self.repo.get_by_user_id(user_id)
        if wallet is None:
            raise NotFoundError("کیف پول پیدا نشد.")
        return wallet
