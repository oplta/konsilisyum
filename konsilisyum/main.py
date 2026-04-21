from __future__ import annotations

import asyncio
import sys
import threading

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from konsilisyum.api.keypool import KeyPool
from konsilisyum.api.mistral import MistralClient
from konsilisyum.commands.handler import CommandHandler
from konsilisyum.commands.parser import InputType, parse_input
from konsilisyum.config.settings import Config
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import (
    APIKey,
    Agent,
    Message,
    Session,
    SessionStatus,
    SpeakerType,
    Topic,
)
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager

console = Console()

AGENT_COLORS = {
    "Atlas": "bold red",
    "Mira": "bold cyan",
    "Kaan": "bold yellow",
}


def get_style(speaker: str, agents: list[Agent]) -> str:
    for a in agents:
        if a.name == speaker:
            return f"bold {a.color}" if a.color != "#ffffff" else "bold white"
    return "bold white"


def print_message(msg: Message, agents: list[Agent]):
    style = get_style(msg.speaker, agents)
    if msg.speaker_type == SpeakerType.SYSTEM:
        console.print(f"[dim][{msg.timestamp:%H:%M:%S}] SISTEM: {msg.content}[/dim]")
    elif msg.speaker_type == SpeakerType.USER:
        console.print(f"[bold cyan][{msg.timestamp:%H:%M:%S}] Sen:[/bold cyan] {msg.content}")
    else:
        role = ""
        for a in agents:
            if a.name == msg.speaker:
                role = f" ({a.role})"
                break
        console.print(
            f"[{style}][{msg.timestamp:%H:%M:%S}] {msg.speaker}{role}:[/{style}] "
            f"{msg.content}"
        )


def print_welcome(session: Session):
    console.print()
    console.print(Panel(
        "[bold]KONSILISYUM[/bold]\n[dim]Yasayan Fikir Meclisi[/dim]",
        border_style="bright_blue",
    ))
    console.print()
    console.print("[bold]Konsil uyeleri:[/bold]")
    for a in session.agents:
        status = {"active": "\u25cf", "muted": "\u25cb", "removed": "\u2717"}.get(a.status.value, "?")
        console.print(f"  {status} [bold]{a.name}[/bold] ({a.role}) — {a.goal}")
    console.print()


def print_status_bar(session: Session):
    topic = session.current_topic.content if session.current_topic else "Yok"
    status_icon = "\u25cf" if session.status == SessionStatus.RUNNING else "\u25cb"
    status_text = "CALISIYOR" if session.status == SessionStatus.RUNNING else "DURAKLATILDI"
    agents = ", ".join(a.name for a in session.active_agents)
    console.print(
        f"[dim]{'─' * 60}[/dim]\n"
        f"[dim]{status_icon} {status_text} | Tur: {session.current_turn} | "
        f"Konu: {topic} | Ajanlar: {agents}[/dim]"
    )


