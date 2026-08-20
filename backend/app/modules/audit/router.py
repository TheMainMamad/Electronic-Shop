from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import Page, PageParams
from app.db.session import get_db_session
from app.modules.audit.schemas import AuditLogPublic
from app.modules.audit.service import list_audit_logs
from app.modules.auth.dependencies import require_permission

router = APIRouter(tags=["audit"])


@router.get(
    "/admin/audit-logs",
    response_model=Page[AuditLogPublic],
    dependencies=[Depends(require_permission("audit.read"))],
)
async def list_admin_audit_logs(
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
) -> Page[AuditLogPublic]:
    items, total = await list_audit_logs(
        session, offset=page_params.offset, limit=page_params.page_size
    )
    return Page.create(
        [AuditLogPublic.model_validate(item) for item in items], total, page_params
    )
