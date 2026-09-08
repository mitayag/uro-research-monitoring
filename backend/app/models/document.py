import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ResearchDocument(Base):
    __tablename__ = "research_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(100), nullable=False)  # PROPOSAL, FINAL_PAPER, TURNITIN_RESULT, etc.
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    research = relationship("Research", back_populates="documents")
    versions = relationship("ResearchDocumentVersion", back_populates="document", cascade="all, delete-orphan")


class ResearchDocumentVersion(Base):
    __tablename__ = "research_document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("research_documents.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    workflow_stage = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    checksum = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)

    document = relationship("ResearchDocument", back_populates="versions")
