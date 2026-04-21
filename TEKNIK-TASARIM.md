# Konsilisyum — Teknik Tasarım Dokümanı

> Bu doküman, URUN-TANIMI.md'de tanımlanan ürünün uygulama düzeyindeki teknik tasarımını içerir.
> Her modülün iç mantığı, veri yapıları, API akışları, hata yönetimi ve test stratejisi burada belirtilir.

---

## İçindekiler

1. [Veri Modelleri ve Veri Yapıları](#1-veri-modelleri-ve-veri-yapıları)
2. [Prompt Mimarisi](#2-prompt-mimarisi)
3. [Orkestratör Detaylı Akış Diyagramı](#3-orkestratör-detaylı-akış-diyagramı)
4. [API Katmanı ve Anahtar Yönetimi](#4-api-katmanı-ve-anahtar-yönetimi)
5. [Hafıza Katmanı Detaylı Tasarım](#5-hafıza-katmanı-detaylı-tasarım)
6. [TUI Mimarisi](#6-tui-mimarisi)
7. [Komut Sistemi Mimarisi](#7-komut-sistemi-mimarisi)
8. [Oturum ve Kalıcılık](#8-oturum-ve-kalıcılık)
9. [Hata Yönetimi ve Güvenlik](#9-hata-yönetimi-ve-güvenlik)
10. [Eşzamanlılık ve Performans](#10-eşzamanlılık-ve-performans)
11. [Yapılandırma Sistemi](#11-yapılandırma-sistemi)
12. [Test Stratejisi](#12-test-stratejisi)

---

## 1. Veri Modelleri ve Veri Yapıları

### 1.1 Agent (Ajan)

```python
@dataclass
class Agent:
    id: str                    # Benzersiz tanımlayıcı (UUID veya slug)
    name: str                  # Görünen ad: "Atlas"
    role: str                  # Rol: "Stratejist"
    goal: str                  # Amaç: "Fikirleri uygulanabilir eylem planına çevirmek"
    blind_spot: str            # Kör nokta: "İnsan maliyetini küçümseme eğilimi"
    style: str                 # Konuşma stili: "Kısa, net, karar odaklı"
    trigger: str               # Tetikleyici: "Belirsizlik görünce çerçeve kurar"
    color: str                 # TUI renk kodu: "#ff6b6b"
    status: AgentStatus        # active | muted | removed
    api_key_id: str | None     # Atanmış API anahtarı ID'si (None ise havuzdan al)
    created_at: datetime       # Oluşturulma zamanı
    turn_count: int            # Kaç kez konuştu
    last_turn: int             # Son konuştuğu tur numarası

class AgentStatus(Enum):
    ACTIVE = "active"
    MUTED = "muted"
    REMOVED = "removed"
```

**Tasarım kararları:**

- `id` alanı name'den bağımsız. Kullanıcı aynı isimli ajanı silip yeniden ekleyebilir, ID çakışmaz.
- `api_key_id` None olabilir. Bu durumda orkestratör havuzdan bir anahtar atar.
- `turn_count` ve `last_turn` orkestratörün konuşmacı seçiminde kullandığı istatistiksel veriler.
- `color` alanı TUI'de mesaj rengini belirler. Varsayılan paletten otomatik atanır.

### 1.2 Message (Mesaj)

```python
@dataclass
class Message:
    id: str                       # Benzersiz mesaj ID'si
    turn: int                     # Tur numarası
    speaker: str                  # "Atlas" | "Mira" | "Kaan" | "Kullanıcı" | "Sistem"
    speaker_type: SpeakerType     # agent | user | system
    content: str                  # Mesaj içeriği
    timestamp: datetime           # Oluşturulma zamanı
    topic: str                    # Bu mesajın ait olduğu konu
    metadata: dict                # Ek veri: token sayısı, model, API key kullanımı
    reply_to: str | None          # Yanıtlanan mesaj ID'si (varsa)
    is_summary: bool              # Özet mesajı mı?

class SpeakerType(Enum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"
```

**Tasarım kararları:**

- Her mesaj bir `turn` numarasına sahiptir. Kullanıcı mesajları da turn alır ama ajanları tüketmez.
- `reply_to` alanı tartışma zincirlerini takip etmeye olanak verir. "Kaan → Mira'nın mesajına cevap" ilişkisi kurulabilir.
- `is_summary` ile özet mesajları normal mesajlardan ayrılır. Bağlam penceresinde özetler farklı ele alınır.
- `metadata` esnek bir dict'tir: `{"tokens": 145, "model": "mistral-small", "api_key": "key-01"}` gibi.

### 1.3 Topic (Konu)

```python
@dataclass
class Topic:
    id: str                      # Benzersiz konu ID'si
    content: str                 # Konu metni
    mode: TopicMode              # focus | evolve
    created_at: datetime         # Oluşturulma zamanı
    created_by: str              # "kullanıcı" | "sistem" | ajan adı
    parent_id: str | None        # Önceki konunun ID'si (evrilmişse)
    turn_started: int            # Hangi turda başladı
    turn_ended: int | None       # Hangi turda bitti (hâlâ aktifse None)

class TopicMode(Enum):
    FOCUS = "focus"              # Konu sabit, kayma engellenir
    EVOLVE = "evolve"            # Konu doğal olarak evrilir
```

**Tasarım kararları:**

- Konu geçmişini tutmak için `parent_id` zinciri kullanılır. Bu sayede "konu nasıl evrildi" takip edilebilir.
- `mode` alanı orkestratörün davranışını değiştirir. Focus modunda ajanların konu dışına çıkması engellenir, evolve modunda serbest bırakılır.

### 1.4 Session (Oturum)

```python
@dataclass
class Session:
    id: str                         # Benzersiz oturum ID'si (UUID)
    name: str                       # Oturum adı (otomatik veya kullanıcı tanımlı)
    created_at: datetime            # Başlangıç zamanı
    status: SessionStatus           # running | paused | ended
    agents: list[Agent]             # Aktif ajanlar
    messages: list[Message]         # Tüm mesajlar
    topics: list[Topic]             # Konu geçmişi
    current_topic: Topic | None     # Aktif konu
    current_turn: int               # Mevcut tur numarası
    user_role: UserRole             # Kullanıcının rolü
    summary_interval: int           # Kaç turda bir özet (varsayılan: 20)
    max_auto_turns: int             # Maksimum otomatik tur (varsayılan: 50)
    auto_turns_since_user: int      # Kullanıcı müdahalesiz geçen tur sayısı
    config_hash: str                # Yapılandırma dosyasının hash'i

class SessionStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"

class UserRole(Enum):
    OBSERVER = "observer"
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    REFEREE = "referee"
```

**Tasarım kararları:**

- `auto_turns_since_user` sayacı her kullanıcı müdahalesinde sıfırlanır. `max_auto_turns`'e ulaşınca otomatik duraklama yapılır.
- `config_hash` oturumun hangi yapılandırma ile başladığını kaydeder. Yapılandırma değişirse uyarı verilebilir.

### 1.5 APIKey (API Anahtarı)

```python
@dataclass
class APIKey:
    id: str                     # Anahtar tanımlayıcı: "key-01"
    key: str                    # Mistral API anahtarı
    assigned_agent: str | None  # Atanmış ajan ID'si (None ise havuzda)
    is_pool: bool               # Havuz anahtarı mı?
    usage_count: int            # Toplam kullanım sayısı
    token_count: int            # Toplam tüketilen token
    last_used: datetime | None  # Son kullanım zamanı
    last_error: str | None      # Son hata mesajı
    error_count: int            # Toplam hata sayısı
    rate_limited_until: datetime | None  # Rate limit sonu zamanı
    status: KeyStatus           # active | exhausted | rate_limited | error

class KeyStatus(Enum):
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
```

**Tasarım kararları:**

- Her anahtar kendi durumunu takip eder. `rate_limited_until` ile zaman bazlı rate limit yönetimi yapılır.
- `error_count` belirli bir eşiği geçen anahtarlar otomatik olarak devre dışı bırakılır.
- 50+ anahtar olduğu için tek anahtar arızası sistemi durdurmaz.

### 1.6 Summary (Özet)

```python
@dataclass
class Summary:
    id: str                         # Benzersiz özet ID'si
    turn_range: tuple[int, int]     # (başlangıç turu, bitiş turu)
    content: str                    # Özet metni
    key_points: list[str]           # Anahtar noktalar
    disagreements: list[str]        # Anlaşmazlıklar
    decisions: list[str]            # Çıkan kararlar
    topic_drift: str | None         # Konu kayması var mı?
    created_at: datetime
```

---

## 2. Prompt Mimarisi

### 2.1 Yapı

Her ajan için API'ye gönderilen prompt üç bölümden oluşur:

```
┌─────────────────────────────────────┐
│  SYSTEM PROMPT (sabit)              │  ← Persona + kurallar + hafıza
├─────────────────────────────────────┤
│  CONTEXT WINDOW (dinamik)           │  ← Son N mesaj + aktif özet
├─────────────────────────────────────┤
│  GENERATION DIRECTIVE (dinamik)     │  ← Bu turda ne yapması gerektiği
└─────────────────────────────────────┘
```

### 2.2 System Prompt Şablonu

```
Sen {name}'sın. Rolün: {role}.

Amaç: {goal}
Kör noktan: {blind_spot} — Buna dikkat et, ama bunun için özür dileme.
Konuşma stilin: {style}
Tetikleyicin: {trigger}

Konsil Kuralları:
- 500 kelimeyi geçme.
- Kendi görüşünü savun ama diğerlerini dinle.
- Tekrar yapmaktan kaçın. Daha önce söylediğin bir şeyi tekrar söyleme.
- Diğer ajanlara isimleriyle hitap et.
- Tartışmaya yapıcı katkı yap. Sadece sesini duyurmak için konuşma.
- Eğer bir şey söyleyecek yeni bir şey yoksa, "Pas" de.

Senin kişisel notların:
{agent_memory}
```

**Tasarım kararları:**

- Kör nokta "dikkat et ama özür dileme" şeklinde ifade edilir. Aksi takdirde ajan sürekli "haklısınız ama kör noktam..." der.
- "Pas" mekanizması: ajan söyleyecek bir şey yoksa pas geçebilir. Bu anlamsız üretimi önler.
- `agent_memory` her turda güncellenir ve ajanın kişisel notlarını içerir.

### 2.3 Context Window

```
[ÖZET - Son 20 turun özeti]
{latest_summary}

[YAKIN GEÇMİŞ - Son 8 mesaj]
[Tur {turn-7}] {speaker_7}: {content_7}
[Tur {turn-6}] {speaker_6}: {content_6}
...
[Tur {turn-1}] {speaker_1}: {content_1}
[Tur {turn}] {speaker}: {content}
```

**Boyut hesabı:**

- Özet: ~200 token
- Her mesaj: ~100-200 token (ortalama 150)
- 8 mesaj: ~1200 token
- System prompt: ~200 token
- Generation directive: ~50 token
- Toplam bağlam: ~1650 token giriş + 300 token çıkış = ~1950 token/tur
- Mistral-small fiyatıyla: ~$0.002/tur → 1000 tur = ~$2

### 2.4 Generation Directive

Orkestratör her turda generation directive'i dinamik oluşturur:

```python
def build_generation_directive(agent: Agent, context: TurnContext) -> str:
    parts = []

    # Temel yönerge
    parts.append(f"Konu: {context.current_topic}")
    parts.append(f"Sen sıradaki konuşmacısın. Tartışmaya katkı yap.")

    # Özel yönergeler
    if context.is_replying_to:
        parts.append(f"{context.reply_to_speaker} sana direkt sordu. Cevap ver.")
    
    if context.topic_changed:
        parts.append(f"Konu değişti. Yeni konu: {context.current_topic}")
    
    if context.user_message_pending:
        parts.append(f"Kullanıcı bir mesaj bıraktı: \"{context.user_message}\"")
        parts.append("Buna tepki ver.")
    
    if context.turns_since_contribution > 3:
        parts.append("Uzun süredir konuşmadın. Görüşünü belirt.")
    
    if context.near_summary_turn:
        parts.append("Özet turu yaklaşıyor. Ana hatlarıyla özetle.")

    return "\n".join(parts)
```

### 2.5 Hafıza Güncelleme Prompt'u

Her 5 turda bir, ajanın kişisel hafızası güncellenir:

```
Sen {name}'sın. Tartışmanın şu ana kadar olan bölümünü değerlendir.

Kendi notlarını güncelle. Sadece sana önemli gelen noktaları, 
senin için kritik olan anlaşmazlıkları ve kişisel izlenimlerini yaz.

Format:
- [ANAHTAR NOKTA] ...
- [İTİRAZ] ...
- [İZLENİM] ...
- [KARAR] ...

Mevcut notların:
{current_memory}

Son 5 tur:
{recent_messages}

Güncellenmiş notların:
```

---

## 3. Orkestratör Detaylı Akış Diyagramı

### 3.1 Ana Döngü

```
┌──────────────┐
│   BAŞLANGIÇ  │  Session oluşturulur, ajanlar yüklenir, konu verilir
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────────────┐
│  TUR BAŞI    │────▶│  Kullanıcı girdisi   │
│              │     │    var mı?           │
└──────┬───────┘     └──────┬───────────────┘
       │                    │
       │              ┌─────┴─────┐
       │              │ EVET      │ HAYIR
       │              ▼           │
       │     ┌──────────────┐    │
       │     │  Girdiyi     │    │
       │     │  ayrıştır    │    │
       │     └──────┬───────┘    │
       │            │            │
       │            ▼            │
       │     ┌──────────────┐    │
       │     │  Komut mu?   │    │
       │     └──────┬───────┘    │
       │        ┌───┴───┐       │
       │        │EVET   │HAYIR  │
       │        ▼       ▼       │
       │   ┌────────┐ ┌───────┐ │
       │   │Komut   │ │Mesaj  │ │
       │   │işle    │ │olarak │ │
       │   │        │ │kaydet │ │
       │   └───┬────┘ └───┬───┘ │
       │       │          │     │
       │       └────┬─────┘     │
       │            │           │
       │            ▼           │
       │     ┌──────────────┐   │
       │     │auto_turns = 0│   │  Kullanıcı müdahalesi sayacını sıfırla
       │     └──────┬───────┘   │
       │            │           │
       └────────────┼───────────┘
                    │
                    ▼
           ┌──────────────┐
           │  Duraklatı-  │──── EVET ──▶ Kullanıcı girdisini bekle
           │  lmış mı?    │              (resume komutuna kadar blokla)
           └──────┬───────┘
                  │ HAYIR
                  ▼
           ┌──────────────┐
           │  Maks otomatik│──── EVET ──▶ Otomatik duraklat, 
           │  tur aşıldı  │              kullanıcıya sor
           │  mı?         │
           └──────┬───────┘
                  │ HAYIR
                  ▼
           ┌──────────────┐
           │  Özet zamanı │──── EVET ──▶ Özet oluştur, 
           │  mı?         │              bağlamı sıkıştır
           └──────┬───────┘
                  │ HAYIR
                  ▼
           ┌──────────────┐
           │  Hafıza      │──── EVET ──▶ Ajanların kişisel
           │  güncelleme  │              hafızasını güncelle
           │  zamanı mı?  │
           └──────┬───────┘
                  │ HAYIR
                  ▼
           ┌──────────────────────────┐
           │  KONUŞMACI SEÇİMİ        │
           │                          │
           │  Adaylar:                │
           │  1. Mute olmamış ajanlar │
           │  2. Removed olmayanlar   │
           │                          │
           │  Puanlama:               │
           │  + Cevap bekleyen var mı │
           │  + Uzun süredi susan     │
           │  + Konuya ilgili         │
           │  - Son konuşmacı         │
           │  + Rastgele faktör       │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │  TEKRAR KONTROLÜ         │
           │                          │
           │  Seçilen ajanın son 3    │
           │  mesajı ile son 5 ortak  │
           │  mesajı karşılaştır      │
           │                          │
           │  Benzerlik > %70 ?       │
           │  → EVET: Pas veya farklı │
           │    açı iste              │
           │  → HAYIR: Devam         │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │  PROMPT OLUŞTUR          │
           │                          │
           │  System prompt (persona) │
           │  + Context window        │
           │  + Generation directive  │
           │  + Ajan hafızası         │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │  MISTRAL API ÇAĞRISI     │
           │                          │
           │  API anahtarı seç        │
           │  İsteği gönder           │
           │  Yanıtı al               │
           │  Token sayısını kaydet   │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │  YANIT İŞLEME            │
           │                          │
           │  Uzunluk kontrolü       │
           │  "Pas" tespiti          │
           │  Mesajı oluştur         │
           │  Geçmişe ekle           │
           │  JSONL'ye yaz           │
           │  TUI'ye gönder          │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │  TUR SAYACI GÜNCELLE     │
           │                          │
           │  turn += 1               │
           │  auto_turns += 1         │
           │  agent.turn_count += 1   │
           │  agent.last_turn = turn  │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌──────────────────────────┐
           │  BEKLE (tur arası gecike)│
           │                          │
           │  Varsayılan: 2 saniye    │
           │  Kullanıcı girdisi       │
           │  kontrol et              │
           └──────────┬───────────────┘
                      │
                      ▼
                  ┌────────┐
                  │ TUR    │─────▶ Ana döngüye dön
                  │ BAŞI   │
                  └────────┘
```

### 3.2 Konuşmacı Seçim Algoritması

```python
def select_speaker(agents: list[Agent], context: TurnContext) -> Agent:
    candidates = [a for a in agents if a.status == AgentStatus.ACTIVE]
    
    if not candidates:
        raise NoActiveAgentError("Konuşacak aktif ajan yok")
    
    scores = {}
    for agent in candidates:
        score = 0.0
        
        # 1. Cevap bekleyen var mı? (+3)
        if context.pending_reply_to == agent.name:
            score += 3.0
        
        # 2. Uzun süredir susan (+2)
        turns_silent = context.current_turn - agent.last_turn
        score += min(turns_silent * 0.5, 2.0)
        
        # 3. Son konuşmacı cezası (-3)
        if context.last_speaker == agent.name:
            score -= 3.0
        
        # 4. Kullanıcı bir ajana direkt sordu (+5)
        if context.user_directed_to == agent.name:
            score += 5.0
        
        # 5. Konuya ilgili mi? (basit anahtar kelime eşleşmesi)
        relevance = compute_topic_relevance(agent, context.current_topic)
        score += relevance * 1.0
        
        # 6. Rastgele faktör (tahmin edilebilirliği kır)
        score += random.uniform(0, 0.5)
        
        scores[agent.id] = score
    
    # En yüksek puanlıyı seç
    winner_id = max(scores, key=scores.get)
    return next(a for a in candidates if a.id == winner_id)
```

### 3.3 Tekrar Algılama

```python
def detect_repetition(new_content: str, recent_messages: list[Message], threshold: float = 0.7) -> bool:
    """
    Basit kelime örtüşmesi ile tekrar algılama.
    MVP için yeterli. Faz 2'de embedding benzerliğine geçilebilir.
    """
    new_words = set(normalize(new_content).split())
    
    for msg in recent_messages[-5:]:
        msg_words = set(normalize(msg.content).split())
        overlap = len(new_words & msg_words) / max(len(new_words), 1)
        if overlap > threshold:
            return True
    
    return False

def normalize(text: str) -> str:
    """Metni normalize et: küçük harf, noktalama temizle, stop word çıkar."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    stop_words = {'ve', 'da', 'de', 'bu', 'şu', 'bir', 'için', 'ile', 'ama', 'fakat', 
                  'gibi', 'olarak', 'çok', 'daha', 'en', 'the', 'a', 'an', 'is', 'are'}
    words = [w for w in text.split() if w not in stop_words]
    return ' '.join(words)
```

### 3.4 Konu Kayması Algılama

```python
def detect_topic_drift(recent_messages: list[Message], current_topic: str, mode: TopicMode) -> bool:
    """
    Focus modunda: konu dışına çıkma algıla
    Evolve modunda: konu değişimini tespit et ve yeni konu öner
    """
    if mode == TopicMode.EVOLVE:
        return False  # Evolve modunda kayma sorun değil
    
    # Son 3 mesajın konuyla ilişkisini kontrol et
    topic_words = set(normalize(current_topic).split())
    for msg in recent_messages[-3:]:
        msg_words = set(normalize(msg.content).split())
        overlap = len(topic_words & msg_words) / max(len(topic_words), 1)
        if overlap < 0.15:  # Konuyla çok az ilişki
            return True
    
    return False
```

---

## 4. API Katmanı ve Anahtar Yönetimi

### 4.1 Mistral API İstemcisi

```python
class MistralClient:
    """
    Mistral Chat API'ye istek gönderen istemci.
    Dokümantasyon: https://docs.mistral.ai/api/#tag/chat
    """
    
    BASE_URL = "https://api.mistral.ai/v1"
    MODEL = "mistral-small-latest"  # MVP için yeterli
    MAX_TOKENS = 300                 # Çıkış token limiti
    TEMPERATURE = 0.7                # Yaratıcılık
    
    async def complete(
        self,
        system_prompt: str,
        context: str,
        directive: str,
        api_key: str,
    ) -> CompletionResult:
        """
        Tek bir tamamlama isteği gönder.
        
        Returns:
            CompletionResult(content=str, tokens_in=int, tokens_out=int, model=str)
        """
        ...
```

**API isteği yapısı:**

```json
{
  "model": "mistral-small-latest",
  "messages": [
    {"role": "system", "content": "<system_prompt>"},
    {"role": "user", "content": "<context + directive>"}
  ],
  "max_tokens": 300,
  "temperature": 0.7
}
```

**Neden `mistral-small-latest`?**

- Hızlı yanıt süresi (tartışma ritmi için kritik)
- Düşük maliyet ($0.1/M giriş token, $0.3/M çıkış token)
- Çoklu persona ayrımı yapabiliyor
- 50+ API anahtarı ile maliyet zaten sorun değil

### 4.2 API Anahtarı Havuzu

```python
class KeyPool:
    """
    Çoklu API anahtarı yönetimi.
    Her ajan mümkünse kendi anahtarını kullanır.
    Rate limit veya hata durumunda havuzdan yedek alınır.
    """
    
    def __init__(self, keys: list[APIKey]):
        self.keys = {k.id: k for k in keys}
        self.pool_keys = [k for k in keys if k.is_pool]
        self.round_robin_idx = 0
    
    def get_key(self, agent_id: str | None = None) -> APIKey:
        """
        Ajan için uygun API anahtarı döndür.
        
        Öncelik sırası:
        1. Ajan'a atanmış aktif anahtar
        2. Havuzdan sıradaki aktif anahtar (round-robin)
        3. Herhangi bir aktif anahtar
        
        Hiçbiri yoksa NoAvailableKeyError fırlat.
        """
        ...
    
    def report_success(self, key_id: str, tokens_used: int):
        """Başarılı kullanımı kaydet."""
        ...
    
    def report_error(self, key_id: str, error: str):
        """Hatayı kaydet. Rate limit ise süre not et."""
        ...
    
    def health_check(self) -> dict:
        """Tüm anahtarların durumunu raporla."""
        ...
```

**Hata senaryoları ve tepkiler:**

| Senaryo | Tespit | Tepki |
|---------|--------|-------|
| Rate limit (429) | HTTP 429 + `Retry-After` header | `rate_limited_until` güncelle, havuzdan başka anahtar al |
| Geçersiz anahtar (401) | HTTP 401 | Anahtarı `EXHAUSTED` işaretle, kullanıcıya bildir |
| Sunucu hatası (5xx) | HTTP 500/502/503 | 3 kez retry (exponential backoff), sonra hata bildir |
| Timeout | 30 saniye üstü | Retry, sonra sonraki anahtara geç |
| Kota aşıldı | HTTP 402 | Anahtarı `EXHAUSTED` işaretle |

### 4.3 Retry Mekanizması

```python
async def call_with_retry(
    client: MistralClient,
    prompt: PromptBundle,
    key_pool: KeyPool,
    max_retries: int = 3,
) -> CompletionResult:
    """
    Exponential backoff ile retry.
    Her retry'da farklı anahtar dene.
    """
    for attempt in range(max_retries):
        key = key_pool.get_key(agent_id=prompt.agent_id)
        try:
            result = await client.complete(
                system_prompt=prompt.system,
                context=prompt.context,
                directive=prompt.directive,
                api_key=key.key,
            )
            key_pool.report_success(key.id, result.tokens_in + result.tokens_out)
            return result
        except RateLimitError as e:
            key_pool.report_error(key.id, "rate_limited")
            wait = e.retry_after or (2 ** attempt)
            await asyncio.sleep(wait)
        except (ServerError, TimeoutError) as e:
            key_pool.report_error(key.id, str(e))
            await asyncio.sleep(2 ** attempt)
        except AuthError:
            key_pool.report_error(key.id, "auth_failed")
            continue  # Farklı anahtar dene
    
    raise AllKeysExhaustedError("Tüm anahtarlar tükendi veya hata veriyor")
```

---

## 5. Hafıza Katmanı Detaylı Tasarım

### 5.1 Mimari Genel Görünüm

```
┌─────────────────────────────────────────────────┐
│                MEMORY MANAGER                    │
│                                                  │
│  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ Shared       │  │ Agent Memory Store       │  │
│  │ History      │  │                          │  │
│  │              │  │  Atlas: [not1, not2, ...] │  │
│  │ [msg1,       │  │  Mira:  [not1, not2, ...] │  │
│  │  msg2,       │  │  Kaan:  [not1, not2, ...] │  │
│  │  msg3, ...]  │  │                          │  │
│  │              │  └─────────────────────────┘  │
│  └──────┬───────┘                                │
│         │                                        │
│  ┌──────▼───────┐  ┌─────────────────────────┐  │
│  │ Context      │  │ Summary Store            │  │
│  │ Window       │  │                          │  │
│  │ Builder      │  │  [summary1, summary2]    │  │
│  │              │  │                          │  │
│  │ Son N mesaj  │  │  Her 20 turda bir        │  │
│  │ + son özet   │  │  üretilen özet           │  │
│  └──────────────┘  └─────────────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 5.2 MemoryManager Sınıfı

```python
class MemoryManager:
    """
    Tüm hafıza katmanlarını yöneten merkezi sınıf.
    """
    
    CONTEXT_WINDOW_SIZE = 8      # Son 8 mesaj
    SUMMARY_INTERVAL = 20       # Her 20 turda bir özet
    MEMORY_UPDATE_INTERVAL = 5  # Her 5 turda ajan hafızası güncelle
    MAX_AGENT_MEMORY_ITEMS = 20 # Ajan başına maksimum not sayısı
    
    def __init__(self, session: Session, api_client: MistralClient):
        self.session = session
        self.api_client = api_client
        self.shared_history: list[Message] = []
        self.agent_memories: dict[str, list[str]] = {}  # agent_id -> [notlar]
        self.summaries: list[Summary] = []
    
    def add_message(self, message: Message):
        """Paylaşılan geçmişe mesaj ekle."""
        self.shared_history.append(message)
    
    def build_context_window(self, agent: Agent) -> str:
        """
        Ajan için bağlam penceresi oluştur.
        
        İçerik:
        1. Son özet (varsa)
        2. Son 8 mesaj
        """
        parts = []
        
        # Son özet
        if self.summaries:
            latest = self.summaries[-1]
            parts.append(f"[ÖZET - Tur {latest.turn_range[0]}-{latest.turn_range[1]}]")
            parts.append(latest.content)
            parts.append("")
        
        # Son N mesaj
        recent = self.shared_history[-self.CONTEXT_WINDOW_SIZE:]
        for msg in recent:
            if msg.is_summary:
                continue  # Özet mesajları atla (yukarıda zaten var)
            parts.append(f"[Tur {msg.turn}] {msg.speaker}: {msg.content}")
        
        return "\n".join(parts)
    
    def get_agent_memory(self, agent_id: str) -> str:
        """Ajanın kişisel notlarını döndür."""
        notes = self.agent_memories.get(agent_id, [])
        if not notes:
            return "Henüz kişisel notun yok."
        return "\n".join(f"- {note}" for note in notes)
    
    async def update_agent_memory(self, agent: Agent):
        """
        Ajanın kişisel hafızasını güncelle.
        API çağrısı ile yapılır.
        """
        current_memory = self.get_agent_memory(agent.id)
        recent = self.shared_history[-5:]
        recent_text = "\n".join(
            f"[Tur {m.turn}] {m.speaker}: {m.content}" for m in recent
        )
        
        prompt = MEMORY_UPDATE_PROMPT.format(
            name=agent.name,
            current_memory=current_memory,
            recent_messages=recent_text
        )
        
        result = await self.api_client.complete(
            system_prompt="Sen bir hafıza asistanısın. Notları güncelle.",
            context=prompt,
            directive="Güncellenmiş notları yaz.",
            api_key=agent.api_key_id
        )
        
        # Notları parse et ve sakla
        notes = parse_memory_notes(result.content)
        self.agent_memories[agent.id] = notes[-self.MAX_AGENT_MEMORY_ITEMS:]
    
    async def generate_summary(self) -> Summary:
        """
        Tartışma özeti oluştur.
        API çağrısı ile yapılır.
        """
        # Son özetten bu yana olan mesajları al
        last_summary_turn = self.summaries[-1].turn_range[1] if self.summaries else 0
        messages = [
            m for m in self.shared_history 
            if m.turn > last_summary_turn and not m.is_summary
        ]
        
        messages_text = "\n".join(
            f"[Tur {m.turn}] {m.speaker}: {m.content}" for m in messages
        )
        
        prompt = SUMMARY_PROMPT.format(
            topic=self.session.current_topic.content,
            messages=messages_text,
            turn_range=f"{last_summary_turn + 1}-{self.session.current_turn}"
        )
        
        result = await self.api_client.complete(
            system_prompt="Sen bir tartışma özetleyicisisin.",
            context=prompt,
            directive="Özet oluştur.",
            api_key=None  # Havuzdan anahtar al
        )
        
        summary = parse_summary(result, last_summary_turn + 1, self.session.current_turn)
        self.summaries.append(summary)
        
        # Özet mesajını da geçmişe ekle
        summary_msg = Message(
            id=str(uuid4()),
            turn=self.session.current_turn,
            speaker="Sistem",
            speaker_type=SpeakerType.SYSTEM,
            content=f"[ÖZET] {summary.content}",
            timestamp=datetime.now(),
            topic=self.session.current_topic.content,
            metadata={"tokens": result.tokens_in + result.tokens_out},
            reply_to=None,
            is_summary=True
        )
        self.shared_history.append(summary_msg)
        
        return summary
    
    def should_update_memory(self, turn: int) -> bool:
        return turn > 0 and turn % self.MEMORY_UPDATE_INTERVAL == 0
    
    def should_summarize(self, turn: int) -> bool:
        return turn > 0 and turn % self.SUMMARY_INTERVAL == 0
```

### 5.3 Hafıza Akış Zaman Çizelgesi

```
Tur 1-4:   Normal konuşma, shared_history büyüyor
Tur 5:     Ajan hafızaları güncellenir (her 5 turda)
Tur 6-9:   Normal konuşma
Tur 10:    Ajan hafızaları güncellenir
Tur 11-19: Normal konuşma
Tur 20:    ÖZET üretilir + ajan hafızaları güncellenir
            → Bağlam penceresi özet + son 8 mesaj olarak sıkıştırılır
Tur 21-24: Normal konuşma (artık özet üzerinden çalışıyor)
Tur 25:    Ajan hafızaları güncellenir
Tur 26-39: Normal konuşma
Tur 40:    İkinci özet üretilir
            → Artık iki özet var: [1-20] ve [21-40]
            → Eski özetler korunur ama bağlam penceresinde sadece son özet gösterilir
...
```

---

## 6. TUI Mimarisi

### 6.1 Widget Hiyerarşisi

```
App (KonsilisyumApp)
├── Header (KonsilHeader)
│   ├── Static: "🏛 KONSILISYUM"
│   ├── Static: Konu metni
│   ├── Static: Durum göstergesi
│   └── Static: Tur sayacı + ajan listesi
│
├── Middle (Horizontal)
│   ├── MessageLog (RichLog)
│   │   └── [Mesajlar burada akar]
│   │
│   └── Sidebar (Vertical, width=30)
│       ├── AgentList
│       │   └── [Her ajan için: renk kutusu + isim + durum]
│       ├── TopicInfo
│       │   └── Aktif konu + mod
│       └── StatsPanel
│           └── Tur sayısı, token sayısı, süre
│
├── Footer (KonsilFooter)
│   ├── Static: "Sıradaki: {agent}" | Komut ipuçları
│   └── Input (KonsilInput)
│       └── Kullanıcı girdi satırı
```

### 6.2 Textual App Tanımı

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual import work

class KonsilisyumApp(App):
    """Konsilisyum TUI uygulaması."""
    
    CSS_PATH = "theme.tcss"
    TITLE = "Konsilisyum"
    
    BINDINGS = [
        ("ctrl+q", "quit", "Çık"),
        ("ctrl+p", "toggle_pause", "Duraklat/Devam"),
        ("ctrl+s", "request_summary", "Özet"),
    ]
    
    # Reactive state
    is_running: reactive[bool] = reactive(True)
    current_turn: reactive[int] = reactive(0)
    current_topic: reactive[str] = reactive("")
    next_speaker: reactive[str] = reactive("")
    
    def compose(self) -> ComposeResult:
        yield KonsilHeader()
        with Horizontal():
            yield MessageLog()
            with Vertical(id="sidebar"):
                yield AgentList()
                yield TopicInfo()
                yield StatsPanel()
        yield KonsilFooter()
    
    def on_input_submitted(self, event: Input.Submitted):
        """Kullanıcı girdiğinde."""
        user_input = event.value.strip()
        if not user_input:
            return
        event.input.value = ""
        self.process_user_input(user_input)
    
    @work(exclusive=True)
    async def run_council_loop(self):
        """Arka planda çalışan konsil döngüsü."""
        while self.is_running:
            if self.is_paused:
                await asyncio.sleep(0.5)
                continue
            await self.orchestrator.execute_turn()
            self.current_turn = self.session.current_turn
    
    def add_message_to_log(self, message: Message):
        """Mesajı TUI mesaj akışına ekle."""
        agent = get_agent_by_name(message.speaker)
        color = agent.color if agent else "white"
        formatted = f"[{color}][Tur {message.turn}] {message.speaker}:[/{color}] {message.content}"
        self.query_one(MessageLog).write(formatted)
```

### 6.3 Mesaj Formatlama

```python
def format_message(message: Message, agents: list[Agent]) -> str:
    agent = next((a for a in agents if a.name == message.speaker), None)
    
    if message.speaker_type == SpeakerType.SYSTEM:
        return f"[dim][{message.timestamp:%H:%M:%S}] SİSTEM: {message.content}[/dim]"
    
    if message.speaker_type == SpeakerType.USER:
        return f"[bold cyan][{message.timestamp:%H:%M:%S}] Sen:[/bold cyan] {message.content}"
    
    # Ajan mesajı
    color = agent.color if agent else "white"
    role_tag = f"({agent.role})" if agent else ""
    return (
        f"[bold {color}][{message.timestamp:%H:%M:%S}] "
        f"{message.speaker} {role_tag}:[/bold {color}]\n"
        f"  {message.content}"
    )
```

### 6.4 Renk Paleti

```python
AGENT_COLORS = [
    "#ff6b6b",  # Kırmızı
    "#4ecdc4",  # Teal
    "#ffe66d",  # Sarı
    "#a8e6cf",  # Yeşil
    "#ff8a5c",  # Turuncu
    "#6c5ce7",  # Mor
    "#fd79a8",  # Pembe
    "#00cec9",  # Cyan
]

# Varsayılan atama:
# Atlas -> #ff6b6b (kırmızı, stratejist kararlılığı)
# Mira  -> #4ecdc4 (teal, etikçinin sakinliği)
# Kaan  -> #ffe66d (sarı, şüphecinin keskinliği)
```

---

## 7. Komut Sistemi Mimarisi

### 7.1 Komut Ayrıştırıcı

```python
@dataclass
class ParsedCommand:
    command: str                  # Komut adı: "ask", "spawn", "say"
    args: dict[str, str]          # Argümanlar: {"agent": "Mira", "message": "etik risk?"}
    raw: str                      # Ham girdi: "/ask Mira bu önerinin etik riski ne"

class CommandParser:
    """
    Kullanıcı girdisini komut veya mesaj olarak sınıflandırır.
    """
    
    # Komut tanımları: (isim, parametre sayısı, parametre isimleri)
    COMMANDS = {
        # Temel
        "help":    {"params": [], "desc": "Komutları göster"},
        "pause":   {"params": [], "desc": "Akışı duraklat"},
        "resume":  {"params": [], "desc": "Akışı devam ettir"},
        "quit":    {"params": [], "desc": "Konsilden çık"},
        "status":  {"params": [], "desc": "Oturum durumu"},
        
        # Katılım
        "say":     {"params": ["message"], "desc": "Mesaj bırak"},
        "ask":     {"params": ["agent", "message"], "desc": "Ajana soru sor"},
        "think":   {"params": ["message"], "desc": "Mesaj enjekte et"},
        
        # Konu
        "topic":   {"params": ["topic"], "desc": "Konu değiştir"},
        "evolve":  {"params": [], "desc": "Konu evrimini serbest bırak"},
        "focus":   {"params": [], "desc": "Konuyu merkeze çek"},
        
        # Ajan yönetimi
        "agents":  {"params": [], "desc": "Ajan listesi"},
        "spawn":   {"params": ["definition"], "desc": "Yeni ajan ekle"},
        "kick":    {"params": ["agent"], "desc": "Ajan çıkar"},
        "mute":    {"params": ["agent"], "desc": "Ajan sustur"},
        "unmute":  {"params": ["agent"], "desc": "Ajan aç"},
        "profile": {"params": ["agent"], "desc": "Ajan profili"},
        "edit":    {"params": ["agent", "field", "value"], "desc": "Ajan düzenle"},
        
        # Rol
        "role":    {"params": ["role"], "desc": "Kullanıcı rolü ata"},
        
        # Çıktı
        "summary":  {"params": [], "desc": "Tartışma özeti"},
        "decisions":{"params": [], "desc": "Karar taslakları"},
        "actions":  {"params": [], "desc": "Yapılacaklar listesi"},
        "map":      {"params": [], "desc": "Karşıt görüş haritası"},
        "export":   {"params": ["format"], "desc": "Dışa aktar"},
        
        # Sistem
        "save":   {"params": [], "desc": "Oturumu kaydet"},
        "load":   {"params": ["file"], "desc": "Oturum yükle"},
        "keys":   {"params": [], "desc": "API anahtar durumu"},
        "config": {"params": [], "desc": "Yapılandırma"},
    }
    
    def parse(self, raw_input: str) -> ParsedCommand | UserMessage:
        """
        Girdiyi ayrıştır.
        
        Returns:
            ParsedCommand: Komut tanındı
            UserMessage: "/" ile başlamıyor, normal mesaj
        """
        raw = raw_input.strip()
        
        if not raw.startswith("/"):
            # Normal mesaj — /say ile eşdeğer
            return UserMessage(content=raw)
        
        # Komut adını çıkart
        parts = raw[1:].split(maxsplit=1)
        cmd_name = parts[0].lower()
        cmd_body = parts[1] if len(parts) > 1 else ""
        
        if cmd_name not in self.COMMANDS:
            return UnknownCommand(raw=raw, attempted_command=cmd_name)
        
        cmd_def = self.COMMANDS[cmd_name]
        args = self._parse_args(cmd_name, cmd_def["params"], cmd_body)
        
        return ParsedCommand(command=cmd_name, args=args, raw=raw)
    
    def _parse_args(self, cmd: str, params: list[str], body: str) -> dict:
        """Komut gövdesini parametrelere göre ayrıştır."""
        if not params:
            return {}
        
        if len(params) == 1:
            return {params[0]: body}
        
        # İlk parametre agent adı olabilir
        if params[0] == "agent":
            parts = body.split(maxsplit=1)
            agent_name = parts[0] if parts else ""
            rest = parts[1] if len(parts) > 1 else ""
            
            if len(params) == 2:
                return {params[0]: agent_name, params[1]: rest}
            
            # edit: /edit Atlas role Yeni rol
            if len(params) == 3:
                field = rest.split(maxsplit=1)[0] if rest else ""
                value = rest.split(maxsplit=1)[1] if " " in rest else ""
                return {params[0]: agent_name, params[1]: field, params[2]: value}
        
        return {p: body for p in params}
```

### 7.2 Komut İşleyici

```python
class CommandHandler:
    """
    Ayrıştırılan komutları çalıştırır.
    Her komut metodu bir CommandResult döndürür.
    """
    
    def __init__(self, session: Session, orchestrator: Orchestrator, 
                 memory: MemoryManager, key_pool: KeyPool, app: KonsilisyumApp):
        self.session = session
        self.orchestrator = orchestrator
        self.memory = memory
        self.key_pool = key_pool
        self.app = app
    
    async def handle(self, parsed: ParsedCommand) -> CommandResult:
        """Komutu dispatch et."""
        handler = getattr(self, f"cmd_{parsed.command}", None)
        if not handler:
            return CommandResult(success=False, message=f"Bilinmeyen komut: {parsed.command}")
        return await handler(**parsed.args)
    
    async def cmd_pause(self) -> CommandResult:
        self.orchestrator.pause()
        return CommandResult(success=True, message="⏸ Akış duraklatıldı")
    
    async def cmd_resume(self) -> CommandResult:
        self.orchestrator.resume()
        return CommandResult(success=True, message="▶ Akış devam ediyor")
    
    async def cmd_say(self, message: str) -> CommandResult:
        msg = Message(
            id=str(uuid4()),
            turn=self.session.current_turn,
            speaker="Kullanıcı",
            speaker_type=SpeakerType.USER,
            content=message,
            timestamp=datetime.now(),
            topic=self.session.current_topic.content,
            metadata={},
            reply_to=None,
            is_summary=False
        )
        self.memory.add_message(msg)
        self.session.auto_turns_since_user = 0
        return CommandResult(success=True, message=None)  # Mesaj zaten logda görünecek
    
    async def cmd_ask(self, agent: str, message: str) -> CommandResult:
        # Ajan adını bul (fuzzy match)
        target = self._find_agent(agent)
        if not target:
            return CommandResult(success=False, message=f"Ajan bulunamadı: {agent}")
        
        msg = Message(
            id=str(uuid4()),
            turn=self.session.current_turn,
            speaker="Kullanıcı",
            speaker_type=SpeakerType.USER,
            content=f"@{target.name} {message}",
            timestamp=datetime.now(),
            topic=self.session.current_topic.content,
            metadata={"directed_to": target.name},
            reply_to=None,
            is_summary=False
        )
        self.memory.add_message(msg)
        self.orchestrator.set_pending_reply(target.name)
        self.session.auto_turns_since_user = 0
        return CommandResult(success=True, message=None)
    
    async def cmd_spawn(self, definition: str) -> CommandResult:
        """'/spawn Nova Yaratıcı Yeni fikirler üretmek Çok soyut kalır Fantezi, metafor dolu ...'"""
        parts = definition.split()
        if len(parts) < 3:
            return CommandResult(
                success=False, 
                message="Kullanım: /spawn isim rol amaç [kör_nokta] [stil] [tetikleyici]"
            )
        
        agent = Agent(
            id=str(uuid4()),
            name=parts[0],
            role=parts[1],
            goal=parts[2],
            blind_spot=parts[3] if len(parts) > 3 else "Belirtilmedi",
            style=parts[4] if len(parts) > 4 else "Normal",
            trigger=parts[5] if len(parts) > 5 else "Belirtilmedi",
            color=AGENT_COLORS[len(self.session.agents) % len(AGENT_COLORS)],
            status=AgentStatus.ACTIVE,
            api_key_id=None,
            created_at=datetime.now(),
            turn_count=0,
            last_turn=0
        )
        
        self.session.agents.append(agent)
        return CommandResult(success=True, message=f"✦ {agent.name} ({agent.role}) konsile katıldı")
    
    async def cmd_kick(self, agent: str) -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(success=False, message=f"Ajan bulunamadı: {agent}")
        target.status = AgentStatus.REMOVED
        return CommandResult(success=True, message=f"✗ {target.name} konsilden çıkarıldı")
    
    async def cmd_mute(self, agent: str) -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(success=False, message=f"Ajan bulunamadı: {agent}")
        target.status = AgentStatus.MUTED
        return CommandResult(success=True, message=f"🔇 {target.name} susturuldu")
    
    async def cmd_unmute(self, agent: str) -> CommandResult:
        target = self._find_agent(agent)
        if not target:
            return CommandResult(success=False, message=f"Ajan bulunamadı: {agent}")
        target.status = AgentStatus.ACTIVE
        return CommandResult(success=True, message=f"🔊 {target.name} geri açıldı")
    
    async def cmd_topic(self, topic: str) -> CommandResult:
        old_topic = self.session.current_topic
        new_topic = Topic(
            id=str(uuid4()),
            content=topic,
            mode=old_topic.mode if old_topic else TopicMode.EVOLVE,
            created_at=datetime.now(),
            created_by="kullanıcı",
            parent_id=old_topic.id if old_topic else None,
            turn_started=self.session.current_turn,
            turn_ended=None
        )
        if old_topic:
            old_topic.turn_ended = self.session.current_turn
        self.session.topics.append(new_topic)
        self.session.current_topic = new_topic
        return CommandResult(success=True, message=f"📌 Konu değişti: {topic}")
    
    async def cmd_summary(self) -> CommandResult:
        summary = await self.memory.generate_summary()
        return CommandResult(success=True, message=summary.content)
    
    async def cmd_agents(self) -> CommandResult:
        lines = []
        for a in self.session.agents:
            status_icon = {"active": "●", "muted": "○", "removed": "✗"}[a.status.value]
            lines.append(f"  {status_icon} {a.name} ({a.role}) — Tur sayısı: {a.turn_count}")
        return CommandResult(success=True, message="\n".join(lines))
    
    async def cmd_role(self, role: str) -> CommandResult:
        try:
            self.session.user_role = UserRole(role)
            return CommandResult(success=True, message=f"Rol: {role}")
        except ValueError:
            return CommandResult(
                success=False, 
                message=f"Geçersiz rol. Seçenekler: {', '.join(r.value for r in UserRole)}"
            )
    
    async def cmd_keys(self) -> CommandResult:
        health = self.key_pool.health_check()
        lines = [f"  Toplam: {health['total']} | Aktif: {health['active']} | Hatalı: {health['error']}"]
        return CommandResult(success=True, message="\n".join(lines))
    
    def _find_agent(self, name: str) -> Agent | None:
        """Büyük/küçük harf duyarsız ajan arama."""
        name_lower = name.lower()
        for a in self.session.agents:
            if a.name.lower() == name_lower:
                return a
        # Prefix match
        for a in self.session.agents:
            if a.name.lower().startswith(name_lower):
                return a
        return None


@dataclass
class CommandResult:
    success: bool
    message: str | None  # None ise TUI'da gösterme
```

---

## 8. Oturum ve Kalıcılık

### 8.1 JSONL Formatı

Her mesaj bir JSON satırı olarak yazılır:

```jsonl
{"id":"msg-001","turn":1,"speaker":"Atlas","speaker_type":"agent","content":"Merhaba...","timestamp":"2026-04-20T14:30:00","topic":"Yapay zekâ","metadata":{"tokens":145},"reply_to":null,"is_summary":false}
{"id":"msg-002","turn":2,"speaker":"Mira","speaker_type":"agent","content":"Katılıyorum ama...","timestamp":"2026-04-20T14:30:05","topic":"Yapay zekâ","metadata":{"tokens":167},"reply_to":"msg-001","is_summary":false}
```

### 8.2 SessionManager

```python
class SessionManager:
    """
    Oturum kaydetme, yükleme ve dışa aktarma.
    """
    
    SESSIONS_DIR = "data/sessions"
    
    def __init__(self):
        self.sessions_dir = Path(self.SESSIONS_DIR)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, session: Session):
        """Oturumu diske kaydet."""
        # 1. Session metadata
        meta_path = self.sessions_dir / f"{session.id}.json"
        meta = {
            "id": session.id,
            "name": session.name,
            "created_at": session.created_at.isoformat(),
            "status": session.status.value,
            "current_turn": session.current_turn,
            "current_topic": asdict(session.current_topic) if session.current_topic else None,
            "user_role": session.user_role.value,
            "agents": [asdict(a) for a in session.agents],
            "topics": [asdict(t) for t in session.topics],
            "summaries": [asdict(s) for s in session.memory.summaries] if session.memory else [],
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        
        # 2. Mesajlar (append-only JSONL)
        messages_path = self.sessions_dir / f"{session.id}.jsonl"
        with open(messages_path, "a", encoding="utf-8") as f:
            for msg in session.memory.shared_history:
                if not getattr(msg, "_saved", False):
                    f.write(json.dumps(asdict(msg), ensure_ascii=False) + "\n")
                    msg._saved = True
    
    def load(self, session_id: str) -> Session:
        """Kaydedilmiş oturumu yükle."""
        meta_path = self.sessions_dir / f"{session_id}.json"
        messages_path = self.sessions_dir / f"{session_id}.jsonl"
        
        if not meta_path.exists():
            raise SessionNotFoundError(f"Oturum bulunamadı: {session_id}")
        
        meta = json.loads(meta_path.read_text())
        
        # Mesajları yükle
        messages = []
        if messages_path.exists():
            for line in messages_path.read_text().strip().split("\n"):
                if line:
                    msg_data = json.loads(line)
                    msg = Message(**msg_data)
                    msg._saved = True
                    messages.append(msg)
        
        # Session nesnesini oluştur
        session = Session(
            id=meta["id"],
            name=meta["name"],
            created_at=datetime.fromisoformat(meta["created_at"]),
            status=SessionStatus(meta["status"]),
            agents=[Agent(**a) for a in meta["agents"]],
            messages=messages,
            topics=[Topic(**t) for t in meta["topics"]],
            current_topic=Topic(**meta["current_topic"]) if meta["current_topic"] else None,
            current_turn=meta["current_turn"],
            user_role=UserRole(meta["user_role"]),
            ...
        )
        
        return session
    
    def list_sessions(self) -> list[dict]:
        """Tüm kaydedilmiş oturumları listele."""
        sessions = []
        for meta_path in self.sessions_dir.glob("*.json"):
            meta = json.loads(meta_path.read_text())
            sessions.append({
                "id": meta["id"],
                "name": meta["name"],
                "created_at": meta["created_at"],
                "turn_count": meta["current_turn"],
                "status": meta["status"],
            })
        return sorted(sessions, key=lambda s: s["created_at"], reverse=True)
    
    def export(self, session: Session, fmt: str) -> str:
        """
        Oturumu farklı formatlarda dışa aktar.
        
        fmt: "jsonl" | "md" | "txt"
        """
        if fmt == "jsonl":
            return self._export_jsonl(session)
        elif fmt == "md":
            return self._export_markdown(session)
        elif fmt == "txt":
            return self._export_text(session)
        raise ValueError(f"Desteklenmeyen format: {fmt}")
    
    def _export_markdown(self, session: Session) -> str:
        lines = [
            f"# {session.name}",
            f"**Konu:** {session.current_topic.content}",
            f"**Tarih:** {session.created_at:%Y-%m-%d %H:%M}",
            f"**Tur Sayısı:** {session.current_turn}",
            "",
            "---",
            "",
        ]
        for msg in session.memory.shared_history:
            if msg.is_summary:
                lines.append(f"### 📋 Özet (Tur {msg.turn})")
            else:
                lines.append(f"**[{msg.speaker}]** (Tur {msg.turn}):")
            lines.append(msg.content)
            lines.append("")
        return "\n".join(lines)
```

### 8.3 Otomatik Kaydetme

```python
# Her turda otomatik kaydet (append-only, performanslı)
AUTO_SAVE_INTERVAL = 5  # Her 5 turda bir

# SessionManager.save() sadece yeni (henüz kaydedilmemiş) mesajları yazar
# Bu sayede her seferinde tüm dosya yeniden yazılmaz
```

### 8.4 Dosya Yapısı

```
data/
├── config.yaml
└── sessions/
    ├── abc123.json          # Session metadata
    ├── abc123.jsonl         # Mesaj kayıtları
    ├── def456.json
    ├── def456.jsonl
    └── ...
```

---

## 9. Hata Yönetimi ve Güvenlik

### 9.1 Hata Hiyerarşisi

```python
class KonsilisyumError(Exception):
    """Temel hata sınıfı."""
    pass

class NoActiveAgentError(KonsilisyumError):
    """Konuşacak aktif ajan kalmadı."""
    pass

class AllKeysExhaustedError(KonsilisyumError):
    """Tüm API anahtarları tükendi."""
    pass

class SessionNotFoundError(KonsilisyumError):
    """Oturum dosyası bulunamadı."""
    pass

class InvalidCommandError(KonsilisyumError):
    """Geçersiz komut."""
    pass

class AgentNotFoundError(KonsilisyumError):
    """Ajan bulunamadı."""
    pass

class QuotaExceededError(KonsilisyumError):
    """API kotası aşıldı."""
    pass

# API hataları
class RateLimitError(KonsilisyumError):
    retry_after: int | None
    
class AuthError(KonsilisyumError):
    pass

class ServerError(KonsilisyumError):
    pass
```

### 9.2 Hata Kurtarma Stratejileri

| Hata | Kaynak | Kurtarma |
|------|--------|----------|
| API timeout | Ağ | 3 retry, sonra sonraki anahtar |
| Rate limit | Mistral | Sonraki anahtar, retry_after kadar bekle |
| Geçersiz anahtar | Kullanıcı | Anahtarı devre dışı bırak, kullanıcıya bildir |
| Sunucu hatası | Mistral | Exponential backoff ile retry |
| Tüm anahtarlar tükendi | Sistem | Otomatik duraklat, kullanıcıya bildir |
| Ajan yok | Kullanıcı | Tüm ajanları kicklediyse uyarı ver |
| Oturum bozuk | Disk | Son kayıttan yükle, kayıp mesajları atla |
| Token limit aşıldı | Model | Mesajı kes, "[...kesildi]" ekle |
| JSON parse hatası | Model çıktısı | Hata mesajı göster, bir sonraki turda devam et |
| Disk dolu | Dosya sistemi | TUI'da uyarı, oturumu memory'de tut |

### 9.3 Graceful Degradation

```python
async def safe_execute_turn(self) -> TurnResult:
    """
    Tek bir turu güvenli şekilde çalıştır.
    Hata olsa bile sistemi çökertmez.
    """
    try:
        return await self.orchestrator.execute_turn()
    except AllKeysExhaustedError:
        self.app.add_system_message(
            "⚠ Tüm API anahtarları tükendi. /keys ile durumu kontrol edin."
        )
        self.orchestrator.pause()
        return TurnResult(status="error", message="keys_exhausted")
    except NoActiveAgentError:
        self.app.add_system_message(
            "⚠ Konuşacak aktif ajan yok. /spawn ile yeni ajan ekleyin."
        )
        self.orchestrator.pause()
        return TurnResult(status="error", message="no_agents")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}", exc_info=True)
        self.app.add_system_message(f"⚠ Hata: {e}. Sonraki turda devam edilecek.")
        await asyncio.sleep(5)
        return TurnResult(status="error", message=str(e))
```

### 9.4 Güvenlik Önlemleri

- **API anahtarları** config.yaml'da saklanır, JSONL kayıtlarına yazılmaz
- **Prompt injection**: Kullanıcı mesajı doğrudan prompt'a eklenir ama system prompt ile ayrılır
- **Token bomb**: max_tokens=300 ile çıkış sınırı var
- **Döngü bomb**: max_auto_turns=50 ile otomatik tur sınırı var
- **Dosya izinleri**: Session dosyaları kullanıcı izinleriyle oluşturulur

---

## 10. Eşzamanlılık ve Performans

### 10.1 Async Mimari

```
Main Thread (Textual TUI event loop)
│
├── User Input Handler (sync, TUI thread)
│   └── Komut ayrıştırma ve dispatch
│
└── Council Loop (async, background worker)
    │
    ├── Orkestratör tur döngüsü
    │   ├── Konuşmacı seçimi (sync, hızlı)
    │   ├── Prompt oluşturma (sync, hızlı)
    │   ├── API çağrısı (async, bekleme)
    │   ├── Yanıt işleme (sync, hızlı)
    │   ├── JSONL yazma (async, I/O)
    │   └── TUI güncelleme (call_from_thread)
    │
    └── Memory güncelleme (async, arka plan)
        ├── Ajan hafıza güncelleme
        └── Öret üretme
```

### 10.2 Gecikme Yönetimi

```python
class ThrottleConfig:
    """Tur arası gecikme ayarları."""
    
    TURN_DELAY_SECONDS = 2.0        # Normal tur arası bekleme
    POST_USER_DELAY_SECONDS = 3.0   # Kullanıcı mesajından sonra ek bekleme
    API_TIMEOUT_SECONDS = 30.0      # API çağrısı timeout
    MEMORY_UPDATE_TIMEOUT = 45.0    # Hafıza güncelleme timeout
    SUMMARY_TIMEOUT = 60.0          # Özet üretim timeout

class TurnThrottler:
    """Tur arası gecikme ve hız kontrolü."""
    
    def __init__(self, config: ThrottleConfig):
        self.config = config
        self.last_turn_time = 0
    
    async def wait_between_turns(self, had_user_input: bool):
        """Tur arası bekle. Kullanıcı girdisi kontrolü için fırsat ver."""
        delay = self.config.TURN_DELAY_SECONDS
        if had_user_input:
            delay = self.config.POST_USER_DELAY_SECONDS
        
        # Interruptible wait: her 0.5 saniyede bir kontrol et
        elapsed = 0
        while elapsed < delay:
            await asyncio.sleep(0.5)
            elapsed += 0.5
            # Burada pause kontrolü yapılabilir
```

### 10.3 Performans Hedefleri

| Metrik | Hedef | Not |
|--------|-------|-----|
| Tur başına toplam süre | < 5 saniye | API çağrısı dahil |
| TUI güncelleme gecikmesi | < 100ms | Mesaj ekleme |
| Komut yanıt süresi | < 50ms | Ayrıştırma + dispatch |
| JSONL yazma | < 10ms | Append-only |
| Oturum yükleme | < 2 saniye | 1000 mesaj için |
| Bellek kullanımı | < 200MB | Normal çalışma |

---

## 11. Yapılandırma Sistemi

### 11.1 config.yaml

```yaml
# Konsilisyum Yapılandırma Dosyası

# LLM Ayarları
llm:
  model: "mistral-small-latest"
  max_tokens: 300
  temperature: 0.7
  base_url: "https://api.mistral.ai/v1"

# API Anahtarları
api_keys:
  - id: "key-01"
    key: "${MISTRAL_KEY_01}"     # Çevre değişkeni referansı
    assigned: "Atlas"
  - id: "key-02"
    key: "${MISTRAL_KEY_02}"
    assigned: "Mira"
  - id: "key-03"
    key: "${MISTRAL_KEY_03}"
    assigned: "Kaan"
  - id: "pool-01"
    key: "${MISTRAL_POOL_01}"
    pool: true
  - id: "pool-02"
    key: "${MISTRAL_POOL_02}"
    pool: true
  # ... daha fazla pool anahtarı

# Varsayılan Ajanlar
agents:
  - name: "Atlas"
    role: "Stratejist"
    goal: "Fikirleri uygulanabilir eylem planına çevirmek"
    blind_spot: "İnsan maliyetini küçümseme eğilimi"
    style: "Kısa, net, karar odaklı"
    trigger: "Belirsizlik görünce çerçeve kurar"
    color: "#ff6b6b"
    
  - name: "Mira"
    role: "Etikçi"
    goal: "İnsan etkisini ve uzun vadeli riskleri sorgulamak"
    blind_spot: "Aşırı temkinlilik"
    style: "Sakin, analitik, uyarıcı"
    trigger: "Güç asimetrisi görünce itiraz eder"
    color: "#4ecdc4"
    
  - name: "Kaan"
    role: "Şüpheci"
    goal: "Boş varsayımları ve romantik fikirleri delmek"
    blind_spot: "Yapıcı olmadan eleştirmek"
    style: "Sert, kısa, meydan okuyan"
    trigger: "Kanıtsız iddia görünce baskı kurar"
    color: "#ffe66d"

# Hafıza Ayarları
memory:
  context_window_size: 8        # Son N mesaj
  summary_interval: 20          # Her N turda özet
  memory_update_interval: 5     # Her N turda ajan hafıza güncelle
  max_agent_memory_items: 20    # Ajan başına maks not

# Orkestratör Ayarları
orchestrator:
  turn_delay: 2.0               # Tur arası bekleme (saniye)
  post_user_delay: 3.0          # Kullanıcı mesajı sonrası bekleme
  max_auto_turns: 50            # Maks otomatik tur
  repetition_threshold: 0.7     # Tekrar eşiği
  max_message_words: 500        # Maks mesaj kelime sayısı

# TUI Ayarları
tui:
  show_timestamps: true
  show_roles: true
  sidebar_width: 30
  theme: "dark"

# Oturum Ayarları
session:
  auto_save_interval: 5         # Her N turda otomatik kaydet
  sessions_dir: "data/sessions"

# Çıktı Ayarları
output:
  summary_model: "mistral-medium-latest"  # Özet için daha güçlü model
  export_dir: "data/exports"
```

### 11.2 Ayar Yönetimi

```python
from pydantic import BaseModel
from pydantic-settings import BaseSettings

class LLMConfig(BaseModel):
    model: str = "mistral-small-latest"
    max_tokens: int = 300
    temperature: float = 0.7
    base_url: str = "https://api.mistral.ai/v1"

class MemoryConfig(BaseModel):
    context_window_size: int = 8
    summary_interval: int = 20
    memory_update_interval: int = 5
    max_agent_memory_items: int = 20

class OrchestratorConfig(BaseModel):
    turn_delay: float = 2.0
    post_user_delay: float = 3.0
    max_auto_turns: int = 50
    repetition_threshold: float = 0.7
    max_message_words: int = 500

class AppConfig(BaseSettings):
    llm: LLMConfig = LLMConfig()
    api_keys: list[dict] = []
    agents: list[dict] = []
    memory: MemoryConfig = MemoryConfig()
    orchestrator: OrchestratorConfig = OrchestratorConfig()
    session: dict = {}
    tui: dict = {}
    output: dict = {}
    
    class Config:
        env_file = ".env"
        yaml_file = "data/config.yaml"
    
    @classmethod
    def load(cls) -> "AppConfig":
        """YAML dosyasından ve çevre değişkenlerinden yapılandırmayı yükle."""
        yaml_path = Path(cls.Config.yaml_file)
        if yaml_path.exists():
            with open(yaml_path) as f:
                data = yaml.safe_load(f) or {}
            # ${ENV_VAR} referanslarını çöz
            data = cls._resolve_env_vars(data)
            return cls(**data)
        return cls()
    
    @staticmethod
    def _resolve_env_vars(data: dict) -> dict:
        """${VAR} kalıplarını çevre değişkenleriyle değiştir."""
        import os
        import re
        
        def resolve(value):
            if isinstance(value, str):
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for match in matches:
                    env_val = os.environ.get(match, "")
                    value = value.replace(f"${{{match}}}", env_val)
                return value
            elif isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve(v) for v in value]
            return value
        
        return resolve(data)
```

---

## 12. Test Stratejisi

### 12.1 Test Katmanları

```
┌──────────────────────────────────────┐
│           E2E TESTLERİ               │  Tam sistem: başlat → konuş → komut → çık
├──────────────────────────────────────┤
│         INTEGRATION TESTLERİ         │  Modüller arası: orkestratör + API + hafıza
├──────────────────────────────────────┤
│           UNIT TESTLERİ              │  Tek sınıf/fonksiyon: komut ayrıştırma, 
│                                      │  konuşmacı seçimi, tekrar algılama
└──────────────────────────────────────┘
```

### 12.2 Unit Testler

```python
# tests/test_command_parser.py

class TestCommandParser:
    def test_normal_message(self):
        parser = CommandParser()
        result = parser.parse("Merhaba, bu bir mesaj")
        assert isinstance(result, UserMessage)
        assert result.content == "Merhaba, bu bir mesaj"
    
    def test_slash_command(self):
        parser = CommandParser()
        result = parser.parse("/pause")
        assert isinstance(result, ParsedCommand)
        assert result.command == "pause"
    
    def test_ask_command(self):
        parser = CommandParser()
        result = parser.parse("/ask Mira etik risk ne")
        assert result.command == "ask"
        assert result.args["agent"] == "Mira"
        assert result.args["message"] == "etik risk ne"
    
    def test_unknown_command(self):
        parser = CommandParser()
        result = parser.parse("/bilinmeyen argüman")
        assert isinstance(result, UnknownCommand)
    
    def test_empty_input(self):
        parser = CommandParser()
        result = parser.parse("")
        assert isinstance(result, UserMessage)
        assert result.content == ""


# tests/test_speaker_selection.py

class TestSpeakerSelection:
    def test_basic_rotation(self):
        """Ajanlar dönüşümlü seçilmeli."""
        agents = [create_agent("Atlas"), create_agent("Mira"), create_agent("Kaan")]
        context = TurnContext(last_speaker="Atlas", current_turn=5)
        selected = select_speaker(agents, context)
        assert selected.name != "Atlas"  # Son konuşmacı tekrar seçilmemeli
    
    def test_reply_priority(self):
        """Cevap bekleyen ajan öncelikli."""
        agents = [create_agent("Atlas"), create_agent("Mira"), create_agent("Kaan")]
        context = TurnContext(pending_reply_to="Mira", current_turn=5)
        selected = select_speaker(agents, context)
        assert selected.name == "Mira"
    
    def test_muted_excluded(self):
        """Mute olanlar seçilmemeli."""
        agents = [create_agent("Atlas"), create_agent("Mira", muted=True)]
        context = TurnContext(current_turn=5)
        selected = select_speaker(agents, context)
        assert selected.name == "Atlas"
    
    def test_no_active_agents(self):
        """Aktif ajan yoksa hata fırlat."""
        agents = [create_agent("Atlas", muted=True), create_agent("Mira", removed=True)]
        context = TurnContext(current_turn=5)
        with pytest.raises(NoActiveAgentError):
            select_speaker(agents, context)


# tests/test_repetition.py

class TestRepetitionDetection:
    def test_detect_obvious_repetition(self):
        msg = Message(content="Bu konuda yapay zekâ tehlikeli olabilir")
        recent = [Message(content="Bu konuda yapay zekâ tehlikeli olabilir diye düşünüyorum")]
        assert detect_repetition(msg.content, recent, threshold=0.7) == True
    
    def test_no_repetition(self):
        msg = Message(content="Tamamen farklı bir konudan bahsetmek istiyorum")
        recent = [Message(content="Ekonomik göstergeler bu ay iyi")]
        assert detect_repetition(msg.content, recent, threshold=0.7) == False


# tests/test_key_pool.py

class TestKeyPool:
    def test_assigned_key_priority(self):
        """Ajan atanmış anahtarı kullanmalı."""
        pool = KeyPool([
            APIKey(id="k1", key="x", assigned_agent="Atlas"),
            APIKey(id="k2", key="y", is_pool=True),
        ])
        key = pool.get_key(agent_id="Atlas")
        assert key.id == "k1"
    
    def test_fallback_to_pool(self):
        """Atanmış anahtar yoksa havuzdan al."""
        pool = KeyPool([
            APIKey(id="k1", key="x", assigned_agent="Atlas"),
            APIKey(id="k2", key="y", is_pool=True),
        ])
        key = pool.get_key(agent_id="Mira")
        assert key.id == "k2"
    
    def test_rate_limited_skipped(self):
        """Rate limitli anahtar atlanmalı."""
        pool = KeyPool([
            APIKey(id="k1", key="x", is_pool=True, status=KeyStatus.RATE_LIMITED),
            APIKey(id="k2", key="y", is_pool=True),
        ])
        key = pool.get_key()
        assert key.id == "k2"


# tests/test_memory.py

class TestMemoryManager:
    def test_context_window_size(self):
        """Bağlam penceresi son N mesajı içermeli."""
        memory = MemoryManager(session=mock_session, api_client=mock_client)
        for i in range(20):
            memory.add_message(create_message(turn=i, content=f"Mesaj {i}"))
        
        context = memory.build_context_window(agent=mock_agent)
        lines = [l for l in context.split("\n") if l.startswith("[Tur")]
        assert len(lines) == 8  # CONTEXT_WINDOW_SIZE
    
    def test_summary_included(self):
        """Bağlam penceresinde son özet olmalı."""
        memory = MemoryManager(session=mock_session, api_client=mock_client)
        memory.summaries = [Summary(content="Özet metni", turn_range=(0, 20))]
        
        context = memory.build_context_window(agent=mock_agent)
        assert "ÖZET" in context
        assert "Özet metni" in context
```

### 12.3 Integration Testler

```python
# tests/test_orchestrator.py

class TestOrchestrator:
    @pytest.fixture
    def mock_api(self):
        """API çağrılarını mock'la."""
        ...
    
    async def test_full_cycle(self, mock_api):
        """3 ajan 1 tur dönüşümlü konuşmalı."""
        ...
    
    async def test_user_interruption(self, mock_api):
        """Kullanıcı mesajı ajan sırasını değiştirmeli."""
        ...
    
    async def test_auto_pause(self, mock_api):
        """max_auto_turns sonunda otomatik duraklamalı."""
        ...
```

### 12.4 Test Komutları

```bash
# Tüm testler
pytest tests/ -v

# Sadece unit testler
pytest tests/test_command_parser.py tests/test_speaker_selection.py tests/test_repetition.py -v

# Coverage
pytest tests/ --cov=konsilisyum --cov-report=term-missing

# Integration (API mock ile)
pytest tests/test_orchestrator.py -v
```

---

## Ek A: Örnek Prompt Akışı

### Tur 1 — Atlas konuşuyor

**System Prompt:**
```
Sen Atlas'sın. Rolün: Stratejist.

Amaç: Fikirleri uygulanabilir eylem planına çevirmek
Kör noktan: İnsan maliyetini küçümseme eğilimi — Buna dikkat et, ama bunun için özür dileme.
Konuşma stilin: Kısa, net, karar odaklı
Tetikleyicin: Belirsizlik görünce çerçeve kurar

Konsil Kuralları:
- 500 kelimeyi geçme.
- Kendi görüşünü savun ama diğerlerini dinle.
- Tekrar yapmaktan kaçın.
- Diğer ajanlara isimleriyle hitap et.
- Tartışmaya yapıcı katkı yap.
- Eğer söyleyecek yeni bir şey yoksa, "Pas" de.

Senin kişisel notların:
Henüz kişisel notun yok.
```

**Context Window:**
```
Konu: Yapay zekâ eğitimi geleceği nasıl şekillendirir?
[Sistem notu: Tartışmanın ilk turu. Görüşünü belirt.]
```

**Generation Directive:**
```
Konu: Yapay zekâ eğitimi geleceği nasıl şekillendirir?
Sen sıradaki konuşmacısın. Tartışmaya katkı yap.
Bu tartışmanın ilk turu. Perspektifini ortaya koy.
```

**Atlas'ın Yanıtı:**
```
Yapay zekâ eğitimi konusunda net bir çerçeve kurmamız gerekiyor. 
Üç eksen var: eğitim içeriği, eğitim yöntemi ve erişim.

İçerik açısından: sadece teknik beceri değil, 
etik muhakeme ve insan-AI işbirliği öğretmeliyiz.

Yöntem açısından: kişiselleştirilmiş öğrenme yolları 
AI'nın en güçlü katkısı olabilir.

Erişim açısından: tehlike açık — 
kaynaklı ülkeler arasında uçurum büyüyor.

Öneri: Bu üç ekseni ayrı ayrı tartışalım.
Sizce hangisi en kritik?
```

### Tur 2 — Mira'ya yanıt hakkı

**Generation Directive:**
```
Konu: Yapay zekâ eğitimi geleceği nasıl şekillendirir?
Sen sıradaki konuşmacısın. Tartışmaya katkı yap.
Atlas bir soru sordu. Cevap ver veya kendi perspektifini ekle.
```

---

## Ek B: Bağımlılıklar

```toml
# pyproject.toml

[project]
name = "konsilisyum"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "textual>=0.47.0",       # TUI framework
    "rich>=13.0.0",          # Terminal formatting
    "httpx>=0.25.0",         # Async HTTP client (Mistral API)
    "pydantic>=2.0.0",       # Veri doğrulama
    "pydantic-settings>=2.0.0",  # Yapılandırma
    "pyyaml>=6.0",           # YAML parsing
    "click>=8.0.0",          # CLI framework
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
]

[project.scripts]
konsilisyum = "konsilisyum.main:main"
```

---

## Ek C: Model Seçim Rehberi

| Model | Kullanım | Maliyet (1M token) | Hız |
|-------|----------|---------------------|------|
| `mistral-small-latest` | Ajan konuşmaları (varsayılan) | $0.1 / $0.3 | Hızlı |
| `mistral-medium-latest` | Özet, karar, analiz | $0.6 / $1.8 | Orta |
| `mistral-large-latest` | Karmaşık çıktılar (opsiyonel) | $2.0 / $6.0 | Yavaş |

**Strateji:** Normal turlar için `small`, özet ve derin analiz için `medium`, gerekirse `large`. Bu şekilde maliyet optimize edilir.

---

## Ek D: Token Bütçesi

### Tek Tur Tahmini

| Bileşen | Token |
|---------|-------|
| System prompt | ~200 |
| Context window (son 8 mesaj) | ~1200 |
| Generation directive | ~50 |
| **Toplam giriş** | **~1450** |
| Çıkış (ajan mesajı) | ~200-300 |
| **Toplam tur** | **~1700** |

### 100 Tur Tahmini

| Kalem | Token | Maliyet (small) |
|-------|-------|-----------------|
| Ajan turları (100 × 1700) | 170,000 | $0.17 |
| Özet (5 × 2000, medium) | 10,000 | $0.02 |
| Hafıza güncelleme (20 × 1500) | 30,000 | $0.04 |
| **Toplam** | **210,000** | **~$0.23** |

1000 tur ≈ $2.3. 50 API anahtarı ile pratikte sınırsız.
