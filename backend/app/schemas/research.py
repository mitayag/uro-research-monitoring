from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class ResearchStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    FOR_DEAN_ENDORSEMENT = "FOR_DEAN_ENDORSEMENT"
    ENDORSED_TO_URO = "ENDORSED_TO_URO"
    URO_RECEIVED = "URO_RECEIVED"
    INITIAL_REVIEW = "INITIAL_REVIEW"
    INITIAL_REVISION_REQUIRED = "INITIAL_REVISION_REQUIRED"
    INITIAL_REVISION_SUBMITTED = "INITIAL_REVISION_SUBMITTED"
    INITIAL_REVIEW_PASSED = "INITIAL_REVIEW_PASSED"
    PROPOSAL_TURNITIN = "PROPOSAL_TURNITIN"
    PROPOSAL_TURNITIN_REVISION_REQUIRED = "PROPOSAL_TURNITIN_REVISION_REQUIRED"
    PROPOSAL_TURNITIN_RESUBMITTED = "PROPOSAL_TURNITIN_RESUBMITTED"
    PROPOSAL_TURNITIN_PASSED = "PROPOSAL_TURNITIN_PASSED"
    READY_FOR_EXTERNAL_EVALUATION = "READY_FOR_EXTERNAL_EVALUATION"
    EXTERNAL_EVALUATION = "EXTERNAL_EVALUATION"
    EXTERNAL_EVALUATION_REVISION_REQUIRED = "EXTERNAL_EVALUATION_REVISION_REQUIRED"
    SELECTIVE_EXTERNAL_REEVALUATION = "SELECTIVE_EXTERNAL_REEVALUATION"
    EXTERNAL_EVALUATION_PASSED = "EXTERNAL_EVALUATION_PASSED"
    FOR_IRB_REVIEW = "FOR_IRB_REVIEW"
    IRB_REVISION_REQUIRED = "IRB_REVISION_REQUIRED"
    PROPOSAL_APPROVED = "PROPOSAL_APPROVED"
    RESEARCH_IN_PROGRESS = "RESEARCH_IN_PROGRESS"
    FINAL_PAPER_DUE = "FINAL_PAPER_DUE"
    FINAL_PAPER_SUBMITTED = "FINAL_PAPER_SUBMITTED"
    FINAL_PAPER_TURNITIN = "FINAL_PAPER_TURNITIN"
    FINAL_PAPER_TURNITIN_REVISION_REQUIRED = "FINAL_PAPER_TURNITIN_REVISION_REQUIRED"
    FINAL_PAPER_TURNITIN_PASSED = "FINAL_PAPER_TURNITIN_PASSED"
    FINAL_BLIND_EVALUATION = "FINAL_BLIND_EVALUATION"
    FINAL_EVALUATION_REVISION_REQUIRED = "FINAL_EVALUATION_REVISION_REQUIRED"
    SELECTIVE_FINAL_REEVALUATION = "SELECTIVE_FINAL_REEVALUATION"
    FINAL_BLIND_EVALUATION_PASSED = "FINAL_BLIND_EVALUATION_PASSED"
    COMPLETED = "COMPLETED"
    READY_FOR_PRESENTATION = "READY_FOR_PRESENTATION"
    READY_FOR_PUBLICATION = "READY_FOR_PUBLICATION"
    ARCHIVED = "ARCHIVED"
    # Legacy aliases (for API backward compatibility)
    INITIAL_EVALUATION = "INITIAL_EVALUATION"
    INITIAL_EVALUATION_REVISION_REQUIRED = "INITIAL_EVALUATION_REVISION_REQUIRED"


class AuthorIn(BaseModel):
    name: str = Field(..., max_length=200)
    affiliation: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    contribution_pct: Optional[int] = Field(None, ge=0, le=100)
    is_lead: bool = False
    user_id: Optional[str] = None


class ResearchCreate(BaseModel):
    title: str = Field(..., max_length=500)
    lead_proponent_id: Optional[str] = None
    nature_of_research: Optional[str] = None
    target_journal: Optional[str] = None
    research_agenda: Optional[str] = None
    is_continuation: bool = False
    continuation_ref: Optional[str] = None
    mobile_number: Optional[str] = None
    institutional_email: Optional[str] = None
    academic_year_id: Optional[str] = None
    authors: list[AuthorIn] = []


class ResearchUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    nature_of_research: Optional[str] = None
    target_journal: Optional[str] = None
    research_agenda: Optional[str] = None
    is_continuation: Optional[bool] = None
    continuation_ref: Optional[str] = None
    mobile_number: Optional[str] = None
    institutional_email: Optional[str] = None


class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    contribution_pct: Optional[int] = None
    is_lead: bool = False


class ResearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tracking_number: str
    title: str
    lead_proponent_id: str
    lead_proponent_name: Optional[str] = None
    status: ResearchStatusEnum
    academic_year_id: Optional[str] = None
    nature_of_research: Optional[str] = None
    target_journal: Optional[str] = None
    research_agenda: Optional[str] = None
    is_continuation: bool = False
    continuation_ref: Optional[str] = None
    mobile_number: Optional[str] = None
    institutional_email: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    school_college_id: Optional[str] = None
    school_name: Optional[str] = None
    department_name: Optional[str] = None
    assigned_dean_id: Optional[str] = None
    assigned_dean_name: Optional[str] = None
    authors: list[AuthorResponse] = []


class ResearchListResponse(BaseModel):
    items: list[ResearchResponse]
    total: int
    page: int
    page_size: int


class StatusTransitionRequest(BaseModel):
    action: str = Field(..., description="Action name matching a valid workflow transition")
    remarks: Optional[str] = None
    document_version_id: Optional[str] = None


class StatusTransitionResponse(BaseModel):
    research_id: str
    prior_status: ResearchStatusEnum
    new_status: ResearchStatusEnum
    action: str
    message: str


# === Phase 3 Schemas ===

class InitialReviewCreate(BaseModel):
    remarks_researcher: Optional[str] = None
    remarks_internal: Optional[str] = None


class ChecklistItemUpdate(BaseModel):
    checklist_label: str
    status: Optional[str] = None  # COMPLIANT, NOT_COMPLIANT, NOT_APPLICABLE
    remarks: Optional[str] = None


class InitialReviewChecklistUpdate(BaseModel):
    items: list[ChecklistItemUpdate]


class InitialReviewDecision(BaseModel):
    remarks_researcher: Optional[str] = None
    remarks_internal: Optional[str] = None
    revision_instructions: Optional[str] = None


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    checklist_label: str
    status: Optional[str] = None
    remarks: Optional[str] = None


class InitialReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    research_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    decision: Optional[str] = None
    remarks_researcher: Optional[str] = None
    remarks_internal: Optional[str] = None
    revision_instructions: Optional[str] = None
    started_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    round_number: int = 1
    items: list[ChecklistItemResponse] = []


class TurnitinAttemptCreate(BaseModel):
    document_version_id: str
    similarity_score: float = Field(..., ge=0, le=100)
    result: str  # ACCEPTABLE or REVISION_REQUIRED
    report_file: Optional[str] = None
    remarks_researcher: Optional[str] = None
    remarks_internal: Optional[str] = None


class TurnitinAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    research_id: str
    document_version_id: str
    attempt_number: int
    similarity_score: Optional[float] = None
    threshold_at_decision: Optional[float] = None
    result: str
    report_file: Optional[str] = None
    remarks_researcher: Optional[str] = None
    remarks_internal: Optional[str] = None
    recorded_by: str
    recorded_by_name: Optional[str] = None
    recorded_at: Optional[datetime] = None


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    version_number: int
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    uploaded_by: str
    uploaded_by_name: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    workflow_stage: Optional[str] = None
    reason: Optional[str] = None
    is_active: bool = True


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    research_id: str
    document_type: str
    created_at: Optional[datetime] = None
    versions: list[DocumentVersionResponse] = []


class RevisionRequestCreate(BaseModel):
    findings: str
    revision_instructions: str
    internal_remarks: Optional[str] = None


class ResearcherRevisionSubmit(BaseModel):
    response_to_reviewer: Optional[str] = None


class Phase3DashboardResponse(BaseModel):
    awaiting_receipt: int = 0
    initial_review: int = 0
    revision_required: int = 0
    turnitin_pending: int = 0
    turnitin_revision: int = 0
    turnitin_passed: int = 0
    ready_for_external: int = 0
