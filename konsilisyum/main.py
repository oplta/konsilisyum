from __future__ import annotations

import asyncio
import sys
import threading

from rich.console import Console
from rich.panel import Panel

from konsilisyum.bootstrap import AppBootstrapper
from konsilisyum.commands.parser import InputType, parse_input
from konsilisyum.config.settings import Config
from konsilisyum.core.errors import AllKeysExhaustedError, NoActiveAgentError
from konsilisyum.core.logging import setup_logging
from konsilisyum.core.models import Agent, Message, Session, SessionStatus, SpeakerType, Topic

console = Console()

# Setup structured logging
logger = setup_logging()  # type: ignore[assignment]

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


def print_message(msg: Message, agents: list[Agent], console_instance: Console | None = None):
    out = console_instance or console
    style = get_style(msg.speaker, agents)
    if msg.speaker_type == SpeakerType.SYSTEM:
        out.print(f"[dim][{msg.timestamp:%H:%M:%S}] SISTEM: {msg.content}[/dim]")
    elif msg.speaker_type == SpeakerType.USER:
        out.print(f"[bold cyan][{msg.timestamp:%H:%M:%S}] Sen:[/bold cyan] {msg.content}")
    else:
        role = ""
        for a in agents:
            if a.name == msg.speaker:
                role = f" ({a.role})"
                break
        out.print(
            f"[{style}][{msg.timestamp:%H:%M:%S}] {msg.speaker}{role}:[/{style}] {msg.content}"
        )


def print_welcome(session: Session, console_instance: Console | None = None):
    out = console_instance or console
    out.print()
    out.print(
        Panel(
            "[bold]KONSILISYUM[/bold]\n[dim]Yasayan Fikir Meclisi[/dim]",
            border_style="bright_blue",
        )
    )
    out.print()
    out.print("[bold]Konsil uyeleri:[/bold]")
    for a in session.agents:
        status = {"active": "\u25cf", "muted": "\u25cb", "removed": "\u2717"}.get(
            a.status.value, "?"
        )
        out.print(f"  {status} [bold]{a.name}[/bold] ({a.role}) — {a.goal}")
    out.print()


def print_status_bar(session: Session, console_instance: Console | None = None):
    out = console_instance or console
    topic = session.current_topic.content if session.current_topic else "Yok"
    status_icon = "\u25cf" if session.status == SessionStatus.RUNNING else "\u25cb"
    status_text = "CALISIYOR" if session.status == SessionStatus.RUNNING else "DURAKLATILDI"
    agents = ", ".join(a.name for a in session.active_agents)
    out.print(
        f"[dim]{'─' * 60}[/dim]\n"
        f"[dim]{status_icon} {status_text} | Tur: {session.current_turn} | "
        f"Konu: {topic} | Ajanlar: {agents}[/dim]"
    )


