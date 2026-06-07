from __future__ import annotations

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, RichLog, Static

from konsilisyum.api.keypool import KeyPool
from konsilisyum.commands.handler import CommandHandler
from konsilisyum.commands.parser import InputType, parse_input
from konsilisyum.config.settings import Config
from konsilisyum.core.logging import setup_logging
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import (
    APIKey,
    Agent,
    AgentStatus,
    Message,
    Session,
    SessionStatus,
    SpeakerType,
    Topic,
    TopicMode,
)
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager

# Setup structured logging
logger = setup_logging()


class MessageLog(RichLog):
    pass


class AgentList(Static):
    agents: reactive[list[Agent]] = reactive([])

    def render(self) -> str:
        lines = ["[bold]Ajanlar[/bold]", ""]
        for a in self.agents:
            icon = {"active": "[green]●[/green]", "muted": "[yellow]○[/yellow]", "removed": "[red]✗[/red]"}.get(
                a.status.value, "?"
            )
            lines.append(f"{icon} {a.name}")
            lines.append(f"  [dim]{a.role}[/dim]")
            lines.append(f"  [dim]Tur: {a.turn_count}[/dim]")
            lines.append("")
        return "\n".join(lines)


class TopicInfo(Static):
    topic: reactive[str] = reactive("")
    mode: reactive[str] = reactive("evolve")

    def render(self) -> str:
        mode_icon = "🔒" if self.mode == "focus" else "🔓"
        return f"[bold]Konu[/bold]\n\n{mode_icon} {self.topic}"


class StatsPanel(Static):
    turn: reactive[int] = reactive(0)
    status: reactive[str] = reactive("running")

    def render(self) -> str:
        status_icon = "●" if self.status == "running" else "○"
        status_text = "ÇALIŞIYOR" if self.status == "running" else "DURAKLATILDI"
        return f"[bold]Durum[/bold]\n\n{status_icon} {status_text}\nTur: {self.turn}"


