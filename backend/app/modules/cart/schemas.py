import uuid

from pydantic import BaseModel, Field

from app.common.money import Money


class CartItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartItemPublic(BaseModel):
    product_id: uuid.UUID
    name: str
    slug: str
    unit_price: Money
    quantity: int
    subtotal: Money
    available_stock: int


class CartSummary(BaseModel):
    items: list[CartItemPublic]
    subtotal: Money
    total: Money
