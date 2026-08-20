import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import PermissionDeniedError
from app.modules.auth.dependencies import require_permission
from app.modules.auth.repository import UserRepository
from app.modules.users.models import User, UserRole
from app.security.csrf import CSRF_HEADER_NAME
from app.security.password import hash_password


def _unique_user() -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    return {
        "email": f"user{suffix}@example.com",
        "username": f"user{suffix}",
        "password": "Str0ngPass!word",
        "first_name": "کاربر",
        "last_name": "تستی",
    }


async def _register(client: AsyncClient) -> dict[str, str]:
    payload = _unique_user()
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    """CSRF cookie rotates on every register/login/refresh, so always read the
    current value instead of caching it once."""
    token = client.cookies.get("csrf_token")
    assert token is not None
    return {CSRF_HEADER_NAME: token}


async def test_register_sets_session_cookies(client: AsyncClient) -> None:
    payload = await _register(client)

    body = (await client.get("/api/v1/auth/me")).json()
    assert body["email"] == payload["email"]
    assert body["role"] == UserRole.customer.value


async def test_duplicate_email_registration_is_rejected(client: AsyncClient) -> None:
    payload = await _register(client)

    response = await client.post(
        "/api/v1/auth/register",
        json={**payload, "username": payload["username"] + "x"},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_login_with_wrong_password_returns_generic_error(client: AsyncClient) -> None:
    payload = await _register(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "totally-wrong"},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 401
    assert "نادرست" in response.json()["error"]["message"]


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_rotates_and_old_token_reuse_is_rejected(client: AsyncClient) -> None:
    await _register(client)

    old_refresh_cookie = client.cookies.get("refresh_token")
    assert old_refresh_cookie is not None

    refreshed = await client.post("/api/v1/auth/refresh", headers=_csrf_headers(client))
    assert refreshed.status_code == 200
    new_refresh_cookie = client.cookies.get("refresh_token")
    assert new_refresh_cookie != old_refresh_cookie

    # Replay the now-revoked original refresh token: must fail and, per the
    # rotation design, this also revokes the whole token family.
    client.cookies.set("refresh_token", old_refresh_cookie)
    replay = await client.post("/api/v1/auth/refresh", headers=_csrf_headers(client))
    assert replay.status_code == 401

    # Even the legitimately-rotated token is now dead because reuse detection
    # revoked the entire family.
    client.cookies.set("refresh_token", new_refresh_cookie)
    after_breach = await client.post("/api/v1/auth/refresh", headers=_csrf_headers(client))
    assert after_breach.status_code == 401


async def test_logout_revokes_session(client: AsyncClient) -> None:
    await _register(client)
    csrf_cookie = client.cookies.get("csrf_token")
    logout_response = await client.post(
        "/api/v1/auth/logout", headers={CSRF_HEADER_NAME: csrf_cookie}
    )
    assert logout_response.status_code == 204

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


async def test_mutating_request_without_csrf_header_is_rejected(client: AsyncClient) -> None:
    await _register(client)
    csrf_cookie = client.cookies.get("csrf_token")
    assert csrf_cookie is not None

    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Str0ngPass!word", "new_password": "AnotherStr0ng!pass"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"


async def test_mutating_request_with_valid_csrf_header_succeeds(client: AsyncClient) -> None:
    await _register(client)
    csrf_cookie = client.cookies.get("csrf_token")

    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Str0ngPass!word", "new_password": "AnotherStr0ng!pass"},
        headers={CSRF_HEADER_NAME: csrf_cookie},
    )
    assert response.status_code == 204


async def test_permission_denied_for_customer_role(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    payload = _unique_user()

    customer = User(
        email=payload["email"],
        username=payload["username"],
        hashed_password=hash_password(payload["password"]),
        role=UserRole.customer,
    )
    repo.add(customer)
    await db_session.flush()

    dependency = require_permission("user.manage")
    with pytest.raises(PermissionDeniedError):
        await dependency(customer)

    admin = User(
        email=f"admin-{payload['email']}",
        username=f"admin-{payload['username']}",
        hashed_password=hash_password(payload["password"]),
        role=UserRole.admin,
    )
    repo.add(admin)
    await db_session.flush()

    result = await dependency(admin)
    assert result is admin
