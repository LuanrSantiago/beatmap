from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Index, UniqueConstraint, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Venue(Base):
    __tablename__ = "venues"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String(200), nullable=False)
    city       = Column(String(100), nullable=False)
    state      = Column(CHAR(2), nullable=False)
    address    = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    events     = relationship("Event", back_populates="venue")

    __table_args__ = (
        UniqueConstraint("name", "city", name="uq_venue_name_city"),
        Index("idx_venues_city", "city"),
    )

class Event(Base):
    __tablename__ = "events"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(300), nullable=False)
    event_date   = Column(DateTime(timezone=True), nullable=False)
    ticket_price = Column(Numeric(10, 2))
    ticket_url   = Column(Text)
    venue_id     = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False)
    source_id    = Column(UUID(as_uuid=True), ForeignKey("scraper_sources.id"))
    scraped_at   = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at   = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    venue        = relationship("Venue", back_populates="events")

    __table_args__ = (
        UniqueConstraint("name", "event_date", "venue_id", name="uq_event"),
        Index("idx_events_date", "event_date"),
    )