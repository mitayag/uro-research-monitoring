from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.database import get_db
from app.models.research import Research, ResearchAuthor, ResearchStatus, ResearchStatusHistory
from app.models.user import User, Role, UserRole, UserAffiliation, DepartmentUnit, SchoolCollege
from app.models.document import ResearchDocument, ResearchDocumentVersion
from app.schemas.research import (
    ResearchResponse,
    ResearchListResponse,
    AuthorResponse,
    StatusTransitionRequest,
    StatusTransitionResponse,
    ResearchStatusEnum,
)
from app.security.auth import get_current_user, get_current_user_roles, hash_password
from app.services.workflow import (
    can_transition,
    get_target_status,
    get_valid_actions,
    can_user_perform_action,
)


router = APIRouter(prefix="/dean", tags=["Dean Module"])


class DeanActionRequest(BaseModel):
    remarks: Optional[str] = None


def _get_user_name(db: Session, user_id: uuid.UUID) -> Optional[str]:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else None


def _get_dean_school_scope(db: Session, user_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Get the school/college ID that the Dean is affiliated with."""
    affiliation = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(
            UserAffiliation.user_id == user_id,
            UserAffiliation.is_primary == True,
        )
        .first()
    )
    if affiliation:
        dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == affiliation.department_unit_id).first()
        if dept:
            return dept.school_college_id
    return None


def _get_dean_school_name(db: Session, user_id: uuid.UUID) -> Optional[str]:
    """Get the school/college name that the Dean is affiliated with."""
    school_id = _get_dean_school_scope(db, user_id)
    if school_id:
        school = db.query(SchoolCollege).filter(SchoolCollege.id == school_id).first()
        return school.name if school else None
    return None


def _get_researcher_school_id(db: Session, user_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Get the school/college ID for a researcher based on their affiliation."""
    affiliation = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(
            UserAffiliation.user_id == user_id,
            UserAffiliation.is_primary == True,
        )
        .first()
    )
    if affiliation:
        dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == affiliation.department_unit_id).first()
        if dept:
            return dept.school_college_id
    return None


def _resolve_researcher_routing(db: Session, lead_proponent_id: uuid.UUID) -> tuple[Optional[uuid.UUID], Optional[uuid.UUID]]:
    """Resolve school_college_id and assigned_dean_id for a lead proponent.
    Returns (school_college_id, assigned_dean_id) or (None, None) if unresolvable.
    """
    school_id = _get_researcher_school_id(db, lead_proponent_id)
    if not school_id:
        return None, None
    school = db.query(SchoolCollege).filter(SchoolCollege.id == school_id).first()
    if not school or not school.dean_user_id:
        return school_id, None
    return school_id, school.dean_user_id


def _get_school_research_ids(db: Session, school_id: uuid.UUID) -> list[uuid.UUID]:
    """Get all research IDs belonging to a school/college via stored routing or affiliation lookup."""
    # Prefer stored school_college_id on research
    stored_ids = [
        r.id for r in
        db.query(Research.id).filter(Research.school_college_id == school_id).all()
    ]
    if stored_ids:
        return stored_ids
    # Fallback: affiliation-based lookup
    user_ids = [
        ua.user_id for ua in
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(DepartmentUnit.school_college_id == school_id)
        .all()
    ]
    if not user_ids:
        return []
    research_ids = [
        r.id for r in
        db.query(Research.id).filter(
            or_(
                Research.lead_proponent_id.in_(user_ids),
                Research.created_by.in_(user_ids),
            )
        ).all()
    ]
    return research_ids


def _to_research_response(db: Session, r: Research) -> dict:
    """Convert a Research object to a response dict."""
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

    return {
        "id": str(r.id),
        "tracking_number": r.tracking_number,
        "title": r.title,
        "lead_proponent_id": str(r.lead_proponent_id),
        "lead_proponent_name": _get_user_name(db, r.lead_proponent_id),
        "status": r.status.value,
        "nature_of_research": r.nature_of_research,
        "target_journal": r.target_journal,
        "research_agenda": r.research_agenda,
        "is_continuation": r.is_continuation,
        "continuation_ref": r.continuation_ref,
        "mobile_number": r.mobile_number,
        "institutional_email": r.institutional_email,
        "created_by": str(r.created_by),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "school_college_id": str(r.school_college_id) if r.school_college_id else None,
        "school_name": school_name,
        "department_name": dept_name,
        "assigned_dean_id": str(r.assigned_dean_id) if r.assigned_dean_id else None,
        "assigned_dean_name": dean_name,
        "authors": [
            {
                "id": str(a.id),
                "name": a.name,
                "affiliation": a.affiliation,
                "email": a.email,
                "contribution_pct": a.contribution_pct,
                "is_lead": a.is_lead,
            }
            for a in r.authors
        ],
    }


