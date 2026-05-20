"""
scraper/save_to_db.py — BeatMap
Versão 2.0 — Suporte a múltiplas fontes (Sympla, Ingresso Rápido, Ticket360)

MUDANÇAS em relação à v1:
- save_eventos() agora recebe o parâmetro `fonte` em vez de hardcodar "Sympla"
- get_source_id() substituiu get_sympla_source_id() — genérica para qualquer fonte
- atualizar_last_scraped() já era genérica, sem mudança
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models.event import Venue, Event
import app.models.scraper  # Necessário para o SQLAlchemy registrar o model ScraperSource
from dotenv import load_dotenv
import pytz

load_dotenv()


def get_or_create_venue(db: Session, nome: str, cidade: str, estado: str) -> Venue:
    """
    Busca um venue existente ou cria um novo.

    "get_or_create" é um padrão muito comum em projetos com banco:
    evita duplicatas sem precisar de try/except toda hora.
    A constraint UNIQUE (name, city) no banco garante a unicidade,
    mas a gente verifica antes para não gerar erro desnecessário.
    """
    venue = db.query(Venue).filter_by(name=nome, city=cidade).first()
    if venue:
        return venue

    venue = Venue(name=nome, city=cidade, state=estado)
    db.add(venue)
    db.commit()
    db.refresh(venue)  # ← refresh carrega o id gerado pelo banco
    print(f"  [novo venue] {nome} — {cidade}/{estado}")
    return venue


def get_source_id(db: Session, fonte: str):
    """
    Retorna o UUID da fonte na tabela scraper_sources.

    MUDANÇA v2: era get_sympla_source_id() hardcoded.
    Agora recebe o nome da fonte como parâmetro.
    Funciona para Sympla, Ingresso Rápido, Ticket360, etc.
    """
    result = db.execute(
        text("SELECT id FROM scraper_sources WHERE name = :nome LIMIT 1"),
        {"nome": fonte}
    ).fetchone()
    return result[0] if result else None


def atualizar_last_scraped(db: Session, source_name: str):
    """Atualiza o campo last_scraped_at da fonte no banco."""
    db.execute(
        text("UPDATE scraper_sources SET last_scraped_at = :now WHERE name = :name"),
        {"now": datetime.now(timezone.utc), "name": source_name}
    )
    db.commit()


def save_eventos(eventos: list[dict], fonte: str = "Sympla") -> dict:
    """
    Salva uma lista de eventos no banco de dados.

    MUDANÇA v2: parâmetro `fonte` com default "Sympla" para não quebrar
    código antigo que chama save_eventos(dados) sem o segundo argumento.

    Fluxo para cada evento:
    1. Cria ou busca o venue
    2. Localiza o timezone
    3. Verifica se o evento já existe (proteção contra duplicatas)
    4. Salva o evento novo
    """
    db = SessionLocal()
    criados = 0
    duplicatas = 0
    erros = 0
    source_id = get_source_id(db, fonte)

    if not source_id:
        print(f"  ⚠  Fonte '{fonte}' não encontrada em scraper_sources!")
        print(f"     Verifique se o registro existe no banco.")

    brt = pytz.timezone("America/Sao_Paulo")

    try:
        for ev in eventos:
            try:
                venue = get_or_create_venue(
                    db, ev["venue"], ev["cidade"], ev["estado"]
                )

                event_date = ev["data"]
                if event_date and event_date.tzinfo is None:
                    event_date = brt.localize(event_date)

                # Verifica duplicata antes de tentar inserir
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
                print(f"  ✓ salvo: {ev['nome']} ({ev['cidade']}/{ev['estado']})")

            except Exception as e:
                db.rollback()
                erros += 1
                print(f"  ✗ erro: {ev.get('nome')} — {e}")

        atualizar_last_scraped(db, fonte)

    finally:
        db.close()

    return {"criados": criados, "duplicatas": duplicatas, "erros": erros}