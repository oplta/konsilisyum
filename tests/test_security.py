import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, SessionStatus
from konsilisyum.core.orchestrator import Orchestrator

class TestSecurity:
    def test_keypool_report_error_sanitization(self):
        key = APIKey(id="k1", key="secret-api-key-12345")
        pool = KeyPool([key])

        # Simulating an error message that contains the API key
        error_msg = "Authentication failed for key: secret-api-key-12345"
        pool.report_error("k1", error_msg)

        # Check if the key is masked in last_error
        assert "secret-api-key-12345" not in key.last_error
        assert "secr...2345" in key.last_error

    @pytest.mark.asyncio
    async def test_orchestrator_error_sanitization(self):
        key = APIKey(id="k1", key="secret-api-key-12345")
        pool = KeyPool([key])
        agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T", api_key_id="k1")
        session = Session(agents=[agent])
        memory = MagicMock()
        api_client = MagicMock()

        # Mocking an exception that leaks the API key
        api_client.complete_with_retry = AsyncMock(side_effect=Exception("Failed with key secret-api-key-12345"))

        orchestrator = Orchestrator(session, memory, api_client, pool)

        result = await orchestrator.execute_turn()

        assert result.error is not None
        assert "secret-api-key-12345" not in result.error
