import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wallet.models import Wallet, WalletTransaction


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Wallet | None:
        result = await self.session.execute(select(Wallet).where(Wallet.user_id == user_id))
        return result.scalar_one_or_none()

    async def lock_by_user_id(self, user_id: uuid.UUID) -> Wallet | None:
        result = await self.session.execute(
            select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        )
        return result.scalar_one_or_none()

    def add(self, wallet: Wallet) -> None:
        self.session.add(wallet)

    def add_transaction(self, transaction: WalletTransaction) -> None:
        self.session.add(transaction)

    async def list_for_wallet(
        self, wallet_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[list[WalletTransaction], int]:
        total = (
            await self.session.execute(
                select(func.count())
                .select_from(WalletTransaction)
                .where(WalletTransaction.wallet_id == wallet_id)
            )
        ).scalar_one()
        result = await self.session.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars()), total
