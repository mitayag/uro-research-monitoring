import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class IRBDecision(str, enum.Enum):
    REVISION_REQUIRED = "REVISION_REQUIRED"
    NOT_APPROVED = "NOT_APPROVED"
    APPROVED = "APPROVED"


class IRBReview(Base):
    __tablename__ = "irb_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("research_document_versions.id"), nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(SAEnum(IRBDecision), nullable=False)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    round_number = Column(Integer, default=1)

    research = relationship("Research", back_populates="irb_reviews")
