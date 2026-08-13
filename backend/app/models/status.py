from sqlalchemy import Column, DateTime, ForeignKey, Enum as SAEnum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.models.auth_stub import auth_users  # noqa: F401 — precisa estar importado para a FK abaixo resolver

class UserEventStatus(Base):
    __tablename__ = "user_event_status"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    event_id   = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    status     = Column(SAEnum("going", "thinking", "bought", "not_going", name="attendance_status"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    event      = relationship("Event")

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_user_event"),
        Index("idx_status_user", "user_id"),
        Index("idx_status_event", "event_id"),
    )