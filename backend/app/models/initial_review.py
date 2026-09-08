import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ReviewDecision(str, enum.Enum):
    PASS = "PASS"
    REVISION_REQUIRED = "REVISION_REQUIRED"


class ChecklistItemStatus(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NOT_COMPLIANT = "NOT_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class InitialReview(Base):
    __tablename__ = "initial_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(SAEnum(ReviewDecision), nullable=True)
    remarks_researcher = Column(Text, nullable=True)
    remarks_internal = Column(Text, nullable=True)
    revision_instructions = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    decided_at = Column(DateTime(timezone=True), nullable=True)
    round_number = Column(Integer, default=1)

    research = relationship("Research")
    reviewer = relationship("User")
    items = relationship("InitialReviewItem", back_populates="review", cascade="all, delete-orphan")


class InitialReviewItem(Base):
    __tablename__ = "initial_review_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("initial_reviews.id", ondelete="CASCADE"), nullable=False)
    checklist_label = Column(String(300), nullable=False)
    status = Column(SAEnum(ChecklistItemStatus), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    review = relationship("InitialReview", back_populates="items")
