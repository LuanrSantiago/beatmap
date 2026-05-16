from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.database import SessionLocal
from app.models.event import Venue, Event
import app.models.scraper
from dotenv import load_dotenv
import pytz

load_dotenv()

def get_or_create_venue(db: Session, nome: str, cidade: str, estado: str) -> Venue:
    venue = db.query(Venue).filter_by(name=nome, city=cidade).first()
    if venue:
        return venue
    venue = Venue(name=nome, city=cidade, state=estado)
    db.add(venue)
    db.commit()
    db.refresh(venue)
    print(f"  [novo venue] {nome} — {cidade}/{estado}")
    return venue

def get_sympla_source_id(db: Session):
    result = db.execute(
        text("SELECT id FROM scraper_sources WHERE name = 'Sympla' LIMIT 1")
    ).fetchone()
    return result[0] if result else None

def save_eventos(eventos: list[dict]) -> dict:
    db = SessionLocal()
    criados = 0
    duplicatas = 0
    erros = 0

    source_id = get_sympla_source_id(db)

    try:
        for ev in eventos:
            try:
                venue = get_or_create_venue(
                    db, ev["venue"], ev["cidade"], ev["estado"]
                )

                event_date = ev["data"]
                if event_date and event_date.tzinfo is None:
                    brt = pytz.timezone("America/Sao_Paulo")
                    event_date = brt.localize(event_date)

                existente = db.query(Event).filter_by(
                    name=ev["nome"],
                    event_date=event_date,
                    venue_id=venue.id
                ).first()

                if existente:
                    duplicatas += 1
                    continue

                evento = Event(
                    name=ev["nome"],
                    event_date=event_date,
                    ticket_url=ev.get("url"),
                    venue_id=venue.id,
                    source_id=source_id,
                )
                db.add(evento)
                db.commit()
                criados += 1
                print(f"  ✓ salvo: {ev['nome']}")

            except Exception as e:
                db.rollback()
                erros += 1
                print(f"  ✗ erro: {ev.get('nome')} — {e}")

    finally:
        db.close()

    return {"criados": criados, "duplicatas": duplicatas, "erros": erros}