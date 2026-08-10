"""Testes das rotas públicas de eventos (GET /events/, GET /events/{id})."""
import uuid
from datetime import datetime, timedelta, timezone

from app.models.event import Venue, Event


def test_lista_eventos_futuros(client, event_futuro, event_passado):
    resp = client.get("/events/")
    assert resp.status_code == 200
    nomes = [e["name"] for e in resp.json()]
    assert "Rave Teste" in nomes
    assert "Rave Passada" not in nomes  # eventos passados não devem aparecer


def test_lista_eventos_filtra_por_cidade(client, db_session, event_futuro):
    outra_venue = Venue(name="Warung Beach Club", city="Itajaí", state="SC")
    db_session.add(outra_venue)
    db_session.commit()
    db_session.refresh(outra_venue)

    db_session.add(Event(
        name="Rave Itajaí",
        event_date=datetime.now(timezone.utc) + timedelta(days=5),
        venue_id=outra_venue.id,
    ))
    db_session.commit()

    resp = client.get("/events/", params={"city": "Itajaí"})
    assert resp.status_code == 200
    nomes = [e["name"] for e in resp.json()]
    assert nomes == ["Rave Itajaí"]


def test_lista_eventos_respeita_limit(client, db_session, venue):
    for i in range(5):
        db_session.add(Event(
            name=f"Evento {i}",
            event_date=datetime.now(timezone.utc) + timedelta(days=i + 1),
            venue_id=venue.id,
        ))
    db_session.commit()

    resp = client.get("/events/", params={"limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_evento_por_id(client, event_futuro):
    resp = client.get(f"/events/{event_futuro.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Rave Teste"
    assert body["venue"]["city"] == "Camboriú"


def test_get_evento_inexistente_retorna_404(client):
    resp = client.get(f"/events/{uuid.uuid4()}")
    assert resp.status_code == 404