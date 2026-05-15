import pytest
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager
from pathlib import Path

class TestSecurity:
    def test_key_masking_logic(self):
        keys = [
            APIKey(id="k1", key="sk-1234567890abcdef"), # Long key
            APIKey(id="k2", key="secret"),             # Short key
        ]
        pool = KeyPool(keys)

        text = "Error with sk-1234567890abcdef and secret"
        masked = pool.mask_secrets(text)

        assert "sk-1...cdef" in masked
        assert "***" in masked
        assert "sk-1234567890abcdef" not in masked
        assert "secret" not in masked

    def test_report_error_masking(self):
        keys = [APIKey(id="k1", key="sk-longsecretkey123")]
        pool = KeyPool(keys)

        pool.report_error("k1", "Failed with sk-longsecretkey123")
        assert "sk-l...y123" in pool.keys["k1"].last_error
        assert "sk-longsecretkey123" not in pool.keys["k1"].last_error

    @pytest.mark.asyncio
    async def test_orchestrator_error_masking(self):
        keys = [APIKey(id="k1", key="sk-leakedkey")]
        pool = KeyPool(keys)

        session = Session(agents=[Agent(name="A", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
        session.current_topic = Topic(content="Test")
        memory = MagicMock()
        api_client = MagicMock()
        # Mock completion to raise exception containing the key
        api_client.complete_with_retry = AsyncMock(side_effect=Exception("Unauthorized: sk-leakedkey"))

        orch = Orchestrator(session, memory, api_client, pool)
        result = await orch.execute_turn()

        assert "sk-l...dkey" in result.error
        assert "sk-leakedkey" not in result.error

    def test_session_manager_traversal(self, tmp_path):
        sm = SessionManager(sessions_dir=str(tmp_path))

        with pytest.raises(ValueError, match="Gecersiz oturum ID"):
            sm._safe_path("../etc/passwd", ".json")

        with pytest.raises(ValueError, match="Gecersiz oturum ID"):
            sm._safe_path("sub/dir", ".json")

    def test_session_manager_save_traversal_prevention(self, tmp_path):
        sm = SessionManager(sessions_dir=str(tmp_path))
        session = Session(id="../traversal")

        with pytest.raises(ValueError, match="Gecersiz oturum ID"):
            sm.save(session)
