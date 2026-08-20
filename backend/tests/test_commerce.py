import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.integrations.zarinpal as zarinpal_module
from app.integrations.zarinpal import PaymentRequestResult, PaymentVerifyResult
from app.main import create_app
from app.modules.catalog.models import Category, Product, ProductInventory
from app.security.csrf import CSRF_HEADER_NAME


async def _fetch_inventory(db_session: AsyncSession, product_id: uuid.UUID) -> ProductInventory:
    # The app's routes commit through separate sessions; this session's
    # identity map won't see those changes without an explicit expire.
    db_session.expire_all()
    result = await db_session.execute(
        select(ProductInventory).where(ProductInventory.product_id == product_id)
    )
    return result.scalar_one()


def _slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    token = client.cookies.get("csrf_token")
    assert token is not None
    return {CSRF_HEADER_NAME: token}


async def _register(client: AsyncClient) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    payload = {
        "email": f"com{suffix}@example.com",
        "username": f"com{suffix}",
        "password": "Str0ngPass!word",
    }
    headers = {}
    existing = client.cookies.get("csrf_token")
    if existing:
        headers = {CSRF_HEADER_NAME: existing}
    response = await client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return payload


async def _seed_product(
    db_session: AsyncSession, *, stock: int = 10, price: str = "10000"
) -> Product:
    category = Category(name="دسته", slug=_slug("cat"))
    db_session.add(category)
    await db_session.flush()

    product = Product(
        sku=_slug("SKU"),
        name="محصول تستی",
        slug=_slug("product"),
        price=price,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.flush()
    db_session.add(ProductInventory(product_id=product.id, stock_total=stock, stock_reserved=0))
    await db_session.commit()
    await db_session.refresh(product)
    return product


@dataclass
class FakeZarinPalClient:
    verify_calls: int = 0
    should_verify_succeed: bool = True
    configured: bool = True

    def is_configured(self) -> bool:
        return self.configured

    async def request_payment(
        self, *, amount_rial: int, description: str, callback_url: str
    ) -> PaymentRequestResult:
        # Tests share one real, non-isolated database (no per-test
        # transaction rollback), and payments.authority is globally unique —
        # a per-instance counter would collide across different test
        # functions each starting their own fake client back at 1.
        authority = f"FAKE-AUTHORITY-{uuid.uuid4().hex}"
        return PaymentRequestResult(authority=authority, payment_url=f"https://fake/{authority}")

    async def verify_payment(self, *, amount_rial: int, authority: str) -> PaymentVerifyResult:
        self.verify_calls += 1
        if self.should_verify_succeed:
            return PaymentVerifyResult(
                success=True, reference_id="REF123", raw_response={"ok": True}
            )
        return PaymentVerifyResult(success=False, reference_id=None, raw_response={"ok": False})


@pytest.fixture
async def fake_zarinpal() -> AsyncGenerator[FakeZarinPalClient]:
    fake = FakeZarinPalClient()
    zarinpal_module.set_zarinpal_client(fake)
    yield fake
    zarinpal_module._client = None  # noqa: SLF001 - test-only reset


async def test_add_to_cart_is_idempotent(client: AsyncClient, db_session: AsyncSession) -> None:
    product = await _seed_product(db_session)
    await _register(client)
    key = str(uuid.uuid4())

    for _ in range(2):
        response = await client.post(
            "/api/v1/cart/items",
            json={"product_id": str(product.id), "quantity": 2},
            headers={**_csrf_headers(client), "Idempotency-Key": key},
        )
        assert response.status_code == 201, response.text

    summary = await client.get("/api/v1/cart")
    items = summary.json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 2  # not 4 — the retry was a no-op replay


async def test_add_to_cart_rejects_reused_key_for_different_payload(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _seed_product(db_session)
    await _register(client)
    key = str(uuid.uuid4())

    first = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers={**_csrf_headers(client), "Idempotency-Key": key},
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers={**_csrf_headers(client), "Idempotency-Key": key},
    )
    assert second.status_code == 422
    assert second.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


async def test_add_to_cart_without_key_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _seed_product(db_session)
    await _register(client)
    response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


async def test_add_to_cart_beyond_stock_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _seed_product(db_session, stock=2)
    await _register(client)
    response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 5},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 409


