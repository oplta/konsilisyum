import pytest
from unittest.mock import AsyncMock, MagicMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.memory import MemoryManager
from konsilisyum.api.mistral import MistralClient

def test_keypool_mask_secrets():
    keys = [
        APIKey(id="k1", key="sk-long-secret-key-12345", is_pool=True),
        APIKey(id="k2", key="short", is_pool=True),
    ]
    pool = KeyPool(keys)

    text = "Error: API key sk-long-secret-key-12345 is invalid. Also check short."
    masked = pool.mask_secrets(text)

    assert "sk-l...2345" in masked
    assert "sk-long-secret-key-12345" not in masked
    assert "***" in masked
    assert "short" not in masked

def test_keypool_report_error_masks_all_secrets():
    keys = [
        APIKey(id="k1", key="secret-one-123456789", is_pool=True),
        APIKey(id="k2", key="secret-two-987654321", is_pool=True),
    ]
    pool = KeyPool(keys)

    # Reporting error for k1, but the message contains k2's secret
    pool.report_error("k1", "Failed with key secret-two-987654321")

    key1 = pool.keys["k1"]
    assert "secr...4321" in key1.last_error
    assert "secret-two-987654321" not in key1.last_error

@pytest.mark.asyncio
async def test_orchestrator_execute_turn_masks_exceptions():
    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")
    session = Session(agents=[agent])
    session.current_topic = Topic(content="Test")
    memory = MemoryManager()

    secret = "sk-leaked-key-999"
    key_pool = KeyPool([APIKey(id="k1", key=secret, is_pool=True)])

    api_client = MagicMock(spec=MistralClient)
    # Simulate an exception that leaks the secret
    api_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Unauthorized: {secret}"))

    orchestrator = Orchestrator(session, memory, api_client, key_pool)

    result = await orchestrator.execute_turn()

    assert result.error is not None
    assert "sk-l...-999" in result.error
    assert secret not in result.error
