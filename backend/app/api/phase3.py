"""
Phase 3 API: URO Receipt, Initial Review, Proposal Turnitin.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.research import Research, ResearchStatus, ResearchStatusHistory
from app.models.document import ResearchDocument, ResearchDocumentVersion
from app.models.initial_review import InitialReview, InitialReviewItem, ReviewDecision, ChecklistItemStatus
from app.models.turnitin import SimilarityCheckAttempt, TurnitinStage, TurnitinResult
from app.models.notification import Notification
from app.models.audit import AuditEvent
from app.models.user import User, UserRole, Role
from app.models.settings import SystemSetting
from app.schemas.research import (
    InitialReviewCreate,
    InitialReviewResponse,
    ChecklistItemResponse,
    InitialReviewDecision,
    InitialReviewChecklistUpdate,
    TurnitinAttemptCreate,
    TurnitinAttemptResponse,
    DocumentResponse,
    DocumentVersionResponse,
    ResearchStatusEnum,
)
from app.security.auth import get_current_user, get_current_user_roles
from app.services.workflow import (
    can_transition,
    get_target_status,
    get_valid_actions,
    can_user_perform_action,
)

router = APIRouter(prefix="/research", tags=["Phase 3 — Initial Review & Turnitin"])


def _get_user_name(db: Session, user_id: uuid.UUID) -> Optional[str]:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else None


def _get_threshold(db: Session) -> float:
    setting = db.query(SystemSetting).filter(SystemSetting.key == "turnitin_proposal_threshold").first()
    return float(setting.value) if setting else 15.0


def _record_audit(db: Session, research_id: uuid.UUID, event_type: str, actor: User, roles: list[str], details: dict = None):
    audit = AuditEvent(
        id=uuid.uuid4(),
        research_id=research_id,
        event_type=event_type,
        actor_id=actor.id,
        actor_role=roles[0] if roles else "UNKNOWN",
        details=details or {},
    )
    db.add(audit)


def _create_notification(db: Session, user_id: uuid.UUID, research_id: uuid.UUID, notif_type: str, title: str, message: str):
    notif = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        research_id=research_id,
        type=notif_type,
        title=title,
        message=message,
    )
    db.add(notif)


# ============================================================
# URO RECEIPT
# ============================================================

@router.post("/{research_id}/receive")
def receive_submission(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "RECEIVE_BY_URO"):
        raise HTTPException(status_code=400, detail=f"Cannot receive: current status is {research.status.value}")

    if not can_user_perform_action(roles, "RECEIVE_BY_URO"):
        raise HTTPException(status_code=403, detail="Not authorized to receive submissions")

    prior = research.status
    research.status = ResearchStatus.URO_RECEIVED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.URO_RECEIVED,
        action="RECEIVE_BY_URO",
        actor_id=current_user.id,
        actor_role=roles[0],
    )
    db.add(history)
    _record_audit(db, research.id, "URO_RECEIVED", current_user, roles, {
        "received_by": str(current_user.id),
        "received_at": datetime.now(timezone.utc).isoformat(),
    })

    # Notify lead proponent
    _create_notification(
        db, research.lead_proponent_id, research.id,
        "URO_RECEIVED",
        "Submission Received by URO",
        f"Your research application \"{research.title}\" has been received by URO and is being processed.",
    )

    db.commit()
    return {"message": "Submission received by URO", "status": "URO_RECEIVED"}


# ============================================================
# INITIAL REVIEW
# ============================================================

@router.post("/{research_id}/initial-review")
def start_initial_review(
    research_id: str,
    body: InitialReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "BEGIN_INITIAL_REVIEW"):
        raise HTTPException(status_code=400, detail=f"Cannot start review: current status is {research.status.value}")

    if not can_user_perform_action(roles, "BEGIN_INITIAL_REVIEW"):
        raise HTTPException(status_code=403, detail="Not authorized to start initial review")

    # Determine round number
    existing = db.query(InitialReview).filter(InitialReview.research_id == research.id).count()

    prior = research.status
    research.status = ResearchStatus.INITIAL_REVIEW
    research.updated_at = datetime.now(timezone.utc)

    review = InitialReview(
        id=uuid.uuid4(),
        research_id=research.id,
        reviewer_id=current_user.id,
        round_number=existing + 1,
    )
    db.add(review)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.INITIAL_REVIEW,
        action="BEGIN_INITIAL_REVIEW",
        actor_id=current_user.id,
        actor_role=roles[0],
    )
    db.add(history)
    _record_audit(db, research.id, "INITIAL_REVIEW_STARTED", current_user, roles, {"round": existing + 1})

    db.commit()
    db.refresh(review)

    return {
        "id": str(review.id),
        "research_id": str(research.id),
        "round_number": review.round_number,
        "message": "Initial review started",
    }


@router.get("/{research_id}/initial-review")
def get_current_initial_review(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    review = (
        db.query(InitialReview)
        .filter(InitialReview.research_id == research.id)
        .order_by(InitialReview.round_number.desc())
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="No initial review found")

    items = (
        db.query(InitialReviewItem)
        .filter(InitialReviewItem.review_id == review.id)
        .order_by(InitialReviewItem.created_at)
        .all()
    )

    return InitialReviewResponse(
        id=str(review.id),
        research_id=str(review.research_id),
        reviewer_id=str(review.reviewer_id),
        reviewer_name=_get_user_name(db, review.reviewer_id),
        decision=review.decision.value if review.decision else None,
        remarks_researcher=review.remarks_researcher,
        remarks_internal=review.remarks_internal,
        revision_instructions=review.revision_instructions,
        started_at=review.started_at,
        decided_at=review.decided_at,
        round_number=review.round_number,
        items=[
            ChecklistItemResponse(
                id=str(item.id),
                checklist_label=item.checklist_label,
                status=item.status.value if item.status else None,
                remarks=item.remarks,
            )
            for item in items
        ],
    )


@router.patch("/{research_id}/initial-review/checklist")
def update_checklist(
    research_id: str,
    body: InitialReviewChecklistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    review = (
        db.query(InitialReview)
        .filter(InitialReview.research_id == research.id, InitialReview.decision.is_(None))
        .order_by(InitialReview.round_number.desc())
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="No active review found")

    # Clear existing items
    db.query(InitialReviewItem).filter(InitialReviewItem.review_id == review.id).delete()

    for item_data in body.items:
        status_val = ChecklistItemStatus(item_data.status) if item_data.status else None
        item = InitialReviewItem(
            id=uuid.uuid4(),
            review_id=review.id,
            checklist_label=item_data.checklist_label,
            status=status_val,
            remarks=item_data.remarks,
        )
        db.add(item)

    db.commit()
    return {"message": "Checklist updated"}


@router.post("/{research_id}/initial-review/pass")
def pass_initial_review(
    research_id: str,
    body: InitialReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "INITIAL_REVIEW_PASS"):
        raise HTTPException(status_code=400, detail=f"Cannot pass review: current status is {research.status.value}")

    if not can_user_perform_action(roles, "INITIAL_REVIEW_PASS"):
        raise HTTPException(status_code=403, detail="Not authorized to pass initial review")

    review = (
        db.query(InitialReview)
        .filter(InitialReview.research_id == research.id, InitialReview.decision.is_(None))
        .order_by(InitialReview.round_number.desc())
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="No active review found")

    review.decision = ReviewDecision.PASS
    review.remarks_researcher = body.remarks_researcher
    review.remarks_internal = body.remarks_internal
    review.decided_at = datetime.now(timezone.utc)

    prior = research.status
    research.status = ResearchStatus.INITIAL_REVIEW_PASSED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.INITIAL_REVIEW_PASSED,
        action="INITIAL_REVIEW_PASS",
        actor_id=current_user.id,
        actor_role=roles[0],
    )
    db.add(history)
    _record_audit(db, research.id, "INITIAL_REVIEW_PASSED", current_user, roles, {"round": review.round_number})

    _create_notification(
        db, research.lead_proponent_id, research.id,
        "INITIAL_REVIEW_PASSED",
        "Initial Review Passed",
        f"Your research application \"{research.title}\" has passed the initial review.",
    )

    db.commit()
    return {"message": "Initial review passed", "status": "INITIAL_REVIEW_PASSED"}


@router.post("/{research_id}/initial-review/revision")
def request_initial_review_revision(
    research_id: str,
    body: InitialReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "INITIAL_REVIEW_REVISION"):
        raise HTTPException(status_code=400, detail=f"Cannot request revision: current status is {research.status.value}")

    if not can_user_perform_action(roles, "INITIAL_REVIEW_REVISION"):
        raise HTTPException(status_code=403, detail="Not authorized to request revision")

    review = (
        db.query(InitialReview)
        .filter(InitialReview.research_id == research.id, InitialReview.decision.is_(None))
        .order_by(InitialReview.round_number.desc())
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="No active review found")

    review.decision = ReviewDecision.REVISION_REQUIRED
    review.remarks_researcher = body.remarks_researcher
    review.remarks_internal = body.remarks_internal
    review.revision_instructions = body.revision_instructions
    review.decided_at = datetime.now(timezone.utc)

    prior = research.status
    research.status = ResearchStatus.INITIAL_REVISION_REQUIRED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.INITIAL_REVISION_REQUIRED,
        action="INITIAL_REVIEW_REVISION",
        actor_id=current_user.id,
        actor_role=roles[0],
        remarks=body.remarks_researcher,
    )
    db.add(history)
    _record_audit(db, research.id, "INITIAL_REVIEW_REVISION_REQUESTED", current_user, roles, {"round": review.round_number})

    _create_notification(
        db, research.lead_proponent_id, research.id,
        "INITIAL_REVISION_REQUIRED",
        "Revision Required — Initial Review",
        f"Your research application \"{research.title}\" requires revision after initial review. Please review the findings and submit a revised proposal.",
    )

    db.commit()
    return {"message": "Revision required", "status": "INITIAL_REVISION_REQUIRED"}


@router.post("/{research_id}/initial-review/resubmit")
def resubmit_initial_review(
    research_id: str,
    body: InitialReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "RESUBMIT_INITIAL_REVISION"):
        raise HTTPException(status_code=400, detail=f"Cannot resubmit: current status is {research.status.value}")

    if not can_user_perform_action(roles, "RESUBMIT_INITIAL_REVISION"):
        raise HTTPException(status_code=403, detail="Not authorized to resubmit")

    prior = research.status
    research.status = ResearchStatus.INITIAL_REVISION_SUBMITTED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.INITIAL_REVISION_SUBMITTED,
        action="RESUBMIT_INITIAL_REVISION",
        actor_id=current_user.id,
        actor_role=roles[0],
        remarks=body.remarks_researcher,
    )
    db.add(history)
    _record_audit(db, research.id, "INITIAL_REVIEW_RESUBMITTED", current_user, roles)

    # Notify URO
    db.commit()
    return {"message": "Revision resubmitted", "status": "INITIAL_REVISION_SUBMITTED"}


# ============================================================
# PROPOSAL TURNITIN
# ============================================================

@router.post("/{research_id}/turnitin")
def create_turnitin_attempt(
    research_id: str,
    body: TurnitinAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_user_perform_action(roles, "BEGIN_PROPOSAL_TURNITIN"):
        raise HTTPException(status_code=403, detail="Not authorized to create Turnitin attempt")

    # Validate document version exists
    doc_version = db.query(ResearchDocumentVersion).filter(
        ResearchDocumentVersion.id == uuid.UUID(body.document_version_id)
    ).first()
    if not doc_version:
        raise HTTPException(status_code=404, detail="Document version not found")

    # Get threshold at time of check
    threshold = _get_threshold(db)

    # Determine attempt number
    existing = db.query(SimilarityCheckAttempt).filter(
        SimilarityCheckAttempt.research_id == research.id,
        SimilarityCheckAttempt.stage == TurnitinStage.PROPOSAL,
    ).count()

    result_enum = TurnitinResult.ACCEPTABLE if body.result == "ACCEPTABLE" else TurnitinResult.REVISION_REQUIRED

    attempt = SimilarityCheckAttempt(
        id=uuid.uuid4(),
        research_id=research.id,
        document_version_id=doc_version.id,
        stage=TurnitinStage.PROPOSAL,
        attempt_number=existing + 1,
        similarity_score=body.similarity_score,
        threshold_at_decision=threshold,
        result=result_enum,
        report_file=body.report_file,
        remarks_researcher=body.remarks_researcher,
        remarks_internal=body.remarks_internal,
        recorded_by=current_user.id,
    )
    db.add(attempt)

    _record_audit(db, research.id, "TURNITIN_RESULT_RECORDED", current_user, roles, {
        "attempt_number": existing + 1,
        "similarity_score": body.similarity_score,
        "result": body.result,
        "threshold": threshold,
    })

    db.commit()
    db.refresh(attempt)

    return TurnitinAttemptResponse(
        id=str(attempt.id),
        research_id=str(attempt.research_id),
        document_version_id=str(attempt.document_version_id),
        attempt_number=attempt.attempt_number,
        similarity_score=attempt.similarity_score,
        threshold_at_decision=attempt.threshold_at_decision,
        result=attempt.result.value,
        report_file=attempt.report_file,
        remarks_researcher=attempt.remarks_researcher,
        remarks_internal=attempt.remarks_internal,
        recorded_by=str(attempt.recorded_by),
        recorded_by_name=_get_user_name(db, attempt.recorded_by),
        recorded_at=attempt.recorded_at,
    )


@router.get("/{research_id}/turnitin")
def get_turnitin_attempts(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    attempts = (
        db.query(SimilarityCheckAttempt)
        .filter(
            SimilarityCheckAttempt.research_id == research.id,
            SimilarityCheckAttempt.stage == TurnitinStage.PROPOSAL,
        )
        .order_by(SimilarityCheckAttempt.attempt_number)
        .all()
    )

    return [
        TurnitinAttemptResponse(
            id=str(a.id),
            research_id=str(a.research_id),
            document_version_id=str(a.document_version_id),
            attempt_number=a.attempt_number,
            similarity_score=a.similarity_score,
            threshold_at_decision=a.threshold_at_decision,
            result=a.result.value,
            report_file=a.report_file,
            remarks_researcher=a.remarks_researcher,
            remarks_internal=a.remarks_internal,
            recorded_by=str(a.recorded_by),
            recorded_by_name=_get_user_name(db, a.recorded_by),
            recorded_at=a.recorded_at,
        )
        for a in attempts
    ]


@router.post("/{research_id}/turnitin/revision")
def request_turnitin_revision(
    research_id: str,
    body: InitialReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "TURNITIN_REVISION"):
        raise HTTPException(status_code=400, detail=f"Cannot request Turnitin revision: current status is {research.status.value}")

    if not can_user_perform_action(roles, "TURNITIN_REVISION"):
        raise HTTPException(status_code=403, detail="Not authorized")

    prior = research.status
    research.status = ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED,
        action="TURNITIN_REVISION",
        actor_id=current_user.id,
        actor_role=roles[0],
        remarks=body.remarks_researcher,
    )
    db.add(history)
    _record_audit(db, research.id, "TURNITIN_REVISION_REQUESTED", current_user, roles)

    _create_notification(
        db, research.lead_proponent_id, research.id,
        "TURNITIN_REVISION_REQUIRED",
        "Proposal Turnitin — Revision Required",
        f"Your proposal for \"{research.title}\" requires revision following Turnitin checking.",
    )

    db.commit()
    return {"message": "Turnitin revision required", "status": "PROPOSAL_TURNITIN_REVISION_REQUIRED"}


@router.post("/{research_id}/turnitin/resubmit")
def resubmit_turnitin(
    research_id: str,
    body: InitialReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "RESUBMIT_TURNITIN_REVISION"):
        raise HTTPException(status_code=400, detail=f"Cannot resubmit: current status is {research.status.value}")

    if not can_user_perform_action(roles, "RESUBMIT_TURNITIN_REVISION"):
        raise HTTPException(status_code=403, detail="Not authorized")

    prior = research.status
    research.status = ResearchStatus.PROPOSAL_TURNITIN_RESUBMITTED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.PROPOSAL_TURNITIN_RESUBMITTED,
        action="RESUBMIT_TURNITIN_REVISION",
        actor_id=current_user.id,
        actor_role=roles[0],
    )
    db.add(history)
    _record_audit(db, research.id, "TURNITIN_REVISION_SUBMITTED", current_user, roles)

    db.commit()
    return {"message": "Turnitin revision resubmitted", "status": "PROPOSAL_TURNITIN_RESUBMITTED"}


@router.post("/{research_id}/turnitin/pass")
def pass_turnitin(
    research_id: str,
    body: InitialReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    if not can_transition(research.status, "TURNITIN_PASSED"):
        raise HTTPException(status_code=400, detail=f"Cannot pass Turnitin: current status is {research.status.value}")

    if not can_user_perform_action(roles, "TURNITIN_PASSED"):
        raise HTTPException(status_code=403, detail="Not authorized to pass Turnitin")

    prior = research.status
    research.status = ResearchStatus.PROPOSAL_TURNITIN_PASSED
    research.updated_at = datetime.now(timezone.utc)

    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior,
        new_status=ResearchStatus.PROPOSAL_TURNITIN_PASSED,
        action="TURNITIN_PASSED",
        actor_id=current_user.id,
        actor_role=roles[0],
    )
    db.add(history)
    _record_audit(db, research.id, "TURNITIN_PASSED", current_user, roles)

    _create_notification(
        db, research.lead_proponent_id, research.id,
        "TURNITIN_PASSED",
        "Proposal Turnitin Approved",
        f"Your proposal Turnitin check for \"{research.title}\" has been approved.",
    )

    db.commit()
    return {"message": "Turnitin passed", "status": "PROPOSAL_TURNITIN_PASSED"}


# ============================================================
# DOCUMENT MANAGEMENT
# ============================================================

@router.post("/{research_id}/documents")
def upload_document(
    research_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("Research Proposal"),
    reason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Find or create document record
    doc = db.query(ResearchDocument).filter(
        ResearchDocument.research_id == research.id,
        ResearchDocument.document_type == document_type,
    ).first()

    if not doc:
        doc = ResearchDocument(
            id=uuid.uuid4(),
            research_id=research.id,
            document_type=document_type,
        )
        db.add(doc)
        db.flush()

    # Determine next version number
    last_version = (
        db.query(ResearchDocumentVersion)
        .filter(ResearchDocumentVersion.document_id == doc.id)
        .order_by(ResearchDocumentVersion.version_number.desc())
        .first()
    )
    next_version = (last_version.version_number + 1) if last_version else 1

    # Save file
    import os, hashlib
    upload_dir = os.path.join("/data/uploads", str(research.id))
    os.makedirs(upload_dir, exist_ok=True)

    content = file.file.read()
    checksum = hashlib.sha256(content).hexdigest()
    stored_name = f"{document_type.lower().replace(' ', '_')}_v{next_version}_{checksum[:12]}_{file.filename}"
    file_path = os.path.join(upload_dir, stored_name)

    with open(file_path, "wb") as f:
        f.write(content)

    version = ResearchDocumentVersion(
        id=uuid.uuid4(),
        document_id=doc.id,
        version_number=next_version,
        original_filename=file.filename,
        stored_filename=stored_name,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        uploaded_by=current_user.id,
        workflow_stage=research.status.value,
        reason=reason,
        checksum=checksum,
        is_active=True,
    )
    db.add(version)

    _record_audit(db, research.id, "DOCUMENT_UPLOADED", current_user, [], {
        "document_type": document_type,
        "version": next_version,
        "filename": file.filename,
    })

    db.commit()
    db.refresh(version)

    return {
        "document_id": str(doc.id),
        "version_id": str(version.id),
        "version_number": version.version_number,
        "filename": file.filename,
        "message": f"Document uploaded as version {next_version}",
    }


@router.get("/{research_id}/documents")
def list_documents(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    docs = (
        db.query(ResearchDocument)
        .filter(ResearchDocument.research_id == research.id)
        .all()
    )

    result = []
    for doc in docs:
        versions = (
            db.query(ResearchDocumentVersion)
            .filter(ResearchDocumentVersion.document_id == doc.id)
            .order_by(ResearchDocumentVersion.version_number.desc())
            .all()
        )
        result.append(DocumentResponse(
            id=str(doc.id),
            research_id=str(doc.research_id),
            document_type=doc.document_type,
            created_at=doc.created_at,
            versions=[
                DocumentVersionResponse(
                    id=str(v.id),
                    document_id=str(v.document_id),
                    version_number=v.version_number,
                    original_filename=v.original_filename,
                    stored_filename=v.stored_filename,
                    mime_type=v.mime_type,
                    file_size=v.file_size,
                    uploaded_by=str(v.uploaded_by),
                    uploaded_by_name=_get_user_name(db, v.uploaded_by),
                    uploaded_at=v.uploaded_at,
                    workflow_stage=v.workflow_stage,
                    reason=v.reason,
                    is_active=v.is_active,
                )
                for v in versions
            ],
        ))

    return result


# ============================================================
# DASHBOARD COUNTERS
# ============================================================

@router.get("/phase3/dashboard")
def get_phase3_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func

    counts = dict(
        db.query(Research.status, func.count(Research.id))
        .group_by(Research.status)
        .all()
    )

    return {
        "awaiting_receipt": counts.get(ResearchStatus.ENDORSED_TO_URO, 0),
        "initial_review": counts.get(ResearchStatus.INITIAL_REVIEW, 0),
        "revision_required": counts.get(ResearchStatus.INITIAL_REVISION_REQUIRED, 0),
        "turnitin_pending": counts.get(ResearchStatus.PROPOSAL_TURNITIN, 0) + counts.get(ResearchStatus.PROPOSAL_TURNITIN_RESUBMITTED, 0),
        "turnitin_revision": counts.get(ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED, 0),
        "turnitin_passed": counts.get(ResearchStatus.PROPOSAL_TURNITIN_PASSED, 0),
        "ready_for_external": counts.get(ResearchStatus.READY_FOR_EXTERNAL_EVALUATION, 0),
    }


# ============================================================
# THRESHOLD CONFIGURATION
# ============================================================

@router.get("/settings/turnitin-threshold")
def get_turnitin_threshold(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "turnitin_proposal_threshold").first()
    return {
        "threshold": float(setting.value) if setting else 15.0,
        "description": setting.description if setting else "Proposal Turnitin similarity threshold (%)",
    }


@router.put("/settings/turnitin-threshold")
def update_turnitin_threshold(
    threshold: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    if "ADMIN" not in roles and "URO_DIRECTOR" not in roles:
        raise HTTPException(status_code=403, detail="Only administrators or URO Director can change threshold")

    if threshold < 0 or threshold > 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")

    setting = db.query(SystemSetting).filter(SystemSetting.key == "turnitin_proposal_threshold").first()
    if setting:
        old_value = setting.value
        setting.value = str(threshold)
        setting.updated_by = current_user.id
        setting.updated_at = datetime.now(timezone.utc)
    else:
        old_value = "15.0"
        setting = SystemSetting(
            id=uuid.uuid4(),
            key="turnitin_proposal_threshold",
            value=str(threshold),
            description="Proposal Turnitin similarity threshold (%)",
            updated_by=current_user.id,
        )
        db.add(setting)

    _record_audit(db, None, "TURNITIN_THRESHOLD_CHANGED", current_user, roles, {
        "old_threshold": old_value,
        "new_threshold": str(threshold),
    })

    db.commit()
    return {"threshold": threshold, "message": f"Threshold updated from {old_value}%"}
