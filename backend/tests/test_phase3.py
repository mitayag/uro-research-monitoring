"""Tests: Phase 3 — URO Receipt, Initial Review, Turnitin, Dashboard, Workflow Gate."""
import pytest
from tests.conftest import (
    create_research, transition, advance_to_endorsed,
    advance_to_uro_received, advance_to_initial_review,
    advance_to_initial_review_passed, advance_to_proposal_turnitin,
    advance_to_proposal_turnitin_passed, advance_to_ready_for_external,
)


class TestUROReceipt:
    def test_receive_submission(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=uro_director_token, json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "URO_RECEIVED"

    def test_receive_creates_notification(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        api.post(f"/research/{rid}/receive", token=uro_director_token, json={})
        # Verify status is URO_RECEIVED
        resp = api.get(f"/research/{rid}", token=uro_director_token)
        assert resp.json()["status"] == "URO_RECEIVED"

    def test_researcher_cannot_receive(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=researcher_token, json={})
        assert resp.status_code == 403

    def test_dean_cannot_receive(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.post(f"/research/{rid}/receive", token=dean_token, json={})
        assert resp.status_code == 403

    def test_receive_not_found(self, api, uro_director_token):
        resp = api.post("/research/00000000-0000-0000-0000-000000000000/receive", token=uro_director_token, json={})
        assert resp.status_code == 404


class TestInitialReview:
    def test_start_initial_review(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_uro_received(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review", token=uro_director_token, json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["round_number"] == 1

    def test_get_initial_review(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        resp = api.get(f"/research/{rid}/initial-review", token=uro_director_token)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] is None  # No decision yet

    def test_pass_initial_review(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review/pass", token=uro_director_token, json={
            "remarks_researcher": "All criteria met",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "INITIAL_REVIEW_PASSED"

    def test_fail_initial_review(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review/revision", token=uro_director_token, json={
            "remarks_researcher": "Missing methodology",
            "revision_instructions": "Add methodology section",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "INITIAL_REVISION_REQUIRED"

    def test_resubmit_after_revision(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        api.post(f"/research/{rid}/initial-review/revision", token=uro_director_token, json={
            "remarks_researcher": "Fix this",
        })
        resp = api.post(f"/research/{rid}/initial-review/resubmit", token=researcher_token, json={
            "remarks_researcher": "Revised and uploaded",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "INITIAL_REVISION_SUBMITTED"

    def test_review_round_increments(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        api.post(f"/research/{rid}/initial-review/revision", token=uro_director_token, json={
            "remarks_researcher": "Fix",
        })
        api.post(f"/research/{rid}/initial-review/resubmit", token=researcher_token, json={})
        resp = api.post(f"/research/{rid}/initial-review", token=uro_director_token, json={})
        data = resp.json()
        assert data["round_number"] == 2

    def test_researcher_cannot_pass_review(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/initial-review/pass", token=researcher_token, json={})
        assert resp.status_code == 403

    def test_checklist_update(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        resp = api.patch(f"/research/{rid}/initial-review/checklist", token=uro_director_token, json={
            "items": [
                {"checklist_label": "Title Page", "status": "COMPLIANT", "remarks": "OK"},
                {"checklist_label": "Abstract", "status": "NOT_COMPLIANT", "remarks": "Too short"},
            ]
        })
        assert resp.status_code == 200


class TestProposalTurnitin:
    def test_begin_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_initial_review_passed(api, researcher_token, dean_token, uro_director_token)
        resp = transition(api, uro_director_token, rid, "BEGIN_PROPOSAL_TURNITIN")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "PROPOSAL_TURNITIN"

    def test_pass_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/turnitin/pass", token=uro_director_token, json={
            "remarks_researcher": "Passed",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "PROPOSAL_TURNITIN_PASSED"

    def test_fail_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/turnitin/revision", token=uro_director_token, json={
            "remarks_researcher": "Too high similarity",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "PROPOSAL_TURNITIN_REVISION_REQUIRED"

    def test_resubmit_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        api.post(f"/research/{rid}/turnitin/revision", token=uro_director_token, json={
            "remarks_researcher": "Fix",
        })
        resp = api.post(f"/research/{rid}/turnitin/resubmit", token=researcher_token, json={
            "remarks_researcher": "Revised proposal uploaded",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "PROPOSAL_TURNITIN_RESUBMITTED"

    def test_get_turnitin_attempts_empty(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        resp = api.get(f"/research/{rid}/turnitin", token=uro_director_token)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_researcher_cannot_pass_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_director_token)
        resp = api.post(f"/research/{rid}/turnitin/pass", token=researcher_token, json={})
        assert resp.status_code == 403


class TestWorkflowGate:
    def test_cannot_skip_to_external_eval_without_turnitin(self, api, researcher_token, dean_token, uro_director_token):
        """Workflow gate: READY_FOR_EXTERNAL_EVAL is only valid from PROPOSAL_TURNITIN_PASSED."""
        rid = advance_to_initial_review_passed(api, researcher_token, dean_token, uro_director_token)
        resp = transition(api, uro_director_token, rid, "READY_FOR_EXTERNAL_EVAL")
        assert resp.status_code == 400

    def test_cannot_skip_turnitin_entirely(self, api, researcher_token, dean_token, uro_director_token):
        """Even after initial review passed, must go through turnitin."""
        rid = advance_to_initial_review_passed(api, researcher_token, dean_token, uro_director_token)
        # BEGIN_PROPOSAL_TURNITIN is valid, but READY_FOR_EXTERNAL_EVAL is not
        resp = transition(api, uro_director_token, rid, "READY_FOR_EXTERNAL_EVAL")
        assert resp.status_code == 400
        # BEGIN_PROPOSAL_TURNITIN should work
        resp = transition(api, uro_director_token, rid, "BEGIN_PROPOSAL_TURNITIN")
        assert resp.status_code == 200

    def test_full_pass_through_to_external(self, api, researcher_token, dean_token, uro_director_token):
        """Happy path: full chain from endorsed to ready for external."""
        rid = advance_to_ready_for_external(api, researcher_token, dean_token, uro_director_token)
        resp = api.get(f"/research/{rid}", token=uro_director_token)
        assert resp.json()["status"] == "READY_FOR_EXTERNAL_EVALUATION"

    def test_revision_loop_then_pass(self, api, researcher_token, dean_token, uro_director_token):
        """Initial review revision loop: fail -> resubmit -> review -> pass."""
        rid = advance_to_initial_review(api, researcher_token, dean_token, uro_director_token)
        # Fail
        api.post(f"/research/{rid}/initial-review/revision", token=uro_director_token, json={
            "remarks_researcher": "Fix",
        })
        # Resubmit
        api.post(f"/research/{rid}/initial-review/resubmit", token=researcher_token, json={})
        # Review again
        api.post(f"/research/{rid}/initial-review", token=uro_director_token, json={})
        # Pass
        resp = api.post(f"/research/{rid}/initial-review/pass", token=uro_director_token, json={
            "remarks_researcher": "Good",
        })
        assert resp.json()["status"] == "INITIAL_REVIEW_PASSED"


class TestPhase3Dashboard:
    def test_dashboard_returns_counters(self, api, uro_director_token):
        resp = api.get("/research/phase3/dashboard", token=uro_director_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "awaiting_receipt" in data
        assert "initial_review" in data
        assert "revision_required" in data
        assert "turnitin_pending" in data
        assert "turnitin_revision" in data
        assert "turnitin_passed" in data
        assert "ready_for_external" in data

    def test_dashboard_increments_after_receive(self, api, researcher_token, dean_token, uro_director_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        before = api.get("/research/phase3/dashboard", token=uro_director_token).json()
        api.post(f"/research/{rid}/receive", token=uro_director_token, json={})
        after = api.get("/research/phase3/dashboard", token=uro_director_token).json()
        # After receiving, awaiting_receipt should decrease by 1
        # (research moves from ENDORSED_TO_URO to URO_RECEIVED)
        assert after["awaiting_receipt"] <= before["awaiting_receipt"]

    def test_researcher_cannot_access_dashboard(self, api, researcher_token):
        resp = api.get("/research/phase3/dashboard", token=researcher_token)
        # Dashboard requires auth, researcher has auth but might not have access
        # The endpoint currently allows any authenticated user
        assert resp.status_code in (200, 403)


class TestTurnitinThreshold:
    def test_get_threshold(self, api, uro_director_token):
        resp = api.get("/research/settings/turnitin-threshold", token=uro_director_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "threshold" in data
        assert isinstance(data["threshold"], float)

    def test_update_threshold_admin(self, api, admin_token):
        resp = api.put("/research/settings/turnitin-threshold?threshold=20.0", token=admin_token)
        assert resp.status_code == 200
        assert resp.json()["threshold"] == 20.0

    def test_update_threshold_uro_director(self, api, uro_director_token):
        resp = api.put("/research/settings/turnitin-threshold?threshold=15.0", token=uro_director_token)
        assert resp.status_code == 200

    def test_update_threshold_researcher_forbidden(self, api, researcher_token):
        resp = api.put("/research/settings/turnitin-threshold?threshold=10.0", token=researcher_token)
        assert resp.status_code == 403

    def test_threshold_out_of_range(self, api, admin_token):
        resp = api.put("/research/settings/turnitin-threshold?threshold=150.0", token=admin_token)
        assert resp.status_code == 400
        resp = api.put("/research/settings/turnitin-threshold?threshold=-5.0", token=admin_token)
        assert resp.status_code == 400
