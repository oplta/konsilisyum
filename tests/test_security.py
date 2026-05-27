import pytest
import os
import shutil
from pathlib import Path
from konsilisyum.api.keypool import KeyPool
from konsilisyum.core.models import APIKey, Session
from konsilisyum.core.session import SessionManager

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
