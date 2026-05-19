import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Session, Agent, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager
from konsilisyum.core.memory import MemoryManager

@pytest.mark.asyncio
async def test_orchestrator_masks_secrets_in_errors():
    secret_key = "sk-sensitive-key-12345"
    key_pool = KeyPool([APIKey(id="k1", key=secret_key, is_pool=True)])

    session = Session(agents=[Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
    memory = MemoryManager()

    api_client = MagicMock()
    # Mock complete_with_retry to raise an exception containing the secret
    api_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Error with key {secret_key}"))

    orchestrator = Orchestrator(session, memory, api_client, key_pool)

    result = await orchestrator.execute_turn()

    assert result.error is not None
    assert secret_key not in result.error
    assert "sk-s...2345" in result.error

def test_keypool_masks_all_secrets_in_report_error():
    key1 = "sk-key-one-1111"
    key2 = "sk-key-two-2222"
    pool = KeyPool([
        APIKey(id="k1", key=key1),
        APIKey(id="k2", key=key2)
    ])

    # report error for k1, but message contains k2 as well
    error_msg = f"Failed using {key1}, also leaked {key2}"
    pool.report_error("k1", error_msg)

    reported_error = pool.keys["k1"].last_error
    assert key1 not in reported_error
    assert key2 not in reported_error

def test_session_manager_directory_traversal_jsonl(tmp_path):
    sessions_dir = tmp_path / "sessions"
    sm = SessionManager(sessions_dir=str(sessions_dir))

    bad_session_id = "../evil"
    session = Session(id=bad_session_id)

    # This should raise ValueError because of _safe_path
    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm.save(session)

    # Check if evil.jsonl was created in the parent directory
    evil_jsonl = tmp_path / "evil.jsonl"
    assert not evil_jsonl.exists()
