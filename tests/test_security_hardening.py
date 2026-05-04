import pytest
from pathlib import Path
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Session
from konsilisyum.core.session import SessionManager

def test_keypool_mask_secrets():
    keys = [
        APIKey(id="k1", key="sk-1234567890abcdef"),
        APIKey(id="k2", key="short"),
    ]
    pool = KeyPool(keys)

    text = "Error with sk-1234567890abcdef and short key."
    masked = pool.mask_secrets(text)

    assert "sk-1234567890abcdef" not in masked
    assert "short" not in masked
    assert "sk-1...cdef" in masked
    assert "***" in masked

def test_keypool_report_error_masks_all_keys():
    keys = [
        APIKey(id="k1", key="sk-1234567890abcdef"),
        APIKey(id="k2", key="sk-secondary-key-12345"),
    ]
    pool = KeyPool(keys)

    # Report error on k1 but include k2 in message
    pool.report_error("k1", "Failed using sk-1234567890abcdef. Also leaked sk-secondary-key-12345")

    last_error = pool.keys["k1"].last_error
    assert "sk-1234567890abcdef" not in last_error
    assert "sk-secondary-key-12345" not in last_error
    assert "sk-1...cdef" in last_error
    assert "sk-s...2345" in last_error

def test_session_manager_path_traversal(tmp_path):
    manager = SessionManager(sessions_dir=str(tmp_path))

    malicious_id = "../evil"
    session = Session(id=malicious_id)

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        manager.save(session)

    with pytest.raises(ValueError, match="Gecersiz oturum ID"):
        manager.load(malicious_id)

def test_session_manager_save_consistent_protection(tmp_path):
    # Ensure both files are protected in save
    manager = SessionManager(sessions_dir=str(tmp_path))
    session = Session(id="valid-id")

    # This should work
    manager.save(session)
    assert (tmp_path / "valid-id.json").exists()
    assert (tmp_path / "valid-id.jsonl").exists()
