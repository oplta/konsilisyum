"""Tests for the CLI application helpers."""

import io

from rich.console import Console

from konsilisyum.core.models import Agent, Message, Session, SpeakerType
from konsilisyum.main import (
    KonsilisyumApp,
    get_style,
    print_message,
    print_status_bar,
    print_welcome,
)


class TestMainHelpers:
    def test_get_style_known_agent(self):
        agents = [
            Agent(
                name="Atlas",
                role="Stratejist",
                goal="G",
                blind_spot="B",
                style="S",
                trigger="T",
                color="#ff0000",
            )
        ]
        assert "bold" in get_style("Atlas", agents)

    def test_get_style_unknown_agent(self):
        agents = []
        assert get_style("Unknown", agents) == "bold white"

    def _capture_print(self, fn):
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, width=80)
        fn(console)
        return buffer.getvalue()

    def test_print_message_agent(self):
        agents = [
            Agent(
                name="Atlas",
                role="Stratejist",
                goal="G",
                blind_spot="B",
                style="S",
                trigger="T",
                color="#ff0000",
            )
        ]
        msg = Message(
            turn=1,
            speaker="Atlas",
            content="Test message",
            speaker_type=SpeakerType.AGENT,
            topic="Test",
        )
        output = self._capture_print(lambda c: print_message(msg, agents, c))
        assert "Atlas" in output
        assert "Test message" in output

    def test_print_message_user(self):
        msg = Message(
            turn=1,
            speaker="Kullanici",
            content="User message",
            speaker_type=SpeakerType.USER,
            topic="Test",
        )
        output = self._capture_print(lambda c: print_message(msg, [], c))
        assert "User message" in output

    def test_print_welcome(self):
        session = Session(
            agents=[
                Agent(
                    name="Atlas",
                    role="Stratejist",
                    goal="G",
                    blind_spot="B",
                    style="S",
                    trigger="T",
                )
            ]
        )
        output = self._capture_print(lambda c: print_welcome(session, c))
        assert "KONSILISYUM" in output
        assert "Atlas" in output

    def test_print_status_bar(self):
        session = Session(
            agents=[
                Agent(
                    name="Atlas",
                    role="Stratejist",
                    goal="G",
                    blind_spot="B",
                    style="S",
                    trigger="T",
                )
            ]
        )
        output = self._capture_print(lambda c: print_status_bar(session, c))
        assert "CALISIYOR" in output
        assert "Atlas" in output


class TestKonsilisyumApp:
    def test_app_initialization(self):
        app = KonsilisyumApp()
        assert app.config is not None
        assert app.bootstrapper is not None
