import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from konsilisyum.web.app import app
from konsilisyum.web.routes import _sessions


@pytest.fixture
def client():
    _sessions.clear()
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEYS", "test-key-1,test-key-2,test-key-3")


class TestCreateSession:
    def test_create_session_success(self, client):
        response = client.post("/api/sessions", json={"topic": "Test konusu"})
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Test konusu"
        assert data["status"] == "running"
        assert len(data["agents"]) == 3
        assert data["turn"] == 0

    def test_create_session_returns_agents(self, client):
        response = client.post("/api/sessions", json={"topic": "Test"})
        data = response.json()
        agent_names = [a["name"] for a in data["agents"]]
        assert "Atlas" in agent_names
        assert "Mira" in agent_names
        assert "Kaan" in agent_names

    def test_create_session_stores_in_memory(self, client):
        response = client.post("/api/sessions", json={"topic": "Test"})
        session_id = response.json()["id"]
        assert session_id in _sessions


class TestGetSession:
    def test_get_existing_session(self, client):
        create_resp = client.post("/api/sessions", json={"topic": "Test"})
        session_id = create_resp.json()["id"]

        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["topic"] == "Test"

    def test_get_nonexistent_session(self, client):
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404


class TestListSessions:
    def test_list_sessions_empty(self, client):
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
