import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.common.money import Money
from app.modules.orders.models import OrderStatus


class ShippingAddress(BaseModel):
    recipient_name: str = Field(max_length=150)
    province: str = Field(max_length=100)
    city: str = Field(max_length=100)
    address_line: str = Field(max_length=500)
    postal_code: str = Field(max_length=20)
    phone_number: str = Field(max_length=20)


class CheckoutRequest(BaseModel):
    shipping_address: ShippingAddress | None = None


class OrderItemPublic(BaseModel):
    product_id: uuid.UUID | None
    product_name: str
    sku: str
    unit_price: Money
    quantity: int
    subtotal: Money

    model_config = {"from_attributes": True}


class OrderPublic(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    subtotal: Money
    total: Money
    shipping_address: dict[str, str] | None
    items: list[OrderItemPublic]
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusUpdateRequest(BaseModel):
    new_status: OrderStatus
    note: str | None = Field(default=None, max_length=500)
