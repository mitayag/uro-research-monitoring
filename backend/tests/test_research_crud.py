"""Tests: Research CRUD — create, list, get, update, tracking numbers."""
import pytest
from tests.conftest import create_research


class TestCreateResearch:
    def test_create_research_success(self, api, researcher_token):
        r = create_research(api, researcher_token, "My Test Research")
        assert r["title"] == "My Test Research"
        assert r["status"] == "DRAFT"
        assert r["tracking_number"].startswith("HAU-RES-")
        assert len(r["authors"]) == 1
        assert r["authors"][0]["is_lead"] is True

    def test_create_research_no_title_fails(self, api, researcher_token):
        resp = api.post("/research", token=researcher_token, json={
            "authors": [{"name": "Test", "is_lead": True}],
        })
        assert resp.status_code == 422

    def test_create_research_multiple_authors(self, api, researcher_token):
        r = create_research(api, researcher_token, "Multi-Author")
        resp = api.patch(f"/research/{r['id']}", token=researcher_token, json={
            "title": "Multi-Author Updated",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Multi-Author Updated"

    def test_create_research_generates_unique_tracking_numbers(self, api, researcher_token):
        r1 = create_research(api, researcher_token, "First")
        r2 = create_research(api, researcher_token, "Second")
        assert r1["tracking_number"] != r2["tracking_number"]
        # Both should be sequential
        num1 = int(r1["tracking_number"].split("-")[-1])
        num2 = int(r2["tracking_number"].split("-")[-1])
        assert num2 == num1 + 1


class TestListResearch:
    def test_list_returns_items(self, api, researcher_token):
        resp = api.get("/research", token=researcher_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_with_search(self, api, researcher_token):
        r = create_research(api, researcher_token, "Unique Searchable Title XYZ")
        resp = api.get("/research?search=Unique+Searchable", token=researcher_token)
        assert resp.status_code == 200
        titles = [i["title"] for i in resp.json()["items"]]
        assert "Unique Searchable Title XYZ" in titles

    def test_list_with_status_filter(self, api, researcher_token):
        resp = api.get("/research?status_filter=DRAFT", token=researcher_token)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "DRAFT"

    def test_list_pagination(self, api, researcher_token):
        resp = api.get("/research?page=1&page_size=2", token=researcher_token)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2


class TestGetResearch:
    def test_get_research_by_id(self, api, researcher_token):
        r = create_research(api, researcher_token, "Get Me")
        resp = api.get(f"/research/{r['id']}", token=researcher_token)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Me"

    def test_get_research_not_found(self, api, researcher_token):
        resp = api.get("/research/00000000-0000-0000-0000-000000000000", token=researcher_token)
        assert resp.status_code == 404

    def test_get_research_invalid_id(self, api, researcher_token):
        resp = api.get("/research/not-a-uuid", token=researcher_token)
        assert resp.status_code in (400, 422, 500)


class TestUpdateResearch:
    def test_update_title(self, api, researcher_token):
        r = create_research(api, researcher_token, "Original Title")
        resp = api.patch(f"/research/{r['id']}", token=researcher_token, json={
            "title": "Updated Title",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_update_fields(self, api, researcher_token):
        r = create_research(api, researcher_token, "Field Test")
        resp = api.patch(f"/research/{r['id']}", token=researcher_token, json={
            "nature_of_research": "Quantitative",
            "target_journal": "IEEE Transactions",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["nature_of_research"] == "Quantitative"
        assert data["target_journal"] == "IEEE Transactions"

    def test_update_not_found(self, api, researcher_token):
        resp = api.patch("/research/00000000-0000-0000-0000-000000000000", token=researcher_token, json={
            "title": "X",
        })
        assert resp.status_code == 404


class TestResearchStats:
    def test_stats_summary(self, api, admin_token):
        resp = api.get("/research/stats/summary", token=admin_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "by_status" in data
        assert isinstance(data["by_status"], dict)


class TestNewSubmissionRegression:
    """Regression tests for the New Submission button fix."""

    def test_researcher_can_create_draft(self, api, researcher_token):
        r = create_research(api, researcher_token, "New Submission Regression Test")
        assert r["status"] == "DRAFT"
        assert r["tracking_number"].startswith("HAU-RES-")

    def test_anonymous_cannot_create_draft(self, api):
        resp = api.post("/research", json={
            "title": "Anonymous Test",
            "authors": [{"name": "Hacker", "is_lead": True}],
        })
        assert resp.status_code == 401

    def test_draft_has_correct_initial_status(self, api, researcher_token):
        r = create_research(api, researcher_token, "Status Check")
        assert r["status"] == "DRAFT"
        # Verify it can be listed as draft
        resp = api.get(f"/research/{r['id']}", token=researcher_token)
        assert resp.json()["status"] == "DRAFT"

    def test_draft_can_be_edited(self, api, researcher_token):
        r = create_research(api, researcher_token, "Editable Draft")
        resp = api.patch(f"/research/{r['id']}", token=researcher_token, json={
            "title": "Editable Draft - Updated",
            "nature_of_research": "Qualitative",
            "research_agenda": "Test abstract",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Editable Draft - Updated"
        assert data["nature_of_research"] == "Qualitative"

    def test_draft_submission_transitions_correctly(self, api, researcher_token):
        r = create_research(api, researcher_token, "Submit Test")
        assert r["status"] == "DRAFT"
        resp = api.post(f"/research/{r['id']}/transition", token=researcher_token, json={
            "action": "SUBMIT",
        })
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "SUBMITTED"
        # Verify persisted
        resp = api.get(f"/research/{r['id']}", token=researcher_token)
        assert resp.json()["status"] == "SUBMITTED"

    def test_create_with_all_fields(self, api, researcher_token):
        resp = api.post("/research", token=researcher_token, json={
            "title": "Full Field Test",
            "nature_of_research": "Mixed Methods",
            "research_agenda": "This is a test abstract for the research",
            "target_journal": "IEEE Transactions on Education",
            "is_continuation": True,
            "continuation_ref": "Previous Research 2024",
            "mobile_number": "+63 917 123 4567",
            "institutional_email": "researcher@hau.edu.ph",
            "authors": [
                {"name": "Lead Researcher", "is_lead": True, "affiliation": "HAU", "email": "lead@hau.edu.ph"},
                {"name": "Co-Researcher", "is_lead": False, "affiliation": "UEST", "email": "co@uest.edu.ph"},
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Full Field Test"
        assert data["nature_of_research"] == "Mixed Methods"
        assert data["is_continuation"] is True
        assert len(data["authors"]) == 2

    def test_dean_can_create_draft(self, api, dean_token):
        r = create_research(api, dean_token, "Dean Created Draft")
        assert r["status"] == "DRAFT"

    def test_uro_director_can_create_draft(self, api, uro_director_token):
        r = create_research(api, uro_director_token, "URO Created Draft")
        assert r["status"] == "DRAFT"

    def test_admin_can_create_draft(self, api, admin_token):
        r = create_research(api, admin_token, "Admin Created Draft")
        assert r["status"] == "DRAFT"
