"""Tests for config/settings.py."""

import os
from pathlib import Path

import pytest
import yaml

from konsilisyum.config.settings import Config, DEFAULT_CONFIG, load_env
from konsilisyum.core.models import Agent


class TestLoadEnv:
    def test_loads_valid_env_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY_1=secret1\nTEST_KEY_2=secret2\n")
        load_env(str(env_file))
        assert os.environ.get("TEST_KEY_1") == "secret1"
        assert os.environ.get("TEST_KEY_2") == "secret2"
        del os.environ["TEST_KEY_1"]
        del os.environ["TEST_KEY_2"]

    def test_skips_comments_and_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\n\nREAL_KEY=value\n")
        load_env(str(env_file))
        assert os.environ.get("REAL_KEY") == "value"
        del os.environ["REAL_KEY"]

    def test_skips_existing_env_vars(self, tmp_path):
        os.environ["EXISTING_KEY"] = "original"
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_KEY=overridden\n")
        load_env(str(env_file))
        assert os.environ["EXISTING_KEY"] == "original"
        del os.environ["EXISTING_KEY"]

    def test_ignores_missing_file(self, tmp_path):
        load_env(str(tmp_path / "nonexistent.env"))


class TestConfig:
    def test_default_config(self):
        cfg = Config()
        assert cfg.llm["provider"] == "mistral"
        assert cfg.llm["model"] == "mistral-small-latest"
        assert cfg.memory["context_window_size"] == 8
        assert cfg.orchestrator["turn_delay"] == 2.0

    def test_load_from_yaml(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.safe_dump({
            "llm": {"model": "gpt-4o-mini"},
            "memory": {"context_window_size": 12},
        }))
        monkeypatch.setenv("MISTRAL_MODEL", "")
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        cfg = Config.load(str(config_file))
        assert cfg.llm["model"] == "gpt-4o-mini"
        assert cfg.memory["context_window_size"] == 12
        assert cfg.llm["provider"] == "mistral"

    def test_deep_merge_nested(self):
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10}}
        Config._deep_merge(base, override)
        assert base["a"]["b"] == 10
        assert base["a"]["c"] == 2
        assert base["d"] == 3

    def test_resolve_env_vars_in_string(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "resolved")
        result = Config._resolve_env_vars("prefix-${MY_VAR}-suffix")
        assert result == "prefix-resolved-suffix"

    def test_resolve_env_vars_in_dict(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        data = {"host": "${DB_HOST}", "port": 5432}
        result = Config._resolve_env_vars(data)
        assert result["host"] == "localhost"
        assert result["port"] == 5432

    def test_resolve_env_vars_in_list(self, monkeypatch):
        monkeypatch.setenv("ITEM", "x")
        data = ["${ITEM}", 1, 2]
        result = Config._resolve_env_vars(data)
        assert result[0] == "x"

    def test_resolve_env_vars_unchanged(self):
        assert Config._resolve_env_vars(42) == 42
        assert Config._resolve_env_vars(True) is True

    def test_get_agents_default(self):
        cfg = Config()
        agents = cfg.get_agents()
        assert len(agents) == 3
        assert all(isinstance(a, Agent) for a in agents)
        assert agents[0].name == "Atlas"

    def test_get_agents_custom(self):
        cfg = Config({
            "agents": [
                {"name": "Nova", "role": "Dev", "goal": "G", "blind_spot": "B", "style": "S", "trigger": "T"},
            ]
        })
        agents = cfg.get_agents()
        assert len(agents) == 1
        assert agents[0].name == "Nova"

    def test_get_api_keys_from_env(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_API_KEYS", "key1,key2,key3,key4")
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        cfg = Config()
        keys = cfg.get_api_keys("mistral")
        assert len(keys) == 4
        assert keys[0].key == "key1"
        # first 3 keys assigned to default 3 agents, rest go to pool
        assert keys[3].is_pool is True

    def test_get_api_keys_from_config(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        cfg = Config({
            "api_keys": [{"key": "cfg-key", "pool": True}],
        })
        keys = cfg.get_api_keys("mistral")
        assert len(keys) == 1
        assert keys[0].key == "cfg-key"
        assert keys[0].is_pool is True

    def test_get_api_keys_empty(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        cfg = Config({"api_keys": []})
        keys = cfg.get_api_keys("mistral")
        assert keys == []

    def test_get_fallback_key_env(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_API_KEY", "env-fallback")
        cfg = Config()
        assert cfg.get_fallback_key("mistral") == "env-fallback"

    def test_get_fallback_key_from_keys(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        cfg = Config({
            "api_keys": [{"key": "fallback-key"}],
        })
        assert cfg.get_fallback_key("mistral") == "fallback-key"

    def test_get_fallback_key_none(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        cfg = Config({"api_keys": []})
        assert cfg.get_fallback_key("mistral") is None

    def test_get_llm_client_mistral(self):
        cfg = Config()
        client = cfg.get_llm_client()
        assert client.provider == "mistral"
        assert client.model == "mistral-small-latest"

    def test_get_llm_client_openai(self):
        cfg = Config({"llm": {"provider": "openai", "model": "gpt-4o-mini"}})
        client = cfg.get_llm_client()
        assert client.provider == "openai"
        assert client.model == "gpt-4o-mini"

    def test_get_llm_client_anthropic(self):
        cfg = Config({"llm": {"provider": "anthropic", "model": "claude-3-haiku"}})
        client = cfg.get_llm_client()
        assert client.provider == "anthropic"

    def test_get_llm_client_ollama(self):
        cfg = Config({"llm": {"provider": "ollama", "model": "llama3.1"}})
        client = cfg.get_llm_client()
        assert client.provider == "ollama"

    def test_get_llm_client_unknown(self):
        cfg = Config({"llm": {"provider": "unknown"}})
        with pytest.raises(ValueError, match="Bilinmeyen LLM"):
            cfg.get_llm_client()

    def test_load_env_called_on_config_load(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("LOAD_TEST_KEY=loaded\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("LOAD_TEST_KEY", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        Config.load(str(tmp_path / "config.yaml"))
        assert os.environ.get("LOAD_TEST_KEY") == "loaded"
        del os.environ["LOAD_TEST_KEY"]

    def test_mistral_model_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MISTRAL_MODEL", "custom-model")
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        # Call load to trigger env processing
        cfg = Config.load(str(tmp_path / "config.yaml"))
        assert cfg.llm["model"] == "custom-model"
        # reset
        DEFAULT_CONFIG["llm"]["model"] = "mistral-small-latest"
