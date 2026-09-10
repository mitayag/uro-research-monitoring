from fastapi import APIRouter, Depends, HTTPException, Query, status, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timezone
import uuid
import os
import json
import hashlib
import mimetypes
from pathlib import Path

from app.database import get_db
from app.config import get_settings
from app.models.research import Research, ResearchAuthor, ResearchStatus, ResearchStatusHistory
from app.models.user import User, Role, UserRole, SchoolCollege, DepartmentUnit, UserAffiliation
from app.models.document import ResearchDocument, ResearchDocumentVersion
from app.schemas.research import (
    ResearchCreate,
    ResearchUpdate,
    ResearchResponse,
    ResearchListResponse,
    AuthorResponse,
    StatusTransitionRequest,
    StatusTransitionResponse,
    ResearchStatusEnum,
)
from app.security.auth import get_current_user, get_current_user_roles, require_role
from app.services.workflow import (
    can_transition,
    get_target_status,
    get_valid_actions,
    can_user_perform_action,
)


router = APIRouter(prefix="/research", tags=["Research"])

settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _generate_tracking_number(db: Session) -> str:
    """Generate next tracking number: HAU-RES-YYYY-NNN"""
    current_year = datetime.now(timezone.utc).year
    prefix = f"HAU-RES-{current_year}-"
    last = (
        db.query(Research)
        .filter(Research.tracking_number.like(f"{prefix}%"))
        .all()
    )
    if last:
        max_num = max(int(r.tracking_number.split("-")[-1]) for r in last)
        next_num = max_num + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:03d}"


def _get_user_name(db: Session, user_id: uuid.UUID) -> Optional[str]:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else None


def _to_response(db: Session, r: Research) -> ResearchResponse:
    # Resolve lead proponent's department/school
    dept_name = None
    school_name = None
    dean_name = None
    if r.lead_proponent_id:
        aff = (
            db.query(UserAffiliation)
            .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
            .filter(UserAffiliation.user_id == r.lead_proponent_id, UserAffiliation.is_primary == True)
            .first()
        )
        if aff:
            dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == aff.department_unit_id).first()
            if dept:
                dept_name = dept.name
                school = db.query(SchoolCollege).filter(SchoolCollege.id == dept.school_college_id).first()
                if school:
                    school_name = school.name

    if r.assigned_dean_id:
        dean = db.query(User).filter(User.id == r.assigned_dean_id).first()
        if dean:
            dean_name = dean.full_name

    return ResearchResponse(
        id=str(r.id),
        tracking_number=r.tracking_number,
        title=r.title,
        lead_proponent_id=str(r.lead_proponent_id),
        lead_proponent_name=_get_user_name(db, r.lead_proponent_id),
        status=ResearchStatusEnum(r.status.value),
        academic_year_id=str(r.academic_year_id) if r.academic_year_id else None,
        nature_of_research=r.nature_of_research,
        target_journal=r.target_journal,
        research_agenda=r.research_agenda,
        is_continuation=r.is_continuation,
        continuation_ref=r.continuation_ref,
        mobile_number=r.mobile_number,
        institutional_email=r.institutional_email,
        created_by=str(r.created_by),
        created_at=r.created_at,
        updated_at=r.updated_at,
        submitted_at=r.submitted_at,
        completed_at=r.completed_at,
        school_college_id=str(r.school_college_id) if r.school_college_id else None,
        school_name=school_name,
        department_name=dept_name,
        assigned_dean_id=str(r.assigned_dean_id) if r.assigned_dean_id else None,
        assigned_dean_name=dean_name,
        authors=[
            AuthorResponse(
                id=str(a.id),
                name=a.name,
                affiliation=a.affiliation,
                email=a.email,
                contribution_pct=a.contribution_pct,
                is_lead=a.is_lead,
            )
            for a in r.authors
        ],
    )


