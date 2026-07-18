from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventOut

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[EventOut])
def list_events(
    db:   Session = Depends(get_db),
    city: str     = Query(None, description="Filtrar por cidade"),
    skip: int     = Query(0,    ge=0),
    limit: int    = Query(50,   ge=1, le=500),
):
    query = (
        db.query(Event)
        .options(joinedload(Event.venue))
        .filter(Event.event_date > datetime.now(timezone.utc))
        .order_by(asc(Event.event_date))
    )

    if city:
        query = query.filter(Event.venue.has(city=city))

    return query.offset(skip).limit(limit).all()

@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    event = (
        db.query(Event)
        .options(joinedload(Event.venue))
        .filter(Event.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return event