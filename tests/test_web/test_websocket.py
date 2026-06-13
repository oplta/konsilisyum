import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from konsilisyum.web.app import app
from konsilisyum.web.routes import _sessions


@pytest.fixture
def client():
    _sessions.clear()
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEYS", "test-key-1,test-key-2,test-key-3")


class TestWebSocketConnection:
    def test_ws_nonexistent_session(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/session/nonexistent-id"):
                pass

    def test_ws_connect_sends_session_state(self, client):
        create_resp = client.post("/api/sessions", json={"topic": "WS Test"})
        session_id = create_resp.json()["id"]

        with client.websocket_connect(f"/ws/session/{session_id}") as ws:
            data = ws.receive_json()
            assert data["type"] == "session_state"
            assert data["topic"] == "WS Test"
            assert len(data["agents"]) == 3
            assert data["status"] == "running"

    def test_ws_command_pause(self, client):
        create_resp = client.post("/api/sessions", json={"topic": "Pause Test"})
        session_id = create_resp.json()["id"]

        with client.websocket_connect(f"/ws/session/{session_id}") as ws:
            ws.receive_json()

            ws.send_json({"type": "command", "cmd": "pause"})

            data = ws.receive_json()
            while data.get("type") != "status":
                data = ws.receive_json()
            assert data["status"] == "paused"

    def test_ws_command_topic(self, client):
        create_resp = client.post("/api/sessions", json={"topic": "Original"})
        session_id = create_resp.json()["id"]

        with client.websocket_connect(f"/ws/session/{session_id}") as ws:
            ws.receive_json()

            ws.send_json({"type": "command", "cmd": "topic", "args": {"topic": "Yeni konu"}})

            received_topic = False
            for _ in range(10):
                data = ws.receive_json()
                if data.get("type") == "topic_changed":
                    assert data["topic"] == "Yeni konu"
                    received_topic = True
                    break
            assert received_topic
