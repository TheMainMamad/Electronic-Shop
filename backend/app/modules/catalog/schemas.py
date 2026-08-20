import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

_SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=170, pattern=_SLUG_PATTERN)
    parent_id: uuid.UUID | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None
    sort_order: int | None = None


class CategoryMove(BaseModel):
    new_parent_id: uuid.UUID | None = None


class CategoryPublic(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    sort_order: int
    parent_id: uuid.UUID | None
    children: list["CategoryPublic"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=280, pattern=_SLUG_PATTERN)
    short_description: str = Field(default="", max_length=500)
    description: str = ""
    price: Decimal = Field(gt=0)
    discount_price: Decimal | None = Field(default=None, ge=0)
    brand: str = Field(default="", max_length=100)
    category_id: uuid.UUID
    images: list[str] = Field(default_factory=list)
    specifications: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    is_featured: bool = False
    is_popular: bool = False
    initial_stock: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _discount_below_price(self) -> "ProductCreate":
        if self.discount_price is not None and self.discount_price >= self.price:
            raise ValueError("قیمت با تخفیف باید کمتر از قیمت اصلی باشد.")
        return self


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    discount_price: Decimal | None = Field(default=None, ge=0)
    brand: str | None = Field(default=None, max_length=100)
    category_id: uuid.UUID | None = None
    images: list[str] | None = None
    specifications: dict[str, str] | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    is_popular: bool | None = None


class ProductPublic(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    slug: str
    short_description: str
    description: str
    price: Decimal
    discount_price: Decimal | None
    brand: str
    category_id: uuid.UUID
    images: list[str]
    specifications: dict[str, str]
    is_active: bool
    is_featured: bool
    is_popular: bool
    available_stock: int

    model_config = {"from_attributes": True}


class ProductFilterParams(BaseModel):
    category_id: uuid.UUID | None = None
    brand: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    in_stock_only: bool = False
    search: str | None = None
    is_featured: bool | None = None


class InventoryAdjustRequest(BaseModel):
    delta: int
    reason: str = Field(min_length=1, max_length=255)
