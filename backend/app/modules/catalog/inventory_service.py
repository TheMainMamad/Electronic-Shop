import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError
from app.modules.catalog.models import InventoryChangeType, InventoryHistory, ProductInventory
from app.modules.catalog.repository import InventoryRepository


class InventoryService:
    """All stock mutation goes through here so the reserve/commit/release
    invariant (see docs/architecture.md §18) has exactly one implementation.
    Every method locks the ProductInventory row with SELECT ... FOR UPDATE
    before mutating it, which is what makes these safe under concurrent
    requests and multiple backend replicas — the lock lives in Postgres, not
    in process memory.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InventoryRepository(session)

    async def _locked_inventory(self, product_id: uuid.UUID) -> ProductInventory:
        inventory = await self.repo.lock_for_update(product_id)
        if inventory is None:
            raise NotFoundError("موجودی این محصول ثبت نشده است.")
        return inventory

    async def reserve(
        self,
        product_id: uuid.UUID,
        quantity: int,
        *,
        reference_type: str,
        reference_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        inventory = await self._locked_inventory(product_id)
        available = inventory.stock_total - inventory.stock_reserved
        if available < quantity:
            raise ConflictError("موجودی کافی برای این محصول وجود ندارد.")

        inventory.stock_reserved += quantity
        self.repo.add_history(
            InventoryHistory(
                product_id=product_id,
                change_type=InventoryChangeType.reserve,
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                actor_id=actor_id,
            )
        )

    async def release(
        self,
        product_id: uuid.UUID,
        quantity: int,
        *,
        reference_type: str,
        reference_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        inventory = await self._locked_inventory(product_id)
        inventory.stock_reserved = max(0, inventory.stock_reserved - quantity)
        self.repo.add_history(
            InventoryHistory(
                product_id=product_id,
                change_type=InventoryChangeType.release,
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                actor_id=actor_id,
            )
        )

    async def commit_purchase(
        self,
        product_id: uuid.UUID,
        quantity: int,
        *,
        reference_type: str,
        reference_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        inventory = await self._locked_inventory(product_id)
        inventory.stock_total = max(0, inventory.stock_total - quantity)
        inventory.stock_reserved = max(0, inventory.stock_reserved - quantity)
        self.repo.add_history(
            InventoryHistory(
                product_id=product_id,
                change_type=InventoryChangeType.purchase,
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                actor_id=actor_id,
            )
        )

    async def restock(
        self, product_id: uuid.UUID, quantity: int, *, actor_id: uuid.UUID | None = None
    ) -> None:
        inventory = await self._locked_inventory(product_id)
        inventory.stock_total += quantity
        self.repo.add_history(
            InventoryHistory(
                product_id=product_id,
                change_type=InventoryChangeType.restock,
                quantity=quantity,
                reference_type="admin_restock",
                reference_id=None,
                actor_id=actor_id,
            )
        )

    async def adjust(
        self, product_id: uuid.UUID, delta: int, *, actor_id: uuid.UUID | None = None
    ) -> None:
        inventory = await self._locked_inventory(product_id)
        new_total = inventory.stock_total + delta
        if new_total < inventory.stock_reserved:
            raise ConflictError(
                "موجودی جدید نمی‌تواند کمتر از مقدار رزروشده برای سفارش‌های در انتظار باشد."
            )
        inventory.stock_total = new_total
        self.repo.add_history(
            InventoryHistory(
                product_id=product_id,
                change_type=InventoryChangeType.adjust,
                quantity=delta,
                reference_type="admin_adjust",
                reference_id=None,
                actor_id=actor_id,
            )
        )
