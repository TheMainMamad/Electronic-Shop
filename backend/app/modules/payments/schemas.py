import uuid

from pydantic import BaseModel

from app.common.money import Money
from app.modules.payments.models import PaymentStatus


class PaymentInitRequest(BaseModel):
    order_id: uuid.UUID


class PaymentInitResponse(BaseModel):
    payment_id: uuid.UUID
    payment_url: str


class PaymentPublic(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    status: PaymentStatus
    amount: Money
    reference_id: str | None

    model_config = {"from_attributes": True}
