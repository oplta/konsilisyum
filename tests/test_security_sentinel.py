import pytest
import asyncio
from unittest.mock import MagicMock
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.models import Session, Agent, APIKey
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.memory import MemoryManager

@pytest.mark.asyncio
async def test_api_key_leakage_in_orchestrator_error():
    # Setup
    key_val = "sk-very-secret-key-123456789"
    api_key = APIKey(id="k1", key=key_val, is_pool=True)
    key_pool = KeyPool([api_key])

    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T", api_key_id="k1")
    session = Session(agents=[agent])
    memory = MemoryManager()

    # Mock API client to raise an exception containing the key
    api_client = MagicMock()
    api_client.complete_with_retry = MagicMock(side_effect=Exception(f"Error with key {key_val}"))

    orchestrator = Orchestrator(
        session=session,
        memory=memory,
        api_client=api_client,
        key_pool=key_pool
    )

    # Execute turn
    result = await orchestrator.execute_turn()

    # Verify NO leak
    assert result.error is not None
    assert key_val not in result.error, f"API Key {key_val} was leaked in the error message: {result.error}"

@pytest.mark.asyncio
async def test_api_key_leakage_in_keypool_report_error():
    key_val = "sk-another-secret-key"
    api_key = APIKey(id="k2", key=key_val, is_pool=True)
    key_pool = KeyPool([api_key])

    # Report error with the key in the message
    secret_leak = f"System failed while using {key_val}"
    key_pool.report_error("k2", secret_leak)

    key = key_pool.keys["k2"]
    assert key_val not in key.last_error, f"API Key was leaked in last_error: {key.last_error}"
    assert "..." in key.last_error
