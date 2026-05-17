import pytest
import asyncio
import os
from unittest.mock import MagicMock
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import Session, APIKey, Agent
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.session import SessionManager

@pytest.mark.asyncio
async def test_orchestrator_mask_secrets():
    key = "sk-very-secret-key-123456789"
    api_key = APIKey(id="k1", key=key, is_pool=True)
    key_pool = KeyPool([api_key])

    session = Session()
    agent = Agent(name="TestAgent", role="R", goal="G", blind_spot="B", style="S", trigger="T")
    session.agents.append(agent)

    memory = MemoryManager()

    api_client = MagicMock()
    # Mocking complete_with_retry to raise an exception containing the key
    api_client.complete_with_retry.side_effect = Exception(f"Unauthorized: API key {key} is invalid")

    orchestrator = Orchestrator(session, memory, api_client, key_pool)

    result = await orchestrator.execute_turn()

    assert key not in result.error
    assert "sk-v...6789" in result.error

def test_keypool_report_error_masking():
    key = "sk-secret-12345"
    api_key = APIKey(id="k1", key=key)
    pool = KeyPool([api_key])

    pool.report_error("k1", f"Error with key {key}")

    assert key not in api_key.last_error
    assert "sk-s...2345" in api_key.last_error

def test_session_manager_path_traversal():
    sm = SessionManager(sessions_dir="data/test_sessions")
    session = Session(id="../traversal_test")

    with pytest.raises(ValueError, match="Invalid session ID"):
        sm.save(session)

    assert not os.path.exists("data/traversal_test.jsonl")
    assert not os.path.exists("traversal_test.jsonl")

def test_keypool_multi_key_masking():
    k1 = "secret-key-one-12345"
    k2 = "shortkey"  # 8 characters
    pool = KeyPool([
        APIKey(id="1", key=k1),
        APIKey(id="2", key=k2)
    ])

    text = f"Leaking {k1} and {k2}"
    masked = pool.mask_secrets(text)

    assert k1 not in masked
    assert k2 not in masked
    assert "secr...2345" in masked
    assert "***" in masked
