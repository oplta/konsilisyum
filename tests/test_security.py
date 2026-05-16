import pytest
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.models import Session, Agent, APIKey
from konsilisyum.api.keypool import KeyPool

@pytest.mark.asyncio
async def test_orchestrator_error_leaks_api_key():
    # Setup
    raw_key = "sk-mistral-secret-123456789"
    api_key = APIKey(id="k1", key=raw_key, is_pool=True)
    key_pool = KeyPool([api_key])

    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")
    session = Session(agents=[agent])
    memory = MagicMock()

    # Mock API client to throw an exception containing the raw key
    api_client = MagicMock()
    api_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Unauthorized: {raw_key}"))

    orchestrator = Orchestrator(
        session=session,
        memory=memory,
        api_client=api_client,
        key_pool=key_pool
    )

    # Execute turn
    result = await orchestrator.execute_turn()

    # Verification - It should NOT leak the key
    assert raw_key not in result.error
    assert "sk-m...6789" in result.error or "***" in result.error
    print(f"\n[SECURITY TEST] Masked error: {result.error}")

@pytest.mark.asyncio
async def test_keypool_report_error_leaks_api_key():
    raw_key = "sk-mistral-secret-987654321"
    api_key = APIKey(id="k1", key=raw_key, is_pool=True)
    key_pool = KeyPool([api_key])

    # Report error containing the raw key
    error_msg = f"API Error with key {raw_key}"
    key_pool.report_error("k1", error_msg)

    # Verification - KeyPool.report_error has some masking but it might be incomplete
    # or we want to verify centralized masking
    key = key_pool.keys["k1"]

    # Current implementation in keypool.py:
    # if key.key in error:
    #     error = error.replace(key.key, f"{key.key[:4]}...{key.key[-4:]}")

    # We want to ensure that even if multiple keys are present, they are all masked.
    # And we want to move to a more robust mask_secrets method.
    assert raw_key not in key.last_error
