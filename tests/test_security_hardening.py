import pytest
import asyncio
from unittest.mock import MagicMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Session, Agent
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager

def test_api_key_masking():
    keys = [
        APIKey(id="k1", key="sk-1234567890abcdef"),
        APIKey(id="k2", key="short"),
    ]
    pool = KeyPool(keys)

    # Test mask_secrets
    text = "Error with key sk-1234567890abcdef and another short"
    masked = pool.mask_secrets(text)
    assert "sk-1234567890abcdef" not in masked
    assert "sk-1...cdef" in masked
    assert "short" not in masked
    assert "***" in masked

    # Test report_error
    pool.report_error("k1", "Failed for sk-1234567890abcdef")
    assert "sk-1234567890abcdef" not in pool.keys["k1"].last_error
    assert "sk-1...cdef" in pool.keys["k1"].last_error

@pytest.mark.asyncio
async def test_orchestrator_error_masking():
    keys = [APIKey(id="k1", key="sk-secret-key-12345")]
    pool = KeyPool(keys)

    session = Session(agents=[Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
    memory = MemoryManager()
    api_client = MagicMock()

    # Mock complete_with_retry to raise an error containing the secret
    api_client.complete_with_retry.side_effect = Exception("Auth failed for sk-secret-key-12345")

    orch = Orchestrator(session, memory, api_client, pool)
    result = await orch.execute_turn()

    assert "sk-secret-key-12345" not in result.error
    assert "sk-s...2345" in result.error

def test_session_path_traversal():
    sm = SessionManager(sessions_dir="/tmp/sessions")
    session = Session(id="../evil")

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm.save(session)

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm.load("../evil")