class KonsilisyumApp:
    def __init__(self):
        self.config = Config.load()
        self.session: Session | None = None
        self.orchestrator: Orchestrator | None = None
        self.memory: MemoryManager | None = None
        self.cmd_handler: CommandHandler | None = None
        self.session_manager: SessionManager | None = None
        self._running = False
        self._user_input_event = threading.Event()
        self._user_input_value: str | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def run(self, topic: str | None = None):
        agents = self.config.get_agents()
        api_keys = self.config.get_api_keys()

        if not api_keys:
            fallback = self.config.get_fallback_key()
            if fallback:
                api_keys = [APIKey(id="fallback", key=fallback, is_pool=True)]
            else:
                console.print("[bold red]Hata: API anahtari bulunamadi.[/bold red]")
                console.print("data/config.yaml dosyasinda api_keys ekleyin veya")
                console.print("MISTRAL_API_KEY cevre degiskenini ayarlayin.")
                sys.exit(1)

        key_pool = KeyPool(api_keys)

        api_client = MistralClient(
            model=self.config.llm.get("model", "mistral-small-latest"),
            max_tokens=self.config.llm.get("max_tokens", 300),
            temperature=self.config.llm.get("temperature", 0.7),
        )

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
            agents=agents,
            current_topic=session_topic,
        )

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

        self.session_manager = SessionManager(
            self.config.session_config.get("sessions_dir", "data/sessions")
        )

        print_welcome(self.session)

        if not topic:
            console.print("[dim]Konu girin veya /help ile komutlari gorun:[/dim]")
            console.print("[dim]Bos birakirsaniz serbest tartisma baslar.[/dim]")
            raw_topic = console.input("[bold green]> [/bold green]").strip()
            if raw_topic:
                if raw_topic.startswith("/"):
                    parsed = parse_input(raw_topic)
                    if parsed.input_type == InputType.COMMAND and parsed.command == "load":
                        self._handle_input(raw_topic)
                        return
                    elif parsed.input_type == InputType.COMMAND:
                        self._handle_input(raw_topic)
                else:
                    topic_obj = Topic(content=raw_topic, created_by="kullanici")
                    self.session.current_topic = topic_obj
                    self.session.topics.append(topic_obj)
                    console.print()
            else:
                console.print("[dim]Serbest tartisma basliyor...[/dim]")
                console.print()

        self._running = True
        self._loop = asyncio.new_event_loop()

        council_thread = threading.Thread(target=self._run_council_loop, daemon=True)
        council_thread.start()

        try:
            self._input_loop()
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self._running = False
            if self.session:
                self.session.status = SessionStatus.ENDED
                self.session_manager.save(self.session)
                console.print("\n[dim]Oturum kaydedildi. Hosca kalin.[/dim]")

    def _run_council_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._council_loop())

    async def _council_loop(self):
        while self._running:
            if self.session.status == SessionStatus.PAUSED:
                await asyncio.sleep(0.5)
                continue

            if not self.session.active_agents:
                console.print("[bold red]Aktif ajan kalmadi. /spawn ile ajan ekleyin.[/bold red]")
                self.orchestrator.pause()
                continue

            try:
                result = await self.orchestrator.execute_turn()
            except RuntimeError as e:
                console.print(f"[bold red]Hata: {e}[/bold red]")
                self.orchestrator.pause()
                continue

            if result.error == "max_auto_turns":
                console.print(
                    "[bold yellow]Maksimum otomatik tur asildi. "
                    "/resume ile devam edin veya /say ile katilin.[/bold yellow]"
                )
                continue

            if result.error:
                console.print(f"[bold red]API Hatasi: {result.error}[/bold red]")
                continue

            if result.is_pas:
                pass
            elif result.message:
                print_message(result.message, self.session.agents)

            if result.summary:
                console.print()
                console.print(Panel(
                    result.summary.content,
                    title=f"[bold]Ozet (Tur {result.summary.turn_range[0]}-{result.summary.turn_range[1]})[/bold]",
                    border_style="dim",
                ))
                console.print()

            if self.session.current_turn % self.config.session_config.get("auto_save_interval", 5) == 0:
                self.session_manager.save(self.session)

    def _input_loop(self):
        while self._running:
            try:
                raw = console.input("[bold green]> [/bold green]")
            except (EOFError, KeyboardInterrupt):
                break

            self._handle_input(raw.strip())

    def _handle_input(self, raw: str):
        if not raw:
            return

        parsed = parse_input(raw)

        if parsed.input_type == InputType.EMPTY:
            return

        if parsed.input_type == InputType.MESSAGE:
            msg = Message(
                turn=self.session.current_turn,
                speaker="Kullanici",
                content=raw,
                speaker_type=SpeakerType.USER,
                topic=self.session.current_topic.content if self.session.current_topic else "",
            )
            self.memory.add_message(msg)
            self.session.messages.append(msg)
            self.orchestrator.set_user_message(raw)
            self.session.auto_turns_since_user = 0
            console.print(f"[bold cyan]Sen:[/bold cyan] {raw}")
            return

        if parsed.input_type == InputType.COMMAND:
            result = asyncio.run_coroutine_threadsafe(
                self.cmd_handler.handle(parsed.command, parsed.args),
                self._loop,
            ).result()

            if result.message:
                console.print(result.message)

            if result.should_quit:
                self._running = False
                self.session.status = SessionStatus.ENDED
                self.session_manager.save(self.session)
                console.print("[dim]Oturum kaydedildi. Hosca kalin.[/dim]")
                sys.exit(0)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Konsilisyum - Yasayan Fikir Meclisi")
    parser.add_argument("topic", nargs="?", default=None, help="Tartisma konusu")
    parser.add_argument("--config", default="data/config.yaml", help="Yapilandirma dosyasi")
    args = parser.parse_args()

    app = KonsilisyumApp()
    app.run(topic=args.topic)


if __name__ == "__main__":
    main()
