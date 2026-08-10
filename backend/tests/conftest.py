"""
tests/conftest.py — BeatMap
Fixtures compartilhadas por todos os testes: banco SQLite em memória
(troca o Postgres real só durante os testes) e dois clientes de teste:

- `client`: sobrescreve tanto o banco quanto a autenticação (usuário fake fixo).
  Usado para testar a LÓGICA das rotas (events, status), sem se preocupar com JWT.
- `client_auth_real`: sobrescreve só o banco, mantém a validação real de
  get_current_user_id. Usado nos testes de app/auth.py (tests/test_auth.py).
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Precisa estar setado ANTES de importar app.database (ele lê no import).
# Usamos SQLite em memória só para os testes — o Postgres real não é tocado.
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "https://exemplo-teste.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "chave-fake-de-teste")


# --- Compat #1: afinidade de tipo no SQLite ---
# O nome de tipo que o SQLAlchemy gera pra UUID no SQLite é literalmente "UUID",
# que não bate com nenhuma regra de afinidade TEXT do SQLite (ele só reconhece
# "CHAR", "CLOB", "TEXT" no nome do tipo). Sem bater em nenhuma regra, o SQLite
# usa afinidade NUMERIC por padrão — e um hex totalmente numérico (tipo
# "00000000000000000000000000000099", que é o .hex de um UUID de teste)
# é silenciosamente convertido pra inteiro puro, perdendo os zeros à esquerda
# (foi o bug do "int object has no attribute replace"). Forçamos "CHAR(32)"
# pra garantir afinidade TEXT. Só afeta o SQLite de teste — em produção
# (Postgres) esse @compiles nem é usado, o Postgres já tem UUID nativo.
@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


# --- Compat #2: strings soltas viram UUID antes de gravar ---
# Em produção (Postgres/psycopg2), passar uma string onde se espera um UUID
# funciona sem problema — o driver converte sozinho. No SQLite, o
# bind_processor do SQLAlchemy exige um uuid.UUID já pronto. Isso importa
# porque event_id chega como string em algumas rotas, e user_id vem como
# string direto do JWT (payload["sub"]) — nunca convertido explicitamente
# pra uuid.UUID no código de produção, porque o Postgres nunca precisou disso.
_original_bind_processor = PG_UUID.bind_processor


def _tolerant_bind_processor(self, dialect):
    original = _original_bind_processor(self, dialect)
    if original is None:
        return None

    def process(value):
        if dialect.name == "sqlite" and isinstance(value, str):
            value = uuid.UUID(value)
        return original(value)

    return process


PG_UUID.bind_processor = _tolerant_bind_processor

from app.database import Base, get_db
from app.models.event import Venue, Event
from app.models.status import UserEventStatus  # noqa: F401 — precisa ser importado p/ create_all() ver a tabela
from app.auth import get_current_user_id
from app.main import app

# Event.source_id referencia "scraper_sources.id", mas o model ScraperSource
# não faz parte deste conjunto de testes (não mexemos em scrapers aqui).
# Criamos uma tabela mínima só pra o create_all() conseguir resolver essa FK —
# não é usada em nenhum teste, é puramente estrutural.
scraper_sources_stub = Table(
    "scraper_sources",
    Base.metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
)

# StaticPool + check_same_thread=False: garante que todas as conexões abertas
# durante o teste (TestClient roda em thread própria) enxerguem o MESMO banco
# em memória, em vez de cada conexão criar um SQLite vazio novo.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FAKE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture(scope="function")
def db_session():
    """Cria as tabelas do zero antes de cada teste e derruba tudo depois."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente com banco de teste E autenticação mockada (usuário fixo)."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user_id():
        return str(FAKE_USER_ID)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_auth_real(db_session):
    """Cliente com banco de teste, mas SEM mockar a autenticação — usado em test_auth.py."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def venue(db_session):
    v = Venue(name="Green Valley", city="Camboriú", state="SC", address="Rod. dos Municípios")
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


@pytest.fixture
def event_futuro(db_session, venue):
    e = Event(
        name="Rave Teste",
        event_date=datetime.now(timezone.utc) + timedelta(days=10),
        ticket_price=100.00,
        ticket_url="https://exemplo.com/ingresso",
        venue_id=venue.id,
    )
    db_session.add(e)
    db_session.commit()
    db_session.refresh(e)
    return e


@pytest.fixture
def event_passado(db_session, venue):
    e = Event(
        name="Rave Passada",
        event_date=datetime.now(timezone.utc) - timedelta(days=10),
        venue_id=venue.id,
    )
    db_session.add(e)
    db_session.commit()
    db_session.refresh(e)
    return e