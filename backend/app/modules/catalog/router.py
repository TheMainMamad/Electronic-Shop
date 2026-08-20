import uuid
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache import cache_get_json, cache_set_json
from app.common.errors import NotFoundError
from app.common.pagination import Page, PageParams
from app.db.session import get_db_session
from app.integrations.storage import get_image_storage
from app.modules.auth.dependencies import CurrentUser, require_permission
from app.modules.catalog.inventory_service import InventoryService
from app.modules.catalog.models import Product
from app.modules.catalog.repository import ProductRepository
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryMove,
    CategoryPublic,
    CategoryUpdate,
    InventoryAdjustRequest,
    ProductCreate,
    ProductPublic,
    ProductUpdate,
)
from app.modules.catalog.service import (
    CATEGORY_TREE_CACHE_KEY,
    FEATURED_PRODUCTS_CACHE_KEY,
    POPULAR_PRODUCTS_CACHE_KEY,
    CategoryService,
    ProductService,
    product_cache_key,
)

router = APIRouter(tags=["catalog"])

_SORTABLE_COLUMNS = {"created_at", "price", "name"}


def _available_stock(product: Product) -> int:
    if product.inventory is None:
        return 0
    return max(0, product.inventory.stock_total - product.inventory.stock_reserved)


def _serialize_product(product: Product) -> ProductPublic:
    return ProductPublic(
        id=product.id,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        short_description=product.short_description,
        description=product.description,
        price=product.price,
        discount_price=product.discount_price,
        brand=product.brand,
        category_id=product.category_id,
        images=product.images,
        specifications=product.specifications,
        is_active=product.is_active,
        is_featured=product.is_featured,
        is_popular=product.is_popular,
        available_stock=_available_stock(product),
    )


# --- Categories -------------------------------------------------------------


@router.get("/categories", response_model=list[CategoryPublic])
async def get_category_tree(
    session: AsyncSession = Depends(get_db_session),
) -> list[CategoryPublic]:
    cached = await cache_get_json(CATEGORY_TREE_CACHE_KEY)
    if cached is not None:
        return [CategoryPublic.model_validate(item) for item in cached]

    tree = await CategoryService(session).get_tree()
    result = [CategoryPublic.model_validate(category) for category in tree]
    payload = [item.model_dump(mode="json") for item in result]
    await cache_set_json(CATEGORY_TREE_CACHE_KEY, payload)
    return result


