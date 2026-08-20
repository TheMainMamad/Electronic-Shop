import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.core.config import get_settings
from app.integrations.zarinpal import ZarinPalClient, ZarinPalNotConfigured, get_zarinpal_client
from app.modules.orders.models import OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderService
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.users.models import User

settings = get_settings()

_TOMAN_TO_RIAL = 10


class PaymentService:
    def __init__(self, session: AsyncSession, zarinpal: ZarinPalClient | None = None) -> None:
        self.session = session
        self.repo = PaymentRepository(session)
        self.orders = OrderRepository(session)
        self.zarinpal = zarinpal or get_zarinpal_client()

    async def init_payment(self, user: User, order_id: uuid.UUID) -> tuple[Payment, str]:
        order = await self.orders.get_by_id(order_id)
        if order is None:
            raise NotFoundError("سفارش پیدا نشد.")
        if order.user_id != user.id:
            raise PermissionDeniedError("شما اجازه دسترسی به این سفارش را ندارید.")
        if order.status not in (OrderStatus.awaiting_payment, OrderStatus.payment_failed):
            raise ConflictError("این سفارش در وضعیتی نیست که بتوان برای آن پرداخت انجام داد.")

        payment = Payment(
            order_id=order.id,
            user_id=user.id,
            gateway="zarinpal",
            amount=order.total,
            status=PaymentStatus.initiated,
        )
        self.repo.add(payment)
        await self.session.flush()

        try:
            result = await self.zarinpal.request_payment(
                amount_rial=int(order.total) * _TOMAN_TO_RIAL,
                description=f"پرداخت سفارش {order.id}",
                callback_url=settings.zarinpal_callback_url,
            )
        except ZarinPalNotConfigured as exc:
            raise ConflictError(str(exc)) from exc

        payment.authority = result.authority
        return payment, result.payment_url

    async def handle_callback(self, authority: str, gateway_status: str) -> Payment:
        payment = await self.repo.get_by_authority(authority)
        if payment is None:
            raise NotFoundError("تراکنش پرداخت پیدا نشد.")

        claimed = await self.repo.try_claim(
            payment.id, from_status=PaymentStatus.initiated, to_status=PaymentStatus.pending
        )
        if not claimed:
            # Already processed (or concurrently being processed) by a prior
            # callback/verification call — replay the stored outcome instead
            # of re-verifying with the gateway or re-touching the order.
            # The in-memory object may still hold the pre-race "initiated"
            # status, so pull the row's real, now-final state.
            await self.session.refresh(payment)
            return payment

        order_service = OrderService(self.session)

        if gateway_status != "OK":
            payment.status = PaymentStatus.failed
            await order_service.mark_payment_failed(payment.order_id)
            return payment

        verify_result = await self.zarinpal.verify_payment(
            amount_rial=int(payment.amount) * _TOMAN_TO_RIAL, authority=authority
        )
        payment.raw_gateway_response = verify_result.raw_response

        if verify_result.success:
            payment.status = PaymentStatus.verified
            payment.reference_id = verify_result.reference_id
            payment.verified_at = datetime.now(UTC)
            await order_service.mark_paid(payment.order_id)
        else:
            payment.status = PaymentStatus.failed
            await order_service.mark_payment_failed(payment.order_id)

        return payment
