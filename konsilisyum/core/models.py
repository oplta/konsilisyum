from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class AgentStatus(Enum):
    ACTIVE = "active"
    MUTED = "muted"
    REMOVED = "removed"


class SpeakerType(Enum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


class SessionStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"


class TopicMode(Enum):
    FOCUS = "focus"
    EVOLVE = "evolve"


class UserRole(Enum):
    OBSERVER = "observer"
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    REFEREE = "referee"


class KeyStatus(Enum):
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class Agent:
    name: str
    role: str
    goal: str
    blind_spot: str
    style: str
    trigger: str
    color: str = "#ffffff"
    status: AgentStatus = AgentStatus.ACTIVE
    api_key_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    turn_count: int = 0
    last_turn: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "blind_spot": self.blind_spot,
            "style": self.style,
            "trigger": self.trigger,
            "color": self.color,
            "status": self.status.value,
            "api_key_id": self.api_key_id,
            "turn_count": self.turn_count,
            "last_turn": self.last_turn,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Agent:
        data = dict(data)
        data["status"] = AgentStatus(data["status"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class Message:
    turn: int
    speaker: str
    content: str
    speaker_type: SpeakerType
    topic: str
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    reply_to: str | None = None
    is_summary: bool = False
    _saved: bool = field(default=False, repr=False)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "turn": self.turn,
            "speaker": self.speaker,
            "speaker_type": self.speaker_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "metadata": self.metadata,
            "reply_to": self.reply_to,
            "is_summary": self.is_summary,
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        data = dict(data)
        data["speaker_type"] = SpeakerType(data["speaker_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class Topic:
    content: str
    mode: TopicMode = TopicMode.EVOLVE
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "kullanici"
    parent_id: str | None = None
    turn_started: int = 0
    turn_ended: int | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "mode": self.mode.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_id": self.parent_id,
            "turn_started": self.turn_started,
            "turn_ended": self.turn_ended,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Topic:
        data = dict(data)
        data["mode"] = TopicMode(data["mode"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class APIKey:
    id: str
    key: str = field(repr=False)
    assigned_agent: str | None = None
    is_pool: bool = False
    usage_count: int = 0
    token_count: int = 0
    last_used: datetime | None = None
    last_error: str | None = None
    error_count: int = 0
    rate_limited_until: datetime | None = None
    status: KeyStatus = KeyStatus.ACTIVE

    def to_dict(self, mask: bool = True) -> dict:
        key_val = self.key
        if mask and len(key_val) > 8:
            key_val = f"{key_val[:4]}...{key_val[-4:]}"
        elif mask:
            key_val = "***"

        return {
            "id": self.id,
            "key": key_val,
            "assigned_agent": self.assigned_agent,
            "is_pool": self.is_pool,
            "usage_count": self.usage_count,
            "token_count": self.token_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "rate_limited_until": self.rate_limited_until.isoformat() if self.rate_limited_until else None,
            "status": self.status.value,
        }


@dataclass
class Summary:
    content: str
    turn_range: tuple[int, int]
    key_points: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    agents: list[Agent] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    topics: list[Topic] = field(default_factory=list)
    current_topic: Topic | None = None
    current_turn: int = 0
    status: SessionStatus = SessionStatus.RUNNING
    user_role: UserRole = UserRole.PARTICIPANT
    auto_turns_since_user: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Konsilisyum Oturumu"
    created_at: datetime = field(default_factory=datetime.now)
    summary_interval: int = 20
    max_auto_turns: int = 50

    def to_meta_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "current_turn": self.current_turn,
            "current_topic": self.current_topic.to_dict() if self.current_topic else None,
            "user_role": self.user_role.value,
            "auto_turns_since_user": self.auto_turns_since_user,
            "agents": [a.to_dict() for a in self.agents],
            "topics": [t.to_dict() for t in self.topics],
            "summary_interval": self.summary_interval,
            "max_auto_turns": self.max_auto_turns,
        }

    @property
    def active_agents(self) -> list[Agent]:
        return [a for a in self.agents if a.status == AgentStatus.ACTIVE]
