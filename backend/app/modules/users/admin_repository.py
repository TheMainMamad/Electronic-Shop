from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User


class UsersAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self, *, search: str | None, offset: int, limit: int
    ) -> tuple[list[User], int]:
        query = select(User)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(User.email.ilike(term), User.username.ilike(term))
            )

        total = (
            await self.session.execute(select(func.count()).select_from(query.subquery()))
        ).scalar_one()
        result = await self.session.execute(
            query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars()), total
