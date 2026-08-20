import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.modules.tickets.models import Ticket, TicketStatus
from app.modules.users.models import User, UserRole
from app.security.csrf import CSRF_HEADER_NAME
from app.tasks.ticket_tasks import _auto_close_stale_tickets


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    token = client.cookies.get("csrf_token")
    assert token is not None
    return {CSRF_HEADER_NAME: token}


async def _register(client: AsyncClient) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    payload = {
        "email": f"tik{suffix}@example.com",
        "username": f"tik{suffix}",
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


async def test_create_ticket_and_view_own(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "مشکل در پرداخت", "message": "پرداخت من انجام نشد."},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "waiting_for_support"
    assert len(body["messages"]) == 1

    detail = await client.get(f"/api/v1/tickets/{body['id']}")
    assert detail.status_code == 200


async def test_customer_cannot_view_another_users_ticket(client: AsyncClient) -> None:
    await _register(client)
    created = await client.post(
        "/api/v1/tickets",
        json={"subject": "پیگیری سفارش", "message": "سفارشم کجاست؟"},
        headers=_csrf_headers(client),
    )
    ticket_id = created.json()["id"]

    other_app = create_app()
    other_transport = ASGITransport(app=other_app)
    async with AsyncClient(transport=other_transport, base_url="http://test") as other_client:
        await _register(other_client)
        response = await other_client.get(f"/api/v1/tickets/{ticket_id}")
        assert response.status_code == 403


async def test_customer_reply_moves_ticket_to_waiting_for_support(client: AsyncClient) -> None:
    await _register(client)
    created = await client.post(
        "/api/v1/tickets",
        json={"subject": "موجودی محصول", "message": "این کالا کی موجود میشه؟"},
        headers=_csrf_headers(client),
    )
    ticket_id = created.json()["id"]

    reply = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        json={"message": "همچنان منتظرم."},
        headers=_csrf_headers(client),
    )
    assert reply.status_code == 200
    assert reply.json()["status"] == "waiting_for_support"
    assert len(reply.json()["messages"]) == 2


async def test_support_reply_requires_permission(client: AsyncClient) -> None:
    await _register(client)
    created = await client.post(
        "/api/v1/tickets",
        json={"subject": "زمان ارسال", "message": "چند روز طول می‌کشد؟"},
        headers=_csrf_headers(client),
    )
    ticket_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/admin/tickets/{ticket_id}/messages",
        json={"message": "به‌زودی ارسال می‌شود."},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 403


async def test_admin_reply_moves_ticket_to_waiting_for_customer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    customer_payload = await _register(client)
    created = await client.post(
        "/api/v1/tickets",
        json={"subject": "سوال درباره گارانتی", "message": "گارانتی دارد؟"},
        headers=_csrf_headers(client),
    )
    ticket_id = created.json()["id"]

    admin_app = create_app()
    admin_transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=admin_transport, base_url="http://test") as admin_client:
        admin_payload = await _register(admin_client)
        await _make_admin(admin_client, db_session, admin_payload["email"])

        reply = await admin_client.post(
            f"/api/v1/admin/tickets/{ticket_id}/messages",
            json={"message": "بله، ۱۲ ماه گارانتی دارد."},
            headers=_csrf_headers(admin_client),
        )
        assert reply.status_code == 200, reply.text
        assert reply.json()["status"] == "waiting_for_customer"

    assert customer_payload


async def test_auto_close_stale_ticket(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"stale{user_id.hex[:8]}@example.com",
        username=f"stale{user_id.hex[:8]}",
        hashed_password="x",
        role=UserRole.customer,
    )
    db_session.add(user)
    await db_session.flush()

    stale_ticket = Ticket(
        user_id=user_id,
        subject="سوال قدیمی",
        status=TicketStatus.waiting_for_customer,
        last_response_at=datetime.now(UTC) - timedelta(hours=30),
    )
    fresh_ticket = Ticket(
        user_id=user_id,
        subject="سوال تازه",
        status=TicketStatus.waiting_for_customer,
        last_response_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.add_all([stale_ticket, fresh_ticket])
    await db_session.commit()

    closed_count = await _auto_close_stale_tickets()
    assert closed_count >= 1

    await db_session.refresh(stale_ticket)
    await db_session.refresh(fresh_ticket)
    assert stale_ticket.status == TicketStatus.closed
    assert stale_ticket.closed_at is not None
    assert fresh_ticket.status == TicketStatus.waiting_for_customer


async def test_auto_close_is_idempotent_on_rerun(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"idem{user_id.hex[:8]}@example.com",
        username=f"idem{user_id.hex[:8]}",
        hashed_password="x",
        role=UserRole.customer,
    )
    db_session.add(user)
    await db_session.flush()

    ticket = Ticket(
        user_id=user_id,
        subject="یک سوال",
        status=TicketStatus.waiting_for_customer,
        last_response_at=datetime.now(UTC) - timedelta(hours=48),
    )
    db_session.add(ticket)
    await db_session.commit()

    ticket_id = ticket.id  # read before expire_all() below invalidates the attribute
    first_run = await _auto_close_stale_tickets()
    assert first_run >= 1
    second_run = await _auto_close_stale_tickets()

    db_session.expire_all()
    result = await db_session.execute(select(Ticket).where(Ticket.id == ticket_id))
    reloaded = result.scalar_one()
    assert reloaded.status == TicketStatus.closed
    # Already-closed ticket isn't a candidate on the second pass.
    assert second_run == 0
