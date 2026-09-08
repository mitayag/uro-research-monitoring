from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.database import get_db
from app.models.research import Research, ResearchAuthor, ResearchStatus, ResearchStatusHistory
from app.models.user import User, Role, UserRole
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


def _generate_tracking_number(db: Session) -> str:
    """Generate next tracking number: HAU-RES-YYYY-NNN"""
    current_year = datetime.now(timezone.utc).year
    prefix = f"HAU-RES-{current_year}-"
    last = (
        db.query(Research)
        .filter(Research.tracking_number.like(f"{prefix}%"))
        .order_by(Research.tracking_number.desc())
        .first()
    )
    if last:
        last_num = int(last.tracking_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:03d}"


def _get_user_name(db: Session, user_id: uuid.UUID) -> Optional[str]:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else None


def _to_response(db: Session, r: Research) -> ResearchResponse:
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
        remarks=data.remarks,
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
