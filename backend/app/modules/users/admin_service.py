import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError
from app.modules.audit.service import write_audit_log
from app.modules.auth.repository import UserRepository
from app.modules.users.admin_repository import UsersAdminRepository
from app.modules.users.models import User
from app.modules.users.schemas import AdminUserUpdate


class UsersAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UsersAdminRepository(session)
        self.users = UserRepository(session)

    async def list_users(
        self, *, search: str | None, offset: int, limit: int
    ) -> tuple[list[User], int]:
        return await self.repo.search(search=search, offset=offset, limit=limit)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("کاربر پیدا نشد.")
        return user

    async def update_user(
        self, user_id: uuid.UUID, data: AdminUserUpdate, *, actor_id: uuid.UUID
    ) -> User:
        user = await self.get_user(user_id)

        if data.role is not None and data.role != user.role:
            if user.id == actor_id:
                raise ConflictError("نمی‌توانید نقش خودتان را تغییر دهید.")
            await write_audit_log(
                self.session,
                actor_id=actor_id,
                action="user.role_changed",
                resource_type="user",
                resource_id=user.id,
                metadata={"from": user.role.value, "to": data.role.value},
            )
            user.role = data.role

        if data.is_active is not None and data.is_active != user.is_active:
            await write_audit_log(
                self.session,
                actor_id=actor_id,
                action="user.activated" if data.is_active else "user.deactivated",
                resource_type="user",
                resource_id=user.id,
            )
            user.is_active = data.is_active

        return user
