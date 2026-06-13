"""Tests for the application bootstrapper."""

from konsilisyum.bootstrap import AppBootstrapper
from konsilisyum.config.settings import Config


class TestAppBootstrapper:
    def test_initialize_without_keys_fails(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEYS", raising=False)
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        config = Config(
            {
                "llm": {"provider": "mistral"},
                "api_keys": [],
            }
        )
        bootstrapper = AppBootstrapper(config)
        assert not bootstrapper.initialize()

    def test_initialize_with_keys_succeeds(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_API_KEYS", "test-key-1,test-key-2")
        config = Config.load()
        bootstrapper = AppBootstrapper(config)
        assert bootstrapper.initialize("Test topic")
        assert bootstrapper.session is not None
        assert bootstrapper.session.current_topic is not None
        assert bootstrapper.session.current_topic.content == "Test topic"
        assert bootstrapper.orchestrator is not None
        assert bootstrapper.memory is not None
        assert bootstrapper.cmd_handler is not None
        assert bootstrapper.session_manager is not None
        assert len(bootstrapper.api_keys) == 2