def _require_dean_role(current_user: User, roles: list[str], db: Session) -> uuid.UUID:
    """Verify user is a Dean and return their school/college ID."""
    if "DEAN" not in roles and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Access restricted to Dean role")
    school_id = _get_dean_school_scope(db, current_user.id)
    if not school_id and "ADMIN" not in roles:
        raise HTTPException(status_code=400, detail="Dean is not affiliated with any school/college")
    return school_id


@router.get("/stats")
def get_dean_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get dashboard statistics for the Dean's school/college."""
    school_id = _require_dean_role(current_user, roles, db)
    school_name = _get_dean_school_name(db, current_user.id)

    if "ADMIN" in roles and not school_id:
        # Admin without school affiliation sees all
        query = db.query(Research)
    else:
        research_ids = _get_school_research_ids(db, school_id)
        query = db.query(Research).filter(Research.id.in_(research_ids)) if research_ids else db.query(Research).filter(Research.id == None)

    total = query.count()
    by_status = (
        query.with_entities(Research.status, func.count(Research.id))
        .group_by(Research.status)
        .all()
    )
    status_counts = {s.value: c for s, c in by_status}

    # Pending endorsement
    pending_endorsement = status_counts.get("FOR_DEAN_ENDORSEMENT", 0)

    # Active (not draft, not completed, not archived)
    active = sum(c for s, c in by_status if s.value not in ["DRAFT", "COMPLETED", "ARCHIVED"])

    # Needs attention (revision required statuses)
    needs_attention_statuses = [
        "INITIAL_REVISION_REQUIRED",
        "PROPOSAL_TURNITIN_REVISION_REQUIRED",
        "EXTERNAL_EVALUATION_REVISION_REQUIRED",
        "IRB_REVISION_REQUIRED",
        "FINAL_PAPER_TURNITIN_REVISION_REQUIRED",
        "FINAL_EVALUATION_REVISION_REQUIRED",
    ]
    needs_attention = sum(status_counts.get(s, 0) for s in needs_attention_statuses)

    # Under evaluation
    under_evaluation_statuses = [
        "EXTERNAL_EVALUATION",
        "READY_FOR_EXTERNAL_EVALUATION",
        "FINAL_BLIND_EVALUATION",
    ]
    under_evaluation = sum(status_counts.get(s, 0) for s in under_evaluation_statuses)

    # Under implementation
    under_implementation_statuses = [
        "RESEARCH_IN_PROGRESS",
        "FINAL_PAPER_DUE",
        "FINAL_PAPER_SUBMITTED",
    ]
    under_implementation = sum(status_counts.get(s, 0) for s in under_implementation_statuses)

    completed = status_counts.get("COMPLETED", 0) + status_counts.get("READY_FOR_PRESENTATION", 0) + status_counts.get("READY_FOR_PUBLICATION", 0)

    return {
        "total": total,
        "pending_endorsement": pending_endorsement,
        "active": active,
        "needs_attention": needs_attention,
        "under_evaluation": under_evaluation,
        "under_implementation": under_implementation,
        "completed": completed,
        "by_status": status_counts,
        "school_name": school_name,
    }


@router.get("/endorsements")
def get_pending_endorsements(
    search: Optional[str] = None,
    sort: str = Query("oldest", regex="^(oldest|newest)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get submissions awaiting Dean endorsement."""
    school_id = _require_dean_role(current_user, roles, db)

    query = db.query(Research).options(joinedload(Research.authors)).filter(
        Research.status == ResearchStatus.FOR_DEAN_ENDORSEMENT
    )

    # School scoping: prefer assigned_dean_id, fallback to school_college_id, fallback to affiliation lookup
    if "ADMIN" not in roles:
        # First filter by assigned_dean_id (most precise)
        dean_filtered = query.filter(Research.assigned_dean_id == current_user.id)
        if dean_filtered.count() > 0:
            query = dean_filtered
        elif school_id:
            # Fallback to school_college_id
            school_filtered = query.filter(Research.school_college_id == school_id)
            if school_filtered.count() > 0:
                query = school_filtered
            else:
                # Final fallback: affiliation-based lookup
                research_ids = _get_school_research_ids(db, school_id)
                query = query.filter(Research.id.in_(research_ids)) if research_ids else query.filter(Research.id == None)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Research.title.ilike(search_term),
                Research.tracking_number.ilike(search_term),
            )
        )

    if sort == "oldest":
        query = query.order_by(Research.submitted_at.asc().nullslast(), Research.created_at.asc())
    else:
        query = query.order_by(Research.submitted_at.desc().nullslast(), Research.created_at.desc())

    items = query.all()

    return [
        {
            "id": str(r.id),
            "tracking_number": r.tracking_number,
            "title": r.title,
            "lead_proponent_name": _get_user_name(db, r.lead_proponent_id),
            "status": r.status.value,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "nature_of_research": r.nature_of_research,
        }
        for r in items
    ]


