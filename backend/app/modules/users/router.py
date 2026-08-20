import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import Page, PageParams
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser, require_permission
from app.modules.users.admin_service import UsersAdminService
from app.modules.users.schemas import AdminUserPublic, AdminUserUpdate

router = APIRouter(tags=["users"])


@router.get(
    "/admin/users",
    response_model=Page[AdminUserPublic],
    dependencies=[Depends(require_permission("user.read"))],
)
async def list_users(
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
    search: str | None = None,
) -> Page[AdminUserPublic]:
    items, total = await UsersAdminService(session).list_users(
        search=search, offset=page_params.offset, limit=page_params.page_size
    )
    return Page.create(
        [AdminUserPublic.model_validate(item) for item in items], total, page_params
    )


@router.get(
    "/admin/users/{user_id}",
    response_model=AdminUserPublic,
    dependencies=[Depends(require_permission("user.read"))],
)
async def get_user(
    user_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> AdminUserPublic:
    user = await UsersAdminService(session).get_user(user_id)
    return AdminUserPublic.model_validate(user)


@router.patch(
    "/admin/users/{user_id}",
    response_model=AdminUserPublic,
    dependencies=[Depends(require_permission("user.manage"))],
)
async def update_user(
    user_id: uuid.UUID,
    data: AdminUserUpdate,
    admin: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AdminUserPublic:
    user = await UsersAdminService(session).update_user(user_id, data, actor_id=admin.id)
    await session.commit()
    return AdminUserPublic.model_validate(user)
