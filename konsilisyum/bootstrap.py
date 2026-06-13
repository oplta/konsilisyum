"""Shared bootstrap logic for CLI and TUI applications."""

from __future__ import annotations

from typing import cast

from konsilisyum.api.keypool import KeyPool
from konsilisyum.api.llm import BaseLLMClient
from konsilisyum.commands.handler import CommandHandler
from konsilisyum.config.settings import Config
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import APIKey, Session, Topic, TopicMode
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager


class AppBootstrapper:
    """Initializes all runtime components for a Konsilisyum session."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config.load()
        self.agents = self.config.get_agents()
        self.api_keys: list[APIKey] = []
        self.key_pool: KeyPool | None = None
        self.api_client: BaseLLMClient | None = None
        self.memory: MemoryManager | None = None
        self.session: Session | None = None
        self.orchestrator: Orchestrator | None = None
        self.cmd_handler: CommandHandler | None = None
        self.session_manager: SessionManager | None = None

    def initialize(self, topic: str | None = None) -> bool:
        """Bootstrap all components. Returns True on success."""
        self.api_keys = self.config.get_api_keys()
        if not self.api_keys:
            fallback = self.config.get_mistral_fallback_key()
            if fallback:
                self.api_keys = [APIKey(id="fallback", key=fallback, is_pool=True)]
            else:
                return False

        self.key_pool = KeyPool(self.api_keys)
        self.api_client = self.config.get_llm_client()

        self.memory = MemoryManager(
            context_window_size=self.config.memory.get("context_window_size", 8),
            summary_interval=self.config.memory.get("summary_interval", 20),
            memory_update_interval=self.config.memory.get("memory_update_interval", 5),
        )

        session_topic = None
        if topic:
            session_topic = Topic(
                content=topic,
                mode=TopicMode.EVOLVE,
                created_by="kullanici",
            )

        self.session = Session(
            agents=self.agents,
            current_topic=session_topic,
        )
        if session_topic:
            self.session.topics.append(session_topic)

        self.orchestrator = Orchestrator(
            session=self.session,
            memory=self.memory,
            api_client=cast(BaseLLMClient, self.api_client),
            key_pool=self.key_pool,
            turn_delay=self.config.orchestrator.get("turn_delay", 2.0),
            max_auto_turns=self.config.orchestrator.get("max_auto_turns", 50),
        )

        self.session_manager = SessionManager(
            self.config.session_config.get("sessions_dir", "data/sessions")
        )

        self.cmd_handler = CommandHandler(
            session=self.session,
            orchestrator=self.orchestrator,
            memory=self.memory,
            key_pool=self.key_pool,
            session_manager=self.session_manager,
        )

        return True
