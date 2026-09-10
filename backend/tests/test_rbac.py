"""Tests: RBAC — cross-role authorization for all workflow actions."""
import pytest
from tests.conftest import create_research, transition, advance_to_endorsed


class TestResearcherRBAC:
    def test_researcher_can_create(self, api, researcher_token):
        r = create_research(api, researcher_token)
        assert r["status"] == "DRAFT"

    def test_researcher_can_submit_own(self, api, researcher_token):
        r = create_research(api, researcher_token)
        resp = transition(api, researcher_token, r["id"], "SUBMIT")
        assert resp.status_code == 200

    def test_researcher_can_forward_to_dean(self, api, researcher_token):
        """SUBMIT now auto-routes to FOR_DEAN_ENDORSEMENT."""
        r = create_research(api, researcher_token)
        resp = transition(api, researcher_token, r["id"], "SUBMIT")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "FOR_DEAN_ENDORSEMENT"

    def test_researcher_cannot_endorse(self, api, researcher_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        resp = transition(api, researcher_token, r["id"], "DEAN_ENDORSE")
        assert resp.status_code == 403

    def test_researcher_cannot_receive(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=researcher_token, json={})
        assert resp.status_code == 403

    def test_researcher_cannot_begin_review(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_uro_received
        rid = advance_to_uro_received(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review", token=researcher_token, json={})
        assert resp.status_code == 403

    def test_researcher_can_resubmit_revision(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_initial_review
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        api.post(f"/research/{rid}/initial-review/revision", token=uro_director_token, json={
            "remarks_researcher": "Fix",
        })
        resp = api.post(f"/research/{rid}/initial-review/resubmit", token=researcher_token, json={})
        assert resp.status_code == 200

    def test_researcher_can_resubmit_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_proposal_turnitin
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        api.post(f"/research/{rid}/turnitin/revision", token=uro_director_token, json={
            "remarks_researcher": "Fix",
        })
        resp = api.post(f"/research/{rid}/turnitin/resubmit", token=researcher_token, json={})
        assert resp.status_code == 200


class TestDeanRBAC:
    def test_dean_can_endorse(self, api, researcher_token, dean_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        transition(api, researcher_token, r["id"], "FORWARD_TO_DEAN")
        resp = transition(api, dean_token, r["id"], "DEAN_ENDORSE")
        assert resp.status_code == 200

    def test_dean_can_reject(self, api, researcher_token, dean_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        transition(api, researcher_token, r["id"], "FORWARD_TO_DEAN")
        resp = transition(api, dean_token, r["id"], "DEAN_REJECT")
        assert resp.status_code == 200

    def test_dean_cannot_receive(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=dean_token, json={})
        assert resp.status_code == 403

    def test_dean_cannot_begin_review(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_uro_received
        rid = advance_to_uro_received(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review", token=dean_token, json={})
        assert resp.status_code == 403


class TestURODirectorRBAC:
    def test_uro_director_can_receive(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=uro_director_token, json={})
        assert resp.status_code == 200

    def test_uro_director_can_begin_review(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_uro_received
        rid = advance_to_uro_received(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review", token=uro_director_token, json={})
        assert resp.status_code == 200

    def test_uro_director_can_pass_review(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_initial_review
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review/pass", token=uro_director_token, json={
            "remarks_researcher": "Good",
        })
        assert resp.status_code == 200

    def test_uro_director_can_begin_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_initial_review_passed
        rid = advance_to_initial_review_passed(api, researcher_token, dean_token, uro_director_token)
        resp = transition(api, uro_director_token, rid, "BEGIN_PROPOSAL_TURNITIN")
        assert resp.status_code == 200

    def test_uro_director_can_pass_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_proposal_turnitin
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/turnitin/pass", token=uro_director_token, json={
            "remarks_researcher": "Passed",
        })
        assert resp.status_code == 200

    def test_uro_director_can_ready_for_external(self, api, researcher_token, dean_token, uro_director_token):
        from tests.conftest import advance_to_proposal_turnitin_passed
        rid = advance_to_proposal_turnitin_passed(api, researcher_token, dean_token, uro_director_token)
        resp = transition(api, uro_director_token, rid, "READY_FOR_EXTERNAL_EVAL")
        assert resp.status_code == 200

    def test_uro_director_cannot_endorse(self, api, researcher_token, uro_director_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        transition(api, researcher_token, r["id"], "FORWARD_TO_DEAN")
        resp = transition(api, uro_director_token, r["id"], "DEAN_ENDORSE")
        assert resp.status_code == 403


class TestUROStaffRBAC:
    def test_uro_staff_can_receive(self, api, researcher_token, dean_token, uro_staff_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=uro_staff_token, json={})
        assert resp.status_code == 200

    def test_uro_staff_can_begin_review(self, api, researcher_token, dean_token, uro_staff_token):
        from tests.conftest import advance_to_uro_received
        rid = advance_to_uro_received(api, researcher_token, dean_token, uro_staff_token)
        resp = api.post(f"/research/{rid}/initial-review", token=uro_staff_token, json={})
        assert resp.status_code == 200

    def test_uro_staff_cannot_pass_review(self, api, researcher_token, dean_token, uro_staff_token):
        from tests.conftest import advance_to_initial_review
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_staff_token)
        resp = api.post(f"/research/{rid}/initial-review/pass", token=uro_staff_token, json={})
        assert resp.status_code == 403

    def test_uro_staff_cannot_pass_turnitin(self, api, researcher_token, dean_token, uro_director_token, uro_staff_token):
        from tests.conftest import advance_to_proposal_turnitin
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/turnitin/pass", token=uro_staff_token, json={})
        assert resp.status_code == 403


class TestAdminRBAC:
    def test_admin_can_do_everything(self, api, admin_token):
        """Admin should be able to perform any action."""
        r = create_research(api, admin_token, "Admin Test")
        rid = r["id"]
        # Submit (auto-routes to FOR_DEAN_ENDORSEMENT)
        resp = transition(api, admin_token, rid, "SUBMIT")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "FOR_DEAN_ENDORSEMENT"
        # Endorse
        resp = transition(api, admin_token, rid, "DEAN_ENDORSE")
        assert resp.status_code == 200
        # Receive
        resp = api.post(f"/research/{rid}/receive", token=admin_token, json={})
        assert resp.status_code == 200
        # Begin review
        resp = api.post(f"/research/{rid}/initial-review", token=admin_token, json={})
        assert resp.status_code == 200
        # Pass review
        resp = api.post(f"/research/{rid}/initial-review/pass", token=admin_token, json={"remarks_researcher": "OK"})
        assert resp.status_code == 200
        # Begin turnitin
        resp = transition(api, admin_token, rid, "BEGIN_PROPOSAL_TURNITIN")
        assert resp.status_code == 200
        # Pass turnitin
        resp = api.post(f"/research/{rid}/turnitin/pass", token=admin_token, json={"remarks_researcher": "OK"})
        assert resp.status_code == 200
        # Ready for external
        resp = transition(api, admin_token, rid, "READY_FOR_EXTERNAL_EVAL")
        assert resp.status_code == 200


class TestAnonymousAccess:
    def test_no_token_all_endpoints(self, api):
        """All protected endpoints should reject anonymous access."""
        endpoints = [
            ("GET", "/research"),
            ("GET", "/research/stats/summary"),
            ("GET", "/auth/me"),
            ("GET", "/research/phase3/dashboard"),
        ]
        for method, path in endpoints:
            if method == "GET":
                resp = api.get(path)
            else:
                resp = api.post(path)
            assert resp.status_code == 401, f"{method} {path} should require auth"
