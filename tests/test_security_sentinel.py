import pytest
from unittest.mock import MagicMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, Message, SpeakerType
from konsilisyum.core.orchestrator import Orchestrator, TurnResult
from konsilisyum.core.memory import MemoryManager

@pytest.mark.asyncio
async def test_api_key_leakage_in_orchestrator_fixed():
    # Setup
    key_val = "sk-mistral-very-secret-key-12345678"
    api_key = APIKey(id="test-key", key=key_val, is_pool=True)
    key_pool = KeyPool([api_key])

    agent = Agent(name="TestAgent", role="Tester", goal="Test", blind_spot="None", style="Normal", trigger="None")
    session = Session(agents=[agent])
    memory = MemoryManager()

    # Mock API client to raise an exception containing the key
    api_client = MagicMock()
    api_client.complete_with_retry.side_effect = Exception(f"Failed with key {key_val}")

    orchestrator = Orchestrator(
        session=session,
        memory=memory,
        api_client=api_client,
        key_pool=key_pool
    )

    # Execute turn
    result = await orchestrator.execute_turn()

    # Verify leak is gone
    assert key_val not in result.error
    assert "sk-m...5678" in result.error
    print(f"\nRedacted error: {result.error}")

def test_key_pool_mask_secrets_exists():
    key_pool = KeyPool([APIKey(id="k1", key="secret-key-long-enough")])
    assert hasattr(key_pool, 'mask_secrets')

    masked = key_pool.mask_secrets("My secret is secret-key-long-enough")
    assert masked == "secr...ough" or masked == "My secret is secr...ough"
