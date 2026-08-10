"""
alembic/env.py — BeatMap
Configurado para:
1. Ler DATABASE_URL do .env (mesma variável usada por app/database.py),
   em vez do placeholder hardcoded no alembic.ini.
2. Apontar para os models reais do projeto, para que `--autogenerate`
   consiga comparar o schema do banco com as classes SQLAlchemy.
3. Ignorar o stub auth.users nas comparações (existe só pra resolver a FK
   em Python — não é uma tabela que o Alembic deveria criar/gerenciar).
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Garante que "app.*" seja importável a partir daqui (alembic/ está um
# nível abaixo da raiz do backend, onde ficam pytest.ini e a pasta app/).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

# --- Import dos models: precisa ser TUDO que tiver tabela, senão o
# --- autogenerate não vê e acha que a tabela "não deveria existir"
# --- (e pode chegar a gerar um DROP TABLE na migration).
from app.database import Base
from app.models.event import Venue, Event  # noqa: F401
from app.models.status import UserEventStatus  # noqa: F401
from app.models.scraper import ScraperSource  # noqa: F401
from app.models.auth_stub import auth_users  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Sobrescreve o placeholder do alembic.ini com a DATABASE_URL real do .env
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata é o que o --autogenerate usa para comparar
# "o que os models dizem que deveria existir" x "o que existe no banco"
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Exclui o stub auth.users das comparações do autogenerate.
    Ele existe só pra permitir a ForeignKey de user_event_status.user_id
    ser resolvida em Python — a tabela real é gerenciada pelo Supabase Auth,
    o Alembic não deve tentar criar, alterar ou dropar ela.
    """
    if type_ == "table" and getattr(object, "schema", None) == "auth":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()