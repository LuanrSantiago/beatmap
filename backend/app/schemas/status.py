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


# ─── NOVO: usado pela tela "Minhas Interações" ──────────────────
# Junta o status com os dados do evento (nome, data, local), pra não
# precisar de uma segunda chamada no frontend nem depender da lista
# geral de eventos (que tem limite de 200 e pode não conter tudo).

class VenueResumo(BaseModel):
    name:  str
    city:  str
    state: str

    model_config = {"from_attributes": True}


class EventoResumo(BaseModel):
    id:         UUID
    name:       str
    event_date: datetime
    ticket_url: str | None = None
    venue:      VenueResumo

    model_config = {"from_attributes": True}


class StatusDetalhadoOut(BaseModel):
    id:         UUID
    event_id:   UUID
    status:     AttendanceStatus
    updated_at: datetime
    event:      EventoResumo

    model_config = {"from_attributes": True}