import uuid
from datetime import datetime

from pydantic import BaseModel

from app.modules.users.models import UserRole


class AdminUserPublic(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