@router.post(
    "/admin/categories",
    response_model=CategoryPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def create_category(
    data: CategoryCreate, session: AsyncSession = Depends(get_db_session)
) -> CategoryPublic:
    category = await CategoryService(session).create(data)
    await session.commit()
    return CategoryPublic.model_validate(category)


@router.patch(
    "/admin/categories/{category_id}",
    response_model=CategoryPublic,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def update_category(
    category_id: uuid.UUID, data: CategoryUpdate, session: AsyncSession = Depends(get_db_session)
) -> CategoryPublic:
    category = await CategoryService(session).update(category_id, data)
    await session.commit()
    return CategoryPublic.model_validate(category)


@router.post(
    "/admin/categories/{category_id}/move",
    response_model=CategoryPublic,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def move_category(
    category_id: uuid.UUID, data: CategoryMove, session: AsyncSession = Depends(get_db_session)
) -> CategoryPublic:
    category = await CategoryService(session).move(category_id, data.new_parent_id)
    await session.commit()
    return CategoryPublic.model_validate(category)


@router.delete(
    "/admin/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def delete_category(
    category_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> None:
    await CategoryService(session).delete(category_id)
    await session.commit()


# --- Products -----------------------------------------------------------------


@router.get("/products", response_model=Page[ProductPublic])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page_params: Annotated[PageParams, Depends()],
    category_id: uuid.UUID | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock_only: bool = False,
    search: str | None = None,
    sort_by: Literal["created_at", "price", "name"] = "created_at",
    sort_desc: bool = True,
) -> Page[ProductPublic]:
    repo = ProductRepository(session)
    items, total = await repo.search(
        category_id=category_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        search=search,
        sort_by=sort_by if sort_by in _SORTABLE_COLUMNS else "created_at",
        sort_desc=sort_desc,
        offset=page_params.offset,
        limit=page_params.page_size,
    )
    return Page.create([_serialize_product(p) for p in items], total, page_params)


@router.get("/products/featured", response_model=list[ProductPublic])
async def featured_products(
    session: AsyncSession = Depends(get_db_session),
) -> list[ProductPublic]:
    cached = await cache_get_json(FEATURED_PRODUCTS_CACHE_KEY)
    if cached is not None:
        return [ProductPublic.model_validate(item) for item in cached]

    products = await ProductRepository(session).list_flagged(featured=True)
    result = [_serialize_product(p) for p in products]
    payload = [item.model_dump(mode="json") for item in result]
    await cache_set_json(FEATURED_PRODUCTS_CACHE_KEY, payload)
    return result


@router.get("/products/popular", response_model=list[ProductPublic])
async def popular_products(
    session: AsyncSession = Depends(get_db_session),
) -> list[ProductPublic]:
    cached = await cache_get_json(POPULAR_PRODUCTS_CACHE_KEY)
    if cached is not None:
        return [ProductPublic.model_validate(item) for item in cached]

    products = await ProductRepository(session).list_flagged(popular=True)
    result = [_serialize_product(p) for p in products]
    payload = [item.model_dump(mode="json") for item in result]
    await cache_set_json(POPULAR_PRODUCTS_CACHE_KEY, payload)
    return result


@router.get("/products/{slug}", response_model=ProductPublic)
async def get_product(slug: str, session: AsyncSession = Depends(get_db_session)) -> ProductPublic:
    cached = await cache_get_json(product_cache_key(slug))
    if cached is not None:
        return ProductPublic.model_validate(cached)

    product = await ProductRepository(session).get_by_slug(slug)
    if product is None:
        raise NotFoundError("محصول موردنظر پیدا نشد.")

    result = _serialize_product(product)
    await cache_set_json(product_cache_key(slug), result.model_dump(mode="json"))
    return result


@router.post(
    "/admin/products",
    response_model=ProductPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("product.create"))],
)
async def create_product(
    data: ProductCreate, session: AsyncSession = Depends(get_db_session)
) -> ProductPublic:
    product = await ProductService(session).create(data)
    await session.commit()
    return _serialize_product(product)


@router.patch(
    "/admin/products/{product_id}",
    response_model=ProductPublic,
    dependencies=[Depends(require_permission("product.update"))],
)
async def update_product(
    product_id: uuid.UUID, data: ProductUpdate, session: AsyncSession = Depends(get_db_session)
) -> ProductPublic:
    product = await ProductService(session).update(product_id, data)
    await session.commit()
    return _serialize_product(product)


@router.delete(
    "/admin/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("product.delete"))],
)
async def archive_product(
    product_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> None:
    await ProductService(session).archive(product_id)
    await session.commit()


@router.post(
    "/admin/products/{product_id}/inventory/restock",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("product.update"))],
)
async def restock_product(
    product_id: uuid.UUID,
    data: InventoryAdjustRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await InventoryService(session).restock(product_id, data.delta, actor_id=user.id)
    await session.commit()


@router.post(
    "/admin/products/{product_id}/inventory/adjust",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("product.update"))],
)
async def adjust_product_inventory(
    product_id: uuid.UUID,
    data: InventoryAdjustRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await InventoryService(session).adjust(product_id, data.delta, actor_id=user.id)
    await session.commit()


@router.post(
    "/admin/uploads/product-image",
    dependencies=[Depends(require_permission("product.update"))],
)
async def upload_product_image(file: UploadFile) -> dict[str, str]:
    content = await file.read()
    storage = get_image_storage()
    url = storage.save(content=content, content_type=file.content_type or "")
    return {"url": url}
