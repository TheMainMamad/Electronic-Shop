from celery import Celery

from app.core.config import get_settings

settings = get_settings()


def _with_db(redis_url: str, db: int) -> str:
    base = redis_url.rsplit("/", 1)[0] if redis_url.count("/") >= 3 else redis_url.rstrip("/")
    return f"{base}/{db}"


broker_url = _with_db(str(settings.redis_url), 1)
result_backend_url = _with_db(str(settings.redis_url), 1)

celery_app = Celery(
    "electronics_shop",
    broker=broker_url,
    backend=result_backend_url,
    include=["app.tasks.ticket_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=200,
)

celery_app.conf.beat_schedule = {
    "auto-close-stale-tickets": {
        "task": "app.tasks.ticket_tasks.auto_close_stale_tickets",
        "schedule": 600.0,
    },
}
