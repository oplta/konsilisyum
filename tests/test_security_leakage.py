import pytest
import asyncio
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Session, Agent
from konsilisyum.core.memory import MemoryManager
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_api_key_leakage_in_orchestrator_error():
    # Setup
    secret_key = "sk-sensitive-key-12345678"
    api_key = APIKey(id="key-1", key=secret_key, is_pool=True)
    key_pool = KeyPool([api_key])

    session = Session()
    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")
    session.agents.append(agent)

    memory = MemoryManager()

    api_client = MagicMock()
    # Simulate an error that contains the API key
    api_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Invalid request with key: {secret_key}"))

    orchestrator = Orchestrator(session, memory, api_client, key_pool)

    # Execute
    result = await orchestrator.execute_turn()

    # Verify
    assert result.error is not None
    assert secret_key not in result.error
    assert "sk-s...5678" in result.error or "***" in result.error
