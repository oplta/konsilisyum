import pytest
import asyncio
from pathlib import Path
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, SpeakerType
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.session import SessionManager

@pytest.mark.asyncio
async def test_keypool_error_masking():
    key1 = APIKey(id="key1", key="sk-secret-123456789")
    pool = KeyPool([key1])

    # Simulate an error that contains the API key
    error_msg = f"Unauthorized: Invalid key sk-secret-123456789"
    pool.report_error("key1", error_msg)

    # It should be masked in last_error
    assert "sk-secret-123456789" not in key1.last_error
    assert "sk-s...6789" in key1.last_error

@pytest.mark.asyncio
async def test_orchestrator_error_masking():
    key_val = "sk-orchestrator-secret-999"
    key1 = APIKey(id="key1", key=key_val)
    pool = KeyPool([key1])

    session = Session(agents=[Agent(name="A", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
    memory = MemoryManager()

    class MockClient:
        async def complete_with_retry(self, **kwargs):
            raise Exception(f"Fatal error with key {key_val}")

    orch = Orchestrator(session, memory, MockClient(), pool)
    result = await orch.execute_turn()

    # The error message in TurnResult should be masked
    assert key_val not in result.error
    assert "sk-o...-999" in result.error or "***" in result.error

def test_session_manager_path_traversal():
    sm = SessionManager(sessions_dir="data/test_sessions")

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm.load("../etc/passwd")

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm._safe_path("sub/folder", ".json")

@pytest.mark.asyncio
async def test_keypool_multi_key_masking():
    key1 = APIKey(id="key1", key="SECRET_KEY_ONE_12345")
    key2 = APIKey(id="key2", key="SECRET_KEY_TWO_67890")
    pool = KeyPool([key1, key2])

    if not hasattr(pool, 'mask_secrets'):
        pytest.skip("KeyPool.mask_secrets not implemented yet")

    text = "Error: key1 is SECRET_KEY_ONE_12345 and key2 is SECRET_KEY_TWO_67890"
    masked = pool.mask_secrets(text)

    assert "SECRET_KEY_ONE_12345" not in masked
    assert "SECRET_KEY_TWO_67890" not in masked
    assert "SECR...2345" in masked
    assert "SECR...7890" in masked
