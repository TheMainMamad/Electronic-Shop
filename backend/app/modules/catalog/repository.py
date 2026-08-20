import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.models import (
    Category,
    InventoryHistory,
    Product,
    ProductInventory,
)

_PERSIAN_NORMALIZE_FROM = "يك"
_PERSIAN_NORMALIZE_TO = "یک"


def _normalize_persian(expr: Any) -> ColumnElement[str]:
    return func.translate(expr, _PERSIAN_NORMALIZE_FROM, _PERSIAN_NORMALIZE_TO)


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        return await self.session.get(Category, category_id)

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars())

    async def get_descendant_ids(self, category_id: uuid.UUID) -> set[uuid.UUID]:
        """All descendant ids (not including category_id itself), used to
        block a category from being moved under its own subtree."""
        all_categories = await self.list_all()
        children_by_parent: dict[uuid.UUID | None, list[Category]] = {}
        for category in all_categories:
            children_by_parent.setdefault(category.parent_id, []).append(category)

        descendants: set[uuid.UUID] = set()
        frontier = [category_id]
        while frontier:
            current = frontier.pop()
            for child in children_by_parent.get(current, []):
                if child.id not in descendants:
                    descendants.add(child.id)
                    frontier.append(child.id)
        return descendants

    def add(self, category: Category) -> None:
        self.session.add(category)

    async def has_products(self, category_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(func.count()).select_from(Product).where(Product.category_id == category_id)
        )
        return (result.scalar_one() or 0) > 0

    async def has_children(self, category_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(func.count()).select_from(Category).where(Category.parent_id == category_id)
        )
        return (result.scalar_one() or 0) > 0


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .options(selectinload(Product.inventory))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        result = await self.session.execute(
            select(Product).options(selectinload(Product.inventory)).where(Product.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.session.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    async def get_by_slug_or_sku(self, slug: str, sku: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(or_(Product.slug == slug, Product.sku == sku))
        )
        return result.scalar_one_or_none()

    def add(self, product: Product) -> None:
        self.session.add(product)

    def _base_query(
        self,
        *,
        category_id: uuid.UUID | None,
        brand: str | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        in_stock_only: bool,
        search: str | None,
        is_featured: bool | None,
        is_active: bool | None,
    ) -> Select[tuple[Product]]:
        query = select(Product).options(selectinload(Product.inventory))
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if brand:
            query = query.where(Product.brand == brand)
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        if is_featured is not None:
            query = query.where(Product.is_featured == is_featured)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        if in_stock_only:
            query = query.join(ProductInventory).where(
                ProductInventory.stock_total - ProductInventory.stock_reserved > 0
            )
        if search:
            normalized_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    _normalize_persian(Product.name).ilike(_normalize_persian(normalized_term)),
                    _normalize_persian(Product.description).ilike(
                        _normalize_persian(normalized_term)
                    ),
                    Product.sku.ilike(normalized_term),
                    Product.brand.ilike(normalized_term),
                )
            )
        return query

    async def search(
        self,
        *,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock_only: bool = False,
        search: str | None = None,
        is_featured: bool | None = None,
        is_active: bool | None = True,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        query = self._base_query(
            category_id=category_id,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            search=search,
            is_featured=is_featured,
            is_active=is_active,
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        sort_column = getattr(Product, sort_by)
        query = query.order_by(sort_column.desc() if sort_desc else sort_column.asc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().unique()), total

    async def list_flagged(
        self, *, featured: bool = False, popular: bool = False, limit: int = 8
    ) -> list[Product]:
        query = (
            select(Product)
            .options(selectinload(Product.inventory))
            .where(Product.is_active.is_(True))
        )
        if featured:
            query = query.where(Product.is_featured.is_(True))
        if popular:
            query = query.where(Product.is_popular.is_(True))
        query = query.order_by(Product.updated_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().unique())


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lock_for_update(self, product_id: uuid.UUID) -> ProductInventory | None:
        result = await self.session.execute(
            select(ProductInventory)
            .where(ProductInventory.product_id == product_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    def add_history(self, entry: InventoryHistory) -> None:
        self.session.add(entry)
