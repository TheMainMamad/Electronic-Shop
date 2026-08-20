import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.tickets.models import TicketMessageAuthorRole, TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=1, max_length=5000)
    priority: TicketPriority = TicketPriority.normal


class TicketReplyCreate(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketMessagePublic(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID | None
    author_role: TicketMessageAuthorRole
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    last_response_at: datetime
    messages: list[TicketMessagePublic] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TicketListItem(BaseModel):
    id: uuid.UUID
    subject: str
    status: TicketStatus
    priority: TicketPriority
    last_response_at: datetime

    model_config = {"from_attributes": True}
