import pytest
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.memory import MemoryManager

def test_keypool_mask_secrets():
    key1 = APIKey(id="k1", key="sk-1234567890abcdef")
    key2 = APIKey(id="k2", key="short")
    pool = KeyPool([key1, key2])

    # Check if we can mask secrets (this method will be added)
    if hasattr(pool, "mask_secrets"):
        text = "Error occurred with key sk-1234567890abcdef and short"
        masked = pool.mask_secrets(text)
        assert "sk-1...cdef" in masked
        assert "sk-1234567890abcdef" not in masked
        assert "***" in masked
        assert "short" not in masked

@pytest.mark.asyncio
async def test_orchestrator_leaks_key_in_exception():
    key_val = "sk-leaky-key-12345"
    key = APIKey(id="k1", key=key_val, is_pool=True)
    pool = KeyPool([key])

    session = Session(agents=[Agent(name="A1", role="R", goal="G", blind_spot="B", style="S", trigger="T")])
    session.current_topic = Topic(content="T")
    memory = MemoryManager()

    mock_client = MagicMock()
    # Mocking complete_with_retry to raise an exception containing the key
    mock_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Failed with {key_val}"))

    orchestrator = Orchestrator(session, memory, mock_client, pool)

    result = await orchestrator.execute_turn()

    assert result.error is not None
    # Currently, it leaks. After fix, it should be masked.
    # To make this a reproduction, we expect it to BE in result.error for now,
    # or we can write the test to expect it NOT to be there and watch it fail.
    # Let's expect it NOT to be there, so it fails now.
    assert key_val not in result.error, f"API Key leaked in error message: {result.error}"

def test_keypool_report_error_sanitization():
    key_val = "sk-secret-key-to-mask"
    key = APIKey(id="k1", key=key_val)
    pool = KeyPool([key])

    pool.report_error("k1", f"Something went wrong with {key_val}")

    # KeyPool already has some sanitization, let's verify it
    assert key_val not in key.last_error
    assert "sk-s...mask" in key.last_error
