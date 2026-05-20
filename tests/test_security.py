import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock
from konsilisyum.core.session import SessionManager
from konsilisyum.core.models import Session, Message, SpeakerType, APIKey, Agent
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.orchestrator import Orchestrator

def test_session_manager_traversal_save(tmp_path):
    sessions_dir = tmp_path / "sessions"
    sm = SessionManager(sessions_dir=str(sessions_dir))

    malicious_id = "../evil"
    session = Session(id=malicious_id)

    with pytest.raises(ValueError, match="Invalid session ID"):
        sm.save(session)

def test_key_masking_robustness():
    key1 = APIKey(id="k1", key="secret-key-11111")
    key2 = APIKey(id="k2", key="secret-key-22222")
    pool = KeyPool([key1, key2])

    # If we report an error for k1, but the error message contains k2's key
    error_msg = "Error involving secret-key-22222 and secret-key-11111"
    pool.report_error("k1", error_msg)

    # Both keys should be masked in k1's last_error
    last_error = pool.keys["k1"].last_error
    assert "secret-key-11111" not in last_error
    assert "secret-key-22222" not in last_error
    assert "secr...1111" in last_error
    assert "secr...2222" in last_error

@pytest.mark.asyncio
async def test_orchestrator_error_redaction():
    key = APIKey(id="k1", key="secret-key-123456789")
    pool = KeyPool([key])

    session = Session()
    session.agents = [Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T", api_key_id="k1")]

    mock_api = MagicMock()
    # Mock complete_with_retry to raise an exception containing the secret
    mock_api.complete_with_retry.side_effect = Exception("Failed with key secret-key-123456789")

    orch = Orchestrator(session, MagicMock(), mock_api, pool)

    result = await orch.execute_turn()

    assert "secret-key-123456789" not in result.error
    assert "secr...6789" in result.error
