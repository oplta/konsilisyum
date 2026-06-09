import pytest
import os
import shutil
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Session, Agent
from konsilisyum.core.session import SessionManager
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.orchestrator import Orchestrator


class TestSecurity:
    def test_mask_secrets_logic(self):
        pool = KeyPool([
            APIKey(id="k1", key="sk-long-key-12345678"),
            APIKey(id="k2", key="short"),
        ])

        # Test long key masking (4+4)
        text1 = "Error: invalid key sk-long-key-12345678"
        masked1 = pool.mask_secrets(text1)
        assert "sk-l...5678" in masked1
        assert "sk-long-key-12345678" not in masked1

        # Test short key masking (***)
        text2 = "Auth failed for short"
        masked2 = pool.mask_secrets(text2)
        assert "***" in masked2
        assert "short" not in masked2

        # Test multiple keys and overlapping
        pool.keys["k3"] = APIKey(id="k3", key="sk-long-key") # Substring of k1 if I wasn't careful
        text3 = "Keys: sk-long-key-12345678 and sk-long-key"
        masked3 = pool.mask_secrets(text3)
        assert "sk-l...5678" in masked3
        assert "sk-l...-key" in masked3
        assert "sk-long-key-12345678" not in masked3
        assert "sk-long-key" not in masked3

    def test_session_path_traversal_prevention(self):
        test_dir = Path("test_security_sessions")
        if test_dir.exists():
            shutil.rmtree(test_dir)

        sm = SessionManager(sessions_dir=str(test_dir))

        # Traversal in session ID
        bad_id = "../outside"
        session = Session(id=bad_id)

        with pytest.raises(ValueError, match="Gecersiz oturum ID"):
            sm.save(session)

        # Ensure no files were created outside
        outside_json = Path("outside.json")
        outside_jsonl = Path("outside.jsonl")
        assert not outside_json.exists()
        assert not outside_jsonl.exists()

        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_report_error_sanitization(self):
        pool = KeyPool([
            APIKey(id="k1", key="sk-secret-key-999"),
        ])

        # Report error containing the key
        pool.report_error("k1", "Failed with sk-secret-key-999 at line 10")

        key = pool.keys["k1"]
        assert "sk-s...-999" in key.last_error
        assert "sk-secret-key-999" not in key.last_error


@pytest.mark.asyncio
async def test_orchestrator_masks_key_in_error():
    # Setup
    key_val = "sk-secret-123456789"
    api_key = APIKey(id="k1", key=key_val, is_pool=True)
    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T", api_key_id="k1")
    session = Session(agents=[agent])
    memory = MemoryManager()

    key_pool = KeyPool([api_key])

    api_client = MagicMock()
    # Simulate an error that contains the key
    api_client.complete_with_retry = AsyncMock(side_effect=Exception(f"Invalid key: {key_val}"))

    orchestrator = Orchestrator(session, memory, api_client, key_pool)

    # Execute
    result = await orchestrator.execute_turn()

    # Verify
    assert key_val not in result.error
    assert "sk-s...6789" in result.error


def test_keypool_mask_secrets_ordering():
    # Test that longer keys are masked first
    key1 = "secret_long"
    key2 = "secret"
    pool = KeyPool([
        APIKey(id="k1", key=key1),
        APIKey(id="k2", key=key2)
    ])

    text = f"My keys are {key1} and {key2}"
    masked = pool.mask_secrets(text)

    assert key1 not in masked
    assert key2 not in masked
    assert "secr...long" in masked
    assert "***" in masked


# Sentinel: Additional security tests

@pytest.mark.asyncio
async def test_mask_secrets_function():
    k1 = APIKey(id="k1", key="sk-123456789", is_pool=True)
    k2 = APIKey(id="k2", key="abc", is_pool=True)
    pool = KeyPool([k1, k2])

    text = "Error with key sk-123456789 and small key abc"
    masked = pool.mask_secrets(text)

    assert "sk-123456789" not in masked
    assert "abc" not in masked
    assert "sk-1...6789" in masked
    assert "***" in masked


@pytest.mark.asyncio
async def test_orchestrator_error_redaction():
    key_val = "sk-secret-key-999"
    key = APIKey(id="k1", key=key_val, is_pool=True)
    pool = KeyPool([key])

    session = Session()
    agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T")
    session.agents.append(agent)

    api_client = MagicMock()
    api_client.complete_with_retry.side_effect = Exception(f"Connection failed for {key_val}")

    memory = MagicMock()
    orch = Orchestrator(session, memory, api_client, pool)

    result = await orch.execute_turn()
    assert key_val not in result.error
    assert "sk-s...-999" in result.error


def test_session_manager_traversal_prevention(tmp_path):
    sm = SessionManager(sessions_dir=str(tmp_path))

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm._safe_path("../evil", ".json")

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        sm._safe_path("sub/dir", ".json")


def test_session_manager_save_uses_safe_path(tmp_path, monkeypatch):
    sm = SessionManager(sessions_dir=str(tmp_path))
    session = Session(id="test-session")

    # Track calls to _safe_path
    safe_path_calls = []
    original_safe_path = sm._safe_path

    def mocked_safe_path(sid, ext):
        safe_path_calls.append((sid, ext))
        return original_safe_path(sid, ext)

    monkeypatch.setattr(sm, "_safe_path", mocked_safe_path)

    sm.save(session)

    # Should be called for both .json (meta) and .jsonl (messages)
    extensions = [call[1] for call in safe_path_calls]
    assert ".json" in extensions
    assert ".jsonl" in extensions
