from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.database import get_db
from app.models.user import User, Role, UserRole, UserAffiliation, DepartmentUnit, SchoolCollege
from app.models.research import Research, ResearchStatus
from app.security.auth import get_current_user, get_current_user_roles, hash_password


router = APIRouter(prefix="/admin", tags=["Admin - Organization Management"])


# === Pydantic Schemas ===

class SchoolCollegeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=20)
    description: Optional[str] = None

class SchoolCollegeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DeanAssignRequest(BaseModel):
    dean_user_id: str

class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=20)
    description: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DeanCreate(BaseModel):
    employee_id: str = Field(..., min_length=1, description="Employee ID is required")
    email: str
    password: str = "changeme123"
    first_name: str = Field(..., min_length=1)
    middle_name: Optional[str] = None
    last_name: str = Field(..., min_length=1)

class DeanCreateWithAssignment(BaseModel):
    employee_id: str = Field(..., min_length=1, description="Employee ID is required")
    email: str
    password: str = "changeme123"
    first_name: str = Field(..., min_length=1)
    middle_name: Optional[str] = None
    last_name: str = Field(..., min_length=1)
    school_college_id: str = Field(..., description="School/College to assign Dean to")

class DeanUpdate(BaseModel):
    employee_id: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


# === Authorization Helpers ===

def _require_admin(current_user: User, roles: list[str]):
    if "ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Access restricted to Admin")


# === School/College Endpoints ===

@router.get("/schools/lookup")
def list_schools_for_lookup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Lightweight school list for dropdowns (Admin only)."""
    _require_admin(current_user, roles)

    schools = db.query(SchoolCollege).filter(SchoolCollege.is_active == True).order_by(SchoolCollege.name).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "code": s.code,
            "dean_user_id": str(s.dean_user_id) if s.dean_user_id else None,
        }
        for s in schools
    ]


@router.get("/schools")
def list_schools(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """List all schools/colleges (Admin only)."""
    _require_admin(current_user, roles)

    query = db.query(SchoolCollege)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(SchoolCollege.name.ilike(search_term), SchoolCollege.code.ilike(search_term))
        )

    total = query.count()
    schools = (
        query.order_by(SchoolCollege.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for school in schools:
        dean_name = None
        if school.dean_user_id:
            dean = db.query(User).filter(User.id == school.dean_user_id).first()
            dean_name = dean.full_name if dean else None

        dept_count = db.query(DepartmentUnit).filter(
            DepartmentUnit.school_college_id == school.id,
            DepartmentUnit.is_active == True,
        ).count()

        faculty_count = (
            db.query(User)
            .join(UserAffiliation, User.id == UserAffiliation.user_id)
            .join(DepartmentUnit, UserAffiliation.department_unit_id == DepartmentUnit.id)
            .filter(DepartmentUnit.school_college_id == school.id)
            .count()
        )

        result.append({
            "id": str(school.id),
            "name": school.name,
            "code": school.code,
            "description": school.description,
            "dean_user_id": str(school.dean_user_id) if school.dean_user_id else None,
            "dean_name": dean_name,
            "is_active": school.is_active,
            "department_count": dept_count,
            "faculty_count": faculty_count,
            "created_at": school.created_at.isoformat() if school.created_at else None,
            "updated_at": school.updated_at.isoformat() if school.updated_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.post("/schools", status_code=status.HTTP_201_CREATED)
def create_school(
    data: SchoolCollegeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Create a new School/College (Admin only)."""
    _require_admin(current_user, roles)

    # Normalize code
    normalized_code = data.code.strip().upper()

    if db.query(SchoolCollege).filter(SchoolCollege.code == normalized_code).first():
        raise HTTPException(status_code=400, detail="School/College code already exists")

    if db.query(SchoolCollege).filter(SchoolCollege.name == data.name).first():
        raise HTTPException(status_code=400, detail="A School/College with this name already exists")

    school = SchoolCollege(
        id=uuid.uuid4(),
        name=data.name,
        code=normalized_code,
        description=data.description,
        is_active=True,
    )
    db.add(school)
    db.commit()
    db.refresh(school)

    return {
        "id": str(school.id),
        "name": school.name,
        "code": school.code,
        "description": school.description,
        "is_active": school.is_active,
        "message": "School/College created successfully",
    }


