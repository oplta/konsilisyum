import pytest
import os
from pathlib import Path
from konsilisyum.core.models import Session, Agent, APIKey, SpeakerType, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager
from konsilisyum.core.memory import MemoryManager
from konsilisyum.api.keypool import KeyPool
from konsilisyum.api.mistral import MistralClient

@pytest.mark.asyncio
async def test_orchestrator_error_redaction():
    # Setup
    key = APIKey(id="test-key", key="sk-secret-1234567890", is_pool=True)
    pool = KeyPool([key])
    memory = MemoryManager()

    class MockMistralClient:
        async def complete_with_retry(self, **kwargs):
            raise Exception("Unauthorized: sk-secret-1234567890 has expired")

    session = Session(agents=[Agent(name="A", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
    orchestrator = Orchestrator(session, memory, MockMistralClient(), pool)

    # Execute
    result = await orchestrator.execute_turn()

    # Verify
    assert "sk-secret-1234567890" not in result.error
    assert "sk-s...7890" in result.error or "***" in result.error

def test_session_manager_traversal():
    sm = SessionManager(sessions_dir="data/test_sessions")
    # We want to check if save() uses _safe_path for all files it writes
    # If it doesn't, it might write to a location outside sessions_dir
    session = Session(id="traversal")
    session.id = "../traversal"

    # We expect this to fail due to _safe_path for .json
    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm.save(session)

@pytest.mark.asyncio
async def test_keypool_mask_secrets():
    key = APIKey(id="test", key="supersecretkey123")
    pool = KeyPool([key])

    error_msg = "Error using supersecretkey123: access denied"
    pool.report_error("test", error_msg)

    assert "supersecretkey123" not in pool.keys["test"].last_error
    assert "supe...y123" in pool.keys["test"].last_error
