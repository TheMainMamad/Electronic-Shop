from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.idempotency import IdempotencyGuard, idempotency_guard
from app.db.session import get_db_session
from app.modules.auth.dependencies import CurrentUser
from app.modules.payments.models import PaymentStatus
from app.modules.payments.schemas import PaymentInitRequest, PaymentInitResponse
from app.modules.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentInitResponse, status_code=status.HTTP_201_CREATED)
async def init_payment(
    data: PaymentInitRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
    guard: IdempotencyGuard = Depends(idempotency_guard("payment.init")),
) -> PaymentInitResponse:
    payment, payment_url = await PaymentService(session).init_payment(user, data.order_id)
    result = PaymentInitResponse(payment_id=payment.id, payment_url=payment_url)
    await guard.finish(status.HTTP_201_CREATED, result.model_dump(mode="json"))
    await session.commit()
    return result


@router.get("/callback")
async def payment_callback(
    Authority: str,  # noqa: N803 - ZarinPal's query param casing
    Status: str,  # noqa: N803
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    payment = await PaymentService(session).handle_callback(Authority, Status)
    await session.commit()

    outcome = "paid" if payment.status == PaymentStatus.verified else "failed"
    return RedirectResponse(
        url=f"/checkout/result?order_id={payment.order_id}&status={outcome}",
        status_code=status.HTTP_302_FOUND,
    )
