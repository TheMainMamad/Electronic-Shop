import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.tickets.models import Ticket, TicketMessage


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        result = await self.session.execute(
            select(Ticket).options(selectinload(Ticket.messages)).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    def add(self, ticket: Ticket) -> None:
        self.session.add(ticket)

    def add_message(self, message: TicketMessage) -> None:
        self.session.add(message)

    async def list_for_user(
        self, user_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[list[Ticket], int]:
        total = (
            await self.session.execute(
                select(func.count()).select_from(Ticket).where(Ticket.user_id == user_id)
            )
        ).scalar_one()
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.last_response_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars()), total

    async def list_all(
        self, *, status: str | None, offset: int, limit: int
    ) -> tuple[list[Ticket], int]:
        query = select(Ticket)
        if status:
            query = query.where(Ticket.status == status)

        total = (
            await self.session.execute(select(func.count()).select_from(query.subquery()))
        ).scalar_one()
        result = await self.session.execute(
            query.order_by(Ticket.last_response_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars()), total