class KonsilisyumApp:
    def __init__(self):
        self.config = Config.load()
        self.bootstrapper = AppBootstrapper(self.config)
        self.session = self.bootstrapper.session
        self.orchestrator = self.bootstrapper.orchestrator
        self.memory = self.bootstrapper.memory
        self.cmd_handler = self.bootstrapper.cmd_handler
        self.session_manager = self.bootstrapper.session_manager
        self._running = False
        self._user_input_event = threading.Event()
        self._user_input_value: str | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._logger = logger.bind(component="KonsilisyumApp")  # type: ignore[assignment]

    def run(self, topic: str | None = None):
        self._logger.info(
            "starting_konsilisyum", topic=topic, provider=self.config.llm.get("provider")
        )
        if not self.bootstrapper.initialize(topic):
            self._logger.error("no_api_keys_found", provider=self.config.llm.get("provider"))
            console.print("[bold red]Hata: API anahtari bulunamadi.[/bold red]")
            console.print("data/config.yaml dosyasinda api_keys ekleyin veya")
            console.print(
                f"{self.config.llm.get('provider', 'mistral').upper()}_API_KEYS cevre degiskenini ayarlayin."
            )
            sys.exit(1)

        self.session = self.bootstrapper.session
        self.orchestrator = self.bootstrapper.orchestrator
        self.memory = self.bootstrapper.memory
        self.cmd_handler = self.bootstrapper.cmd_handler
        self.session_manager = self.bootstrapper.session_manager

        self._logger.info(
            "llm_client_initialized",
            provider=self.bootstrapper.api_client.provider,
            model=self.bootstrapper.api_client.model,
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
                self._logger.warning("no_active_agents", session_id=self.session.id)
                console.print("[bold red]Aktif ajan kalmadi. /spawn ile ajan ekleyin.[/bold red]")
                self.orchestrator.pause()
                continue

            try:
                result = await self.orchestrator.execute_turn()
            except NoActiveAgentError:
                self._logger.warning("no_active_agent_error")
                console.print("[bold red]Aktif ajan kalmadi. /spawn ile ajan ekleyin.[/bold red]")
                self.orchestrator.pause()
                continue
            except AllKeysExhaustedError:
                self._logger.error("all_keys_exhausted")
                console.print(
                    "[bold red]Tüm API anahtarlari tukendi. /keys ile kontrol edin.[/bold red]"
                )
                self.orchestrator.pause()
                continue
            except RuntimeError as e:
                self._logger.error("runtime_error", error=str(e))
                console.print(f"[bold red]Hata: {e}[/bold red]")
                self.orchestrator.pause()
                continue

            if result.error == "max_auto_turns":
                self._logger.info("max_auto_turns_reached", turn=self.session.current_turn)
                console.print(
                    "[bold yellow]Maksimum otomatik tur asildi. "
                    "/resume ile devam edin veya /say ile katilin.[/bold yellow]"
                )
                continue

            if result.error:
                self._logger.warning(
                    "api_error", error=result.error, turn=self.session.current_turn
                )
                console.print(f"[bold red]API Hatasi: {result.error}[/bold red]")
                continue

            if result.is_pas:
                if result.error == "tekrar_tespit":
                    self._logger.debug("repetition_detected", turn=self.session.current_turn)
                    console.print("[dim][tekrar tespit edildi, pas gecildi][/dim]")
            elif result.message:
                self._logger.debug(
                    "agent_message",
                    turn=result.message.turn,
                    speaker=result.message.speaker,
                    length=len(result.message.content),
                )
                print_message(result.message, self.session.agents)

            if result.summary:
                self._logger.info("summary_generated", turn_range=result.summary.turn_range)
                console.print()
                console.print(
                    Panel(
                        result.summary.content,
                        title=f"[bold]Ozet (Tur {result.summary.turn_range[0]}-{result.summary.turn_range[1]})[/bold]",
                        border_style="dim",
                    )
                )
                console.print()

            if (
                self.session.current_turn % self.config.session_config.get("auto_save_interval", 5)
                == 0
            ):
                self.session_manager.save(self.session)
                self._logger.debug("session_saved", turn=self.session.current_turn)

    def _input_loop(self):
        while self._running:
            try:
                raw = console.input("[bold green]> [/bold green]")
            except (EOFError, KeyboardInterrupt):
                self._logger.info("shutdown_signal_received")
                break

            self._handle_input(raw.strip())

    def _ensure_ready(self) -> bool:
        if not self.session or not self.orchestrator or not self.memory or not self._loop:
            console.print("[bold red]Hata: Oturum henuz hazir degil.[/bold red]")
            return False
        return True

    def _handle_input(self, raw: str):
        if not raw:
            return

        self._logger.debug("user_input", input=raw[:100])
        parsed = parse_input(raw)

        if parsed.input_type == InputType.EMPTY:
            return

        if parsed.input_type == InputType.MESSAGE:
            if not self._ensure_ready():
                return
            assert self.session is not None
            assert self.memory is not None
            assert self.orchestrator is not None
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
            self._logger.info("user_message", turn=self.session.current_turn, length=len(raw))
            console.print(f"[bold cyan]Sen:[/bold cyan] {raw}")
            return

        if parsed.input_type == InputType.COMMAND:
            if not self._ensure_ready() or not self.cmd_handler or not self.session_manager:
                return
            assert self.cmd_handler is not None
            assert self._loop is not None
            assert self.session is not None
            assert self.session_manager is not None
            self._logger.info("command_executed", command=parsed.command, args=parsed.args)
            result = asyncio.run_coroutine_threadsafe(
                self.cmd_handler.handle(parsed.command, parsed.args or {}),
                self._loop,
            ).result()

            if result.message:
                console.print(result.message)

            if result.should_quit:
                self._logger.info(
                    "quit_command", session_id=self.session.id if self.session else None
                )
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
    parser.add_argument("--tui", action="store_true", help="Textual TUI kullan")
    args = parser.parse_args()

    if args.tui:
        from konsilisyum.tui.app import run_tui

        run_tui(topic=args.topic)
    else:
        app = KonsilisyumApp()
        app.run(topic=args.topic)


if __name__ == "__main__":
    main()
