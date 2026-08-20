import json
import secrets
import uuid as uuid_module

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cookies import REFRESH_TOKEN_COOKIE, clear_auth_cookies, set_auth_cookies
from app.common.errors import ConflictError, UnauthorizedError
from app.common.redis_client import get_redis
from app.core.config import get_settings
from app.db.session import get_db_session
from app.integrations import google_oauth
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    EmailVerificationConfirm,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    UserPublic,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

OAUTH_STATE_TTL_SECONDS = 600


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    return request.headers.get("User-Agent"), request.client.host if request.client else None


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> UserPublic:
    service = AuthService(session)
    user = await service.register(data)
    user_agent, ip_address = _client_meta(request)
    access_token, refresh_token = await service.issue_token_pair(
        user, user_agent=user_agent, ip_address=ip_address
    )
    await session.commit()
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=UserPublic)
async def login(
    data: LoginRequest,
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> UserPublic:
    service = AuthService(session)
    user = await service.authenticate(data.email, data.password)
    user_agent, ip_address = _client_meta(request)
    access_token, refresh_token = await service.issue_token_pair(
        user, user_agent=user_agent, ip_address=ip_address
    )
    await session.commit()
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return UserPublic.model_validate(user)


@router.post("/refresh", response_model=UserPublic)
async def refresh(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
) -> UserPublic:
    if not refresh_token:
        raise UnauthorizedError("نشست شما یافت نشد. دوباره وارد شوید.")

    service = AuthService(session)
    user_agent, ip_address = _client_meta(request)
    access_token, new_refresh_token, user = await service.rotate_refresh_token(
        refresh_token, user_agent=user_agent, ip_address=ip_address
    )
    await session.commit()
    set_auth_cookies(response, access_token=access_token, refresh_token=new_refresh_token)
    return UserPublic.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
) -> None:
    if refresh_token:
        await AuthService(session).logout(refresh_token)
        await session.commit()
    clear_auth_cookies(response)


@router.get("/me", response_model=UserPublic)
async def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    response: Response,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = AuthService(session)
    await service.change_password(user, data.current_password, data.new_password)
    await session.commit()
    clear_auth_cookies(response)


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    data: PasswordResetRequest, session: AsyncSession = Depends(get_db_session)
) -> None:
    await AuthService(session).request_password_reset(data.email)
    await session.commit()


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    data: PasswordResetConfirm, session: AsyncSession = Depends(get_db_session)
) -> None:
    await AuthService(session).confirm_password_reset(data.token, data.new_password)
    await session.commit()


@router.post("/email-verification/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_email_verification(
    data: EmailVerificationConfirm, session: AsyncSession = Depends(get_db_session)
) -> None:
    await AuthService(session).confirm_email_verification(data.token)
    await session.commit()


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    verifier, challenge = google_oauth.generate_pkce_pair()

    redis = get_redis()
    await redis.set(
        f"oauth:google:{state}",
        json.dumps({"nonce": nonce, "verifier": verifier, "action": "login"}),
        ex=OAUTH_STATE_TTL_SECONDS,
    )
    url = google_oauth.build_authorization_url(state=state, nonce=nonce, code_challenge=challenge)
    return RedirectResponse(url)


@router.get("/google/link/start")
async def google_link_start(user: CurrentUser) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    verifier, challenge = google_oauth.generate_pkce_pair()

    redis = get_redis()
    session_payload = {
        "nonce": nonce,
        "verifier": verifier,
        "action": "link",
        "user_id": str(user.id),
    }
    await redis.set(
        f"oauth:google:{state}", json.dumps(session_payload), ex=OAUTH_STATE_TTL_SECONDS
    )
    url = google_oauth.build_authorization_url(state=state, nonce=nonce, code_challenge=challenge)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    redis = get_redis()
    raw_session = await redis.get(f"oauth:google:{state}")
    if raw_session is None:
        raise UnauthorizedError("درخواست ورود با گوگل نامعتبر یا منقضی‌شده است.")
    await redis.delete(f"oauth:google:{state}")
    oauth_session = json.loads(raw_session)

    raw_id_token = await google_oauth.exchange_code(
        code=code, code_verifier=oauth_session["verifier"]
    )
    identity = await google_oauth.verify_id_token(
        raw_id_token, expected_nonce=oauth_session["nonce"]
    )

    service = AuthService(session)
    redirect = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    if oauth_session["action"] == "link":
        current_user = await UserRepository(session).get_by_id(
            uuid_module.UUID(oauth_session["user_id"])
        )
        if current_user is None:
            raise UnauthorizedError("نشست شما نامعتبر است. دوباره وارد شوید.")
        await service.link_google_account(current_user, identity)
        await session.commit()
        return redirect

    try:
        user = await service.login_or_register_with_google(identity)
    except ConflictError:
        await session.rollback()
        raise

    user_agent, ip_address = _client_meta(request)
    access_token, refresh_token = await service.issue_token_pair(
        user, user_agent=user_agent, ip_address=ip_address
    )
    await session.commit()
    set_auth_cookies(redirect, access_token=access_token, refresh_token=refresh_token)
    return redirect
