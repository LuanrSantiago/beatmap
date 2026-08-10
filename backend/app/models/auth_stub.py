"""
app/models/auth_stub.py — BeatMap
Representa a tabela auth.users, gerenciada pelo Supabase Auth (fora do
nosso controle — não é um model ORM de verdade, não temos CRUD sobre ela).

Existe só para o SQLAlchemy conseguir resolver a ForeignKey de
user_event_status.user_id -> auth.users.id. Sem isso, o SQLAlchemy não
acha a tabela referenciada (ela vive no schema "auth", não no "public"),
e levanta NoReferencedTableError.

Fica em um schema diferente ("auth"), então o Alembic não tenta gerenciar
(criar/dropar) essa tabela nas migrations — por padrão, o autogenerate só
compara tabelas do schema padrão (public), a não ser que include_schemas
seja ativado explicitamente no env.py (não é o nosso caso).
"""
from sqlalchemy import Table, Column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

auth_users = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
)