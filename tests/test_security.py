import pytest
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.core.models import APIKey, Agent, Session, SpeakerType
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.memory import MemoryManager

def test_key_leakage_in_keypool():
    key1_val = "sk-key-one-1234567890"
    key2_val = "sk-key-two-0987654321"
    pool = KeyPool([
        APIKey(id="k1", key=key1_val),
        APIKey(id="k2", key=key2_val)
    ])

    # Scenario: Error for k1 contains k2 (leaking another key)
    error_msg = f"Failed using {key1_val}, tried fallback to {key2_val}"
    pool.report_error("k1", error_msg)

    # Current implementation masks its own key (k1) but not others (k2)
    # This should fail if we want ALL managed keys masked
    assert key1_val not in pool.keys["k1"].last_error
    assert key2_val not in pool.keys["k1"].last_error

@pytest.mark.asyncio
async def test_key_leakage_in_orchestrator():
    key_val = "sk-mistral-abcdef123456"
    pool = KeyPool([APIKey(id="k1", key=key_val)])

    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T", api_key_id="k1")
    session = Session(agents=[agent])
    memory = MemoryManager()

    # Mock API Client to throw error with key
    api_client = MagicMock()
    api_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Critical error: {key_val} leaked"))

    orch = Orchestrator(session, memory, api_client, pool)
    result = await orch.execute_turn()

    # This currently leaks the key
    assert result.error is not None
    assert key_val not in result.error
