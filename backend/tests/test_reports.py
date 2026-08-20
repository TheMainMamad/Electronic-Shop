import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Category, Product, ProductInventory
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.users.models import User, UserRole
from app.security.csrf import CSRF_HEADER_NAME


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    token = client.cookies.get("csrf_token")
    assert token is not None
    return {CSRF_HEADER_NAME: token}


async def _register(client: AsyncClient) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    payload = {
        "email": f"rep{suffix}@example.com",
        "username": f"rep{suffix}",
        "password": "Str0ngPass!word",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
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


async def test_dashboard_stats_requires_permission(client: AsyncClient) -> None:
    await _register(client)
    response = await client.get("/api/v1/admin/dashboard/stats")
    assert response.status_code == 403


async def test_dashboard_stats_reflects_seeded_order(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    category = Category(name="دسته گزارش", slug=f"report-cat-{uuid.uuid4().hex[:8]}")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        sku=f"REP-{uuid.uuid4().hex[:8]}",
        name="محصول گزارش",
        slug=f"report-product-{uuid.uuid4().hex[:8]}",
        price=Decimal("40000"),
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.flush()
    db_session.add(ProductInventory(product_id=product.id, stock_total=5, stock_reserved=0))

    buyer_id = uuid.uuid4()
    buyer = User(
        id=buyer_id,
        email=f"buyer{buyer_id.hex[:8]}@example.com",
        username=f"buyer{buyer_id.hex[:8]}",
        hashed_password="x",
        role=UserRole.customer,
    )
    db_session.add(buyer)
    await db_session.flush()

    order = Order(
        user_id=buyer_id,
        status=OrderStatus.paid,
        subtotal=Decimal("40000"),
        total=Decimal("40000"),
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name_snapshot=product.name,
            sku_snapshot=product.sku,
            unit_price_snapshot=Decimal("40000"),
            quantity=1,
            subtotal=Decimal("40000"),
        )
    )
    await db_session.commit()

    payload = await _register(client)
    await _make_admin(client, db_session, payload["email"])

    stats = await client.get("/api/v1/admin/dashboard/stats")
    assert stats.status_code == 200, stats.text
    body = stats.json()
    assert body["total_orders"] >= 1
    assert body["completed_orders"] >= 0
    assert Decimal(body["total_sales"]) >= Decimal("40000")


async def test_dashboard_charts_returns_requested_window(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    payload = await _register(client)
    await _make_admin(client, db_session, payload["email"])

    response = await client.get("/api/v1/admin/dashboard/charts", params={"days": 7})
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["orders_per_day"]) == 7
    assert len(body["revenue_per_day"]) == 7
    assert len(body["registrations_per_day"]) == 7


async def test_admin_report_today_range(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = await _register(client)
    await _make_admin(client, db_session, payload["email"])

    response = await client.get("/api/v1/admin/reports", params={"range": "today"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["range"] == "today"
    assert "sales" in body and "orders" in body and "category_performance" in body


async def test_admin_report_custom_range_requires_dates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    payload = await _register(client)
    await _make_admin(client, db_session, payload["email"])

    response = await client.get("/api/v1/admin/reports", params={"range": "custom"})
    assert response.status_code == 400


async def test_admin_report_custom_range_with_dates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    payload = await _register(client)
    await _make_admin(client, db_session, payload["email"])

    today = datetime.now(UTC).date()
    start = today - timedelta(days=3)
    response = await client.get(
        "/api/v1/admin/reports",
        params={"range": "custom", "start_date": start.isoformat(), "end_date": today.isoformat()},
    )
    assert response.status_code == 200, response.text
