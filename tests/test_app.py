import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_participants():
    """Reset all participant lists to a known state before each test."""
    original = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9

    def test_activity_has_expected_fields(self, client):
        response = client.get("/activities")
        activity = response.json()["Soccer Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        email = "newstudent@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        participants = client.get("/activities").json()["Chess Club"]["participants"]
        assert email in participants

    def test_duplicate_signup_returns_400(self, client):
        email = "newstudent@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        response = client.post("/activities/Chess Club/signup", params={"email": email})
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        response = client.delete(
            "/activities/Soccer Team/signup",
            params={"email": "lucas@mergington.edu"},
        )
        assert response.status_code == 200
        assert "lucas@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        email = "lucas@mergington.edu"
        client.delete("/activities/Soccer Team/signup", params={"email": email})
        participants = client.get("/activities").json()["Soccer Team"]["participants"]
        assert email not in participants

    def test_unregister_non_participant_returns_404(self, client):
        response = client.delete(
            "/activities/Soccer Team/signup",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Unknown Activity/signup",
            params={"email": "lucas@mergington.edu"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
