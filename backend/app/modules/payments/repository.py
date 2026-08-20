import uuid
from typing import Any, cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.models import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, payment: Payment) -> None:
        self.session.add(payment)

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        return await self.session.get(Payment, payment_id)

    async def get_by_authority(self, authority: str) -> Payment | None:
        result = await self.session.execute(select(Payment).where(Payment.authority == authority))
        return result.scalar_one_or_none()

    async def try_claim(
        self, payment_id: uuid.UUID, *, from_status: PaymentStatus, to_status: PaymentStatus
    ) -> bool:
        """Compare-and-swap the payment status. Returns True only if this
        call performed the transition — the mechanism that makes payment
        verification idempotent under replayed/concurrent callbacks (see
        docs/architecture.md §8): whoever loses the race sees rowcount 0 and
        must not re-run verification or touch the order."""
        result = cast(
            "CursorResult[Any]",
            await self.session.execute(
                update(Payment)
                .where(Payment.id == payment_id, Payment.status == from_status)
                .values(status=to_status)
            ),
        )
        return result.rowcount == 1
