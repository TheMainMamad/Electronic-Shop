import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.cart.repository import CartRepository
from app.modules.catalog.inventory_service import InventoryService
from app.modules.catalog.repository import ProductRepository
from app.modules.orders.models import (
    ALLOWED_TRANSITIONS,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
)
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import ShippingAddress
from app.modules.users.models import User, UserRole


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = OrderRepository(session)
        self.cart_repo = CartRepository(session)
        self.products = ProductRepository(session)
        self.inventory = InventoryService(session)

    async def checkout(
        self, user_id: uuid.UUID, shipping_address: ShippingAddress | None
    ) -> Order:
        cart = await self.cart_repo.get_or_create(user_id)
        if not cart.items:
            raise ConflictError("سبد خرید شما خالی است.")

        order = Order(
            user_id=user_id,
            status=OrderStatus.pending,
            subtotal=Decimal(0),
            total=Decimal(0),
            shipping_address=shipping_address.model_dump() if shipping_address else None,
        )
        self.repo.add(order)
        await self.session.flush()

        subtotal = Decimal(0)
        for cart_item in cart.items:
            product = await self.products.get_by_id(cart_item.product_id)
            if product is None or not product.is_active:
                raise ConflictError(
                    f"محصول «{cart_item.product_id}» دیگر در دسترس نیست. "
                    "سبد خرید را به‌روزرسانی کنید."
                )

            unit_price = (
                product.discount_price if product.discount_price is not None else product.price
            )
            item_subtotal = unit_price * cart_item.quantity
            subtotal += item_subtotal

            self.repo.add_item(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    sku_snapshot=product.sku,
                    unit_price_snapshot=unit_price,
                    quantity=cart_item.quantity,
                    subtotal=item_subtotal,
                )
            )

            # Reserve stock now, at order-creation time — not at add-to-cart
            # time — see docs/architecture.md §11.
            await self.inventory.reserve(
                product.id,
                cart_item.quantity,
                reference_type="order",
                reference_id=order.id,
                actor_id=user_id,
            )

        order.subtotal = subtotal
        order.total = subtotal
        self._transition(order, OrderStatus.awaiting_payment, actor_id=user_id)

        await self.cart_repo.clear(cart.id)
        await self.session.flush()

        result = await self.repo.get_by_id(order.id)
        assert result is not None
        return result

    def _transition(
        self,
        order: Order,
        new_status: OrderStatus,
        *,
        actor_id: uuid.UUID | None,
        note: str | None = None,
    ) -> None:
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise ConflictError(
                f"تغییر وضعیت سفارش از «{order.status.value}» به «{new_status.value}» مجاز نیست."
            )
        history = OrderStatusHistory(
            order_id=order.id,
            from_status=order.status,
            to_status=new_status,
            actor_id=actor_id,
            note=note,
            created_at=datetime.now(UTC),
        )
        self.repo.add_history(history)
        order.status = new_status
        if new_status == OrderStatus.cancelled:
            order.cancelled_at = datetime.now(UTC)

    async def mark_paid(self, order_id: uuid.UUID) -> Order:
        order = await self.repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("سفارش پیدا نشد.")

        for item in order.items:
            if item.product_id is not None:
                await self.inventory.commit_purchase(
                    item.product_id,
                    item.quantity,
                    reference_type="order",
                    reference_id=order.id,
                )
        self._transition(order, OrderStatus.paid, actor_id=None, note="پرداخت با موفقیت تأیید شد.")
        return order

    async def mark_payment_failed(self, order_id: uuid.UUID) -> Order:
        order = await self.repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("سفارش پیدا نشد.")

        for item in order.items:
            if item.product_id is not None:
                await self.inventory.release(
                    item.product_id,
                    item.quantity,
                    reference_type="order",
                    reference_id=order.id,
                )
        self._transition(
            order, OrderStatus.payment_failed, actor_id=None, note="پرداخت ناموفق بود."
        )
        return order

    async def cancel(self, order_id: uuid.UUID, user: User) -> Order:
        order = await self.repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("سفارش پیدا نشد.")
        self._authorize_access(order, user)

        if order.status in (OrderStatus.pending, OrderStatus.awaiting_payment, OrderStatus.paid):
            for item in order.items:
                if item.product_id is not None:
                    await self.inventory.release(
                        item.product_id,
                        item.quantity,
                        reference_type="order",
                        reference_id=order.id,
                    )
        self._transition(order, OrderStatus.cancelled, actor_id=user.id, note="سفارش لغو شد.")
        return order

    async def admin_update_status(
        self, order_id: uuid.UUID, new_status: OrderStatus, note: str | None, actor_id: uuid.UUID
    ) -> Order:
        order = await self.repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("سفارش پیدا نشد.")
        self._transition(order, new_status, actor_id=actor_id, note=note)
        return order

    async def get_for_user(self, order_id: uuid.UUID, user: User) -> Order:
        order = await self.repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("سفارش پیدا نشد.")
        self._authorize_access(order, user)
        return order

    def _authorize_access(self, order: Order, user: User) -> None:
        if order.user_id != user.id and user.role not in (UserRole.admin, UserRole.super_admin):
            raise PermissionDeniedError("شما اجازه دسترسی به این سفارش را ندارید.")
