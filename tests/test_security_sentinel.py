import pytest
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.memory import MemoryManager
from konsilisyum.api.mistral import MistralClient

def test_keypool_mask_secrets():
    keys = [
        APIKey(id="k1", key="sk-long-secret-key-12345678"),
        APIKey(id="k2", key="short"),
    ]
    pool = KeyPool(keys)

    text = "Error with sk-long-secret-key-12345678 and short key"
    masked = pool.mask_secrets(text)

    assert "sk-l...5678" in masked
    assert "sk-long-secret-key-12345678" not in masked
    assert "***" in masked
    assert "short" not in masked

def test_keypool_report_error_sanitization():
    keys = [APIKey(id="k1", key="sk-long-secret-key-12345678")]
    pool = KeyPool(keys)

    pool.report_error("k1", "Failed using key sk-long-secret-key-12345678")

    assert pool.keys["k1"].last_error == "Failed using key sk-l...5678"

@pytest.mark.asyncio
async def test_orchestrator_exception_redaction():
    # Setup
    session = Session(agents=[Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
    session.current_topic = Topic(content="Test")

    memory = MagicMock(spec=MemoryManager)
    memory.get_agent_memory.return_value = "No memory"
    memory.build_context_window.return_value = "Context"

    api_client = MagicMock(spec=MistralClient)
    # Simulate an exception that leaks the key
    api_client.complete_with_retry = AsyncMock(side_effect=Exception("Auth failed for sk-leaked-key-99998888"))

    keys = [APIKey(id="k1", key="sk-leaked-key-99998888", is_pool=True)]
    pool = KeyPool(keys)

    orchestrator = Orchestrator(session, memory, api_client, pool)

    # Execute
    result = await orchestrator.execute_turn()

    # Verify
    assert "sk-leaked-key-99998888" not in result.error
    assert "sk-l...8888" in result.error
