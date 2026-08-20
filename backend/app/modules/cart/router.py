import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.idempotency import IdempotencyGuard, idempotency_guard
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser
from app.modules.cart.schemas import CartItemAdd, CartItemUpdate, CartSummary
from app.modules.cart.service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartSummary)
async def get_cart(
    user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> CartSummary:
    return await CartService(session).get_summary(user.id)


@router.post("/items", response_model=CartSummary, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    data: CartItemAdd,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    guard: IdempotencyGuard = Depends(idempotency_guard("cart.add_item")),
) -> CartSummary:
    await CartService(session).add_item(user.id, data.product_id, data.quantity)
    summary = await CartService(session).get_summary(user.id)
    await guard.finish(status.HTTP_201_CREATED, summary.model_dump(mode="json"))
    await session.commit()
    return summary


@router.patch("/items/{product_id}", response_model=CartSummary)
async def update_cart_item(
    product_id: uuid.UUID,
    data: CartItemUpdate,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> CartSummary:
    await CartService(session).update_item(user.id, product_id, data.quantity)
    summary = await CartService(session).get_summary(user.id)
    await session.commit()
    return summary


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    product_id: uuid.UUID,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await CartService(session).remove_item(user.id, product_id)
    await session.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(user: CurrentUser, session: AsyncSession = Depends(get_db_session)) -> None:
    await CartService(session).clear(user.id)
    await session.commit()
