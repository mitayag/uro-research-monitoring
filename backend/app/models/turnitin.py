import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class TurnitinStage(str, enum.Enum):
    PROPOSAL = "PROPOSAL"
    FINAL_PAPER = "FINAL_PAPER"


class TurnitinResult(str, enum.Enum):
    ACCEPTABLE = "ACCEPTABLE"
    REVISION_REQUIRED = "REVISION_REQUIRED"


class SimilarityCheckAttempt(Base):
    __tablename__ = "similarity_check_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("research_document_versions.id"), nullable=False)
    stage = Column(SAEnum(TurnitinStage), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    similarity_score = Column(Float, nullable=True)
    threshold_at_decision = Column(Float, nullable=True)
    result = Column(SAEnum(TurnitinResult), nullable=False)
    report_file = Column(String(500), nullable=True)
    remarks_researcher = Column(Text, nullable=True)
    remarks_internal = Column(Text, nullable=True)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    research = relationship("Research", back_populates="similarity_checks")
