"""Seed initial data for development.

Usage: python -m seed
"""
import uuid
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.user import User, Role, UserRole, SchoolCollege, DepartmentUnit, UserAffiliation
from app.security.auth import hash_password

ROLES = [
    ("ADMIN", "System Administrator"),
    ("URO_DIRECTOR", "URO Director"),
    ("URO_STAFF", "Research Coordinator / URO Staff"),
    ("DEAN", "Dean / Principal / Unit / Department Head"),
    ("RESEARCHER", "Researcher / Scholar"),
    ("EXTERNAL_EVALUATOR", "External Evaluator"),
    ("IRB_REVIEWER", "IRB Reviewer / Administrator"),
    ("FINAL_EVALUATOR", "Final Blind Evaluator"),
]

SCHOOLS = [
    ("SOC", "School of Computing"),
    ("SEA", "School of Engineering and Architecture"),
    ("SBA", "School of Business and Accountancy"),
    ("SED", "School of Education"),
    ("SHTM", "School of Hospitality and Tourism Management"),
    ("SAS", "School of Arts and Sciences"),
    ("CON", "College of Nursing"),
    ("COE", "College of Engineering"),
]

USERS = [
    {
        "email": "admin@hau.edu.ph",
        "password": "admin123",
        "first_name": "System",
        "last_name": "Administrator",
        "roles": ["ADMIN"],
        "school": "SOC",
    },
    {
        "email": "uro.director@hau.edu.ph",
        "password": "director123",
        "first_name": "Marlon",
        "last_name": "Tayag",
        "roles": ["URO_DIRECTOR"],
        "school": "SOC",
    },
    {
        "email": "uro.staff1@hau.edu.ph",
        "password": "staff123",
        "first_name": "Maria",
        "last_name": "Santos",
        "roles": ["URO_STAFF"],
        "school": "SED",
    },
    {
        "email": "uro.staff2@hau.edu.ph",
        "password": "staff123",
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "roles": ["URO_STAFF"],
        "school": "SBA",
    },
    {
        "email": "dean.soc@hau.edu.ph",
        "password": "dean123",
        "first_name": "Elena",
        "last_name": "Garcia",
        "roles": ["DEAN"],
        "school": "SOC",
    },
    {
        "email": "dean.sed@hau.edu.ph",
        "password": "dean123",
        "first_name": "Roberto",
        "last_name": "Ramirez",
        "roles": ["DEAN"],
        "school": "SED",
    },
    {
        "email": "dean.sba@hau.edu.ph",
        "password": "dean123",
        "first_name": "Patricia",
        "last_name": "Cruz",
        "roles": ["DEAN"],
        "school": "SBA",
    },
    {
        "email": "dean.sea@hau.edu.ph",
        "password": "dean123",
        "first_name": "Miguel",
        "last_name": "Santos",
        "roles": ["DEAN"],
        "school": "SEA",
    },
    {
        "email": "dean.shtm@hau.edu.ph",
        "password": "dean123",
        "first_name": "Rosa",
        "last_name": "Mendoza",
        "roles": ["DEAN"],
        "school": "SHTM",
    },
    {
        "email": "dean.sas@hau.edu.ph",
        "password": "dean123",
        "first_name": "Fernando",
        "last_name": "Reyes",
        "roles": ["DEAN"],
        "school": "SAS",
    },
    {
        "email": "dean.con@hau.edu.ph",
        "password": "dean123",
        "first_name": "Gloria",
        "last_name": "Santiago",
        "roles": ["DEAN"],
        "school": "CON",
    },
    {
        "email": "dean.coe@hau.edu.ph",
        "password": "dean123",
        "first_name": "Ricardo",
        "last_name": "Lim",
        "roles": ["DEAN"],
        "school": "COE",
    },
    {
        "email": "researcher1@hau.edu.ph",
        "password": "researcher123",
        "first_name": "Anna",
        "last_name": "Reyes",
        "roles": ["RESEARCHER"],
        "school": "SBA",
    },
    {
        "email": "researcher2@hau.edu.ph",
        "password": "researcher123",
        "first_name": "Kevin",
        "last_name": "Llamas",
        "roles": ["RESEARCHER"],
        "school": "SEA",
    },
    {
        "email": "researcher3@hau.edu.ph",
        "password": "researcher123",
        "first_name": "Catherine",
        "last_name": "Dizon",
        "roles": ["RESEARCHER"],
        "school": "SED",
    },
    {
        "email": "evaluator1@hau.edu.ph",
        "password": "evaluator123",
        "first_name": "Dr. Maria",
        "last_name": "Santos",
        "roles": ["EXTERNAL_EVALUATOR"],
        "school": "SED",
    },
    {
        "email": "evaluator2@hau.edu.ph",
        "password": "evaluator123",
        "first_name": "Prof. John",
        "last_name": "Dela Cruz",
        "roles": ["EXTERNAL_EVALUATOR"],
        "school": "SOC",
    },
    {
        "email": "evaluator3@hau.edu.ph",
        "password": "evaluator123",
        "first_name": "Dr. Anna",
        "last_name": "Reyes",
        "roles": ["EXTERNAL_EVALUATOR"],
        "school": "SBA",
    },
    {
        "email": "evaluator4@hau.edu.ph",
        "password": "evaluator123",
        "first_name": "Dr. Michael",
        "last_name": "Tan",
        "roles": ["EXTERNAL_EVALUATOR"],
        "school": "COE",
    },
    {
        "email": "irb1@hau.edu.ph",
        "password": "irb123",
        "first_name": "Dr. Liza",
        "last_name": "Fernandez",
        "roles": ["IRB_REVIEWER"],
        "school": "CON",
    },
    {
        "email": "irb2@hau.edu.ph",
        "password": "irb123",
        "first_name": "Dr. Carlos",
        "last_name": "Magsino",
        "roles": ["IRB_REVIEWER"],
        "school": "SAS",
    },
    {
        "email": "final1@hau.edu.ph",
        "password": "final123",
        "first_name": "Dr. Patricia",
        "last_name": "Gomez",
        "roles": ["FINAL_EVALUATOR"],
        "school": "SED",
    },
    {
        "email": "final2@hau.edu.ph",
        "password": "final123",
        "first_name": "Dr. Thomas",
        "last_name": "Valdez",
        "roles": ["FINAL_EVALUATOR"],
        "school": "SBA",
    },
    {
        "email": "final3@hau.edu.ph",
        "password": "final123",
        "first_name": "Dr. Ramon",
        "last_name": "Bautista",
        "roles": ["FINAL_EVALUATOR"],
        "school": "SOC",
    },
    {
        "email": "final4@hau.edu.ph",
        "password": "final123",
        "first_name": "Dr. Isabelle",
        "last_name": "Cortez",
        "roles": ["FINAL_EVALUATOR"],
        "school": "SAS",
    },
]

