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


# ─── NOVO: usado pela rota /events/resumo-filtros/ ──────────────
# Alimenta os componentes CityFilter e DateFilter no frontend, sem
# precisar carregar a lista inteira de eventos só pra montar os menus.

class CidadeContagem(BaseModel):
    cidade: str
    total:  int

class PeriodoContagem(BaseModel):
    periodo: str  # formato "M/YYYY", ex: "12/2026" — mesmo formato usado no frontend
    total:   int

class ResumoFiltros(BaseModel):
    cidades:  list[CidadeContagem]
    periodos: list[PeriodoContagem]