@router.post("", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
def create_research(
    data: ResearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tracking_number = _generate_tracking_number(db)

    lead_id = uuid.UUID(data.lead_proponent_id) if data.lead_proponent_id else current_user.id
    academic_year_id = uuid.UUID(data.academic_year_id) if data.academic_year_id else None

    research = Research(
        id=uuid.uuid4(),
        tracking_number=tracking_number,
        title=data.title,
        lead_proponent_id=lead_id,
        status=ResearchStatus.DRAFT,
        academic_year_id=academic_year_id,
        nature_of_research=data.nature_of_research,
        target_journal=data.target_journal,
        research_agenda=data.research_agenda,
        is_continuation=data.is_continuation,
        continuation_ref=data.continuation_ref,
        mobile_number=data.mobile_number,
        institutional_email=data.institutional_email,
        created_by=current_user.id,
    )
    db.add(research)
    db.flush()

    # Add authors
    for author_data in data.authors:
        author = ResearchAuthor(
            id=uuid.uuid4(),
            research_id=research.id,
            user_id=uuid.UUID(author_data.user_id) if author_data.user_id else None,
            name=author_data.name,
            affiliation=author_data.affiliation,
            mobile_number=author_data.mobile_number,
            email=author_data.email,
            contribution_pct=author_data.contribution_pct,
            is_lead=author_data.is_lead,
        )
        db.add(author)

    db.commit()
    db.refresh(research)
    return _to_response(db, research)


def _validate_file(filename: str, file_size: int, content_type: str) -> None:
    """Validate uploaded file extension, MIME type, and size."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a PDF, DOCX, or DOC file.",
        )
    if file_size > MAX_FILE_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE_MB
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the maximum allowed size of {max_mb} MB.",
        )


def _store_file(file_content: bytes, original_filename: str, research_id: str) -> tuple[str, str]:
    """Store file with UUID name, preserve original filename. Returns (stored_filename, checksum)."""
    ext = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    research_dir = Path(settings.UPLOAD_DIR) / research_id
    research_dir.mkdir(parents=True, exist_ok=True)
    file_path = research_dir / stored_filename
    file_path.write_bytes(file_content)
    checksum = hashlib.sha256(file_content).hexdigest()
    return stored_filename, checksum


def _resolve_researcher_routing(db: Session, lead_proponent_id: uuid.UUID):
    """Resolve school_college_id and assigned_dean_id for a lead proponent."""
    aff = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(UserAffiliation.user_id == lead_proponent_id, UserAffiliation.is_primary == True)
        .first()
    )
    if not aff:
        return None, None
    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == aff.department_unit_id).first()
    if not dept:
        return None, None
    school = db.query(SchoolCollege).filter(SchoolCollege.id == dept.school_college_id).first()
    if not school:
        return dept.school_college_id, None
    return school.id, school.dean_user_id


@router.post("/create-with-document", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
async def create_research_with_document(
    title: str = Form(...),
    nature_of_research: Optional[str] = Form(None),
    research_agenda: Optional[str] = Form(None),
    target_journal: Optional[str] = Form(None),
    is_continuation: bool = Form(False),
    continuation_ref: Optional[str] = Form(None),
    mobile_number: Optional[str] = Form(None),
    institutional_email: Optional[str] = Form(None),
    authors_json: str = Form("[]"),
    proposal_document: Optional[UploadFile] = File(None),
    submit: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a research record and optionally upload the proposal document in a single request."""
    # Parse authors
    try:
        authors_data = json.loads(authors_json)
    except json.JSONDecodeError:
        authors_data = []

    # Validate title
    if not title.strip():
        raise HTTPException(status_code=400, detail="Research title is required")

    # Validate proposal document if provided
    if proposal_document and proposal_document.filename:
        file_content = await proposal_document.read()
        file_size = len(file_content)
        content_type = proposal_document.content_type or ""
        _validate_file(proposal_document.filename, file_size, content_type)

    # Create research record
    tracking_number = _generate_tracking_number(db)
    lead_id = current_user.id

    research = Research(
        id=uuid.uuid4(),
        tracking_number=tracking_number,
        title=title.strip(),
        lead_proponent_id=lead_id,
        status=ResearchStatus.DRAFT,
        nature_of_research=nature_of_research,
        target_journal=target_journal,
        research_agenda=research_agenda,
        is_continuation=is_continuation,
        continuation_ref=continuation_ref,
        mobile_number=mobile_number,
        institutional_email=institutional_email,
        created_by=current_user.id,
    )
    db.add(research)
    db.flush()

    # Add authors
    for author_data in authors_data:
        author = ResearchAuthor(
            id=uuid.uuid4(),
            research_id=research.id,
            user_id=uuid.UUID(author_data["user_id"]) if author_data.get("user_id") else None,
            name=author_data.get("name", ""),
            affiliation=author_data.get("affiliation"),
            mobile_number=author_data.get("mobile_number"),
            email=author_data.get("email"),
            contribution_pct=author_data.get("contribution_pct"),
            is_lead=author_data.get("is_lead", False),
        )
        db.add(author)

    db.flush()

    # Upload proposal document if provided
    if proposal_document and proposal_document.filename:
        stored_filename, checksum = _store_file(file_content, proposal_document.filename, str(research.id))

        # Create document record
        document = ResearchDocument(
            id=uuid.uuid4(),
            research_id=research.id,
            document_type="PROPOSAL",
        )
        db.add(document)
        db.flush()

        # Create version record
        version = ResearchDocumentVersion(
            id=uuid.uuid4(),
            document_id=document.id,
            version_number=1,
            original_filename=proposal_document.filename,
            stored_filename=stored_filename,
            mime_type=proposal_document.content_type or mimetypes.guess_type(proposal_document.filename)[0] or "application/octet-stream",
            file_size=file_size,
            uploaded_by=current_user.id,
            workflow_stage="DRAFT",
            checksum=checksum,
        )
        db.add(version)

    # Commit everything
    db.commit()
    db.refresh(research)

    # If submit flag is set, route to Dean endorsement
    if submit:
        # Resolve researcher's school and dean
        school_college_id, assigned_dean_id = _resolve_researcher_routing(db, lead_id)

        if not school_college_id:
            raise HTTPException(
                status_code=400,
                detail="Unable to submit research. Your academic department or school assignment is incomplete. Please contact the University Research Office or system administrator.",
            )
        if not assigned_dean_id:
            raise HTTPException(
                status_code=400,
                detail="Unable to route this submission for Dean endorsement because no Dean is currently assigned to your academic unit. Please contact the University Research Office.",
            )

        # Store routing on research
        research.school_college_id = school_college_id
        research.assigned_dean_id = assigned_dean_id
        research.status = ResearchStatus.FOR_DEAN_ENDORSEMENT
        research.submitted_at = datetime.now(timezone.utc)
        research.updated_at = datetime.now(timezone.utc)

        history = ResearchStatusHistory(
            id=uuid.uuid4(),
            research_id=research.id,
            prior_status=ResearchStatus.DRAFT,
            new_status=ResearchStatus.FOR_DEAN_ENDORSEMENT,
            action="SUBMIT",
            actor_id=current_user.id,
            actor_role="RESEARCHER",
            remarks="Routed to Dean endorsement",
        )
        db.add(history)
        db.commit()
        db.refresh(research)

    return _to_response(db, research)


@router.get("/{research_id}/documents", response_model=list)
def list_research_documents(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents for a research record."""
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    documents = db.query(ResearchDocument).filter(ResearchDocument.research_id == research.id).all()
    result = []
    for doc in documents:
        active_version = (
            db.query(ResearchDocumentVersion)
            .filter(
                ResearchDocumentVersion.document_id == doc.id,
                ResearchDocumentVersion.is_active == True,
            )
            .order_by(ResearchDocumentVersion.version_number.desc())
            .first()
        )
        result.append({
            "id": str(doc.id),
            "research_id": str(doc.research_id),
            "document_type": doc.document_type,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "active_version": {
                "id": str(active_version.id),
                "version_number": active_version.version_number,
                "original_filename": active_version.original_filename,
                "stored_filename": active_version.stored_filename,
                "mime_type": active_version.mime_type,
                "file_size": active_version.file_size,
                "uploaded_by": str(active_version.uploaded_by),
                "uploaded_at": active_version.uploaded_at.isoformat() if active_version.uploaded_at else None,
            } if active_version else None,
        })
    return result


@router.get("/{research_id}/documents/{document_id}/download")
def download_document(
    research_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the active version of a document."""
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Ownership check: researcher can only download own documents
    user_roles = [r.name for r in db.query(Role).join(UserRole).filter(UserRole.user_id == current_user.id).all()]
    if "RESEARCHER" in user_roles and "ADMIN" not in user_roles and "URO_DIRECTOR" not in user_roles:
        if research.lead_proponent_id != current_user.id and research.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to download this document")

    doc = db.query(ResearchDocument).filter(
        ResearchDocument.id == uuid.UUID(document_id),
        ResearchDocument.research_id == research.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    active_version = (
        db.query(ResearchDocumentVersion)
        .filter(
            ResearchDocumentVersion.document_id == doc.id,
            ResearchDocumentVersion.is_active == True,
        )
        .order_by(ResearchDocumentVersion.version_number.desc())
        .first()
    )
    if not active_version:
        raise HTTPException(status_code=404, detail="No active version found")

    file_path = Path(settings.UPLOAD_DIR) / research_id / active_version.stored_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=active_version.original_filename,
        media_type=active_version.mime_type,
    )


@router.get("", response_model=ResearchListResponse)
def list_research(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ResearchStatusEnum] = None,
    search: Optional[str] = None,
    academic_year_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Research).options(joinedload(Research.authors))

    # Role-based filtering: researchers only see their own
    user_roles = [r.name for r in db.query(Role).join(UserRole).filter(UserRole.user_id == current_user.id).all()]
    if "RESEARCHER" in user_roles and "ADMIN" not in user_roles and "URO_DIRECTOR" not in user_roles:
        query = query.filter(
            or_(
                Research.lead_proponent_id == current_user.id,
                Research.created_by == current_user.id,
            )
        )

    if status_filter:
        query = query.filter(Research.status == ResearchStatus(status_filter.value))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Research.title.ilike(search_term),
                Research.tracking_number.ilike(search_term),
            )
        )

    if academic_year_id:
        query = query.filter(Research.academic_year_id == uuid.UUID(academic_year_id))

    total = query.count()
    items = (
        query.order_by(Research.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ResearchListResponse(
        items=[_to_response(db, r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{research_id}", response_model=ResearchResponse)
def get_research(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).options(joinedload(Research.authors)).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    return _to_response(db, research)


@router.patch("/{research_id}", response_model=ResearchResponse)
def update_research(
    research_id: str,
    data: ResearchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Only lead proponent or admin can update
    user_roles = [r.name for r in db.query(Role).join(UserRole).filter(UserRole.user_id == current_user.id).all()]
    if research.lead_proponent_id != current_user.id and "ADMIN" not in user_roles:
        raise HTTPException(status_code=403, detail="Not authorized to update this research")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(research, field, value)

    research.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(research)
    return _to_response(db, research)


@router.post("/{research_id}/transition", response_model=StatusTransitionResponse)
def transition_status(
    research_id: str,
    data: StatusTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Check action is valid from current status
    if not can_transition(research.status, data.action):
        valid = get_valid_actions(research.status)
        raise HTTPException(
            status_code=400,
            detail=f"Action '{data.action}' not valid from status '{research.status.value}'. Valid actions: {valid}",
        )

    # Check user role permission
    if not can_user_perform_action(roles, data.action):
        raise HTTPException(
            status_code=403,
            detail=f"Your roles {roles} are not authorized for action '{data.action}'",
        )

    prior_status = research.status
    new_status = get_target_status(research.status, data.action)

    research.status = new_status
    research.updated_at = datetime.now(timezone.utc)

    # Set timestamps
    if new_status == ResearchStatus.SUBMITTED and not research.submitted_at:
        research.submitted_at = datetime.now(timezone.utc)
    if new_status == ResearchStatus.COMPLETED and not research.completed_at:
        research.completed_at = datetime.now(timezone.utc)

    # Auto-route to Dean endorsement on SUBMIT (skip SUBMITTED state)
    if new_status == ResearchStatus.SUBMITTED:
        school_college_id, assigned_dean_id = _resolve_researcher_routing(db, research.lead_proponent_id)
        if school_college_id and assigned_dean_id:
            research.school_college_id = school_college_id
            research.assigned_dean_id = assigned_dean_id
            new_status = ResearchStatus.FOR_DEAN_ENDORSEMENT
            research.status = new_status
            # Update history to reflect actual final status
            history_remarks = data.remarks or "Routed to Dean endorsement"
        else:
            history_remarks = data.remarks
            if not school_college_id:
                raise HTTPException(status_code=400, detail="Unable to submit: academic affiliation incomplete. Contact URO.")
            if not assigned_dean_id:
                raise HTTPException(status_code=400, detail="Unable to route: no Dean assigned to your school. Contact URO.")
    else:
        history_remarks = data.remarks

    # Record history
    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior_status,
        new_status=new_status,
        action=data.action,
        actor_id=current_user.id,
        actor_role=roles[0] if roles else "UNKNOWN",
        document_version_id=uuid.UUID(data.document_version_id) if data.document_version_id else None,
        remarks=history_remarks,
    )
    db.add(history)
    db.commit()

    return StatusTransitionResponse(
        research_id=str(research.id),
        prior_status=ResearchStatusEnum(prior_status.value),
        new_status=ResearchStatusEnum(new_status.value),
        action=data.action,
        message=f"Status transitioned from {prior_status.value} to {new_status.value}",
    )


@router.get("/{research_id}/valid-actions")
def get_valid_actions_for_research(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    all_actions = get_valid_actions(research.status)
    permitted = [a for a in all_actions if can_user_perform_action(roles, a)]

    return {
        "research_id": str(research.id),
        "current_status": research.status.value,
        "all_actions": all_actions,
        "permitted_actions": permitted,
    }


@router.get("/{research_id}/history")
def get_research_history(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    history = (
        db.query(ResearchStatusHistory)
        .filter(ResearchStatusHistory.research_id == research.id)
        .order_by(ResearchStatusHistory.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(h.id),
            "prior_status": h.prior_status.value if h.prior_status else None,
            "new_status": h.new_status.value,
            "action": h.action,
            "actor_id": str(h.actor_id),
            "actor_role": h.actor_role,
            "remarks": h.remarks,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]


@router.get("/stats/summary")
def get_research_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(func.count(Research.id)).scalar()
    by_status = (
        db.query(Research.status, func.count(Research.id))
        .group_by(Research.status)
        .all()
    )
    return {
        "total": total,
        "by_status": {s.value: c for s, c in by_status},
    }


@router.get("/stats/researcher")
def get_researcher_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get dashboard stats for the logged-in researcher (own records only)."""
    user_roles = [r.name for r in db.query(Role).join(UserRole).filter(UserRole.user_id == current_user.id).all()]
    is_pure_researcher = "RESEARCHER" in user_roles and not any(r in user_roles for r in ["ADMIN", "URO_DIRECTOR", "URO_STAFF"])

    if is_pure_researcher:
        query = db.query(Research).filter(
            or_(
                Research.lead_proponent_id == current_user.id,
                Research.created_by == current_user.id,
            )
        )
    else:
        query = db.query(Research)

    total = query.count()
    by_status = (
        query.with_entities(Research.status, func.count(Research.id))
        .group_by(Research.status)
        .all()
    )

    status_counts = {s.value: c for s, c in by_status}
    active = sum(c for s, c in by_status if s.value not in ["DRAFT", "COMPLETED", "ARCHIVED"])
    drafts = status_counts.get("DRAFT", 0)
    completed = status_counts.get("COMPLETED", 0)

    # Action required: statuses that need researcher action
    action_required_statuses = [
        "INITIAL_REVISION_REQUIRED",
        "PROPOSAL_TURNITIN_REVISION_REQUIRED",
        "EXTERNAL_EVALUATION_REVISION_REQUIRED",
        "IRB_REVISION_REQUIRED",
        "FINAL_PAPER_TURNITIN_REVISION_REQUIRED",
        "FINAL_EVALUATION_REVISION_REQUIRED",
    ]
    action_required = sum(status_counts.get(s, 0) for s in action_required_statuses)

    return {
        "total": total,
        "active": active,
        "drafts": drafts,
        "completed": completed,
        "action_required": action_required,
        "by_status": status_counts,
    }


@router.get("/actions")
def get_researcher_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get action-required items for the logged-in researcher."""
    user_roles = [r.name for r in db.query(Role).join(UserRole).filter(UserRole.user_id == current_user.id).all()]
    is_pure_researcher = "RESEARCHER" in user_roles and not any(r in user_roles for r in ["ADMIN", "URO_DIRECTOR", "URO_STAFF"])

    action_required_statuses = [
        ResearchStatus.INITIAL_REVISION_REQUIRED,
        ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED,
        ResearchStatus.EXTERNAL_EVALUATION_REVISION_REQUIRED,
        ResearchStatus.IRB_REVISION_REQUIRED,
        ResearchStatus.FINAL_PAPER_TURNITIN_REVISION_REQUIRED,
        ResearchStatus.FINAL_EVALUATION_REVISION_REQUIRED,
    ]

    query = db.query(Research).options(joinedload(Research.authors)).filter(
        Research.status.in_(action_required_statuses)
    )

    if is_pure_researcher:
        query = query.filter(
            or_(
                Research.lead_proponent_id == current_user.id,
                Research.created_by == current_user.id,
            )
        )

    items = query.order_by(Research.updated_at.desc()).all()

    return [
        {
            "id": str(r.id),
            "tracking_number": r.tracking_number,
            "title": r.title,
            "status": r.status.value,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "action_required": r.status.value.replace("_REVISION_REQUIRED", "").replace("_", " ").title(),
        }
        for r in items
    ]


@router.get("/activity")
def get_researcher_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page_size: int = Query(10, ge=1, le=50),
):
    """Get recent activity for the logged-in researcher."""
    user_roles = [r.name for r in db.query(Role).join(UserRole).filter(UserRole.user_id == current_user.id).all()]
    is_pure_researcher = "RESEARCHER" in user_roles and not any(r in user_roles for r in ["ADMIN", "URO_DIRECTOR", "URO_STAFF"])

    query = db.query(ResearchStatusHistory).join(Research)

    if is_pure_researcher:
        query = query.filter(
            or_(
                Research.lead_proponent_id == current_user.id,
                Research.created_by == current_user.id,
            )
        )

    history = query.order_by(ResearchStatusHistory.created_at.desc()).limit(page_size).all()

    return [
        {
            "id": str(h.id),
            "research_id": str(h.research_id),
            "action": h.action,
            "new_status": h.new_status.value,
            "prior_status": h.prior_status.value if h.prior_status else None,
            "remarks": h.remarks,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]
