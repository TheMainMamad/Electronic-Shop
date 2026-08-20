import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Cookie, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cookies import ACCESS_TOKEN_COOKIE
from app.common.errors import PermissionDeniedError, UnauthorizedError
from app.db.session import get_db_session
from app.modules.auth.repository import UserRepository
from app.modules.users.models import User
from app.security.jwt import TokenError, decode_access_token
from app.security.permissions import Permission, role_has_permission


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    access_token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE)] = None,
) -> User:
    token = access_token or _bearer_token_from_header(request)
    if not token:
        raise UnauthorizedError("برای ادامه لازم است وارد حساب کاربری خود شوید.")

    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = await UserRepository(session).get_by_id(uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("حساب کاربری شما یافت نشد یا غیرفعال است.")
    return user


def _bearer_token_from_header(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if header and header.startswith("Bearer "):
        return header.removeprefix("Bearer ")
    return None


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(
    permission: Permission,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def dependency(user: CurrentUser) -> User:
        if not role_has_permission(user.role, permission):
            raise PermissionDeniedError("شما اجازه دسترسی به این بخش را ندارید.")
        return user

    return dependency
