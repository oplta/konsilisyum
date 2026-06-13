"""Integration tests for the CLI application loop."""

import asyncio
import threading
import time
from unittest.mock import AsyncMock, patch

import pytest

from konsilisyum.core.models import (
    Agent,
    AgentStatus,
    Message,
    SessionStatus,
    SpeakerType,
)
from konsilisyum.core.orchestrator import TurnResult
from konsilisyum.main import KonsilisyumApp, console


class TestInputLoop:
    @pytest.fixture
    def app(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_API_KEYS", "test-key")
        app = KonsilisyumApp()
        assert app.bootstrapper.initialize("Test topic")
        app.session = app.bootstrapper.session
        app.orchestrator = app.bootstrapper.orchestrator
        app.memory = app.bootstrapper.memory
        app.cmd_handler = app.bootstrapper.cmd_handler
        app.session_manager = app.bootstrapper.session_manager
        app._loop = asyncio.new_event_loop()
        yield app
        if not app._loop.is_closed():
            app._loop.close()

    def test_input_loop_message(self, app):
        responses = iter(["Merhaba"])

        def fake_input(prompt):
            try:
                return next(responses)
            except StopIteration:
                raise EOFError()

        app._running = True
        with patch.object(console, "input", fake_input):
            app._input_loop()

        user_messages = [m for m in app.session.messages if m.speaker_type == SpeakerType.USER]
        assert len(user_messages) == 1
        assert user_messages[0].content == "Merhaba"

    def test_input_loop_command(self, app):
        call_count = 0

        def fake_input(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "/pause"
            raise EOFError()

        def run_loop():
            app._loop.run_forever()

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

        app._running = True
        with patch.object(console, "input", fake_input):
            app._input_loop()

        app._running = False
        app._loop.call_soon_threadsafe(app._loop.stop)
        thread.join(timeout=2)

        assert app.session.status == SessionStatus.PAUSED

    def test_input_loop_eof_stops(self, app):
        app._running = True
        with patch.object(console, "input", side_effect=EOFError()):
            app._input_loop()
        # EOFError breaks the loop; _running is set to False by the caller
        assert app._loop.is_closed() is False


class TestCouncilLoop:
    @pytest.fixture
    def app(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_API_KEYS", "test-key")
        app = KonsilisyumApp()
        assert app.bootstrapper.initialize("Test topic")
        app.session = app.bootstrapper.session
        app.orchestrator = app.bootstrapper.orchestrator
        app.memory = app.bootstrapper.memory
        app.cmd_handler = app.bootstrapper.cmd_handler
        app.session_manager = app.bootstrapper.session_manager
        app.orchestrator.turn_delay = 0
        app._running = True
        return app

    @pytest.mark.asyncio
    async def test_council_loop_executes_turn(self, app):
        msg = Message(
            turn=0,
            speaker="Atlas",
            content="Test reply",
            speaker_type=SpeakerType.AGENT,
            topic="Test topic",
        )
        calls = 0

        async def mock_execute_turn():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0)
            return TurnResult(message=msg)

        app.orchestrator.execute_turn = mock_execute_turn

        async def stop_after():
            await asyncio.sleep(0.5)
            app._running = False

        with patch("konsilisyum.main.print_message"):
            await asyncio.gather(app._council_loop(), stop_after())
        assert calls >= 1

    @pytest.mark.asyncio
    async def test_council_loop_no_active_agents(self, app):
        app.session.agents = [
            Agent(
                name="Atlas",
                role="Stratejist",
                goal="G",
                blind_spot="B",
                style="S",
                trigger="T",
                status=AgentStatus.REMOVED,
            )
        ]

        async def stop_after():
            await asyncio.sleep(1.0)
            app._running = False

        with patch("konsilisyum.main.console"):
            await asyncio.gather(app._council_loop(), stop_after())
        assert app.session.status == SessionStatus.PAUSED
