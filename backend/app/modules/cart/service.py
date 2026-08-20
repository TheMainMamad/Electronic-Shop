import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError
from app.modules.cart.models import Cart, CartItem
from app.modules.cart.repository import CartRepository
from app.modules.cart.schemas import CartItemPublic, CartSummary
from app.modules.catalog.models import Product
from app.modules.catalog.repository import ProductRepository


def _effective_unit_price(product: Product) -> Decimal:
    if product.discount_price is not None:
        return product.discount_price
    return product.price


def _available_stock(product: Product) -> int:
    if product.inventory is None:
        return 0
    return max(0, product.inventory.stock_total - product.inventory.stock_reserved)


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CartRepository(session)
        self.products = ProductRepository(session)

    async def add_item(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> Cart:
        product = await self.products.get_by_id(product_id)
        if product is None or not product.is_active:
            raise NotFoundError("محصول موردنظر پیدا نشد.")

        cart = await self.repo.get_or_create(user_id)
        existing = await self.repo.get_item(cart.id, product_id)
        new_quantity = quantity + (existing.quantity if existing else 0)

        if new_quantity > _available_stock(product):
            raise ConflictError("موجودی کافی برای این تعداد وجود ندارد.")

        if existing is not None:
            existing.quantity = new_quantity
        else:
            self.repo.add_item(
                CartItem(cart_id=cart.id, product_id=product_id, quantity=new_quantity)
            )

        await self.session.flush()
        return await self.repo.get_or_create(user_id)

    async def update_item(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> Cart:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise NotFoundError("محصول موردنظر پیدا نشد.")
        if quantity > _available_stock(product):
            raise ConflictError("موجودی کافی برای این تعداد وجود ندارد.")

        cart = await self.repo.get_or_create(user_id)
        item = await self.repo.get_item(cart.id, product_id)
        if item is None:
            raise NotFoundError("این محصول در سبد خرید شما نیست.")

        item.quantity = quantity
        await self.session.flush()
        return await self.repo.get_or_create(user_id)

    async def remove_item(self, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
        cart = await self.repo.get_or_create(user_id)
        item = await self.repo.get_item(cart.id, product_id)
        if item is not None:
            await self.repo.delete_item(item)

    async def clear(self, user_id: uuid.UUID) -> None:
        cart = await self.repo.get_or_create(user_id)
        await self.repo.clear(cart.id)

    async def get_summary(self, user_id: uuid.UUID) -> CartSummary:
        cart = await self.repo.get_or_create(user_id)
        items: list[CartItemPublic] = []
        subtotal = Decimal(0)

        for cart_item in cart.items:
            product = await self.products.get_by_id(cart_item.product_id)
            if product is None or not product.is_active:
                continue
            unit_price = _effective_unit_price(product)
            item_subtotal = unit_price * cart_item.quantity
            subtotal += item_subtotal
            items.append(
                CartItemPublic(
                    product_id=product.id,
                    name=product.name,
                    slug=product.slug,
                    unit_price=unit_price,
                    quantity=cart_item.quantity,
                    subtotal=item_subtotal,
                    available_stock=_available_stock(product),
                )
            )

        return CartSummary(items=items, subtotal=subtotal, total=subtotal)