class KonsilisyumTUI(App):
    CSS_PATH = "theme.tcss"
    TITLE = "Konsilisyum"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Çık"),
        Binding("ctrl+p", "toggle_pause", "Duraklat/Devam"),
        Binding("ctrl+s", "request_summary", "Özet"),
    ]

    is_running: reactive[bool] = reactive(True)
    current_turn: reactive[int] = reactive(0)
    current_topic: reactive[str] = reactive("")
    next_speaker: reactive[str] = reactive("")

    def __init__(self, topic: str | None = None):
        super().__init__()
        self.config = Config.load()
        self.session: Session | None = None
        self.orchestrator: Orchestrator | None = None
        self.memory: MemoryManager | None = None
        self.cmd_handler: CommandHandler | None = None
        self.session_manager: SessionManager | None = None
        self._council_task: asyncio.Task | None = None
        self._initial_topic = topic
        self._logger = logger.bind(component="KonsilisyumTUI")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield MessageLog(id="messages")
            with Vertical(id="sidebar"):
                yield AgentList(id="agents")
                yield TopicInfo(id="topic")
                yield StatsPanel(id="stats")
        yield Footer()
        yield Input(placeholder="Mesaj veya /komut...", id="input")

    def on_mount(self) -> None:
        self._init_session()
        self._update_sidebar()
        if self._initial_topic:
            self._start_council()
        else:
            self.query_one("#messages", MessageLog).write("[dim]Konu girin veya /load ile oturum yükleyin[/dim]")

    def _init_session(self):
        self._logger.info("initializing_session", topic=self._initial_topic, provider=self.config.llm.get("provider"))
        agents = self.config.get_agents()
        api_keys = self.config.get_api_keys()

        if not api_keys:
            fallback = self.config.get_fallback_key()
            if fallback:
                api_keys = [APIKey(id="fallback", key=fallback, is_pool=True)]
            else:
                self._logger.error("no_api_keys_found")
                self.query_one("#messages", MessageLog).write("[bold red]API anahtarı bulunamadı[/bold red]")
                return

        self._logger.info("api_keys_loaded", count=len(api_keys))
        key_pool = KeyPool(api_keys)
        api_client = self.config.get_llm_client()
        self._logger.info("llm_client_initialized", provider=api_client.provider, model=api_client.model)

        self.memory = MemoryManager(
            context_window_size=self.config.memory.get("context_window_size", 8),
            summary_interval=self.config.memory.get("summary_interval", 20),
            memory_update_interval=self.config.memory.get("memory_update_interval", 5),
        )

        session_topic = None
        if self._initial_topic:
            session_topic = Topic(content=self._initial_topic, mode=TopicMode.EVOLVE, created_by="kullanici")

        self.session = Session(agents=agents, current_topic=session_topic)
        if session_topic:
            self.session.topics.append(session_topic)

        self.orchestrator = Orchestrator(
            session=self.session,
            memory=self.memory,
            api_client=api_client,
            key_pool=key_pool,
            turn_delay=self.config.orchestrator.get("turn_delay", 2.0),
            max_auto_turns=self.config.orchestrator.get("max_auto_turns", 50),
        )

        self.cmd_handler = CommandHandler(
            session=self.session,
            orchestrator=self.orchestrator,
            memory=self.memory,
            key_pool=key_pool,
        )

        self.session_manager = SessionManager(self.config.session_config.get("sessions_dir", "data/sessions"))

        for a in agents:
            self.query_one("#messages", MessageLog).write(f"[dim]● {a.name} ({a.role})[/dim]")

    def _start_council(self):
        if self.session and self.session.current_topic:
            self.current_topic = self.session.current_topic.content
            self._council_task = asyncio.create_task(self._council_loop())

    async def _council_loop(self):
        while self.is_running:
            if self.session.status == SessionStatus.PAUSED:
                await asyncio.sleep(0.5)
                continue

            if not self.session.active_agents:
                self._logger.warning("no_active_agents")
                self.query_one("#messages", MessageLog).write("[bold red]Aktif ajan kalmadı[/bold red]")
                self.orchestrator.pause()
                continue

            try:
                result = await self.orchestrator.execute_turn()
            except Exception as e:
                self._logger.error("orchestrator_error", error=str(e))
                self.query_one("#messages", MessageLog).write(f"[bold red]Hata: {e}[/bold red]")
                self.orchestrator.pause()
                continue

            if result.error == "max_auto_turns":
                self._logger.info("max_auto_turns_reached", turn=self.session.current_turn)
                self.query_one("#messages", MessageLog).write("[bold yellow]Maksimum otomatik tur aşıldı[/bold yellow]")
                continue

            if result.error:
                self._logger.warning("turn_error", error=result.error, turn=self.session.current_turn)
                continue

            if result.message:
                self._logger.debug("agent_message", turn=result.message.turn, speaker=result.message.speaker, length=len(result.message.content))
                self._add_message(result.message)

            if result.summary:
                self._logger.info("summary_generated", turn_range=result.summary.turn_range)
                self.query_one("#messages", MessageLog).write(f"\n[bold]📋 Özet (Tur {result.summary.turn_range[0]}-{result.summary.turn_range[1]})[/bold]")
                self.query_one("#messages", MessageLog).write(result.summary.content)

            self.current_turn = self.session.current_turn
            self._update_sidebar()

    def _add_message(self, msg: Message):
        agent = next((a for a in self.session.agents if a.name == msg.speaker), None)
        color = agent.color if agent else "#ffffff"
        role = f" ({agent.role})" if agent else ""
        self.query_one("#messages", MessageLog).write(f"[{color}][Tur {msg.turn}] {msg.speaker}{role}:[/{color}]")
        self.query_one("#messages", MessageLog).write(msg.content)
        self.query_one("#messages", MessageLog).write("")

    def _update_sidebar(self):
        if self.session:
            self.query_one("#agents", AgentList).agents = self.session.agents
            self.query_one("#topic", TopicInfo).topic = self.session.current_topic.content if self.session.current_topic else "Yok"
            self.query_one("#topic", TopicInfo).mode = self.session.current_topic.mode.value if self.session.current_topic else "evolve"
            self.query_one("#stats", StatsPanel).turn = self.session.current_turn
            self.query_one("#stats", StatsPanel).status = self.session.status.value

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        if not user_input:
            return
        event.input.value = ""

        self._logger.debug("user_input", input=user_input[:100])
        parsed = parse_input(user_input)

        if parsed.input_type == InputType.MESSAGE:
            if not self.session.current_topic:
                topic_obj = Topic(content=user_input, created_by="kullanici")
                self.session.current_topic = topic_obj
                self.session.topics.append(topic_obj)
                self.current_topic = user_input
                self._update_sidebar()
                self._start_council()
                return

            msg = Message(
                turn=self.session.current_turn,
                speaker="Kullanıcı",
                content=user_input,
                speaker_type=SpeakerType.USER,
                topic=self.session.current_topic.content if self.session.current_topic else "",
            )
            self.memory.add_message(msg)
            self.session.messages.append(msg)
            self.orchestrator.set_user_message(user_input)
            self.session.auto_turns_since_user = 0
            self._logger.info("user_message", turn=self.session.current_turn, length=len(user_input))
            self.query_one("#messages", MessageLog).write(f"[bold cyan]Sen:[/bold cyan] {user_input}")
            return

        if parsed.input_type == InputType.COMMAND:
            self._logger.info("command_executed", command=parsed.command, args=parsed.args)
            result = await self.cmd_handler.handle(parsed.command, parsed.args)
            if result.message:
                self.query_one("#messages", MessageLog).write(result.message)
            if result.should_quit:
                self._logger.info("quit_command", session_id=self.session.id if self.session else None)
                self.is_running = False
                self.session.status = SessionStatus.ENDED
                self.session_manager.save(self.session)
                self.exit()

    def action_toggle_pause(self):
        if self.session:
            if self.session.status == SessionStatus.PAUSED:
                self._logger.info("resume")
                self.orchestrator.resume()
                self.query_one("#messages", MessageLog).write("[dim]▶ Akış devam ediyor[/dim]")
            else:
                self._logger.info("pause")
                self.orchestrator.pause()
                self.query_one("#messages", MessageLog).write("[dim]⏸ Akış duraklatıldı[/dim]")
            self._update_sidebar()

    def action_request_summary(self):
        if self.session and self.orchestrator:
            self._logger.info("summary_requested")
            asyncio.create_task(self._do_summary())

    async def _do_summary(self):
        summary = await self.orchestrator._generate_summary()
        if summary:
            self._logger.info("manual_summary_generated", turn_range=summary.turn_range)
            self.query_one("#messages", MessageLog).write(f"\n[bold]📋 Özet[/bold]\n{summary.content}")


def run_tui(topic: str | None = None):
    app = KonsilisyumTUI(topic=topic)
    app.run()
