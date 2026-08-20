import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.common.money import Money
from app.modules.wallet.models import WalletTransactionType


class WalletPublic(BaseModel):
    id: uuid.UUID
    balance: Money


class WalletDepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class AdminWalletAdjustRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=500)


class WalletTransactionPublic(BaseModel):
    id: uuid.UUID
    type: WalletTransactionType
    amount: Money
    balance_after: Money
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
