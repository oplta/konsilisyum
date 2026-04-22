from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from konsilisyum.core.models import Agent, Message, Session, SessionStatus, Topic


class SessionManager:
    def __init__(self, sessions_dir: str = "data/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, session_id: str, extension: str) -> Path:
        # Prevent directory traversal
        if ".." in session_id or "/" in session_id or "\\" in session_id:
            raise ValueError(f"Gecersiz oturum ID: {session_id}")
        return self.sessions_dir / f"{session_id}{extension}"

    def save(self, session: Session):
        meta_path = self._safe_path(session.id, ".json")
        meta = session.to_meta_dict()
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

        messages_path = self.sessions_dir / f"{session.id}.jsonl"
        with open(messages_path, "a", encoding="utf-8") as f:
            for msg in session.messages:
                if not msg._saved:
                    f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + "\n")
                    msg._saved = True

    def load(self, session_id: str) -> Session:
        meta_path = self._safe_path(session_id, ".json")
        if not meta_path.exists():
            raise FileNotFoundError(f"Oturum bulunamadi: {session_id}")

        meta = json.loads(meta_path.read_text())

        messages = []
        messages_path = self._safe_path(session_id, ".jsonl")
        if messages_path.exists():
            for line in messages_path.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    msg = Message.from_dict(json.loads(line))
                    msg._saved = True
                    messages.append(msg)

        agents = [Agent.from_dict(a) for a in meta.get("agents", [])]
        topics = [Topic.from_dict(t) for t in meta.get("topics", [])]
        current_topic = Topic.from_dict(meta["current_topic"]) if meta.get("current_topic") else None

        session = Session(
            id=meta["id"],
            name=meta.get("name", "Konsilisyum Oturumu"),
            created_at=datetime.fromisoformat(meta["created_at"]),
            status=SessionStatus(meta.get("status", "running")),
            agents=agents,
            messages=messages,
            topics=topics,
            current_topic=current_topic,
            current_turn=meta.get("current_turn", 0),
            auto_turns_since_user=meta.get("auto_turns_since_user", 0),
        )
        return session

    def list_sessions(self) -> list[dict]:
        sessions = []
        for meta_path in self.sessions_dir.glob("*.json"):
            try:
                meta = json.loads(meta_path.read_text())
                sessions.append({
                    "id": meta["id"],
                    "name": meta.get("name", ""),
                    "created_at": meta.get("created_at", ""),
                    "turn_count": meta.get("current_turn", 0),
                    "status": meta.get("status", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(sessions, key=lambda s: s.get("created_at", ""), reverse=True)

    def export_markdown(self, session: Session) -> str:
        topic = session.current_topic.content if session.current_topic else "Belirtilmedi"
        lines = [
            f"# {session.name}",
            f"**Konu:** {topic}",
            f"**Tarih:** {session.created_at:%Y-%m-%d %H:%M}",
            f"**Tur Sayisi:** {session.current_turn}",
            "",
            "---",
            "",
        ]
        for msg in session.messages:
            if msg.is_summary:
                lines.append(f"### Ozet (Tur {msg.turn})")
            else:
                lines.append(f"**[{msg.speaker}]** (Tur {msg.turn}):")
            lines.append(msg.content)
            lines.append("")
        return "\n".join(lines)
