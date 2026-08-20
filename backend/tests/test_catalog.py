import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError
from app.modules.catalog.inventory_service import InventoryService
from app.modules.catalog.models import Category, Product, ProductInventory
from app.modules.users.models import User, UserRole
from app.security.csrf import CSRF_HEADER_NAME


def _unique_slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    token = client.cookies.get("csrf_token")
    assert token is not None
    return {CSRF_HEADER_NAME: token}


async def _register(client: AsyncClient) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    payload = {
        "email": f"cat{suffix}@example.com",
        "username": f"cat{suffix}",
        "password": "Str0ngPass!word",
    }
    # A prior user's session may still be on this client, which means a
    # csrf_token cookie already exists and register() becomes subject to the
    # same CSRF check as any other mutating request.
    headers = {}
    existing_csrf = client.cookies.get("csrf_token")
    if existing_csrf:
        headers = {CSRF_HEADER_NAME: existing_csrf}
    response = await client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return payload


async def _make_admin(client: AsyncClient, db_session: AsyncSession, email: str) -> None:
    result = await db_session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one()
    user.role = UserRole.admin
    await db_session.commit()
    # Role is embedded in the JWT at issuance time, so a fresh login is
    # required to pick up the promotion.
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Str0ngPass!word"},
        headers=_csrf_headers(client),
    )


async def _create_category(client: AsyncClient, db_session: AsyncSession) -> str:
    payload = await _register(client)
    await _make_admin(client, db_session, payload["email"])
    slug = _unique_slug("cat")
    response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "دسته آزمایشی", "slug": slug},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_customer_cannot_create_category(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "دسته", "slug": _unique_slug("cat")},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 403


async def test_admin_can_manage_category_tree(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    category_id = await _create_category(client, db_session)

    child_slug = _unique_slug("child")
    child_response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "زیردسته", "slug": child_slug, "parent_id": category_id},
        headers=_csrf_headers(client),
    )
    assert child_response.status_code == 201
    child_id = child_response.json()["id"]

    tree_response = await client.get("/api/v1/categories")
    assert tree_response.status_code == 200
    matching = [c for c in tree_response.json() if c["id"] == category_id]
    assert len(matching) == 1
    assert matching[0]["children"][0]["id"] == child_id


async def test_category_cannot_be_moved_under_its_own_descendant(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    parent_id = await _create_category(client, db_session)
    child_response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "زیردسته", "slug": _unique_slug("child"), "parent_id": parent_id},
        headers=_csrf_headers(client),
    )
    child_id = child_response.json()["id"]

    response = await client.post(
        f"/api/v1/admin/categories/{parent_id}/move",
        json={"new_parent_id": child_id},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 409


async def test_category_cannot_be_its_own_parent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    category_id = await _create_category(client, db_session)
    response = await client.post(
        f"/api/v1/admin/categories/{category_id}/move",
        json={"new_parent_id": category_id},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 409


async def _create_product(
    client: AsyncClient, db_session: AsyncSession, *, initial_stock: int = 5, **overrides: object
) -> dict[str, object]:
    category_id = await _create_category(client, db_session)
    body = {
        "sku": _unique_slug("SKU"),
        "name": "گوشی موبایل تستی",
        "slug": _unique_slug("phone"),
        "price": "15000000",
        "category_id": category_id,
        "initial_stock": initial_stock,
        **overrides,
    }
    response = await client.post(
        "/api/v1/admin/products", json=body, headers=_csrf_headers(client)
    )
    assert response.status_code == 201, response.text
    result: dict[str, object] = response.json()
    return result


async def test_duplicate_sku_rejected(client: AsyncClient, db_session: AsyncSession) -> None:
    product = await _create_product(client, db_session)
    category_id = await _create_category(client, db_session)
    response = await client.post(
        "/api/v1/admin/products",
        json={
            "sku": product["sku"],
            "name": "محصول دیگر",
            "slug": _unique_slug("other"),
            "price": "1000",
            "category_id": category_id,
        },
        headers=_csrf_headers(client),
    )
    assert response.status_code == 409


async def test_discount_price_must_be_below_price(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    category_id = await _create_category(client, db_session)
    response = await client.post(
        "/api/v1/admin/products",
        json={
            "sku": _unique_slug("SKU"),
            "name": "محصول",
            "slug": _unique_slug("p"),
            "price": "1000",
            "discount_price": "1500",
            "category_id": category_id,
        },
        headers=_csrf_headers(client),
    )
    assert response.status_code == 422


async def test_product_detail_and_cache_invalidation_on_update(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _create_product(client, db_session)

    detail = await client.get(f"/api/v1/products/{product['slug']}")
    assert detail.status_code == 200
    assert detail.json()["available_stock"] == 5

    update = await client.patch(
        f"/api/v1/admin/products/{product['id']}",
        json={"name": "نام جدید"},
        headers=_csrf_headers(client),
    )
    assert update.status_code == 200

    detail_after = await client.get(f"/api/v1/products/{product['slug']}")
    assert detail_after.json()["name"] == "نام جدید"


async def test_persian_character_variant_search_normalization(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    product = await _create_product(client, db_session, name="کیبورد مکانیکی")

    # Search using the Arabic ك/ي variants of the Persian ک/ی in the name.
    response = await client.get("/api/v1/products", params={"search": "كيبورد"})
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert product["id"] in ids


async def test_inventory_reserve_prevents_overselling(db_session: AsyncSession) -> None:
    category = Category(name="دسته", slug=_unique_slug("cat"))
    db_session.add(category)
    await db_session.flush()

    product = Product(
        sku=_unique_slug("SKU"),
        name="محصول کم‌موجودی",
        slug=_unique_slug("low-stock"),
        price=1000,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.flush()
    db_session.add(ProductInventory(product_id=product.id, stock_total=2, stock_reserved=0))
    await db_session.flush()

    inventory = InventoryService(db_session)
    ref = uuid.uuid4()
    await inventory.reserve(product.id, 2, reference_type="order", reference_id=ref)

    with pytest.raises(ConflictError, match="موجودی کافی"):
        await inventory.reserve(product.id, 1, reference_type="order", reference_id=uuid.uuid4())
