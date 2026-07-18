"""
create table artist(
    id integer primary key
    name varchar not null
    genre varchar not null
    created_at time
)
"""

import sqlalchemy as sa
from app.database import Base

class Artist(Base):
    __tablename__ = 'artists'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False)
    genre = sa.Column(sa.String(200), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
