import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import NotFoundError
from app.common.pagination import Page, PageParams
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser, require_permission
from app.modules.tickets.models import Ticket
from app.modules.tickets.repository import TicketRepository
from app.modules.tickets.schemas import (
    TicketCreate,
    TicketListItem,
    TicketPublic,
    TicketReplyCreate,
    TicketStatusUpdate,
)
from app.modules.tickets.service import TicketService

router = APIRouter(tags=["tickets"])


def _serialize_ticket(ticket: Ticket) -> TicketPublic:
    return TicketPublic.model_validate(ticket)


async def _fetch_full_ticket(session: AsyncSession, ticket_id: uuid.UUID) -> Ticket:
    ticket = await TicketRepository(session).get_by_id(ticket_id)
    if ticket is None:
        raise NotFoundError("تیکت پیدا نشد.")
    return ticket


@router.post("/tickets", response_model=TicketPublic, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreate, user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> TicketPublic:
    created = await TicketService(session).create(
        user.id, data.subject, data.message, data.priority
    )
    await session.commit()
    ticket = await _fetch_full_ticket(session, created.id)
    return _serialize_ticket(ticket)


@router.get("/tickets", response_model=Page[TicketListItem])
async def list_my_tickets(
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
) -> Page[TicketListItem]:
    items, total = await TicketRepository(session).list_for_user(
        user.id, offset=page_params.offset, limit=page_params.page_size
    )
    return Page.create(
        [TicketListItem.model_validate(item) for item in items], total, page_params
    )


@router.get("/tickets/{ticket_id}", response_model=TicketPublic)
async def get_ticket(
    ticket_id: uuid.UUID, user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> TicketPublic:
    ticket = await TicketService(session).get_for_user(ticket_id, user)
    return _serialize_ticket(ticket)


@router.post("/tickets/{ticket_id}/messages", response_model=TicketPublic)
async def reply_to_ticket(
    ticket_id: uuid.UUID,
    data: TicketReplyCreate,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> TicketPublic:
    await TicketService(session).add_customer_reply(ticket_id, user, data.message)
    await session.commit()
    ticket = await _fetch_full_ticket(session, ticket_id)
    return _serialize_ticket(ticket)


@router.get(
    "/admin/tickets",
    response_model=Page[TicketListItem],
    dependencies=[Depends(require_permission("ticket.read"))],
)
async def admin_list_tickets(
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
    ticket_status: str | None = None,
) -> Page[TicketListItem]:
    items, total = await TicketRepository(session).list_all(
        status=ticket_status, offset=page_params.offset, limit=page_params.page_size
    )
    return Page.create(
        [TicketListItem.model_validate(item) for item in items], total, page_params
    )


@router.get(
    "/admin/tickets/{ticket_id}",
    response_model=TicketPublic,
    dependencies=[Depends(require_permission("ticket.read"))],
)
async def admin_get_ticket(
    ticket_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> TicketPublic:
    ticket = await _fetch_full_ticket(session, ticket_id)
    return _serialize_ticket(ticket)


@router.post(
    "/admin/tickets/{ticket_id}/messages",
    response_model=TicketPublic,
    dependencies=[Depends(require_permission("ticket.respond"))],
)
async def admin_reply_to_ticket(
    ticket_id: uuid.UUID,
    data: TicketReplyCreate,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> TicketPublic:
    await TicketService(session).add_support_reply(ticket_id, user, data.message)
    await session.commit()
    ticket = await _fetch_full_ticket(session, ticket_id)
    return _serialize_ticket(ticket)


@router.patch(
    "/admin/tickets/{ticket_id}/status",
    response_model=TicketPublic,
    dependencies=[Depends(require_permission("ticket.manage"))],
)
async def admin_change_ticket_status(
    ticket_id: uuid.UUID,
    data: TicketStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TicketPublic:
    await TicketService(session).change_status(ticket_id, data.status)
    await session.commit()
    ticket = await _fetch_full_ticket(session, ticket_id)
    return _serialize_ticket(ticket)
