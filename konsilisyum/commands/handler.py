from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from konsilisyum.api.keypool import KeyPool
from konsilisyum.commands.parser import get_help_text
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import (
    Agent,
    AgentStatus,
    Message,
    Session,
    SessionStatus,
    SpeakerType,
    Topic,
    TopicMode,
    UserRole,
)
from konsilisyum.core.orchestrator import Orchestrator


@dataclass
class CommandResult:
    success: bool
    message: str | None = None
    should_quit: bool = False


class CommandHandler:
    def __init__(
        self,
        session: Session,
        orchestrator: Orchestrator,
        memory: MemoryManager,
        key_pool: KeyPool,
    ):
        self.session = session
        self.orchestrator = orchestrator
        self.memory = memory
        self.key_pool = key_pool

    async def handle(self, command: str, args: dict | None = None) -> CommandResult:
        args = args or {}
        handler = getattr(self, f"cmd_{command}", None)
        if not handler:
            return CommandResult(False, f"Bilinmeyen komut: /{command}")
        return await handler(**args)

    async def cmd_help(self) -> CommandResult:
        return CommandResult(True, get_help_text())

    async def cmd_pause(self) -> CommandResult:
        self.orchestrator.pause()
        return CommandResult(True, "Akis duraklatildi. /resume ile devam edin.")

    async def cmd_resume(self) -> CommandResult:
        self.orchestrator.resume()
        return CommandResult(True, "Akis devam ediyor.")

    async def cmd_quit(self) -> CommandResult:
        self.session.status = SessionStatus.ENDED
        return CommandResult(True, "Konsil sona erdi.", should_quit=True)

    async def cmd_status(self) -> CommandResult:
        topic = self.session.current_topic.content if self.session.current_topic else "Yok"
        agents = ", ".join(a.name for a in self.session.active_agents)
        lines = [
            f"Oturum: {self.session.name}",
            f"Durum: {self.session.status.value}",
            f"Tur: {self.session.current_turn}",
            f"Konu: {topic}",
            f"Ajanlar: {agents}",
            f"Kullanici rolu: {self.session.user_role.value}",
        ]
        return CommandResult(True, "\n".join(lines))

    async def cmd_say(self, message: str = "") -> CommandResult:
        if not message:
            return CommandResult(False, "Mesaj bos olamaz. Kullanim: /say mesaj")
        msg = Message(
            turn=self.session.current_turn,
            speaker="Kullanici",
            content=message,
            speaker_type=SpeakerType.USER,
            topic=self.session.current_topic.content if self.session.current_topic else "",
        )
        self.memory.add_message(msg)
        self.session.messages.append(msg)
        self.orchestrator.set_user_message(message)
        self.session.auto_turns_since_user = 0
        return CommandResult(True)

    async def cmd_ask(self, agent: str = "", message: str = "") -> CommandResult:
        if not agent or not message:
            return CommandResult(False, "Kullanim: /ask AjanAdi mesaj")
        target = self._find_agent(agent)
        if not target:
            return CommandResult(False, f"Ajan bulunamadi: {agent}")
        content = f"@{target.name} {message}"
        msg = Message(
            turn=self.session.current_turn,
            speaker="Kullanici",
            content=content,
            speaker_type=SpeakerType.USER,
            topic=self.session.current_topic.content if self.session.current_topic else "",
            metadata={"directed_to": target.name},
        )
        self.memory.add_message(msg)
        self.session.messages.append(msg)
        self.orchestrator.set_pending_reply(target.name)
        self.orchestrator.set_user_message(content)
        self.session.auto_turns_since_user = 0
        return CommandResult(True)

    async def cmd_think(self, message: str = "") -> CommandResult:
        if not message:
            return CommandResult(False, "Kullanim: /think mesaj")
        msg = Message(
            turn=self.session.current_turn,
            speaker="Sistem",
            content=message,
            speaker_type=SpeakerType.SYSTEM,
            topic=self.session.current_topic.content if self.session.current_topic else "",
        )
        self.memory.add_message(msg)
        self.session.messages.append(msg)
        self.orchestrator.set_user_message(message)
        self.session.auto_turns_since_user = 0
        return CommandResult(True)

    async def cmd_topic(self, topic: str = "") -> CommandResult:
        if not topic:
            return CommandResult(False, "Kullanim: /topic yeni konu")
        old_topic = self.session.current_topic
        if old_topic:
            old_topic.turn_ended = self.session.current_turn
        new_topic = Topic(
            content=topic,
            mode=TopicMode.EVOLVE,
            created_by="kullanici",
            parent_id=old_topic.id if old_topic else None,
            turn_started=self.session.current_turn,
        )
        self.session.topics.append(new_topic)
        self.session.current_topic = new_topic
        self.orchestrator.set_user_message(f"Konu degisti: {topic}")
        return CommandResult(True, f"Konu degisti: {topic}")

    async def cmd_evolve(self) -> CommandResult:
        if self.session.current_topic:
            self.session.current_topic.mode = TopicMode.EVOLVE
        return CommandResult(True, "Konu evrimi serbest birakildi.")

    async def cmd_focus(self) -> CommandResult:
        if self.session.current_topic:
            self.session.current_topic.mode = TopicMode.FOCUS
        return CommandResult(True, "Konu merkeze kilitle.")

    async def cmd_agents(self) -> CommandResult:
        lines = []
        for a in self.session.agents:
            icons = {"active": "\u25cf", "muted": "\u25cb", "removed": "\u2717"}
            icon = icons.get(a.status.value, "?")
            lines.append(f"  {icon} {a.name} ({a.role}) — Tur: {a.turn_count}")
        return CommandResult(True, "\n".join(lines))

    async def cmd_spawn(self, definition: str = "") -> CommandResult:
        if not definition:
            return CommandResult(
                False,
                "Kullanim: /spawn isim rol amac [kor_nokta] [stil] [tetikleyici]",
            )
        parts = definition.split()
        if len(parts) < 3:
            return CommandResult(False, "En az isim, rol ve amac gerekli.")

        from konsilisyum.config.defaults import AGENT_COLORS

        color = AGENT_COLORS[len(self.session.agents) % len(AGENT_COLORS)]
        agent = Agent(
            name=parts[0],
            role=parts[1],
            goal=parts[2],
            blind_spot=parts[3] if len(parts) > 3 else "Belirtilmedi",
            style=parts[4] if len(parts) > 4 else "Normal",
            trigger=parts[5] if len(parts) > 5 else "Belirtilmedi",
            color=color,
        )
        self.session.agents.append(agent)
        return CommandResult(True, f"{agent.name} ({agent.role}) konsile katildi")

    async def cmd_kick(self, agent: str = "") -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(False, f"Ajan bulunamadi: {agent}")
        target.status = AgentStatus.REMOVED
        return CommandResult(True, f"{target.name} konsilden cikarildi")

    async def cmd_mute(self, agent: str = "") -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(False, f"Ajan bulunamadi: {agent}")
        target.status = AgentStatus.MUTED
        return CommandResult(True, f"{target.name} susturuldu")

    async def cmd_unmute(self, agent: str = "") -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(False, f"Ajan bulunamadi: {agent}")
        target.status = AgentStatus.ACTIVE
        return CommandResult(True, f"{target.name} geri acildi")

    async def cmd_profile(self, agent: str = "") -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(False, f"Ajan bulunamadi: {agent}")
        lines = [
            f"  Isim: {target.name}",
            f"  Rol: {target.role}",
            f"  Amac: {target.goal}",
            f"  Kor nokta: {target.blind_spot}",
            f"  Stil: {target.style}",
            f"  Tetikleyici: {target.trigger}",
            f"  Durum: {target.status.value}",
            f"  Tur sayisi: {target.turn_count}",
        ]
        return CommandResult(True, "\n".join(lines))

    async def cmd_edit(self, agent: str = "", field: str = "", value: str = "") -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(False, f"Ajan bulunamadi: {agent}")
        editable = {"role", "goal", "blind_spot", "style", "trigger", "name"}
        field_lower = field.lower()
        if field_lower not in editable:
            return CommandResult(False, f"Duzenlenemez alan: {field}. Alanlar: {', '.join(editable)}")
        setattr(target, field_lower, value)
        return CommandResult(True, f"{target.name}.{field_lower} = {value}")

    async def cmd_role(self, role: str = "") -> CommandResult:
        try:
            self.session.user_role = UserRole(role)
            return CommandResult(True, f"Rol: {role}")
        except ValueError:
            options = ", ".join(r.value for r in UserRole)
            return CommandResult(False, f"Gecersiz rol. Secenekler: {options}")

    async def cmd_summary(self) -> CommandResult:
        summary = await self.orchestrator._generate_summary()
        if summary:
            return CommandResult(True, summary.content)
        return CommandResult(False, "Ozet olusturulamadi.")

    async def cmd_decisions(self) -> CommandResult:
        messages = [m for m in self.session.messages if m.speaker_type == SpeakerType.AGENT]
        if not messages:
            return CommandResult(True, "Henuz yeterli tartisma yok.")
        return CommandResult(True, "Karar taslaklari henüz uygulanmadi (Faz 3)")

    async def cmd_actions(self) -> CommandResult:
        return CommandResult(True, "Yapilacaklar listesi henuz uygulanmadi (Faz 3)")

    async def cmd_map(self) -> CommandResult:
        return CommandResult(True, "Karsit gorus haritasi henuz uygulanmadi (Faz 3)")

    async def cmd_export(self, format: str = "md") -> CommandResult:
        return CommandResult(True, "Export henuz uygulanmadi (Faz 2)")

    async def cmd_save(self) -> CommandResult:
        return CommandResult(True, "Oturum kaydedildi (otomatik kayit aktif)")

    async def cmd_load(self, file: str = "") -> CommandResult:
        return CommandResult(False, "Oturum yukleme henuz uygulanmadi (Faz 2)")

    async def cmd_keys(self) -> CommandResult:
        health = self.key_pool.health()
        return CommandResult(
            True,
            f"Toplam: {health['total']} | Aktif: {health['active']} | "
            f"Hatali: {health['error']} | Tukendi: {health['exhausted']}",
        )

    async def cmd_config(self) -> CommandResult:
        return CommandResult(True, "Yapilandirma henuz uygulanmadi (Faz 2)")

    def _find_agent(self, name: str) -> Agent | None:
        name_lower = name.lower()
        for a in self.session.agents:
            if a.name.lower() == name_lower:
                return a
        for a in self.session.agents:
            if a.name.lower().startswith(name_lower):
                return a
        return None
