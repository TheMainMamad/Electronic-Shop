import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.ticket_tasks.auto_close_stale_tickets", bind=True, max_retries=3)
def auto_close_stale_tickets(self: object) -> dict[str, int]:
    """Close tickets waiting on the customer for more than 24h. Implemented in Phase 7."""
    logger.info("auto_close_stale_tickets_noop")
    return {"closed": 0}
