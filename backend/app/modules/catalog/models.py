import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InventoryChangeType(enum.StrEnum):
    restock = "restock"
    reserve = "reserve"
    release = "release"
    purchase = "purchase"
    adjust = "adjust"


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("parent_id <> id", name="ck_category_not_self_parent"),
        Index("ix_categories_parent_id", "parent_id"),
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(170), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # noload: async sessions can't do implicit lazy loads. get_tree() builds
    # and assigns this explicitly; single-object endpoints just get [].
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", cascade="save-update, merge", lazy="noload"
    )
    parent: Mapped["Category | None"] = relationship(
        back_populates="children", remote_side="Category.id"
    )


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_is_active", "is_active"),
    )

    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 0), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 0), nullable=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    images: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    specifications: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # noload: async sessions can't do implicit lazy loads. Callers that need
    # `.inventory` must fetch it via ProductRepository (selectinload) or set
    # it explicitly in-memory right after creating it (see ProductService.create).
    category: Mapped["Category"] = relationship(lazy="noload")
    inventory: Mapped["ProductInventory"] = relationship(
        back_populates="product", uselist=False, cascade="all, delete-orphan", lazy="noload"
    )


class ProductInventory(Base):
    __tablename__ = "product_inventory"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    stock_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Product"] = relationship(back_populates="inventory")

    __table_args__ = (
        CheckConstraint("stock_total >= 0", name="ck_inventory_total_non_negative"),
        CheckConstraint("stock_reserved >= 0", name="ck_inventory_reserved_non_negative"),
        CheckConstraint("stock_reserved <= stock_total", name="ck_inventory_reserved_le_total"),
    )


class InventoryHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inventory_history"
    __table_args__ = (Index("ix_inventory_history_product_id", "product_id"),)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    change_type: Mapped[InventoryChangeType] = mapped_column(
        Enum(InventoryChangeType, name="inventory_change_type", native_enum=True), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