async def test_checkout_creates_order_reserves_stock_and_clears_cart(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _seed_product(db_session, stock=5, price="20000")
    await _register(client)
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 3},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )

    checkout = await client.post(
        "/api/v1/orders",
        json={},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert checkout.status_code == 201, checkout.text
    order = checkout.json()
    assert order["status"] == "awaiting_payment"
    assert order["total"] == "60000"

    cart = await client.get("/api/v1/cart")
    assert cart.json()["items"] == []

    inventory = await _fetch_inventory(db_session, product.id)
    assert inventory.stock_reserved == 3
    assert inventory.stock_total == 5


async def test_checkout_with_empty_cart_is_rejected(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/orders",
        json={},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 409


async def test_customer_cannot_access_another_users_order(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _seed_product(db_session, stock=5)
    await _register(client)
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    checkout = await client.post(
        "/api/v1/orders",
        json={},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    order_id = checkout.json()["id"]

    other_app = create_app()
    other_transport = ASGITransport(app=other_app)
    async with AsyncClient(transport=other_transport, base_url="http://test") as other_client:
        await _register(other_client)
        response = await other_client.get(f"/api/v1/orders/{order_id}")
        assert response.status_code == 403


async def test_payment_init_without_gateway_config_fails_clearly(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _seed_product(db_session, stock=5)
    await _register(client)
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    checkout = await client.post(
        "/api/v1/orders",
        json={},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    order_id = checkout.json()["id"]

    response = await client.post(
        "/api/v1/payments",
        json={"order_id": order_id},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 409
    assert "پیکربندی نشده" in response.json()["error"]["message"]


async def test_payment_verification_is_idempotent_under_replayed_callback(
    client: AsyncClient, db_session: AsyncSession, fake_zarinpal: FakeZarinPalClient
) -> None:
    product = await _seed_product(db_session, stock=5, price="30000")
    await _register(client)
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    checkout = await client.post(
        "/api/v1/orders",
        json={},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    order_id = checkout.json()["id"]

    init_response = await client.post(
        "/api/v1/payments",
        json={"order_id": order_id},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert init_response.status_code == 201, init_response.text
    authority = init_response.json()["payment_url"].rsplit("/", 1)[-1]

    first_callback = await client.get(
        "/api/v1/payments/callback", params={"Authority": authority, "Status": "OK"}
    )
    assert first_callback.status_code in (200, 302)

    order_after_first = await client.get(f"/api/v1/orders/{order_id}")
    assert order_after_first.json()["status"] == "paid"
    assert fake_zarinpal.verify_calls == 1

    # Replay: ZarinPal (or a retrying proxy/browser) hits the same callback
    # again. Verification must not run a second time.
    second_callback = await client.get(
        "/api/v1/payments/callback", params={"Authority": authority, "Status": "OK"}
    )
    assert second_callback.status_code in (200, 302)
    assert fake_zarinpal.verify_calls == 1

    order_after_second = await client.get(f"/api/v1/orders/{order_id}")
    assert order_after_second.json()["status"] == "paid"

    inventory = await _fetch_inventory(db_session, product.id)
    # Purchase committed exactly once: 5 - 1 = 4, not 5 - 2 = 3.
    assert inventory.stock_total == 4
    assert inventory.stock_reserved == 0


async def test_payment_verification_failure_releases_reserved_stock(
    client: AsyncClient, db_session: AsyncSession, fake_zarinpal: FakeZarinPalClient
) -> None:
    fake_zarinpal.should_verify_succeed = False
    product = await _seed_product(db_session, stock=5)
    await _register(client)
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    checkout = await client.post(
        "/api/v1/orders",
        json={},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    order_id = checkout.json()["id"]

    init_response = await client.post(
        "/api/v1/payments",
        json={"order_id": order_id},
        headers={**_csrf_headers(client), "Idempotency-Key": str(uuid.uuid4())},
    )
    authority = init_response.json()["payment_url"].rsplit("/", 1)[-1]

    await client.get("/api/v1/payments/callback", params={"Authority": authority, "Status": "OK"})

    order_after = await client.get(f"/api/v1/orders/{order_id}")
    assert order_after.json()["status"] == "payment_failed"

    inventory = await _fetch_inventory(db_session, product.id)
    assert inventory.stock_total == 5
    assert inventory.stock_reserved == 0