@router.put("/schools/{school_id}")
def update_school(
    school_id: str,
    data: SchoolCollegeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Update a School/College (Admin only)."""
    _require_admin(current_user, roles)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(school_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")

    if data.name is not None:
        school.name = data.name
    if data.code is not None:
        existing = db.query(SchoolCollege).filter(SchoolCollege.code == data.code, SchoolCollege.id != school.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="School code already exists")
        school.code = data.code
    if data.description is not None:
        school.description = data.description
    if data.is_active is not None:
        school.is_active = data.is_active

    school.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "School/College updated successfully"}


@router.post("/schools/{school_id}/deactivate")
def deactivate_school(
    school_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Deactivate a School/College (Admin only)."""
    _require_admin(current_user, roles)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(school_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")

    school.is_active = False
    school.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"School/College '{school.name}' deactivated"}


@router.post("/schools/{school_id}/activate")
def activate_school(
    school_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Activate a School/College (Admin only)."""
    _require_admin(current_user, roles)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(school_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")

    school.is_active = True
    school.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"School/College '{school.name}' activated"}


# === Dean Assignment ===

@router.post("/schools/{school_id}/assign-dean")
def assign_dean(
    school_id: str,
    data: DeanAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Assign a Dean to a School/College (Admin only)."""
    _require_admin(current_user, roles)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(school_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")

    dean = db.query(User).filter(User.id == uuid.UUID(data.dean_user_id)).first()
    if not dean:
        raise HTTPException(status_code=404, detail="User not found")

    if not dean.is_active:
        raise HTTPException(status_code=400, detail="Cannot assign inactive user as Dean")

    # Verify user has DEAN role
    has_dean_role = (
        db.query(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == dean.id, Role.name == "DEAN")
        .first()
    )
    if not has_dean_role:
        raise HTTPException(status_code=400, detail="User does not have the DEAN role")

    school.dean_user_id = dean.id
    school.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"{dean.full_name} assigned as Dean of {school.name}"}


@router.post("/schools/{school_id}/remove-dean")
def remove_dean(
    school_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Remove Dean assignment from a School/College (Admin only)."""
    _require_admin(current_user, roles)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(school_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")

    school.dean_user_id = None
    school.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Dean removed from {school.name}"}


# === Dean User Management ===

@router.get("/deans")
def list_deans(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """List all users with DEAN role (Admin only)."""
    _require_admin(current_user, roles)

    query = (
        db.query(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .filter(Role.name == "DEAN")
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(User.first_name.ilike(search_term), User.last_name.ilike(search_term), User.email.ilike(search_term))
        )

    deans = query.order_by(User.last_name, User.first_name).all()

    result = []
    for dean in deans:
        # Get assigned school
        school = db.query(SchoolCollege).filter(SchoolCollege.dean_user_id == dean.id).first()
        result.append({
            "id": str(dean.id),
            "employee_id": dean.employee_id,
            "first_name": dean.first_name,
            "middle_name": dean.middle_name,
            "last_name": dean.last_name,
            "full_name": dean.full_name,
            "email": dean.email,
            "is_active": dean.is_active,
            "assigned_school_id": str(school.id) if school else None,
            "assigned_school_name": school.name if school else None,
            "created_at": dean.created_at.isoformat() if dean.created_at else None,
        })

    return result


@router.post("/deans", status_code=status.HTTP_201_CREATED)
def create_dean(
    data: DeanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Create a new Dean account (Admin only)."""
    _require_admin(current_user, roles)

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    if data.employee_id and db.query(User).filter(User.employee_id == data.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee ID already exists")

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

    # Assign DEAN role
    dean_role = db.query(Role).filter(Role.name == "DEAN").first()
    if not dean_role:
        raise HTTPException(status_code=500, detail="DEAN role not found in system")
    user_role = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=dean_role.id)
    db.add(user_role)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "message": "Dean account created successfully. Assign to a School/College.",
    }


@router.post("/deans/create-and-assign", status_code=status.HTTP_201_CREATED)
def create_and_assign_dean(
    data: DeanCreateWithAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Create a new Dean account and assign to a School/College in one transaction (Admin only)."""
    _require_admin(current_user, roles)

    # Validate school
    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(data.school_college_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")
    if not school.is_active:
        raise HTTPException(status_code=400, detail="School/College is not active")
    if school.dean_user_id:
        existing_dean = db.query(User).filter(User.id == school.dean_user_id).first()
        dean_name = existing_dean.full_name if existing_dean else "Unknown"
        raise HTTPException(
            status_code=400,
            detail=f"{school.name} already has an assigned Dean: {dean_name}. Remove the current Dean first.",
        )

    # Validate user fields
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    if db.query(User).filter(User.employee_id == data.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    try:
        # 1. Create user
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

        # 2. Assign DEAN role
        dean_role = db.query(Role).filter(Role.name == "DEAN").first()
        if not dean_role:
            raise HTTPException(status_code=500, detail="DEAN role not found in system")
        user_role = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=dean_role.id)
        db.add(user_role)

        # 3. Assign to school
        school.dean_user_id = user.id
        school.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "school_id": str(school.id),
            "school_name": school.name,
            "message": f"{user.full_name} has been assigned as Dean of {school.name}.",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create Dean account. Please try again.")


@router.put("/deans/{user_id}")
def update_dean(
    user_id: str,
    data: DeanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Update a Dean account (Admin only)."""
    _require_admin(current_user, roles)

    target = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify target has DEAN role
    has_dean_role = (
        db.query(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == target.id, Role.name == "DEAN")
        .first()
    )
    if not has_dean_role:
        raise HTTPException(status_code=400, detail="User is not a Dean")

    if data.employee_id is not None:
        existing = db.query(User).filter(User.employee_id == data.employee_id, User.id != target.id).first()
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
        existing = db.query(User).filter(User.email == data.email, User.id != target.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        target.email = data.email
    if data.is_active is not None:
        target.is_active = data.is_active

    target.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Dean account updated successfully"}


# === Department Management (Admin) ===

@router.get("/departments")
def list_all_departments(
    search: Optional[str] = None,
    school_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """List all departments across all schools (Admin only)."""
    _require_admin(current_user, roles)

    query = db.query(DepartmentUnit).join(SchoolCollege)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(DepartmentUnit.name.ilike(search_term), DepartmentUnit.code.ilike(search_term))
        )
    if school_id:
        query = query.filter(DepartmentUnit.school_college_id == uuid.UUID(school_id))

    total = query.count()
    depts = (
        query.order_by(SchoolCollege.name, DepartmentUnit.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for dept in depts:
        school = db.query(SchoolCollege).filter(SchoolCollege.id == dept.school_college_id).first()
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
            "school_college_id": str(dept.school_college_id),
            "school_name": school.name if school else None,
            "is_active": dept.is_active,
            "faculty_count": faculty_count,
            "active_research": active_research,
            "created_at": dept.created_at.isoformat() if dept.created_at else None,
            "updated_at": dept.updated_at.isoformat() if dept.updated_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def admin_create_department(
    data: DepartmentCreate,
    school_id: str = Query(..., description="School/College ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Create a department under a specific School/College (Admin only)."""
    _require_admin(current_user, roles)

    school = db.query(SchoolCollege).filter(SchoolCollege.id == uuid.UUID(school_id)).first()
    if not school:
        raise HTTPException(status_code=404, detail="School/College not found")

    if db.query(DepartmentUnit).filter(DepartmentUnit.code == data.code).first():
        raise HTTPException(status_code=400, detail="Department code already exists")

    dept = DepartmentUnit(
        id=uuid.uuid4(),
        name=data.name,
        code=data.code,
        description=data.description,
        school_college_id=school.id,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return {
        "id": str(dept.id),
        "name": dept.name,
        "code": dept.code,
        "description": dept.description,
        "school_college_id": str(school.id),
        "school_name": school.name,
        "message": f"Department created in {school.name}",
    }


@router.put("/departments/{dept_id}")
def admin_update_department(
    dept_id: str,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Update a department (Admin only)."""
    _require_admin(current_user, roles)

    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == uuid.UUID(dept_id)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

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
def admin_deactivate_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Deactivate a department (Admin only)."""
    _require_admin(current_user, roles)

    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == uuid.UUID(dept_id)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept.is_active = False
    dept.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Department '{dept.name}' deactivated"}


@router.post("/departments/{dept_id}/activate")
def admin_activate_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Activate a department (Admin only)."""
    _require_admin(current_user, roles)

    dept = db.query(DepartmentUnit).filter(DepartmentUnit.id == uuid.UUID(dept_id)).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept.is_active = True
    dept.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Department '{dept.name}' activated"}


# === Admin Stats ===

@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
):
    """Get organization-level statistics (Admin only)."""
    _require_admin(current_user, roles)

    total_schools = db.query(SchoolCollege).count()
    active_schools = db.query(SchoolCollege).filter(SchoolCollege.is_active == True).count()
    total_departments = db.query(DepartmentUnit).count()
    active_departments = db.query(DepartmentUnit).filter(DepartmentUnit.is_active == True).count()

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    deans_assigned = db.query(SchoolCollege).filter(SchoolCollege.dean_user_id.isnot(None)).count()
    schools_without_dean = total_schools - deans_assigned

    total_research = db.query(Research).count()
    active_research = db.query(Research).filter(
        Research.status.notin_([ResearchStatus.DRAFT, ResearchStatus.COMPLETED, ResearchStatus.ARCHIVED])
    ).count()

    return {
        "total_schools": total_schools,
        "active_schools": active_schools,
        "total_departments": total_departments,
        "active_departments": active_departments,
        "total_users": total_users,
        "active_users": active_users,
        "deans_assigned": deans_assigned,
        "schools_without_dean": schools_without_dean,
        "total_research": total_research,
        "active_research": active_research,
    }
