import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.orders.models import Order, OrderItem, OrderStatusHistory


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        result = await self.session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        total = (
            await self.session.execute(
                select(func.count()).select_from(Order).where(Order.user_id == user_id)
            )
        ).scalar_one()
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars()), total

    async def list_all(self, *, offset: int, limit: int) -> tuple[list[Order], int]:
        total = (await self.session.execute(select(func.count()).select_from(Order))).scalar_one()
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars()), total

    def add(self, order: Order) -> None:
        self.session.add(order)

    def add_item(self, item: OrderItem) -> None:
        self.session.add(item)

    def add_history(self, entry: OrderStatusHistory) -> None:
        self.session.add(entry)
