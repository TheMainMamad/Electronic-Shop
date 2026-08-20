import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogPublic(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    audit_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
