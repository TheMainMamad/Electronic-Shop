import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.idempotency import IdempotencyGuard, idempotency_guard
from app.common.pagination import Page, PageParams
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser, require_permission
from app.modules.wallet.repository import WalletRepository
from app.modules.wallet.schemas import (
    AdminWalletAdjustRequest,
    WalletDepositRequest,
    WalletPublic,
    WalletTransactionPublic,
)
from app.modules.wallet.service import WalletService

router = APIRouter(tags=["wallet"])


@router.get("/wallet", response_model=WalletPublic)
async def get_my_wallet(
    user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> WalletPublic:
    wallet = await WalletService(session).get_or_create(user.id)
    await session.commit()
    return WalletPublic(id=wallet.id, balance=wallet.balance)


@router.get("/wallet/transactions", response_model=Page[WalletTransactionPublic])
async def list_my_wallet_transactions(
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    page_params: PageParams = Depends(),
) -> Page[WalletTransactionPublic]:
    wallet = await WalletService(session).get_or_create(user.id)
    items, total = await WalletRepository(session).list_for_wallet(
        wallet.id, offset=page_params.offset, limit=page_params.page_size
    )
    await session.commit()
    return Page.create(
        [WalletTransactionPublic.model_validate(item) for item in items], total, page_params
    )


@router.post(
    "/wallet/deposit",
    response_model=WalletTransactionPublic,
    status_code=status.HTTP_201_CREATED,
)
async def deposit_to_wallet(
    data: WalletDepositRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    guard: IdempotencyGuard = Depends(idempotency_guard("wallet.deposit")),
) -> WalletTransactionPublic:
    transaction = await WalletService(session).deposit(user.id, data.amount)
    result = WalletTransactionPublic.model_validate(transaction)
    await guard.finish(status.HTTP_201_CREATED, result.model_dump(mode="json"))
    await session.commit()
    return result


@router.get(
    "/admin/wallets/{user_id}",
    response_model=WalletPublic,
    dependencies=[Depends(require_permission("wallet.manage"))],
)
async def admin_get_wallet(
    user_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> WalletPublic:
    wallet = await WalletService(session).get_or_create(user_id)
    await session.commit()
    return WalletPublic(id=wallet.id, balance=wallet.balance)


@router.post(
    "/admin/wallets/{user_id}/credit",
    response_model=WalletTransactionPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("wallet.manage"))],
)
async def admin_credit_wallet(
    user_id: uuid.UUID,
    data: AdminWalletAdjustRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    guard: IdempotencyGuard = Depends(idempotency_guard("wallet.admin_credit")),
) -> WalletTransactionPublic:
    transaction = await WalletService(session).admin_credit(
        user_id, data.amount, data.reason, actor_id=user.id
    )
    result = WalletTransactionPublic.model_validate(transaction)
    await guard.finish(status.HTTP_201_CREATED, result.model_dump(mode="json"))
    await session.commit()
    return result


@router.post(
    "/admin/wallets/{user_id}/debit",
    response_model=WalletTransactionPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("wallet.manage"))],
)
async def admin_debit_wallet(
    user_id: uuid.UUID,
    data: AdminWalletAdjustRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    guard: IdempotencyGuard = Depends(idempotency_guard("wallet.admin_debit")),
) -> WalletTransactionPublic:
    transaction = await WalletService(session).admin_debit(
        user_id, data.amount, data.reason, actor_id=user.id
    )
    result = WalletTransactionPublic.model_validate(transaction)
    await guard.finish(status.HTTP_201_CREATED, result.model_dump(mode="json"))
    await session.commit()
    return result
