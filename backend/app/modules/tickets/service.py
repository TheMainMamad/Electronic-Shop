import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.tickets.models import (
    Ticket,
    TicketMessage,
    TicketMessageAuthorRole,
    TicketPriority,
    TicketStatus,
)
from app.modules.tickets.repository import TicketRepository
from app.modules.users.models import User, UserRole

_SUPPORT_ROLES = (UserRole.support, UserRole.admin, UserRole.super_admin)


class TicketService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TicketRepository(session)

    async def create(
        self, user_id: uuid.UUID, subject: str, message: str, priority: TicketPriority
    ) -> Ticket:
        now = datetime.now(UTC)
        ticket = Ticket(
            user_id=user_id,
            subject=subject,
            status=TicketStatus.waiting_for_support,
            priority=priority,
            last_response_at=now,
        )
        self.repo.add(ticket)
        await self.session.flush()

        self.repo.add_message(
            TicketMessage(
                ticket_id=ticket.id,
                author_id=user_id,
                author_role=TicketMessageAuthorRole.customer,
                body=message,
                created_at=now,
            )
        )
        await self.session.flush()
        # Deliberately not touching ticket.messages here (lazy="noload"): the
        # router always re-fetches via TicketRepository.get_by_id, which
        # selectinloads it properly. Setting it to [] here would poison the
        # identity-mapped object with the wrong value for that later fetch
        # to reuse instead of re-querying.
        return ticket

    async def get_for_user(self, ticket_id: uuid.UUID, user: User) -> Ticket:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("تیکت پیدا نشد.")
        if ticket.user_id != user.id and user.role not in _SUPPORT_ROLES:
            raise PermissionDeniedError("شما اجازه دسترسی به این تیکت را ندارید.")
        return ticket

    async def add_customer_reply(self, ticket_id: uuid.UUID, user: User, body: str) -> Ticket:
        ticket = await self.get_for_user(ticket_id, user)
        if ticket.user_id != user.id:
            raise PermissionDeniedError("فقط صاحب تیکت می‌تواند پاسخ مشتری ثبت کند.")
        if ticket.status == TicketStatus.closed:
            raise ConflictError("این تیکت بسته شده است و امکان ارسال پیام جدید وجود ندارد.")

        now = datetime.now(UTC)
        self.repo.add_message(
            TicketMessage(
                ticket_id=ticket.id,
                author_id=user.id,
                author_role=TicketMessageAuthorRole.customer,
                body=body,
                created_at=now,
            )
        )
        ticket.status = TicketStatus.waiting_for_support
        ticket.last_response_at = now
        return ticket

    async def add_support_reply(self, ticket_id: uuid.UUID, actor: User, body: str) -> Ticket:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("تیکت پیدا نشد.")
        if ticket.status == TicketStatus.closed:
            raise ConflictError("این تیکت بسته شده است و امکان ارسال پیام جدید وجود ندارد.")

        now = datetime.now(UTC)
        self.repo.add_message(
            TicketMessage(
                ticket_id=ticket.id,
                author_id=actor.id,
                author_role=TicketMessageAuthorRole.support,
                body=body,
                created_at=now,
            )
        )
        ticket.status = TicketStatus.waiting_for_customer
        ticket.last_response_at = now
        return ticket

    async def change_status(self, ticket_id: uuid.UUID, new_status: TicketStatus) -> Ticket:
        ticket = await self.repo.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("تیکت پیدا نشد.")
        ticket.status = new_status
        if new_status == TicketStatus.closed:
            ticket.closed_at = datetime.now(UTC)
        return ticket
