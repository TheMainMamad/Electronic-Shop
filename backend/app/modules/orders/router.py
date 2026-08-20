import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.idempotency import IdempotencyGuard, idempotency_guard
from app.common.pagination import Page, PageParams
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser, require_permission
from app.modules.orders.models import Order
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import (
    CheckoutRequest,
    OrderItemPublic,
    OrderPublic,
    OrderStatusUpdateRequest,
)
from app.modules.orders.service import OrderService

router = APIRouter(tags=["orders"])


def _serialize_order(order: Order) -> OrderPublic:
    return OrderPublic(
        id=order.id,
        status=order.status,
        subtotal=order.subtotal,
        total=order.total,
        shipping_address=order.shipping_address,
        items=[
            OrderItemPublic(
                product_id=item.product_id,
                product_name=item.product_name_snapshot,
                sku=item.sku_snapshot,
                unit_price=item.unit_price_snapshot,
                quantity=item.quantity,
                subtotal=item.subtotal,
            )
            for item in order.items
        ],
        created_at=order.created_at,
    )


@router.post("/orders", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    guard: IdempotencyGuard = Depends(idempotency_guard("order.checkout")),
) -> OrderPublic:
    order = await OrderService(session).checkout(user.id, data.shipping_address)
    result = _serialize_order(order)
    await guard.finish(status.HTTP_201_CREATED, result.model_dump(mode="json"))
    await session.commit()
    return result


@router.get("/orders", response_model=Page[OrderPublic])
async def list_my_orders(
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
) -> Page[OrderPublic]:
    items, total = await OrderRepository(session).list_for_user(
        user.id, offset=page_params.offset, limit=page_params.page_size
    )
    return Page.create([_serialize_order(o) for o in items], total, page_params)


@router.get("/orders/{order_id}", response_model=OrderPublic)
async def get_order(
    order_id: uuid.UUID, user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> OrderPublic:
    order = await OrderService(session).get_for_user(order_id, user)
    return _serialize_order(order)


@router.post("/orders/{order_id}/cancel", response_model=OrderPublic)
async def cancel_order(
    order_id: uuid.UUID, user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> OrderPublic:
    order = await OrderService(session).cancel(order_id, user)
    result = _serialize_order(order)
    await session.commit()
    return result


@router.get(
    "/admin/orders",
    response_model=Page[OrderPublic],
    dependencies=[Depends(require_permission("order.read"))],
)
async def list_all_orders(
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
) -> Page[OrderPublic]:
    items, total = await OrderRepository(session).list_all(
        offset=page_params.offset, limit=page_params.page_size
    )
    return Page.create([_serialize_order(o) for o in items], total, page_params)


@router.patch(
    "/admin/orders/{order_id}/status",
    response_model=OrderPublic,
    dependencies=[Depends(require_permission("order.manage"))],
)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> OrderPublic:
    order = await OrderService(session).admin_update_status(
        order_id, data.new_status, data.note, user.id
    )
    result = _serialize_order(order)
    await session.commit()
    return result
