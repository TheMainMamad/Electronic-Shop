import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.cart.models import Cart, CartItem


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, user_id: uuid.UUID) -> Cart:
        result = await self.session.execute(
            select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()
        if cart is not None:
            return cart

        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        cart.items = []
        return cart

    async def get_item(self, cart_id: uuid.UUID, product_id: uuid.UUID) -> CartItem | None:
        result = await self.session.execute(
            select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        return result.scalar_one_or_none()

    def add_item(self, item: CartItem) -> None:
        self.session.add(item)

    async def delete_item(self, item: CartItem) -> None:
        await self.session.delete(item)

    async def clear(self, cart_id: uuid.UUID) -> None:
        result = await self.session.execute(select(CartItem).where(CartItem.cart_id == cart_id))
        for item in result.scalars():
            await self.session.delete(item)