@router.get("/research")
def get_school_research(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get research projects belonging to the Dean's school/college."""
    school_id = _require_dean_role(current_user, roles, db)

    query = db.query(Research).options(joinedload(Research.authors))

    # School scoping
    if "ADMIN" not in roles and school_id:
        research_ids = _get_school_research_ids(db, school_id)
        query = query.filter(Research.id.in_(research_ids)) if research_ids else query.filter(Research.id == None)

    if status_filter:
        try:
            status_enum = ResearchStatus(status_filter)
            query = query.filter(Research.status == status_enum)
        except ValueError:
            pass

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Research.title.ilike(search_term),
                Research.tracking_number.ilike(search_term),
            )
        )

    total = query.count()
    items = (
        query.order_by(Research.updated_at.desc().nullslast(), Research.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [_to_research_response(db, r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/researchers")
def get_school_researchers(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get researchers belonging to the Dean's school/college."""
    school_id = _require_dean_role(current_user, roles, db)

    # Get users affiliated with this school
    query = (
        db.query(User)
        .join(UserAffiliation, User.id == UserAffiliation.user_id)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(DepartmentUnit.school_college_id == school_id)
    )

    # Filter to researchers only
    researcher_role = db.query(Role).filter(Role.name == "RESEARCHER").first()
    if researcher_role:
        query = query.join(UserRole, User.id == UserRole.user_id).filter(UserRole.role_id == researcher_role.id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
            )
        )

    users = query.all()

    result = []
    for user in users:
        # Count research
        research_count = db.query(Research).filter(
            or_(
                Research.lead_proponent_id == user.id,
                Research.created_by == user.id,
            )
        ).count()
        active_count = db.query(Research).filter(
            Research.status.notin_([ResearchStatus.DRAFT, ResearchStatus.COMPLETED, ResearchStatus.ARCHIVED]),
            or_(
                Research.lead_proponent_id == user.id,
                Research.created_by == user.id,
            )
        ).count()
        completed_count = db.query(Research).filter(
            Research.status.in_([ResearchStatus.COMPLETED, ResearchStatus.READY_FOR_PRESENTATION, ResearchStatus.READY_FOR_PUBLICATION]),
            or_(
                Research.lead_proponent_id == user.id,
                Research.created_by == user.id,
            )
        ).count()

        # Get latest project
        latest = (
            db.query(Research)
            .filter(or_(Research.lead_proponent_id == user.id, Research.created_by == user.id))
            .order_by(Research.updated_at.desc().nullslast())
            .first()
        )

        result.append({
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
            "total_research": research_count,
            "active_research": active_count,
            "completed_research": completed_count,
            "latest_project": {
                "id": str(latest.id),
                "title": latest.title,
                "status": latest.status.value,
            } if latest else None,
        })

    return result


@router.get("/completed")
def get_completed_research(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get completed research belonging to the Dean's school/college."""
    school_id = _require_dean_role(current_user, roles, db)

    completed_statuses = [
        ResearchStatus.COMPLETED,
        ResearchStatus.READY_FOR_PRESENTATION,
        ResearchStatus.READY_FOR_PUBLICATION,
    ]

    query = db.query(Research).options(joinedload(Research.authors)).filter(
        Research.status.in_(completed_statuses)
    )

    # School scoping
    if "ADMIN" not in roles and school_id:
        research_ids = _get_school_research_ids(db, school_id)
        query = query.filter(Research.id.in_(research_ids)) if research_ids else query.filter(Research.id == None)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Research.title.ilike(search_term),
                Research.tracking_number.ilike(search_term),
            )
        )

    total = query.count()
    items = (
        query.order_by(Research.completed_at.desc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [_to_research_response(db, r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/activity")
def get_dean_activity(
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get recent activity for the Dean's school/college."""
    school_id = _require_dean_role(current_user, roles, db)

    query = db.query(ResearchStatusHistory).join(Research)

    # School scoping
    if "ADMIN" not in roles and school_id:
        research_ids = _get_school_research_ids(db, school_id)
        query = query.filter(Research.id.in_(research_ids)) if research_ids else query.filter(Research.id == None)

    history = query.order_by(ResearchStatusHistory.created_at.desc()).limit(page_size).all()

    return [
        {
            "id": str(h.id),
            "research_id": str(h.research_id),
            "research_title": None,  # Will be filled below
            "action": h.action,
            "new_status": h.new_status.value,
            "prior_status": h.prior_status.value if h.prior_status else None,
            "remarks": h.remarks,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]


@router.get("/monitoring")
def get_dean_monitoring(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get workflow stage counts for the Dean's school/college."""
    school_id = _require_dean_role(current_user, roles, db)

    if "ADMIN" in roles and not school_id:
        query = db.query(Research)
    else:
        research_ids = _get_school_research_ids(db, school_id)
        query = db.query(Research).filter(Research.id.in_(research_ids)) if research_ids else db.query(Research).filter(Research.id == None)

    by_status = (
        query.with_entities(Research.status, func.count(Research.id))
        .group_by(Research.status)
        .all()
    )
    status_counts = {s.value: c for s, c in by_status}

    # Group by workflow stage
    stages = {
        "awaiting_endorsement": status_counts.get("FOR_DEAN_ENDORSEMENT", 0),
        "uro_processing": sum(status_counts.get(s, 0) for s in [
            "ENDORSED_TO_URO", "URO_RECEIVED", "INITIAL_REVIEW",
            "INITIAL_REVISION_REQUIRED", "INITIAL_REVISION_SUBMITTED", "INITIAL_REVIEW_PASSED",
        ]),
        "turnitin_proposal": sum(status_counts.get(s, 0) for s in [
            "PROPOSAL_TURNITIN", "PROPOSAL_TURNITIN_REVISION_REQUIRED",
            "PROPOSAL_TURNITIN_RESUBMITTED", "PROPOSAL_TURNITIN_PASSED",
        ]),
        "external_evaluation": sum(status_counts.get(s, 0) for s in [
            "READY_FOR_EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION",
            "EXTERNAL_EVALUATION_REVISION_REQUIRED", "SELECTIVE_EXTERNAL_REEVALUATION",
            "EXTERNAL_EVALUATION_PASSED",
        ]),
        "irb_review": sum(status_counts.get(s, 0) for s in [
            "FOR_IRB_REVIEW", "IRB_REVISION_REQUIRED", "PROPOSAL_APPROVED",
        ]),
        "implementation": sum(status_counts.get(s, 0) for s in [
            "RESEARCH_IN_PROGRESS", "FINAL_PAPER_DUE", "FINAL_PAPER_SUBMITTED",
        ]),
        "turnitin_final": sum(status_counts.get(s, 0) for s in [
            "FINAL_PAPER_TURNITIN", "FINAL_PAPER_TURNITIN_REVISION_REQUIRED",
            "FINAL_PAPER_TURNITIN_PASSED",
        ]),
        "final_evaluation": sum(status_counts.get(s, 0) for s in [
            "FINAL_BLIND_EVALUATION", "FINAL_EVALUATION_REVISION_REQUIRED",
            "SELECTIVE_FINAL_REEVALUATION", "FINAL_BLIND_EVALUATION_PASSED",
        ]),
        "completed": sum(status_counts.get(s, 0) for s in [
            "COMPLETED", "READY_FOR_PRESENTATION", "READY_FOR_PUBLICATION", "ARCHIVED",
        ]),
    }

    return stages

def _verify_dean_authorization(db: Session, current_user: User, roles: list[str]) -> uuid.UUID:
    """Verify Dean role and return their school ID."""
    if "ADMIN" not in roles and "DEAN" not in roles:
        raise HTTPException(status_code=403, detail="Access restricted to Dean or Admin")
    school_id = _get_dean_school_scope(db, current_user.id)
    if not school_id and "ADMIN" not in roles:
        raise HTTPException(status_code=400, detail="Dean is not affiliated with any school/college")
    return school_id


def _verify_department_in_school(db: Session, department_id: uuid.UUID, school_id: uuid.UUID) -> DepartmentUnit:
    """Verify a department belongs to the specified school."""
    dept = db.query(DepartmentUnit).filter(
        DepartmentUnit.id == department_id,
        DepartmentUnit.school_college_id == school_id,
        DepartmentUnit.is_active == True,
    ).first()
    if not dept:
        raise HTTPException(status_code=403, detail="Department does not belong to your school or is inactive")
    return dept


def _verify_role_assignable(role_name: str):
    """Verify the role is in the Dean-assignable list."""
    if role_name not in DEAN_ASSIGNABLE_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role_name}' cannot be assigned by Dean. Dean-assignable roles: {', '.join(sorted(DEAN_ASSIGNABLE_ROLES))}",
        )


def _is_protected_user(db: Session, user_id: uuid.UUID) -> bool:
    """Check if a user has any protected role."""
    protected_role_ids = [r.id for r in db.query(Role).filter(Role.name.in_(PROTECTED_ROLES)).all()]
    count = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id.in_(protected_role_ids),
    ).count()
    return count > 0


class DeanDepartmentCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=20)
    description: Optional[str] = None


class DeanDepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/departments")
def list_dean_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """List departments in the Dean's assigned School/College."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    depts = db.query(DepartmentUnit).filter(
        DepartmentUnit.school_college_id == school_id,
    ).order_by(DepartmentUnit.name).all()

    result = []
    for dept in depts:
        faculty_count = (
            db.query(User)
            .join(UserAffiliation, User.id == UserAffiliation.user_id)
            .filter(UserAffiliation.department_unit_id == dept.id)
            .count()
        )
        active_research = db.query(Research).filter(
            Research.status.notin_([ResearchStatus.DRAFT, ResearchStatus.COMPLETED, ResearchStatus.ARCHIVED]),
        ).join(User, Research.lead_proponent_id == User.id).join(
            UserAffiliation, User.id == UserAffiliation.user_id
        ).filter(UserAffiliation.department_unit_id == dept.id).count()

        result.append({
            "id": str(dept.id),
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "is_active": dept.is_active,
            "faculty_count": faculty_count,
            "active_research": active_research,
            "created_at": dept.created_at.isoformat() if dept.created_at else None,
            "updated_at": dept.updated_at.isoformat() if dept.updated_at else None,
        })

    return result


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def dean_create_department(
    data: DeanDepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Create a department in the Dean's assigned School/College."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    if db.query(DepartmentUnit).filter(DepartmentUnit.code == data.code).first():
        raise HTTPException(status_code=400, detail="Department code already exists")

    dept = DepartmentUnit(
        id=uuid.uuid4(),
        name=data.name,
        code=data.code,
        description=data.description,
        school_college_id=school_id,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == school_id).first()
    return {
        "id": str(dept.id),
        "name": dept.name,
        "code": dept.code,
        "description": dept.description,
        "school_name": school.name if school else None,
        "message": f"Department created in {school.name if school else 'your school'}",
    }


@router.put("/departments/{dept_id}")
def dean_update_department(
    dept_id: str,
    data: DeanDepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Update a department in the Dean's assigned School/College."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == uuid.UUID(dept_id)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept.school_college_id != school_id:
        raise HTTPException(status_code=403, detail="Department does not belong to your school")

    if data.name is not None:
        dept.name = data.name
    if data.code is not None:
        existing = db.query(DepartmentUnit).filter(DepartmentUnit.code == data.code, DepartmentUnit.id != dept.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists")
        dept.code = data.code
    if data.description is not None:
        dept.description = data.description
    if data.is_active is not None:
        dept.is_active = data.is_active

    dept.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Department updated successfully"}


@router.post("/departments/{dept_id}/deactivate")
def dean_deactivate_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Deactivate a department in the Dean's assigned School/College."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == uuid.UUID(dept_id)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept.school_college_id != school_id:
        raise HTTPException(status_code=403, detail="Department does not belong to your school")

    dept.is_active = False
    dept.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Department '{dept.name}' deactivated"}


@router.post("/departments/{dept_id}/activate")
def dean_activate_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Activate a department in the Dean's assigned School/College."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == uuid.UUID(dept_id)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept.school_college_id != school_id:
        raise HTTPException(status_code=403, detail="Department does not belong to your school")

    dept.is_active = True
    dept.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Department '{dept.name}' activated"}


DEAN_ASSIGNABLE_ROLES = {"RESEARCHER"}

# Roles that are PROTECTED — Dean can never modify users with these roles
PROTECTED_ROLES = {"ADMIN", "URO_DIRECTOR", "URO_STAFF", "DEAN", "EXTERNAL_EVALUATOR", "IRB_REVIEWER", "FINAL_EVALUATOR"}


class AcademicStaffCreate(BaseModel):
    employee_id: Optional[str] = None
    email: str
    password: str = "changeme123"
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    department_id: str
    role_name: str = "RESEARCHER"


class AcademicStaffUpdate(BaseModel):
    employee_id: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/staff")
def list_academic_staff(
    search: Optional[str] = None,
    department_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """List academic staff belonging to the Dean's school/college."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    # Base query: users affiliated with the Dean's school
    query = (
        db.query(User)
        .join(UserAffiliation, User.id == UserAffiliation.user_id)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(DepartmentUnit.school_college_id == school_id)
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                User.employee_id.ilike(search_term),
            )
        )

    if department_id:
        query = query.filter(UserAffiliation.department_unit_id == uuid.UUID(department_id))

    total = query.count()
    users = (
        query.order_by(User.last_name, User.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for user in users:
        # Get primary affiliation
        aff = (
            db.query(UserAffiliation)
            .filter(UserAffiliation.user_id == user.id, UserAffiliation.is_primary == True)
            .first()
        )
        dept_name = None
        dept_id = None
        if aff:
            dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == aff.department_unit_id).first()
            if dept:
                dept_name = dept.name
                dept_id = str(dept.id)

        # Get roles
        user_roles = [ur.role.name for ur in db.query(UserRole).filter(UserRole.user_id == user.id).join(Role).all()]

        # Count research
        research_count = db.query(Research).filter(
            or_(Research.lead_proponent_id == user.id, Research.created_by == user.id)
        ).count()
        active_count = db.query(Research).filter(
            Research.status.notin_([ResearchStatus.DRAFT, ResearchStatus.COMPLETED, ResearchStatus.ARCHIVED]),
            or_(Research.lead_proponent_id == user.id, Research.created_by == user.id),
        ).count()
        completed_count = db.query(Research).filter(
            Research.status.in_([ResearchStatus.COMPLETED, ResearchStatus.READY_FOR_PRESENTATION, ResearchStatus.READY_FOR_PUBLICATION]),
            or_(Research.lead_proponent_id == user.id, Research.created_by == user.id),
        ).count()

        result.append({
            "id": str(user.id),
            "employee_id": user.employee_id,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email,
            "department_id": dept_id,
            "department_name": dept_name,
            "roles": user_roles,
            "is_active": user.is_active,
            "active_research": active_count,
            "completed_research": completed_count,
            "total_research": research_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/staff/departments")
def list_school_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """List departments in the Dean's school/college."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    depts = db.query(DepartmentUnit).filter(
        DepartmentUnit.school_college_id == school_id,
        DepartmentUnit.is_active == True,
    ).order_by(DepartmentUnit.name).all()

    return [
        {"id": str(d.id), "name": d.name, "code": d.code}
        for d in depts
    ]


@router.get("/staff/roles")
def list_assignable_roles():
    """List roles the Dean is allowed to assign."""
    return [
        {"name": "RESEARCHER", "description": "Researcher / Scholar"},
    ]


@router.post("/staff", status_code=status.HTTP_201_CREATED)
def create_academic_staff(
    data: AcademicStaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Create a new academic staff member in the Dean's school/college."""
    school_id = _verify_dean_authorization(db, current_user, roles)

    # Validate role
    _verify_role_assignable(data.role_name)

    # Validate email uniqueness
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Validate employee_id uniqueness if provided
    if data.employee_id:
        if db.query(User).filter(User.employee_id == data.employee_id).first():
            raise HTTPException(status_code=400, detail="Employee ID already exists")

    # Validate department belongs to Dean's school
    dept = _verify_department_in_school(db, uuid.UUID(data.department_id), school_id)

    # Create user
    user = User(
        id=uuid.uuid4(),
        employee_id=data.employee_id,
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        middle_name=data.middle_name,
        last_name=data.last_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Assign role
    role = db.query(Role).filter(Role.name == data.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{data.role_name}' not found")
    user_role = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id)
    db.add(user_role)

    # Create affiliation
    affiliation = UserAffiliation(
        id=uuid.uuid4(),
        user_id=user.id,
        department_unit_id=dept.id,
        is_primary=True,
    )
    db.add(affiliation)

    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "employee_id": user.employee_id,
        "email": user.email,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "department_id": str(dept.id),
        "department_name": dept.name,
        "roles": [data.role_name],
        "is_active": user.is_active,
        "message": "Academic staff created successfully",
    }


@router.put("/staff/{user_id}")
def update_academic_staff(
    user_id: str,
    data: AcademicStaffUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Update an academic staff member's profile."""
    school_id = _verify_dean_authorization(db, current_user, roles)
    target_uid = uuid.UUID(user_id)

    # Get target user
    target = db.query(User).filter(User.id == target_uid).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Protect admin/privileged accounts
    if _is_protected_user(db, target_uid) and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Cannot modify protected user accounts")

    # Verify target belongs to Dean's school
    target_aff = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(
            UserAffiliation.user_id == target_uid,
            UserAffiliation.is_primary == True,
            DepartmentUnit.school_college_id == school_id,
        )
        .first()
    )
    if not target_aff and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="User does not belong to your school")

    # Update fields
    if data.employee_id is not None:
        existing = db.query(User).filter(User.employee_id == data.employee_id, User.id != target_uid).first()
        if existing:
            raise HTTPException(status_code=400, detail="Employee ID already exists")
        target.employee_id = data.employee_id
    if data.first_name is not None:
        target.first_name = data.first_name
    if data.middle_name is not None:
        target.middle_name = data.middle_name
    if data.last_name is not None:
        target.last_name = data.last_name
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email, User.id != target_uid).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        target.email = data.email
    if data.is_active is not None:
        target.is_active = data.is_active

    # Update department affiliation
    if data.department_id is not None:
        dept = _verify_department_in_school(db, uuid.UUID(data.department_id), school_id)
        # Update primary affiliation
        if target_aff:
            target_aff.department_unit_id = dept.id
        else:
            aff = UserAffiliation(
                id=uuid.uuid4(),
                user_id=target_uid,
                department_unit_id=dept.id,
                is_primary=True,
            )
            db.add(aff)

    # Update role
    if data.role_name is not None:
        _verify_role_assignable(data.role_name)
        role = db.query(Role).filter(Role.name == data.role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{data.role_name}' not found")
        # Remove existing academic roles, add new one
        existing_roles = db.query(UserRole).filter(UserRole.user_id == target_uid).all()
        for er in existing_roles:
            db.delete(er)
        user_role = UserRole(id=uuid.uuid4(), user_id=target_uid, role_id=role.id)
        db.add(user_role)

    target.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(target)

    return {"message": "Academic staff updated successfully"}


@router.post("/staff/{user_id}/deactivate")
def deactivate_academic_staff(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Deactivate an academic staff member's account."""
    school_id = _verify_dean_authorization(db, current_user, roles)
    target_uid = uuid.UUID(user_id)

    target = db.query(User).filter(User.id == target_uid).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_protected_user(db, target_uid) and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Cannot deactivate protected user accounts")

    # Verify target belongs to Dean's school
    target_aff = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(
            UserAffiliation.user_id == target_uid,
            UserAffiliation.is_primary == True,
            DepartmentUnit.school_college_id == school_id,
        )
        .first()
    )
    if not target_aff and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="User does not belong to your school")

    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    target.is_active = False
    target.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Account for {target.full_name} deactivated"}


@router.post("/staff/{user_id}/activate")
def activate_academic_staff(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Reactivate an academic staff member's account."""
    school_id = _verify_dean_authorization(db, current_user, roles)
    target_uid = uuid.UUID(user_id)

    target = db.query(User).filter(User.id == target_uid).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify target belongs to Dean's school
    target_aff = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(
            UserAffiliation.user_id == target_uid,
            UserAffiliation.is_primary == True,
            DepartmentUnit.school_college_id == school_id,
        )
        .first()
    )
    if not target_aff and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="User does not belong to your school")

    target.is_active = True
    target.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Account for {target.full_name} reactivated"}


@router.get("/staff/{user_id}")
def get_academic_staff_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get detailed information about an academic staff member."""
    school_id = _verify_dean_authorization(db, current_user, roles)
    target_uid = uuid.UUID(user_id)

    target = db.query(User).filter(User.id == target_uid).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify target belongs to Dean's school
    target_aff = (
        db.query(UserAffiliation)
        .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
        .filter(
            UserAffiliation.user_id == target_uid,
            UserAffiliation.is_primary == True,
            DepartmentUnit.school_college_id == school_id,
        )
        .first()
    )
    if not target_aff and "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="User does not belong to your school")

    # Get department
    dept_name = None
    dept_id = None
    if target_aff:
        dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == target_aff.department_unit_id).first()
        if dept:
            dept_name = dept.name
            dept_id = str(dept.id)

    # Get roles
    user_roles = [ur.role.name for ur in db.query(UserRole).filter(UserRole.user_id == target_uid).join(Role).all()]

    # Get research
    research_items = db.query(Research).filter(
        or_(Research.lead_proponent_id == target_uid, Research.created_by == target_uid)
    ).order_by(Research.updated_at.desc()).all()

    return {
        "id": str(target.id),
        "employee_id": target.employee_id,
        "first_name": target.first_name,
        "middle_name": target.middle_name,
        "last_name": target.last_name,
        "full_name": target.full_name,
        "email": target.email,
        "department_id": dept_id,
        "department_name": dept_name,
        "roles": user_roles,
        "is_active": target.is_active,
        "created_at": target.created_at.isoformat() if target.created_at else None,
        "research": [
            {
                "id": str(r.id),
                "tracking_number": r.tracking_number,
                "title": r.title,
                "status": r.status.value,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in research_items
        ],
    }
@router.post("/{research_id}/endorse")
def endorse_research(
    research_id: str,
    data: DeanActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Endorse a research submission to URO."""
    school_id = _require_dean_role(current_user, roles, db)

    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Verify the submission is awaiting Dean endorsement
    if research.status != ResearchStatus.FOR_DEAN_ENDORSEMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Research is not awaiting Dean endorsement. Current status: {research.status.value}",
        )

    # School scoping check
    if "ADMIN" not in roles and school_id:
        research_ids = _get_school_research_ids(db, school_id)
        if research.id not in research_ids:
            raise HTTPException(status_code=403, detail="Not authorized to endorse research from another school")

    # Perform the endorsement transition
    prior_status = research.status
    new_status = get_target_status(research.status, "DEAN_ENDORSE")
    if not new_status:
        raise HTTPException(status_code=400, detail="Endorsement transition not valid")

    research.status = new_status
    research.updated_at = datetime.now(timezone.utc)

    # Record history
    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior_status,
        new_status=new_status,
        action="DEAN_ENDORSE",
        actor_id=current_user.id,
        actor_role="DEAN",
        remarks=data.remarks,
    )
    db.add(history)
    db.commit()

    return {
        "research_id": str(research.id),
        "prior_status": prior_status.value,
        "new_status": new_status.value,
        "action": "DEAN_ENDORSE",
        "message": f"Research endorsed to URO successfully",
    }


@router.post("/{research_id}/return")
def return_to_researcher(
    research_id: str,
    data: DeanActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Return a research submission to the researcher for revision."""
    school_id = _require_dean_role(current_user, roles, db)

    if not data.remarks or not data.remarks.strip():
        raise HTTPException(status_code=400, detail="Remarks are required when returning to researcher")

    research = db.query(Research).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Verify the submission is awaiting Dean endorsement
    if research.status != ResearchStatus.FOR_DEAN_ENDORSEMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Research is not awaiting Dean endorsement. Current status: {research.status.value}",
        )

    # School scoping check
    if "ADMIN" not in roles and school_id:
        research_ids = _get_school_research_ids(db, school_id)
        if research.id not in research_ids:
            raise HTTPException(status_code=403, detail="Not authorized to return research from another school")

    # Perform the rejection transition
    prior_status = research.status
    new_status = get_target_status(research.status, "DEAN_REJECT")
    if not new_status:
        raise HTTPException(status_code=400, detail="Return transition not valid")

    research.status = new_status
    research.updated_at = datetime.now(timezone.utc)

    # Record history
    history = ResearchStatusHistory(
        id=uuid.uuid4(),
        research_id=research.id,
        prior_status=prior_status,
        new_status=new_status,
        action="DEAN_REJECT",
        actor_id=current_user.id,
        actor_role="DEAN",
        remarks=data.remarks,
    )
    db.add(history)
    db.commit()

    return {
        "research_id": str(research.id),
        "prior_status": prior_status.value,
        "new_status": new_status.value,
        "action": "DEAN_REJECT",
        "message": f"Research returned to researcher",
    }


@router.get("/{research_id}")
def get_research_detail(
    research_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get detailed research information for Dean review."""
    school_id = _require_dean_role(current_user, roles, db)

    research = db.query(Research).options(joinedload(Research.authors)).filter(Research.id == uuid.UUID(research_id)).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # School scoping check
    if "ADMIN" not in roles and school_id:
        research_ids = _get_school_research_ids(db, school_id)
        if research.id not in research_ids:
            raise HTTPException(status_code=403, detail="Not authorized to view research from another school")

    # Get documents
    documents = db.query(ResearchDocument).filter(ResearchDocument.research_id == research.id).all()
    doc_list = []
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
        doc_list.append({
            "id": str(doc.id),
            "document_type": doc.document_type,
            "active_version": {
                "id": str(active_version.id),
                "version_number": active_version.version_number,
                "original_filename": active_version.original_filename,
                "file_size": active_version.file_size,
                "mime_type": active_version.mime_type,
                "uploaded_at": active_version.uploaded_at.isoformat() if active_version.uploaded_at else None,
            } if active_version else None,
        })

    # Get history
    history = (
        db.query(ResearchStatusHistory)
        .filter(ResearchStatusHistory.research_id == research.id)
        .order_by(ResearchStatusHistory.created_at.desc())
        .all()
    )
    history_list = [
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

    return {
        **_to_research_response(db, research),
        "documents": doc_list,
        "history": history_list,
    }


# ============================================================
# ACADEMIC STAFF MANAGEMENT
# ============================================================

# Roles the Dean is allowed to assign (academic roles only)
