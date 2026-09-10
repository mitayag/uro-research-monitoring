import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ResearchStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    FOR_DEAN_ENDORSEMENT = "FOR_DEAN_ENDORSEMENT"
    ENDORSED_TO_URO = "ENDORSED_TO_URO"
    # Phase 3 — URO Receipt & Initial Review
    URO_RECEIVED = "URO_RECEIVED"
    INITIAL_REVIEW = "INITIAL_REVIEW"
    INITIAL_REVISION_REQUIRED = "INITIAL_REVISION_REQUIRED"
    INITIAL_REVISION_SUBMITTED = "INITIAL_REVISION_SUBMITTED"
    INITIAL_REVIEW_PASSED = "INITIAL_REVIEW_PASSED"
    # Phase 3 — Proposal Turnitin
    PROPOSAL_TURNITIN = "PROPOSAL_TURNITIN"
    PROPOSAL_TURNITIN_REVISION_REQUIRED = "PROPOSAL_TURNITIN_REVISION_REQUIRED"
    PROPOSAL_TURNITIN_RESUBMITTED = "PROPOSAL_TURNITIN_RESUBMITTED"
    PROPOSAL_TURNITIN_PASSED = "PROPOSAL_TURNITIN_PASSED"
    READY_FOR_EXTERNAL_EVALUATION = "READY_FOR_EXTERNAL_EVALUATION"
    # Phase 4 — External Evaluation
    EXTERNAL_EVALUATION = "EXTERNAL_EVALUATION"
    EXTERNAL_EVALUATION_REVISION_REQUIRED = "EXTERNAL_EVALUATION_REVISION_REQUIRED"
    SELECTIVE_EXTERNAL_REEVALUATION = "SELECTIVE_EXTERNAL_REEVALUATION"
    EXTERNAL_EVALUATION_PASSED = "EXTERNAL_EVALUATION_PASSED"
    # Phase 5 — IRB Review
    FOR_IRB_REVIEW = "FOR_IRB_REVIEW"
    IRB_REVISION_REQUIRED = "IRB_REVISION_REQUIRED"
    PROPOSAL_APPROVED = "PROPOSAL_APPROVED"
    # Phase 6 — Research Execution
    RESEARCH_IN_PROGRESS = "RESEARCH_IN_PROGRESS"
    FINAL_PAPER_DUE = "FINAL_PAPER_DUE"
    FINAL_PAPER_SUBMITTED = "FINAL_PAPER_SUBMITTED"
    # Phase 7 — Final Paper Turnitin
    FINAL_PAPER_TURNITIN = "FINAL_PAPER_TURNITIN"
    FINAL_PAPER_TURNITIN_REVISION_REQUIRED = "FINAL_PAPER_TURNITIN_REVISION_REQUIRED"
    FINAL_PAPER_TURNITIN_PASSED = "FINAL_PAPER_TURNITIN_PASSED"
    # Phase 8 — Final Blind Evaluation
    FINAL_BLIND_EVALUATION = "FINAL_BLIND_EVALUATION"
    FINAL_EVALUATION_REVISION_REQUIRED = "FINAL_EVALUATION_REVISION_REQUIRED"
    SELECTIVE_FINAL_REEVALUATION = "SELECTIVE_FINAL_REEVALUATION"
    FINAL_BLIND_EVALUATION_PASSED = "FINAL_BLIND_EVALUATION_PASSED"
    # Phase 9 — Completion
    COMPLETED = "COMPLETED"
    READY_FOR_PRESENTATION = "READY_FOR_PRESENTATION"
    READY_FOR_PUBLICATION = "READY_FOR_PUBLICATION"
    ARCHIVED = "ARCHIVED"

    # Legacy aliases for backward compatibility (map old names to new)
    @classmethod
    def _missing_(cls, value):
        _LEGACY = {
            "INITIAL_EVALUATION": cls.INITIAL_REVIEW,
            "INITIAL_EVALUATION_REVISION_REQUIRED": cls.INITIAL_REVISION_REQUIRED,
        }
        return _LEGACY.get(value)


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(20), unique=True, nullable=False)  # e.g., "2025-2026"
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Research(Base):
    __tablename__ = "research"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    lead_proponent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(ResearchStatus), nullable=False, default=ResearchStatus.DRAFT)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True)
    nature_of_research = Column(String(100), nullable=True)
    target_journal = Column(String(200), nullable=True)
    research_agenda = Column(Text, nullable=True)
    is_continuation = Column(Boolean, default=False)
    continuation_ref = Column(String(200), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    institutional_email = Column(String(255), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    school_college_id = Column(UUID(as_uuid=True), ForeignKey("school_colleges.id"), nullable=True)
    assigned_dean_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    lead_proponent = relationship("User", foreign_keys=[lead_proponent_id], back_populates="research_as_lead")
    school_college = relationship("SchoolCollege", foreign_keys=[school_college_id])
    assigned_dean = relationship("User", foreign_keys=[assigned_dean_id])
    authors = relationship("ResearchAuthor", back_populates="research", cascade="all, delete-orphan")
    declarations = relationship("ResearchDeclaration", back_populates="research", cascade="all, delete-orphan")
    documents = relationship("ResearchDocument", back_populates="research", cascade="all, delete-orphan")
    status_history = relationship("ResearchStatusHistory", back_populates="research", cascade="all, delete-orphan")
    readiness = relationship("ResearchReadiness", back_populates="research", uselist=False, cascade="all, delete-orphan")
    milestones = relationship("ResearchMilestone", back_populates="research", cascade="all, delete-orphan")
    similarity_checks = relationship("SimilarityCheckAttempt", back_populates="research", cascade="all, delete-orphan")
    evaluation_assignments = relationship("EvaluationAssignment", back_populates="research", cascade="all, delete-orphan")
    irb_reviews = relationship("IRBReview", back_populates="research", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="research", cascade="all, delete-orphan")


class ResearchAuthor(Base):
    __tablename__ = "research_authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # nullable for external authors
    name = Column(String(200), nullable=False)
    affiliation = Column(String(200), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    contribution_pct = Column(Integer, nullable=True)  # 0-100
    is_lead = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    research = relationship("Research", back_populates="authors")


class ResearchDeclaration(Base):
    __tablename__ = "research_declarations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    declaration_type = Column(String(100), nullable=False)
    consent = Column(Boolean, nullable=False)
    consented_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    consented_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    research = relationship("Research", back_populates="declarations")


class ResearchReadiness(Base):
    __tablename__ = "research_readiness"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), unique=True, nullable=False)
    ready_for_presentation = Column(Boolean, default=False)
    ready_for_publication = Column(Boolean, default=False)
    marked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    marked_at = Column(DateTime(timezone=True), nullable=True)

    research = relationship("Research", back_populates="readiness")


class ResearchStatusHistory(Base):
    __tablename__ = "research_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    prior_status = Column(SAEnum(ResearchStatus), nullable=True)
    new_status = Column(SAEnum(ResearchStatus), nullable=False)
    action = Column(String(100), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(50), nullable=False)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("research_document_versions.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    research = relationship("Research", back_populates="status_history")
