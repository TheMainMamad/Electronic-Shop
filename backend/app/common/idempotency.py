import hashlib
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, IdempotentReplay
from app.common.idempotency_models import IdempotencyKey, IdempotencyStatus
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser

IDEMPOTENCY_TTL = timedelta(hours=24)


class IdempotencyKeyRequiredError(AppError):
    code = "IDEMPOTENCY_KEY_REQUIRED"
    message = "برای این عملیات ارسال هدر Idempotency-Key الزامی است."
    status_code = 400


class IdempotencyKeyReusedError(AppError):
    code = "IDEMPOTENCY_KEY_REUSED"
    message = "این کلید یکتا قبلاً برای درخواست دیگری استفاده شده است."
    status_code = 422


class IdempotencyGuard:
    def __init__(self, session: AsyncSession, record: IdempotencyKey) -> None:
        self._session = session
        self._record = record

    async def finish(self, status_code: int, body: Any) -> None:
        self._record.status = IdempotencyStatus.completed
        self._record.response_status = status_code
        self._record.response_body = body


def idempotency_guard(
    operation: str,
) -> Callable[..., Coroutine[Any, Any, IdempotencyGuard]]:
    async def dependency(
        request: Request,
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_db_session)],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> IdempotencyGuard:
        if not idempotency_key:
            raise IdempotencyKeyRequiredError()

        # Captured up front: session.rollback() below (on the conflict path)
        # expires every object already loaded in this session, including
        # `user` — touching user.id afterwards would trigger an implicit
        # synchronous attribute refresh, which isn't supported under async
        # SQLAlchemy and crashes with MissingGreenlet.
        user_id = user.id

        body_bytes = await request.body()
        request_hash = hashlib.sha256(body_bytes).hexdigest()

        record = IdempotencyKey(
            key=idempotency_key,
            user_id=user_id,
            operation=operation,
            request_hash=request_hash,
            status=IdempotencyStatus.pending,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + IDEMPOTENCY_TTL,
        )
        session.add(record)
        try:
            await session.flush()
        except IntegrityError:
            # A concurrent/prior request already holds this key. Postgres's
            # unique constraint serializes concurrent inserts, so by the time
            # we observe the conflict the other transaction has already
            # committed — we will always see its final state here, never a
            # still-"pending" row.
            await session.rollback()
            existing = (
                await session.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.user_id == user_id,
                        IdempotencyKey.operation == operation,
                        IdempotencyKey.key == idempotency_key,
                    )
                )
            ).scalar_one()

            if existing.request_hash != request_hash:
                raise IdempotencyKeyReusedError() from None

            raise IdempotentReplay(
                existing.response_status or 200, existing.response_body
            ) from None

        return IdempotencyGuard(session, record)

    return dependency
