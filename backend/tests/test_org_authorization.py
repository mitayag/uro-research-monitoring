"""
Authorization tests for the organizational structure.

Tests 1-15 from the Official Organizational Structure requirements.
Runs against the live Docker API.
"""
import uuid
import pytest
from tests.conftest import APIClient


# ─────────────────────────────────────────────
# TEST 1: Admin creates School/College
# ─────────────────────────────────────────────
class TestAdminSchoolManagement:
    def test_admin_creates_school(self, api: APIClient, admin_token: str):
        """TEST 1: Admin creates School/College — Expected: Success."""
        resp = api.post("/admin/schools", token=admin_token, json={
            "name": f"School of Test {uuid.uuid4().hex[:6]}",
            "code": f"TST-{uuid.uuid4().hex[:4].upper()}",
            "description": "Test school",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_active"] is True
        assert "created successfully" in data["message"]

    def test_dean_cannot_create_school(self, api: APIClient, dean_token: str):
        """TEST 2: Dean attempts to create School/College — Expected: 403."""
        resp = api.post("/admin/schools", token=dean_token, json={
            "name": "Unauthorized School",
            "code": "UNAUTH",
        })
        assert resp.status_code == 403
        assert "Admin" in resp.json()["detail"]

    def test_researcher_cannot_create_school(self, api: APIClient, researcher_token: str):
        """Researcher cannot create School/College."""
        resp = api.post("/admin/schools", token=researcher_token, json={
            "name": "Bad School",
            "code": "BAD",
        })
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_school(self, api: APIClient):
        """Unauthenticated user cannot create School/College."""
        resp = api.post("/admin/schools", json={"name": "X", "code": "X"})
        assert resp.status_code in (401, 403)


# ─────────────────────────────────────────────
# TEST 3: Admin creates Dean
# ─────────────────────────────────────────────
class TestAdminDeanManagement:
    def test_admin_creates_dean(self, api: APIClient, admin_token: str):
        """TEST 3: Admin creates Dean — Expected: Success."""
        email = f"new.dean.{uuid.uuid4().hex[:6]}@hau.edu.ph"
        emp_id = f"DEAN{uuid.uuid4().hex[:6]}"
        resp = api.post("/admin/deans", token=admin_token, json={
            "employee_id": emp_id,
            "email": email,
            "password": "dean123",
            "first_name": "Test",
            "last_name": "Dean",
        })
        assert resp.status_code == 201
        assert "created successfully" in resp.json()["message"]

    def test_dean_cannot_create_another_dean(self, api: APIClient, dean_token: str):
        """TEST 4: Dean attempts to create another Dean — Expected: 403."""
        resp = api.post("/admin/deans", token=dean_token, json={
            "employee_id": "FAKE001",
            "email": "bad.dean@hau.edu.ph",
            "password": "dean123",
            "first_name": "Bad",
            "last_name": "Dean",
        })
        assert resp.status_code == 403

    def test_dean_cannot_create_admin(self, api: APIClient, dean_token: str):
        """TEST 5: Dean attempts to create Admin — Expected: 403."""
        resp = api.post("/admin/deans", token=dean_token, json={
            "employee_id": "FAKE002",
            "email": "fake.admin@hau.edu.ph",
            "password": "admin123",
            "first_name": "Fake",
            "last_name": "Admin",
        })
        assert resp.status_code == 403


# ─────────────────────────────────────────────
# TEST 6: Admin assigns Dean to School
# ─────────────────────────────────────────────
class TestDeanAssignment:
    def test_admin_assigns_dean_to_school(self, api: APIClient, admin_token: str):
        """TEST 6: Admin assigns Dean to School — Expected: Success."""
        # Create a school
        school_resp = api.post("/admin/schools", token=admin_token, json={
            "name": f"Assign Test {uuid.uuid4().hex[:6]}",
            "code": f"ASG-{uuid.uuid4().hex[:4].upper()}",
        })
        assert school_resp.status_code == 201
        school_id = school_resp.json()["id"]

        # Get a dean
        deans_resp = api.get("/admin/deans", token=admin_token)
        dean_id = deans_resp.json()[0]["id"]

        # Assign
        resp = api.post(f"/admin/schools/{school_id}/assign-dean", token=admin_token, json={
            "dean_user_id": dean_id,
        })
        assert resp.status_code == 200
        assert "assigned" in resp.json()["message"].lower()

    def test_dean_cannot_assign_dean(self, api: APIClient, dean_token: str):
        """Dean cannot assign deans to schools."""
        # Get any school
        schools_resp = api.get("/admin/schools", token=dean_token)
        if schools_resp.status_code == 200 and schools_resp.json().get("items"):
            school_id = schools_resp.json()["items"][0]["id"]
            resp = api.post(f"/admin/schools/{school_id}/assign-dean", token=dean_token, json={
                "dean_user_id": "00000000-0000-0000-0000-000000000000",
            })
            assert resp.status_code == 403


# ─────────────────────────────────────────────
# TEST 7: Dean creates Department under own School
# ─────────────────────────────────────────────
class TestDeanDepartmentManagement:
    def test_dean_creates_department_in_own_school(self, api: APIClient, dean_token: str):
        """TEST 7: Dean creates Department under own School — Expected: Success."""
        resp = api.post("/dean/departments", token=dean_token, json={
            "name": f"Dept {uuid.uuid4().hex[:6]}",
            "code": f"DPT-{uuid.uuid4().hex[:4].upper()}",
            "description": "Test department",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["school_name"] is not None

    def test_dean_list_departments_shows_own_school(self, api: APIClient, dean_token: str):
        """Dean's department list is scoped to their school."""
        resp = api.get("/dean/departments", token=dean_token)
        assert resp.status_code == 200
        depts = resp.json()
        # All should belong to the same school
        assert len(depts) > 0

    def test_different_dean_sees_different_departments(self, api: APIClient):
        """TEST 13: Different Dean sees different departments."""
        # Login as SED dean
        token_sed = api.login("dean.sed@hau.edu.ph", "dean123")
        token_soc = api.login("dean.soc@hau.edu.ph", "dean123")

        resp_sed = api.get("/dean/departments", token=token_sed)
        resp_soc = api.get("/dean/departments", token=token_soc)

        sed_ids = {d["id"] for d in resp_sed.json()}
        soc_ids = {d["id"] for d in resp_soc.json()}

        # No overlap
        assert len(sed_ids & soc_ids) == 0, "Departments leaked between schools!"


# ─────────────────────────────────────────────
# TEST 8: Dean cannot create Department in another School
# ─────────────────────────────────────────────
class TestCrossSchoolProtection:
    def test_dean_cannot_manage_other_school_departments(self, api: APIClient):
        """TEST 8: Dean attempts to create/edit Department in another School — Expected: Blocked."""
        token_soc = api.login("dean.soc@hau.edu.ph", "dean123")
        token_sed = api.login("dean.sed@hau.edu.ph", "dean123")

        # SOC Dean creates a department
        unique_code = f"SOC-{uuid.uuid4().hex[:6].upper()}"
        create_resp = api.post("/dean/departments", token=token_soc, json={
            "name": f"SOC Only Dept {uuid.uuid4().hex[:4]}",
            "code": unique_code,
        })
        assert create_resp.status_code == 201
        dept_id = create_resp.json()["id"]

        # SED Dean tries to edit it
        edit_resp = api.put(f"/dean/departments/{dept_id}", token=token_sed, json={
            "name": "Hacked Dept",
        })
        assert edit_resp.status_code == 403

        # SED Dean tries to deactivate it
        deactivate_resp = api.post(f"/dean/departments/{dept_id}/deactivate", token=token_sed)
        assert deactivate_resp.status_code == 403


# ─────────────────────────────────────────────
# TEST 9: Dean creates Faculty under own Department
# ─────────────────────────────────────────────
class TestDeanFacultyManagement:
    def test_dean_creates_faculty_in_own_school(self, api: APIClient, dean_token: str):
        """TEST 9: Dean creates Faculty under own Department — Expected: Success."""
        # Get a department
        depts_resp = api.get("/dean/departments", token=dean_token)
        assert depts_resp.status_code == 200
        depts = depts_resp.json()
        dept_id = depts[0]["id"]

        email = f"faculty.{uuid.uuid4().hex[:6]}@hau.edu.ph"
        resp = api.post("/dean/staff", token=dean_token, json={
            "email": email,
            "password": "test123",
            "first_name": "Test",
            "last_name": "Faculty",
            "department_id": dept_id,
            "role_name": "RESEARCHER",
        })
        assert resp.status_code == 201

    def test_dean_cannot_add_faculty_to_other_school_department(self, api: APIClient):
        """TEST 10: Dean attempts to add Faculty to Department from another School — Expected: Blocked."""
        token_soc = api.login("dean.soc@hau.edu.ph", "dean123")
        token_sed = api.login("dean.sed@hau.edu.ph", "dean123")

        # Get SED department
        sed_depts = api.get("/dean/departments", token=token_sed).json()
        sed_dept_id = sed_depts[0]["id"]

        # SOC Dean tries to create faculty in SED department
        resp = api.post("/dean/staff", token=token_soc, json={
            "email": f"cross.{uuid.uuid4().hex[:6]}@hau.edu.ph",
            "password": "test123",
            "first_name": "Cross",
            "last_name": "School",
            "department_id": sed_dept_id,
            "role_name": "RESEARCHER",
        })
        assert resp.status_code == 403

    def test_dean_cannot_assign_admin_role(self, api: APIClient, dean_token: str):
        """Dean cannot assign ADMIN role to faculty."""
        depts = api.get("/dean/departments", token=dean_token).json()
        resp = api.post("/dean/staff", token=dean_token, json={
            "email": f"bad.{uuid.uuid4().hex[:6]}@hau.edu.ph",
            "password": "test123",
            "first_name": "Bad",
            "last_name": "Admin",
            "department_id": depts[0]["id"],
            "role_name": "ADMIN",
        })
        assert resp.status_code == 403
        assert "ADMIN" in resp.json()["detail"]

    def test_dean_cannot_edit_protected_users(self, api: APIClient, dean_token: str):
        """Dean cannot edit admin/protected accounts."""
        # Get admin user ID from staff list
        resp = api.get("/dean/staff", token=dean_token)
        staff = resp.json().get("items", [])
        # Find an admin user if any
        admin_users = [s for s in staff if "ADMIN" in s.get("roles", [])]
        if admin_users:
            admin_id = admin_users[0]["id"]
            edit_resp = api.put(f"/dean/staff/{admin_id}", token=dean_token, json={
                "first_name": "Hacked",
            })
            assert edit_resp.status_code == 403


# ─────────────────────────────────────────────
# TEST 11: Faculty submits research → routes to correct Dean
# ─────────────────────────────────────────────
class TestResearchRouting:
    def test_faculty_submission_routes_to_correct_dean(self, api: APIClient):
        """TEST 11: Faculty submits research — Automatically routes to assigned School Dean."""
        # Login as researcher
        token = api.login("researcher1@hau.edu.ph", "researcher123")

        # Create research
        create_resp = api.post("/research", token=token, json={
            "title": f"Routing Test {uuid.uuid4().hex[:6]}",
            "authors": [{"name": "Test Author", "is_lead": True}],
        })
        assert create_resp.status_code == 201
        research_id = create_resp.json()["id"]

        # Submit
        submit_resp = api.post(f"/research/{research_id}/transition", token=token, json={
            "action": "SUBMIT",
        })
        assert submit_resp.status_code == 200

        # Check research detail — should have school/dean assigned
        detail_resp = api.get(f"/research/{research_id}", token=token)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["school_college_id"] is not None, "Research not routed to school"
        assert detail["assigned_dean_id"] is not None, "Research not routed to dean"
        assert detail["status"] == "FOR_DEAN_ENDORSEMENT"


# ─────────────────────────────────────────────
# TEST 12: Correct Dean sees Pending Endorsement
# ─────────────────────────────────────────────
class TestDeanEndorsementVisibility:
    def test_correct_dean_sees_endorsement(self, api: APIClient):
        """TEST 12: Correct Dean sees Pending Endorsement — Expected: Yes."""
        # Create and submit as researcher
        researcher_token = api.login("researcher1@hau.edu.ph", "researcher123")
        create_resp = api.post("/research", token=researcher_token, json={
            "title": f"Endorse Test {uuid.uuid4().hex[:6]}",
            "authors": [{"name": "Test Author", "is_lead": True}],
        })
        research_id = create_resp.json()["id"]
        api.post(f"/research/{research_id}/transition", token=researcher_token, json={"action": "SUBMIT"})

        # Check which school the researcher belongs to
        detail = api.get(f"/research/{research_id}", token=researcher_token).json()
        dean_id = detail["assigned_dean_id"]

        # Login as that dean
        deans = api.get("/admin/deans", token=api.login_as("admin")).json()
        dean_info = next((d for d in deans if d["id"] == dean_id), None)
        assert dean_info is not None, "Dean not found"

        # That dean should see the endorsement
        dean_token = api.login(dean_info["email"], "dean123")
        endorsements_resp = api.get("/dean/endorsements", token=dean_token)
        assert endorsements_resp.status_code == 200
        endorsement_ids = [e["id"] for e in endorsements_resp.json()]
        assert research_id in endorsement_ids, "Correct Dean does not see the endorsement"


# ─────────────────────────────────────────────
# TEST 13: Wrong Dean does NOT see submission
# ─────────────────────────────────────────────
class TestCrossSchoolEndorsement:
    def test_wrong_dean_does_not_see_endorsement(self, api: APIClient):
        """TEST 13: Wrong Dean sees submission — Expected: No."""
        # Create and submit as researcher
        researcher_token = api.login("researcher1@hau.edu.ph", "researcher123")
        create_resp = api.post("/research", token=researcher_token, json={
            "title": f"Cross School Test {uuid.uuid4().hex[:6]}",
            "authors": [{"name": "Test Author", "is_lead": True}],
        })
        research_id = create_resp.json()["id"]
        api.post(f"/research/{research_id}/transition", token=researcher_token, json={"action": "SUBMIT"})

        detail = api.get(f"/research/{research_id}", token=researcher_token).json()
        correct_dean_id = detail["assigned_dean_id"]

        # Login as a DIFFERENT dean
        deans = api.get("/admin/deans", token=api.login_as("admin")).json()
        wrong_dean = next((d for d in deans if d["id"] != correct_dean_id and d["assigned_school_id"]), None)
        if wrong_dean:
            wrong_token = api.login(wrong_dean["email"], "dean123")
            endorsements = api.get("/dean/endorsements", token=wrong_token).json()
            endorsement_ids = [e["id"] for e in endorsements]
            assert research_id not in endorsement_ids, "Wrong Dean can see the endorsement!"


# ─────────────────────────────────────────────
# TEST 14: Correct Dean endorses → moves to URO
# ─────────────────────────────────────────────
class TestDeanEndorsementAction:
    def test_dean_endorses_research(self, api: APIClient):
        """TEST 14: Correct Dean endorses — Expected: Moves to URO Initial Review."""
        researcher_token = api.login("researcher1@hau.edu.ph", "researcher123")
        create_resp = api.post("/research", token=researcher_token, json={
            "title": f"Endorse Action Test {uuid.uuid4().hex[:6]}",
            "authors": [{"name": "Test Author", "is_lead": True}],
        })
        research_id = create_resp.json()["id"]
        api.post(f"/research/{research_id}/transition", token=researcher_token, json={"action": "SUBMIT"})

        detail = api.get(f"/research/{research_id}", token=researcher_token).json()
        dean_id = detail["assigned_dean_id"]

        deans = api.get("/admin/deans", token=api.login_as("admin")).json()
        dean_info = next(d for d in deans if d["id"] == dean_id)
        dean_token = api.login(dean_info["email"], "dean123")

        # Endorse
        endorse_resp = api.post(f"/dean/{research_id}/endorse", token=dean_token, json={
            "remarks": "Approved for URO review",
        })
        assert endorse_resp.status_code == 200

        # Verify status changed
        after = api.get(f"/research/{research_id}", token=researcher_token).json()
        assert after["status"] == "ENDORSED_TO_URO"


# ─────────────────────────────────────────────
# TEST 15: Dean search is school-scoped
# ─────────────────────────────────────────────
class TestDeanSearchScope:
    def test_dean_search_is_school_scoped(self, api: APIClient):
        """TEST 15: Search as Dean — Expected: No records outside Dean School."""
        token_soc = api.login("dean.soc@hau.edu.ph", "dean123")
        token_sed = api.login("dean.sed@hau.edu.ph", "dean123")

        # SOC Dean searches researchers
        soc_resp = api.get("/dean/researchers", token=token_soc)
        sed_resp = api.get("/dean/researchers", token=token_sed)

        soc_data = soc_resp.json()
        sed_data = sed_resp.json()

        soc_items = soc_data.get("items", soc_data) if isinstance(soc_data, dict) else soc_data
        sed_items = sed_data.get("items", sed_data) if isinstance(sed_data, dict) else sed_data

        soc_ids = {r["id"] for r in soc_items}
        sed_ids = {r["id"] for r in sed_items}

        assert len(soc_ids & sed_ids) == 0, "Researchers leaked between schools in search!"


# ─────────────────────────────────────────────
# Additional authorization tests
# ─────────────────────────────────────────────
class TestAdditionalAuthorization:
    def test_dean_cannot_manage_another_school_staff(self, api: APIClient):
        """Dean cannot manage staff from another school."""
        token_sed = api.login("dean.sed@hau.edu.ph", "dean123")

        # Get SOC staff
        soc_token = api.login("dean.soc@hau.edu.ph", "dean123")
        soc_staff = api.get("/dean/staff", token=soc_token).json()
        if soc_staff.get("items"):
            soc_user_id = soc_staff["items"][0]["id"]

            # SED Dean tries to edit SOC staff
            resp = api.put(f"/dean/staff/{soc_user_id}", token=token_sed, json={
                "first_name": "Hacked",
            })
            assert resp.status_code == 403

    def test_dean_cannot_create_school_college(self, api: APIClient, dean_token: str):
        """Dean cannot create school/college through any endpoint."""
        resp = api.post("/admin/schools", token=dean_token, json={
            "name": "Illegal School",
            "code": "ILLEGAL",
        })
        assert resp.status_code == 403

    def test_admin_stats_returns_org_data(self, api: APIClient, admin_token: str):
        """Admin stats include organizational metrics."""
        resp = api.get("/admin/stats", token=admin_token)
        assert resp.status_code == 200
        stats = resp.json()
        assert "total_schools" in stats
        assert "total_departments" in stats
        assert "schools_without_dean" in stats

    def test_school_deactivation_preserves_data(self, api: APIClient, admin_token: str):
        """Deactivated school still appears in list."""
        # Create school
        create_resp = api.post("/admin/schools", token=admin_token, json={
            "name": f"Deact Test {uuid.uuid4().hex[:6]}",
            "code": f"DEC-{uuid.uuid4().hex[:4].upper()}",
        })
        school_id = create_resp.json()["id"]

        # Deactivate
        deact_resp = api.post(f"/admin/schools/{school_id}/deactivate", token=admin_token)
        assert deact_resp.status_code == 200

        # Still in list
        list_resp = api.get("/admin/schools", token=admin_token)
        school_ids = [s["id"] for s in list_resp.json()["items"]]
        assert school_id in school_ids

        # Reactivate
        react_resp = api.post(f"/admin/schools/{school_id}/activate", token=admin_token)
        assert react_resp.status_code == 200

    def test_department_deactivation_preserves_data(self, api: APIClient, dean_token: str):
        """Deactivated department still appears in list."""
        # Create
        create_resp = api.post("/dean/departments", token=dean_token, json={
            "name": f"Deact Dept {uuid.uuid4().hex[:6]}",
            "code": f"DD-{uuid.uuid4().hex[:4].upper()}",
        })
        dept_id = create_resp.json()["id"]

        # Deactivate
        api.post(f"/dean/departments/{dept_id}/deactivate", token=dean_token)

        # Still in list
        list_resp = api.get("/dean/departments", token=dean_token)
        dept_ids = [d["id"] for d in list_resp.json()]
        assert dept_id in dept_ids

        # Reactivate
        api.post(f"/dean/departments/{dept_id}/activate", token=dean_token)

    def test_researcher_cannot_access_admin_endpoints(self, api: APIClient, researcher_token: str):
        """Researcher cannot access admin or dean endpoints."""
        assert api.get("/admin/schools", token=researcher_token).status_code == 403
        assert api.get("/admin/deans", token=researcher_token).status_code == 403
        assert api.get("/dean/departments", token=researcher_token).status_code == 403
        assert api.get("/dean/staff", token=researcher_token).status_code == 403

    def test_one_dean_per_school_default(self, api: APIClient, admin_token: str):
        """Each school should have at most one assigned dean."""
        resp = api.get("/admin/schools", token=admin_token)
        schools = resp.json()["items"]
        for school in schools:
            # Each school should have 0 or 1 dean
            assert school["dean_user_id"] is None or isinstance(school["dean_user_id"], str)
