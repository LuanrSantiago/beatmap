from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base

class ScraperSource(Base):
    __tablename__ = "scraper_sources"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String(150), nullable=False, unique=True)
    url             = Column(Text, nullable=False, unique=True)
    status          = Column(SAEnum("active", "paused", "error", name="source_status"), nullable=False, default="active")
    last_scraped_at = Column(DateTime(timezone=True))
    error_message   = Column(Text)
    created_at      = Column(DateTime(timezone=True), nullable=False, server_default=func.now())