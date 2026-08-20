import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache import cache_delete
from app.common.errors import ConflictError, NotFoundError
from app.modules.catalog.inventory_service import InventoryService
from app.modules.catalog.models import Category, Product, ProductInventory
from app.modules.catalog.repository import CategoryRepository, ProductRepository
from app.modules.catalog.schemas import CategoryCreate, CategoryUpdate, ProductCreate, ProductUpdate

CATEGORY_TREE_CACHE_KEY = "categories:tree:v1"
FEATURED_PRODUCTS_CACHE_KEY = "products:featured:v1"
POPULAR_PRODUCTS_CACHE_KEY = "products:popular:v1"
HOME_CACHE_KEY = "home:v1"


def product_cache_key(slug: str) -> str:
    return f"product:{slug}:v1"


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoryRepository(session)

    async def create(self, data: CategoryCreate) -> Category:
        if await self.repo.get_by_slug(data.slug):
            raise ConflictError("این نامک دسته‌بندی قبلاً استفاده شده است.")
        if data.parent_id is not None and await self.repo.get_by_id(data.parent_id) is None:
            raise NotFoundError("دسته‌بندی والد پیدا نشد.")

        category = Category(
            name=data.name,
            slug=data.slug,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
        )
        self.repo.add(category)
        await self.session.flush()
        await self._invalidate_tree_cache()
        return category

    async def update(self, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
        category = await self.repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("دسته‌بندی پیدا نشد.")

        if data.name is not None:
            category.name = data.name
        if data.is_active is not None:
            category.is_active = data.is_active
        if data.sort_order is not None:
            category.sort_order = data.sort_order

        await self._invalidate_tree_cache()
        return category

    async def move(self, category_id: uuid.UUID, new_parent_id: uuid.UUID | None) -> Category:
        category = await self.repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("دسته‌بندی پیدا نشد.")

        if new_parent_id is not None:
            if new_parent_id == category_id:
                raise ConflictError("دسته‌بندی نمی‌تواند والد خودش باشد.")
            if await self.repo.get_by_id(new_parent_id) is None:
                raise NotFoundError("دسته‌بندی والد پیدا نشد.")
            descendants = await self.repo.get_descendant_ids(category_id)
            if new_parent_id in descendants:
                raise ConflictError(
                    "دسته‌بندی نمی‌تواند به زیرمجموعه خودش منتقل شود."
                )

        category.parent_id = new_parent_id
        await self._invalidate_tree_cache()
        return category

    async def delete(self, category_id: uuid.UUID) -> None:
        category = await self.repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("دسته‌بندی پیدا نشد.")
        if await self.repo.has_children(category_id):
            raise ConflictError("ابتدا زیردسته‌های این دسته‌بندی را حذف یا منتقل کنید.")
        if await self.repo.has_products(category_id):
            raise ConflictError("این دسته‌بندی دارای محصول است و قابل حذف نیست.")

        await self.session.delete(category)
        await self._invalidate_tree_cache()

    async def get_tree(self) -> list[Category]:
        all_categories = await self.repo.list_all()
        roots: list[Category] = []
        children_map: dict[uuid.UUID, list[Category]] = {}
        for category in all_categories:
            if category.parent_id is None:
                roots.append(category)
            else:
                children_map.setdefault(category.parent_id, []).append(category)

        def attach(node: Category) -> None:
            node.children = children_map.get(node.id, [])
            for child in node.children:
                attach(child)

        for root in roots:
            attach(root)
        return roots

    async def _invalidate_tree_cache(self) -> None:
        await cache_delete(CATEGORY_TREE_CACHE_KEY, HOME_CACHE_KEY)


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductRepository(session)
        self.category_repo = CategoryRepository(session)
        self.inventory = InventoryService(session)

    async def create(self, data: ProductCreate) -> Product:
        if await self.repo.get_by_slug_or_sku(data.slug, data.sku):
            raise ConflictError("محصولی با این نامک یا SKU از قبل وجود دارد.")
        if await self.category_repo.get_by_id(data.category_id) is None:
            raise NotFoundError("دسته‌بندی انتخاب‌شده پیدا نشد.")

        product = Product(
            sku=data.sku,
            name=data.name,
            slug=data.slug,
            short_description=data.short_description,
            description=data.description,
            price=data.price,
            discount_price=data.discount_price,
            brand=data.brand,
            category_id=data.category_id,
            images=data.images,
            specifications=data.specifications,
            is_active=data.is_active,
            is_featured=data.is_featured,
            is_popular=data.is_popular,
        )
        self.repo.add(product)
        await self.session.flush()

        inventory = ProductInventory(
            product_id=product.id, stock_total=data.initial_stock, stock_reserved=0
        )
        self.session.add(inventory)
        await self.session.flush()
        # `inventory` relationship is lazy="noload"; set it in-memory so the
        # immediate response doesn't trigger an unsupported implicit lazy load.
        product.inventory = inventory
        await self._invalidate_product_cache(product.slug)
        return product

    async def update(self, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = await self.repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError("محصول پیدا نشد.")

        old_slug = product.slug
        update_fields = data.model_dump(exclude_unset=True)

        new_category_id = update_fields.get("category_id")
        if new_category_id is not None and await self.category_repo.get_by_id(
            new_category_id
        ) is None:
            raise NotFoundError("دسته‌بندی انتخاب‌شده پیدا نشد.")

        new_price = update_fields.get("price", product.price)
        new_discount = update_fields.get("discount_price", product.discount_price)
        if new_discount is not None and new_discount >= new_price:
            raise ConflictError("قیمت با تخفیف باید کمتر از قیمت اصلی باشد.")

        for field, value in update_fields.items():
            setattr(product, field, value)

        await self._invalidate_product_cache(old_slug)
        if product.slug != old_slug:
            await self._invalidate_product_cache(product.slug)
        return product

    async def archive(self, product_id: uuid.UUID) -> None:
        product = await self.repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError("محصول پیدا نشد.")
        product.is_active = False
        await self._invalidate_product_cache(product.slug)

    async def _invalidate_product_cache(self, slug: str) -> None:
        await cache_delete(
            product_cache_key(slug),
            FEATURED_PRODUCTS_CACHE_KEY,
            POPULAR_PRODUCTS_CACHE_KEY,
            HOME_CACHE_KEY,
        )
