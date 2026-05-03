import pytest
import os
from pathlib import Path
from konsilisyum.core.models import Session, Message, SpeakerType, APIKey, Agent
from konsilisyum.core.session import SessionManager
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.orchestrator import Orchestrator
from unittest.mock import MagicMock, AsyncMock

def test_session_manager_path_traversal_protection(tmp_path):
    sm = SessionManager(sessions_dir=str(tmp_path))
    session = Session(id="../traversal")

    # This should raise ValueError because _safe_path is called in save()
    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm.save(session)

def test_key_pool_mask_secrets():
    keys = [
        APIKey(id="k1", key="sk-1234567890abcdef"),
        APIKey(id="k2", key="short")
    ]
    pool = KeyPool(keys)

    text = "Error with key sk-1234567890abcdef and short"
    masked = pool.mask_secrets(text)
    assert "sk-1...cdef" in masked
    assert "sk-1234567890abcdef" not in masked
    assert "***" in masked
    assert "short" not in masked

@pytest.mark.asyncio
async def test_orchestrator_exception_redaction():
    session = Session(agents=[Agent(name="Atlas", role="Stratejist", goal="X", blind_spot="Y", style="Z", trigger="T")])
    key = APIKey(id="k1", key="sk-SECRET-KEY-1234")
    pool = KeyPool([key])

    api_client = MagicMock()
    api_client.complete_with_retry = AsyncMock(side_effect=Exception("Failed with sk-SECRET-KEY-1234"))

    memory = MagicMock()

    orch = Orchestrator(session, memory, api_client, pool)

    result = await orch.execute_turn()

    assert result.error is not None
    assert "sk-SECRET-KEY-1234" not in result.error
    assert "sk-S...1234" in result.error
