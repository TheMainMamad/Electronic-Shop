import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            audit_metadata=metadata,
            ip_address=ip_address,
        )
    )


async def list_audit_logs(
    session: AsyncSession, *, offset: int, limit: int
) -> tuple[list[AuditLog], int]:
    total = (await session.execute(select(func.count()).select_from(AuditLog))).scalar_one()
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars()), total
