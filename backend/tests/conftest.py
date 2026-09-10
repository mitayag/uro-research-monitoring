"""
Shared fixtures for URO Research Monitoring integration tests.
Runs against the live Docker API at http://api:8000.
"""
import os
import uuid
import pytest
import httpx

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"


class APIClient:
    """Thin wrapper around httpx.Client with auth helpers."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.prefix = API_PREFIX
        self._client = httpx.Client(base_url=base_url, timeout=30.0)
        self.tokens: dict[str, str] = {}

    def _url(self, path: str) -> str:
        return f"{self.prefix}{path}"

    def login(self, email: str, password: str) -> str:
        resp = self._client.post(
            self._url("/auth/login"),
            data={"username": email, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        return token

    def login_as(self, role: str) -> str:
        """Login as a predefined test user and cache the token."""
        if role in self.tokens:
            return self.tokens[role]

        credentials = {
            "researcher": ("researcher1@hau.edu.ph", "researcher123"),
            "dean": ("dean.soc@hau.edu.ph", "dean123"),
            "uro_director": ("uro.director@hau.edu.ph", "director123"),
            "uro_staff": ("uro.staff1@hau.edu.ph", "staff123"),
            "admin": ("admin@hau.edu.ph", "admin123"),
        }
        email, password = credentials[role]
        token = self.login(email, password)
        self.tokens[role] = token
        return token

    def get(self, path: str, token: str = None, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self._client.get(self._url(path), headers=headers, **kwargs)

    def post(self, path: str, token: str = None, json=None, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self._client.post(self._url(path), json=json, headers=headers, **kwargs)

    def patch(self, path: str, token: str = None, json=None, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self._client.patch(self._url(path), json=json, headers=headers, **kwargs)

    def put(self, path: str, token: str = None, json=None, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self._client.put(self._url(path), json=json, headers=headers, **kwargs)


@pytest.fixture(scope="session")
def api():
    """Shared API client for the entire test session."""
    client = APIClient()
    # Verify API is reachable
    resp = client._client.get(f"{BASE_URL}/api/v1/research/stats/summary",
                              headers={"Authorization": f"Bearer {client.login_as('admin')}"})
    assert resp.status_code == 200, f"API not reachable at {BASE_URL}"
    return client


@pytest.fixture(scope="session")
def researcher_token(api: APIClient):
    return api.login_as("researcher")


@pytest.fixture(scope="session")
def dean_token(api: APIClient):
    return api.login_as("dean")


@pytest.fixture(scope="session")
def uro_director_token(api: APIClient):
    return api.login_as("uro_director")


@pytest.fixture(scope="session")
def uro_staff_token(api: APIClient):
    return api.login_as("uro_staff")


@pytest.fixture(scope="session")
def admin_token(api: APIClient):
    return api.login_as("admin")


def create_research(api: APIClient, token: str, title: str = None) -> dict:
    """Create a new research project and return the response dict."""
    if title is None:
        title = f"Test Research {uuid.uuid4().hex[:8]}"
    resp = api.post("/research", token=token, json={
        "title": title,
        "authors": [{"name": "Test Author", "is_lead": True}],
    })
    assert resp.status_code == 201, f"Create research failed: {resp.text}"
    return resp.json()


def transition(api: APIClient, token: str, research_id: str, action: str) -> httpx.Response:
    """Perform a workflow transition."""
    return api.post(f"/research/{research_id}/transition", token=token, json={"action": action})


def advance_to_endorsed(api: APIClient, researcher_token: str, dean_token: str) -> str:
    """Create research and advance it to ENDORSED_TO_URO. Returns research_id."""
    r = create_research(api, researcher_token)
    rid = r["id"]
    transition(api, researcher_token, rid, "SUBMIT")
    transition(api, dean_token, rid, "DEAN_ENDORSE")
    return rid


def advance_to_uro_received(api: APIClient, researcher_token: str, dean_token: str, uro_token: str) -> str:
    """Advance to URO_RECEIVED. Returns research_id."""
    rid = advance_to_endorsed(api, researcher_token, dean_token)
    api.post(f"/research/{rid}/receive", token=uro_token, json={})
    return rid


def advance_to_initial_review(api: APIClient, researcher_token: str, dean_token: str, uro_token: str) -> str:
    """Advance to INITIAL_REVIEW. Returns research_id."""
    rid = advance_to_uro_received(api, researcher_token, dean_token, uro_token)
    api.post(f"/research/{rid}/initial-review", token=uro_token, json={})
    return rid


def advance_to_initial_review_passed(api: APIClient, researcher_token: str, dean_token: str, uro_token: str) -> str:
    """Advance to INITIAL_REVIEW_PASSED. Returns research_id."""
    rid = advance_to_initial_review(api, researcher_token, dean_token, uro_token)
    api.post(f"/research/{rid}/initial-review/pass", token=uro_token, json={"remarks_researcher": "All good"})
    return rid


def advance_to_proposal_turnitin(api: APIClient, researcher_token: str, dean_token: str, uro_token: str) -> str:
    """Advance to PROPOSAL_TURNITIN. Returns research_id."""
    rid = advance_to_initial_review_passed(api, researcher_token, dean_token, uro_token)
    transition(api, uro_token, rid, "BEGIN_PROPOSAL_TURNITIN")
    return rid


def advance_to_proposal_turnitin_passed(api: APIClient, researcher_token: str, dean_token: str, uro_token: str) -> str:
    """Advance to PROPOSAL_TURNITIN_PASSED. Returns research_id."""
    rid = advance_to_proposal_turnitin(api, researcher_token, dean_token, uro_token)
    api.post(f"/research/{rid}/turnitin/pass", token=uro_token, json={"remarks_researcher": "Passed"})
    return rid


def advance_to_ready_for_external(api: APIClient, researcher_token: str, dean_token: str, uro_token: str) -> str:
    """Advance to READY_FOR_EXTERNAL_EVALUATION. Returns research_id."""
    rid = advance_to_proposal_turnitin_passed(api, researcher_token, dean_token, uro_token)
    transition(api, uro_token, rid, "READY_FOR_EXTERNAL_EVAL")
    return rid