DEAN_SCHOOL_ASSIGNMENTS = {
    "dean.soc@hau.edu.ph": "SOC",
    "dean.sed@hau.edu.ph": "SED",
    "dean.sba@hau.edu.ph": "SBA",
    "dean.sea@hau.edu.ph": "SEA",
    "dean.shtm@hau.edu.ph": "SHTM",
    "dean.sas@hau.edu.ph": "SAS",
    "dean.con@hau.edu.ph": "CON",
    "dean.coe@hau.edu.ph": "COE",
}


def seed():
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if existing:
            print("Seed data already exists. Skipping.")
            return

        print("Seeding roles...")
        role_map = {}
        for name, desc in ROLES:
            role = Role(id=uuid.uuid4(), name=name, description=desc)
            db.add(role)
            role_map[name] = role
        db.flush()

        print("Seeding schools/colleges...")
        school_map = {}
        for code, name in SCHOOLS:
            school = SchoolCollege(id=uuid.uuid4(), name=name, code=code)
            db.add(school)
            school_map[code] = school
        db.flush()

        print("Seeding users...")
        dean_user_map = {}
        for user_data in USERS:
            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_active=True,
            )
            db.add(user)
            db.flush()

            for role_name in user_data["roles"]:
                ur = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role_map[role_name].id)
                db.add(ur)

            if user_data.get("school") and user_data["school"] in school_map:
                dept_code = f"DEPT-{user_data['school']}-{user.id.hex[:6].upper()}"
                dept = DepartmentUnit(
                    id=uuid.uuid4(),
                    name=f"Dept of {user_data['first_name']} {user_data['last_name']}",
                    code=dept_code,
                    school_college_id=school_map[user_data["school"]].id,
                )
                db.add(dept)
                db.flush()

                aff = UserAffiliation(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    department_unit_id=dept.id,
                    is_primary=True,
                )
                db.add(aff)

            if user_data["email"] in DEAN_SCHOOL_ASSIGNMENTS:
                dean_user_map[user_data["email"]] = user

        # Assign deans to schools
        print("Assigning deans to schools...")
        for dean_email, school_code in DEAN_SCHOOL_ASSIGNMENTS.items():
            if dean_email in dean_user_map and school_code in school_map:
                school = school_map[school_code]
                school.dean_user_id = dean_user_map[dean_email].id

        db.commit()
        print("Seed data created successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
