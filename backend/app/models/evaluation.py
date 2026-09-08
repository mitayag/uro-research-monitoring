import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class EvaluationType(str, enum.Enum):
    PROPOSAL = "PROPOSAL"
    FINAL = "FINAL"


class AssignmentStatus(str, enum.Enum):
    PENDING_INVITATION = "PENDING_INVITATION"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    IN_REVIEW = "IN_REVIEW"
    SUBMITTED = "SUBMITTED"
    REEVALUATION_REQUIRED = "REEVALUATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


class EvaluatorProfile(Base):
    __tablename__ = "evaluator_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expertise = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    assignments = relationship("EvaluationAssignment", back_populates="evaluator")


class EvaluationAssignment(Base):
    __tablename__ = "evaluation_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("evaluator_profiles.id"), nullable=False)
    evaluation_type = Column(SAEnum(EvaluationType), nullable=False)
    status = Column(SAEnum(AssignmentStatus), nullable=False, default=AssignmentStatus.PENDING_INVITATION)
    round_number = Column(Integer, default=1)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("research_document_versions.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    declined_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    research = relationship("Research", back_populates="evaluation_assignments")
    evaluator = relationship("EvaluatorProfile", back_populates="assignments")
    submissions = relationship("EvaluationSubmission", back_populates="assignment", cascade="all, delete-orphan")


class EvaluationSubmission(Base):
    __tablename__ = "evaluation_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_assignments.id", ondelete="CASCADE"), nullable=False)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("research_document_versions.id"), nullable=False)
    score = Column(Integer, nullable=True)
    pass_fail = Column(String(10), nullable=False)  # PASS or FAIL
    comments = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    assignment = relationship("EvaluationAssignment", back_populates="submissions")
