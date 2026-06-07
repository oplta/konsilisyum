# Veri Modelleri

Konsilisyum'un tüm domain varlıkları `konsilisyum/core/models.py` içinde dataclass olarak tanımlıdır. Bu sayfa her birini açıklar.

## Agent

```python
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
```

### Alanlar

| Alan          | Tip         | Açıklama                                  |
|---------------|-------------|--------------------------------------------|
| `id`          | `str`       | UUID, benzersiz tanımlayıcı               |
| `name`        | `str`       | Görünen ad: "Atlas"                       |
| `role`        | `str`       | Uzmanlık: "Stratejist"                    |
| `goal`        | `str`       | Ajanın amacı                              |
| `blind_spot`  | `str`       | Kör noktası                               |
| `style`       | `str`       | Konuşma üslubu                            |
| `trigger`     | `str`       | Ne zaman atılacağı                        |
| `color`       | `str`       | TUI rengi (hex)                          |
| `status`      | `AgentStatus` | active / muted / removed                |
| `api_key_id`  | `str\|None` | Atanmış API anahtarı                      |
| `turn_count`  | `int`       | Kaç tur konuştu                          |
| `last_turn`   | `int`       | Son konuştuğu tur no                      |
| `created_at`  | `datetime`  | Oluşturulma zamanı                       |

### Örnek

```python
from konsilisyum.core.models import Agent

agent = Agent(
    name="Atlas",
    role="Stratejist",
    goal="Fikirleri uygulanabilir eylem planına çevirmek",
    blind_spot="İnsan maliyetini küçümser",
    style="Kısa, net, karar odaklı",
    trigger="Belirsizlik görünce çerçeve kurar",
    color="#ff6b6b",
)
```

### Metodlar

```python
agent.to_dict()  # JSON serileştirme
Agent.from_dict(data)  # dict'ten oluşturma
```

## Message

```python
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
```

### Alanlar

| Alan           | Tip            | Açıklama                                |
|----------------|----------------|------------------------------------------|
| `id`           | `str`          | UUID                                    |
| `turn`         | `int`          | Tur numarası (1'den başlar)             |
| `speaker`      | `str`          | Konuşan kişi adı (ajan veya "Sen")      |
| `content`      | `str`          | Mesaj metni                             |
| `speaker_type` | `SpeakerType`  | AGENT veya USER                         |
| `topic`        | `str`          | Hangi konu altında                      |
| `timestamp`    | `datetime`     | Gönderilme zamanı                       |
| `metadata`     | `dict`         | Ek veri (tokens, model vs.)             |

### Örnek

```python
from konsilisyum.core.models import Message, SpeakerType

msg = Message(
    turn=1,
    speaker="Atlas",
    content="Net kararlar almak için kurallar dizisi gerekir.",
    speaker_type=SpeakerType.AGENT,
    topic="YZ etiği",
    metadata={"tokens_in": 100, "tokens_out": 50, "model": "mistral-small"},
)
```

## Topic

```python
@dataclass
class Topic:
    content: str
    mode: TopicMode = TopicMode.OPEN
    status: TopicStatus = TopicStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
```

### TopicMode

| Mod       | Açıklama                              |
|-----------|----------------------------------------|
| `OPEN`    | Serbest tartışma (varsayılan)         |
| `FOCUSED` | Belirli bir soruya odaklanır          |
| `PANEL`   | Her ajan sırayla görüş bildirir       |

### TopicStatus

| Durum       | Açıklama                              |
|-------------|----------------------------------------|
| `ACTIVE`    | Şu an bu konu işleniyor               |
| `ARCHIVED`  | Eski, özetlenmiş                      |

## Summary

```python
@dataclass
class Summary:
    turn: int
    text: str
    topic: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
```

Her 20 turda bir üretilen kısa özet. Bağlam penceresine yerleştirilir.

## APIKey

```python
@dataclass
class APIKey:
    id: str = field(default_factory=lambda: str(uuid4()))
    key: str = ""           # sadece RAM'de, diske yazılmaz
    env_var: str = ""       # hangi ortam değişkeninden
    is_pool: bool = True
    status: KeyStatus = KeyStatus.ACTIVE
    last_used: datetime | None = None
    cooldown_until: datetime | None = None
    usage_count: int = 0
```

### KeyStatus

| Durum        | Açıklama                              |
|--------------|----------------------------------------|
| `ACTIVE`     | Kullanılabilir                         |
| `COOLING`    | Rate limit sonrası beklemede          |
| `DISABLED`   | Manuel olarak devre dışı             |
| `INVALID`    | 401 aldı, kullanılamaz                |

!!! warning "Güvenlik"
    `key` alanı diske yazılmaz. Sadece RAM'de yaşar. Kalıcılık için `env_var` kullanılır.

## Session

```python
@dataclass
class Session:
    agents: list[Agent] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    topics: list[Topic] = field(default_factory=list)
    summaries: list[Summary] = field(default_factory=list)
    name: str = ""
    status: SessionStatus = SessionStatus.RUNNING
    current_turn: int = 1
    current_topic: Topic | None = None
    auto_turns_since_user: int = 0
    id: str = field(default_factory=...)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### SessionStatus

| Durum       | Açıklama                              |
|-------------|----------------------------------------|
| `RUNNING`   | Aktif                                  |
| `PAUSED`    | Duraklatıldı                          |
| `ARCHIVED`  | Arşivlendi, salt okunur               |

### Computed Properties

```python
session.active_agents  # status=ACTIVE olan ajanlar
session.total_tokens   # tüm mesajların toplam token'ı
session.duration       # created_at'tan bu yana geçen süre
```

## Enum'lar

```python
class AgentStatus(Enum):
    ACTIVE = "active"
    MUTED = "muted"
    REMOVED = "removed"

class SessionStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    ARCHIVED = "archived"

class TopicMode(Enum):
    OPEN = "open"
    FOCUSED = "focused"
    PANEL = "panel"

class SpeakerType(Enum):
    AGENT = "agent"
    USER = "user"

class KeyStatus(Enum):
    ACTIVE = "active"
    COOLING = "cooling"
    DISABLED = "disabled"
    INVALID = "invalid"
```

## Serileştirme

Tüm modeller JSON'a çevrilebilir:

```python
session_dict = session.to_dict()
json_str = json.dumps(session_dict, ensure_ascii=False, indent=2)

# Geri yükleme
session = Session.from_dict(json.loads(json_str))
```

## Immutable Fields

- `id` — oluşturulduktan sonra değişmez
- `created_at` — sadece constructor'da ayarlanır

`updated_at` her kaydetme işleminde otomatik güncellenir.

## Sonraki Adım

- [Yapılandırma](config.md) — config dosyaları ve ortam değişkenleri
- [Mimari: Hafıza](../architecture/memory.md) — bu modellerin nasıl kullanıldığı
