from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, func
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.models.event import Event, Venue
from app.schemas.event import EventOut, ResumoFiltros

router = APIRouter(prefix="/events", tags=["events"])

# Fuso usado para "quebrar" a data em mês/ano — sem isso, a extração de
# mês/ano do timestamptz usaria o fuso padrão da conexão com o banco, o
# que poderia divergir do que o frontend já mostra pro usuário (que
# sempre exibe a data no fuso local do navegador, tipicamente BRT).
FUSO = "America/Sao_Paulo"


def _filtrar_por_periodo(query, periodo: str):
    """
    Filtra a query por um período no formato "M/YYYY" (ex: "12/2026").
    Em caso de formato inválido, ignora o filtro silenciosamente —
    mesma postura defensiva usada em outros parsers do projeto.
    """
    try:
        mes_str, ano_str = periodo.split("/")
        mes, ano = int(mes_str), int(ano_str)
    except (ValueError, AttributeError):
        return query

    data_no_fuso = func.timezone(FUSO, Event.event_date)
    return query.filter(
        func.extract("month", data_no_fuso) == mes,
        func.extract("year", data_no_fuso) == ano,
    )


@router.get("/", response_model=List[EventOut])
def list_events(
    db:      Session = Depends(get_db),
    city:    str      = Query(None, description="Filtrar por cidade"),
    periodo: str      = Query(None, description="Filtrar por período, formato M/YYYY (ex: 12/2026)"),
    skip:    int      = Query(0,    ge=0),
    limit:   int      = Query(50,   ge=1, le=500),
):
    query = (
        db.query(Event)
        .options(joinedload(Event.venue))
        .filter(Event.event_date > datetime.now(timezone.utc))
        .order_by(asc(Event.event_date))
    )

    if city:
        query = query.filter(Event.venue.has(city=city))

    if periodo:
        query = _filtrar_por_periodo(query, periodo)

    return query.offset(skip).limit(limit).all()


# ─── NOVO: contagens para alimentar os filtros do frontend ──────────
@router.get("/resumo-filtros/", response_model=ResumoFiltros)
def resumo_filtros(db: Session = Depends(get_db)):
    """
    Retorna a contagem de eventos futuros por cidade e por período
    (mês/ano), calculada sobre TODOS os eventos futuros do banco — não
    só uma página. Usado pelos componentes CityFilter/DateFilter para
    montar os atalhos e os dropdowns sem precisar baixar a lista inteira
    de eventos.

    As contagens são independentes entre si (cidade não considera o
    período selecionado e vice-versa) — mesmo comportamento que já
    existia quando esses cálculos eram feitos no frontend.
    """
    agora = datetime.now(timezone.utc)

    cidades_query = (
        db.query(Venue.city, func.count(Event.id))
        .join(Event, Event.venue_id == Venue.id)
        .filter(Event.event_date > agora)
        .group_by(Venue.city)
        .all()
    )
    cidades = [{"cidade": cidade, "total": total} for cidade, total in cidades_query]

    data_no_fuso = func.timezone(FUSO, Event.event_date)
    periodos_query = (
        db.query(
            func.extract("month", data_no_fuso),
            func.extract("year", data_no_fuso),
            func.count(Event.id),
        )
        .filter(Event.event_date > agora)
        .group_by(
            func.extract("month", data_no_fuso),
            func.extract("year", data_no_fuso),
        )
        .all()
    )
    periodos = [
        {"periodo": f"{int(mes)}/{int(ano)}", "total": total}
        for mes, ano, total in periodos_query
    ]

    return {"cidades": cidades, "periodos": periodos}


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