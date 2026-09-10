"""Tests: Workflow transitions — happy paths, invalid transitions, status history."""
import pytest
from tests.conftest import create_research, transition, advance_to_endorsed


class TestSubmissionWorkflow:
    def test_draft_to_submitted(self, api, researcher_token):
        """SUBMIT now auto-routes to FOR_DEAN_ENDORSEMENT."""
        r = create_research(api, researcher_token)
        resp = transition(api, researcher_token, r["id"], "SUBMIT")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "FOR_DEAN_ENDORSEMENT"

    def test_submitted_to_forward_to_dean(self, api, researcher_token):
        """SUBMIT goes directly to FOR_DEAN_ENDORSEMENT (no separate FORWARD_TO_DEAN)."""
        r = create_research(api, researcher_token)
        resp = transition(api, researcher_token, r["id"], "SUBMIT")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "FOR_DEAN_ENDORSEMENT"

    def test_dean_endorse(self, api, researcher_token, dean_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        resp = transition(api, dean_token, r["id"], "DEAN_ENDORSE")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "ENDORSED_TO_URO"

    def test_dean_reject(self, api, researcher_token, dean_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        resp = transition(api, dean_token, r["id"], "DEAN_REJECT")
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "DRAFT"


class TestInvalidTransitions:
    def test_cannot_submit_from_endorsed(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = transition(api, researcher_token, rid, "SUBMIT")
        assert resp.status_code == 400

    def test_cannot_dean_endorse_from_draft(self, api, researcher_token, dean_token):
        r = create_research(api, researcher_token)
        resp = transition(api, dean_token, r["id"], "DEAN_ENDORSE")
        assert resp.status_code == 400

    def test_cannot_receive_from_draft(self, api, researcher_token, uro_director_token):
        r = create_research(api, researcher_token)
        resp = api.post(f"/research/{r['id']}/receive", token=uro_director_token, json={})
        assert resp.status_code == 400

    def test_invalid_action_name(self, api, researcher_token):
        r = create_research(api, researcher_token)
        resp = transition(api, researcher_token, r["id"], "NONEXISTENT_ACTION")
        assert resp.status_code == 400


class TestStatusHistory:
    def test_history_recorded_after_transition(self, api, researcher_token):
        r = create_research(api, researcher_token)
        transition(api, researcher_token, r["id"], "SUBMIT")
        resp = api.get(f"/research/{r['id']}/history", token=researcher_token)
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) >= 1
        actions = [h["action"] for h in history]
        assert "SUBMIT" in actions

    def test_history_shows_all_transitions(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.get(f"/research/{rid}/history", token=researcher_token)
        history = resp.json()
        actions = [h["action"] for h in history]
        assert "SUBMIT" in actions
        assert "DEAN_ENDORSE" in actions


class TestValidActions:
    def test_valid_actions_for_draft(self, api, researcher_token):
        r = create_research(api, researcher_token)
        resp = api.get(f"/research/{r['id']}/valid-actions", token=researcher_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "SUBMIT" in data["all_actions"]

    def test_valid_actions_for_endorsed(self, api, researcher_token, dean_token):
        rid = advance_to_endorsed(api, researcher_token, dean_token)
        resp = api.get(f"/research/{rid}/valid-actions", token=dean_token)
        data = resp.json()
        assert data["current_status"] == "ENDORSED_TO_URO"
