from __future__ import annotations

import re
from datetime import datetime
from uuid import uuid4

from konsilisyum.core.models import Agent, Message, SpeakerType, Summary


STOP_WORDS_TR = {
    "ve", "da", "de", "bu", "su", "bir", "icin", "ile", "ama", "fakat",
    "gibi", "olarak", "cok", "daha", "en", "diye", "ki", "ne", "mi",
    "mı", "mu", "mu", "var", "yok", "her", "hic", "o", "ben", "sen",
    "biz", "siz", "onlar", "ilk", "son", "ayni", "kendi", "nasil",
    "neden", "niye", "hangi", "tum", "bazı", "ise", "cunku", "eger",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
    text = text.replace("ş", "s").replace("ö", "o").replace("ç", "c")
    text = re.sub(r"[^\w\s]", "", text)
    words = [w for w in text.split() if w not in STOP_WORDS_TR and len(w) > 2]
    return " ".join(words)


class MemoryManager:
    def __init__(
        self,
        context_window_size: int = 8,
        summary_interval: int = 20,
        memory_update_interval: int = 5,
        max_agent_memory_items: int = 20,
    ):
        self.context_window_size = context_window_size
        self.summary_interval = summary_interval
        self.memory_update_interval = memory_update_interval
        self.max_agent_memory_items = max_agent_memory_items

        self.history: list[Message] = []
        self.agent_memories: dict[str, list[str]] = {}
        self.summaries: list[Summary] = []

    def add_message(self, message: Message):
        self.history.append(message)

    def build_context_window(self) -> str:
        parts: list[str] = []

        if self.summaries:
            latest = self.summaries[-1]
            parts.append(f"[OZET - Tur {latest.turn_range[0]}-{latest.turn_range[1]}]")
            parts.append(latest.content)
            parts.append("")

        recent = [m for m in self.history if not m.is_summary]
        recent = recent[-self.context_window_size:]
        for msg in recent:
            role_tag = f" ({msg.speaker_type.value})" if msg.speaker_type.value == "user" else ""
            parts.append(f"[Tur {msg.turn}] {msg.speaker}{role_tag}: {msg.content}")

        return "\n".join(parts)

    def get_agent_memory(self, agent_id: str) -> str:
        notes = self.agent_memories.get(agent_id, [])
        if not notes:
            return "Henuz kisisel notun yok."
        return "\n".join(f"- {n}" for n in notes)

    def update_agent_memory(self, agent_id: str, raw_notes: str):
        lines = [l.strip().lstrip("- ").strip() for l in raw_notes.strip().split("\n") if l.strip()]
        existing = self.agent_memories.get(agent_id, [])
        combined = existing + lines
        self.agent_memories[agent_id] = combined[-self.max_agent_memory_items:]

    def add_summary(self, summary: Summary):
        self.summaries.append(summary)
        msg = Message(
            turn=summary.turn_range[1],
            speaker="Sistem",
            content=f"[OZET] {summary.content}",
            speaker_type=SpeakerType.SYSTEM,
            topic="",
            is_summary=True,
            metadata={"summary_id": summary.id},
        )
        self.history.append(msg)

    def should_summarize(self, turn: int) -> bool:
        return turn > 0 and turn % self.summary_interval == 0

    def should_update_memory(self, turn: int) -> bool:
        return turn > 0 and turn % self.memory_update_interval == 0

    def get_messages_since(self, turn: int) -> list[Message]:
        return [m for m in self.history if m.turn > turn and not m.is_summary]

    def detect_repetition(self, new_content: str, threshold: float = 0.7) -> bool:
        normalized_new = normalize(new_content)
        if not normalized_new:
            return False
        new_words = set(normalized_new.split())
        recent = [m for m in self.history if not m.is_summary][-5:]
        for msg in recent:
            msg_words = set(normalize(msg.content).split())
            if not msg_words:
                continue
            overlap = len(new_words & msg_words) / max(len(new_words), 1)
            if overlap > threshold:
                return True
        return False
