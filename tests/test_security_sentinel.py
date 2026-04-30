import pytest
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Agent, Session, Topic
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.memory import MemoryManager
from unittest.mock import MagicMock
import asyncio

def test_api_key_leakage_in_orchestrator_error():
    # Setup
    key = "sk-leaked-key-123456789"
    api_key = APIKey(id="k1", key=key, is_pool=True)
    pool = KeyPool([api_key])

    # Mock API client to raise an exception containing the key
    mock_api = MagicMock()
    mock_api.complete_with_retry.side_effect = Exception(f"Failed with key {key}")

    agent = Agent(name="Test", role="R", goal="G", blind_spot="B", style="S", trigger="T")
    session = Session(agents=[agent], current_topic=Topic(content="Test"))

    memory = MemoryManager()

    orchestrator = Orchestrator(session, memory, mock_api, pool)

    # Execute
    result = asyncio.run(orchestrator.execute_turn())

    # Verify
    assert key not in result.error
    assert "sk-l...6789" in result.error

def test_api_key_leakage_in_keypool_report_error():
    key = "sk-leaked-key-123456789"
    api_key = APIKey(id="k1", key=key, is_pool=True)
    pool = KeyPool([api_key])

    pool.report_error("k1", f"Error with key {key}")

    assert key not in pool.keys["k1"].last_error
    assert "sk-l...6789" in pool.keys["k1"].last_error
