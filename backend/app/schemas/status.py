from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum

class AttendanceStatus(str, Enum):
    going     = "going"
    thinking  = "thinking"
    bought    = "bought"
    not_going = "not_going"

class StatusIn(BaseModel):
    event_id: UUID
    status:   AttendanceStatus

class StatusOut(BaseModel):
    id:         UUID
    user_id:    UUID
    event_id:   UUID
    status:     AttendanceStatus
    updated_at: datetime

    model_config = {"from_attributes": True}