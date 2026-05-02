from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class VenueOut(BaseModel):
    id:      UUID
    name:    str
    city:    str
    state:   str
    address: str | None

    model_config = {"from_attributes": True}

class EventOut(BaseModel):
    id:           UUID
    name:         str
    event_date:   datetime
    ticket_price: Decimal | None
    ticket_url:   str | None
    venue:        VenueOut

    model_config = {"from_attributes": True}