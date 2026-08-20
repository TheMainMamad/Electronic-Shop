import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError
from app.main import create_app
from app.modules.users.models import User, UserRole
from app.modules.wallet.service import WalletService
from app.security.csrf import CSRF_HEADER_NAME


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    token = client.cookies.get("csrf_token")
    assert token is not None
    return {CSRF_HEADER_NAME: token}


async def _register(client: AsyncClient) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    payload = {
        "email": f"wal{suffix}@example.com",
        "username": f"wal{suffix}",
        "password": "Str0ngPass!word",
    }
    headers = {}
    existing = client.cookies.get("csrf_token")
    if existing:
        headers = {CSRF_HEADER_NAME: existing}
    response = await client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return payload


async def _make_admin(client: AsyncClient, db_session: AsyncSession, email: str) -> None:
    result = await db_session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one()
    user.role = UserRole.admin
    await db_session.commit()
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Str0ngPass!word"},
        headers=_csrf_headers(client),
    )


async def test_deposit_increases_balance(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/wallet/deposit",
        json={"amount": "50000"},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    assert response.json()["balance_after"] == "50000"

    wallet = await client.get("/api/v1/wallet")
    assert wallet.json()["balance"] == "50000"


async def test_deposit_is_idempotent(client: AsyncClient) -> None:
    await _register(client)
    key = str(uuid.uuid4())
    for _ in range(2):
        response = await client.post(
            "/api/v1/wallet/deposit",
            json={"amount": "30000"},
            headers={**_csrf_headers(client), "Idempotency-Key": key},
        )
        assert response.status_code == 201

    wallet = await client.get("/api/v1/wallet")
    assert wallet.json()["balance"] == "30000"  # not 60000


async def test_customer_cannot_admin_credit_wallet(client: AsyncClient) -> None:
    payload = await _register(client)
    result = await client.post(
        f"/api/v1/admin/wallets/{uuid.uuid4()}/credit",
        json={"amount": "10000", "reason": "test"},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert result.status_code == 403
    assert payload  # keep the registered payload referenced


async def test_admin_can_credit_and_debit_wallet(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    customer_payload = await _register(client)
    customer_response = await client.get("/api/v1/auth/me")
    customer_id = customer_response.json()["id"]

    admin_app = create_app()
    admin_transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=admin_transport, base_url="http://test") as admin_client:
        admin_payload = await _register(admin_client)
        await _make_admin(admin_client, db_session, admin_payload["email"])

        credit = await admin_client.post(
            f"/api/v1/admin/wallets/{customer_id}/credit",
            json={"amount": "20000", "reason": "جبران مشکل ارسال"},
            headers={**_csrf_headers(admin_client), "Idempotency-Key": str(uuid.uuid4())},
        )
        assert credit.status_code == 201, credit.text
        assert credit.json()["balance_after"] == "20000"

        debit = await admin_client.post(
            f"/api/v1/admin/wallets/{customer_id}/debit",
            json={"amount": "5000", "reason": "اصلاح موجودی"},
            headers={**_csrf_headers(admin_client), "Idempotency-Key": str(uuid.uuid4())},
        )
        assert debit.status_code == 201
        assert debit.json()["balance_after"] == "15000"

    assert customer_payload


async def test_wallet_cannot_go_negative(db_session: AsyncSession) -> None:
    service = WalletService(db_session)
    user_id = uuid.uuid4()

    user = User(
        id=user_id,
        email=f"neg{user_id.hex[:8]}@example.com",
        username=f"neg{user_id.hex[:8]}",
        hashed_password="x",
        role=UserRole.customer,
    )
    db_session.add(user)
    await db_session.flush()

    await service.deposit(user_id, Decimal("1000"))

    with pytest.raises(ConflictError):
        await service.admin_debit(user_id, Decimal("5000"), "test", actor_id=user_id)


async def test_concurrent_deposits_do_not_lose_updates(client: AsyncClient) -> None:
    await _register(client)

    async def deposit() -> None:
        await client.post(
            "/api/v1/wallet/deposit",
            json={"amount": "1000"},
            headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
        )

    await asyncio.gather(*(deposit() for _ in range(5)))

    wallet = await client.get("/api/v1/wallet")
    assert wallet.json()["balance"] == "5000"
