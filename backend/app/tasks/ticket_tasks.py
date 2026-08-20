import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import structlog
from sqlalchemy import CursorResult, select, update

from app.db.session import AsyncSessionFactory
from app.modules.audit.service import write_audit_log
from app.modules.tickets.models import Ticket, TicketMessage, TicketMessageAuthorRole, TicketStatus
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()

STALE_AFTER = timedelta(hours=24)
BATCH_SIZE = 100
AUTO_CLOSE_NOTE = (
    "این تیکت به دلیل عدم پاسخ مشتری طی ۲۴ ساعت گذشته به‌صورت خودکار بسته شد."
)


async def _auto_close_stale_tickets() -> int:
    cutoff = datetime.now(UTC) - STALE_AFTER
    closed_count = 0

    async with AsyncSessionFactory() as session:
        candidates = (
            await session.execute(
                select(Ticket.id)
                .where(
                    Ticket.status == TicketStatus.waiting_for_customer,
                    Ticket.last_response_at < cutoff,
                )
                .limit(BATCH_SIZE)
            )
        ).scalars().all()

        for ticket_id in candidates:
            now = datetime.now(UTC)
            # Conditional UPDATE: the WHERE-clause guard is what makes this
            # safe under multiple concurrent beat/worker instances and safe
            # to retry — a ticket a human already closed in the meantime
            # simply won't match and is silently skipped.
            result = cast(
                "CursorResult[Any]",
                await session.execute(
                    update(Ticket)
                    .where(
                        Ticket.id == ticket_id,
                        Ticket.status == TicketStatus.waiting_for_customer,
                    )
                    .values(status=TicketStatus.closed, closed_at=now)
                ),
            )
            if result.rowcount != 1:
                continue

            session.add(
                TicketMessage(
                    ticket_id=ticket_id,
                    author_id=None,
                    author_role=TicketMessageAuthorRole.system,
                    body=AUTO_CLOSE_NOTE,
                    created_at=now,
                )
            )
            await write_audit_log(
                session,
                actor_id=None,
                action="ticket.auto_closed",
                resource_type="ticket",
                resource_id=ticket_id,
                metadata={"reason": "waiting_for_customer_timeout"},
            )
            await session.commit()
            closed_count += 1

    return closed_count


@celery_app.task(name="app.tasks.ticket_tasks.auto_close_stale_tickets", bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def auto_close_stale_tickets(self: object) -> dict[str, int]:
    closed_count = asyncio.run(_auto_close_stale_tickets())
    logger.info("auto_close_stale_tickets_completed", closed=closed_count)
    return {"closed": closed_count}
