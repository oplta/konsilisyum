# Hafıza Katmanı

Konsilisyum'un hafıza mimarisi üç katmanlıdır. Bu sayede 50+ tur sonra bile ajanlar tutarlı kalır ve bağlam taşması engellenir.

## Üç Katman

```
┌─────────────────────────────────────────────────────┐
│  1. Bağlam Penceresi  (kısa vadeli, son 8 mesaj)    │
├─────────────────────────────────────────────────────┤
│  2. Ajan Hafızası     (uzun vadeli, ajana özel)     │
├─────────────────────────────────────────────────────┤
│  3. Özetler           (arşiv, her 20 turda bir)     │
└─────────────────────────────────────────────────────┘
```

## 1. Bağlam Penceresi

**Modül:** `konsilisyum/core/memory.py`

Her LLM çağrısında son N mesajı içerir. Bu, anlık tutarlılık sağlar.

```python
def build_context_window(self) -> str:
    parts: list[str] = []

    if self.summaries:
        latest = self.summaries[-1]
        parts.append(f"[Önceki özet]: {latest.text}")

    recent = self.history[-self.context_window_size:]
    for msg in recent:
        if msg.speaker_type == SpeakerType.AGENT:
            parts.append(f"[{msg.speaker}]: {msg.content}")
        else:
            parts.append(f"[Kullanıcı]: {msg.content}")

    return "\n".join(parts)
```

### Yapılandırma

```python
MemoryManager(context_window_size=8)  # varsayılan
```

`context_window_size` çok büyük olursa:

- Token kullanımı artar
- LLM yavaşlar
- Maliyet yükselir

Çok küçük olursa:

- Ajan son konuşmaları unutur
- Tekrar algılama zorlaşır
- Tutarlılık bozulur

8 iyi bir varsayılan: yaklaşık 1500 token.

## 2. Ajan Hafızası

Her ajanın **kendi not defteri** vardır. Bu, kişiliğin 50 tur sonra erimesini önler.

```python
self.agent_memories: dict[str, list[str]] = {
    "agent-id-1": [
        "Atlas: İlk turda net kararlar önerdi, ekip bunu kabul etti",
        "Mira: İnsan maliyeti konusunda uyardı, göz ardı edildi",
        "Kaan: Somut örnek istedi, henüz verilmedi"
    ],
    ...
}
```

### Güncelleme

Her 5 turda bir (`memory_update_interval`), bir **özet ajan** çağrılarak hafıza tazelenir:

```python
def update_agent_memories(self, agent: Agent):
    prompt = f"""
    Aşağıdaki mesajlara dayanarak {agent.name} için 3-5 kısa not yaz.
    Notlar ajanın gelecekteki turlarda tutarlı kalmasını sağlamalı.

    Mesajlar:
    {recent_messages}
    """
    notes = self.summarizer_agent.complete(prompt)
    self.agent_memories[agent.id] = notes
```

Bu "özet ajan" normalde aynı LLM kullanır, sadece farklı bir prompt alır.

### Sistem Prompt'a Ekleme

```python
def _build_system_prompt(self, agent: Agent) -> str:
    memory_text = self.memory.get_agent_memory(agent.id)
    return SYSTEM_PROMPT_TEMPLATE.format(
        ...
        memory=memory_text,
    )
```

Ajan kendi notlarını **birinci ağızdan** görür.

## 3. Özetler

`summary_interval` (varsayılan 20) turda bir, tüm konuşma özetlenir.

```python
async def maybe_summarize(self):
    if len(self.history) - self.last_summary_at >= self.summary_interval:
        prompt = "Aşağıdaki konuşmayı 200 kelimede özetle:\n\n" + ...
        summary = await self.summarizer_agent.complete(prompt)
        self.summaries.append(Summary(
            turn=self.last_summary_at,
            text=summary,
            created_at=datetime.now(),
        ))
```

Özet, **bağlam penceresi** içine yerleştirilir:

```
[Önceki özet]: Bu oturumda yapay zeka etiği tartışıldı. Atlas
kuralları, Mira insan etkisini, Kaan kanıt eksikliğini vurguladı.
Şu anki odak: Avrupa Birliği düzenlemeleri.

[Atlas]: Şimdi somut bir öneri getireyim...
```

Bu sayede LLM, son 8 mesajda olmasa bile konuşmanın genel seyrini bilir.

## Tekrar Algılama

`detect_repetition()` Jaccard benzerliği:

```python
def detect_repetition(self, new_content: str, threshold: float = 0.7) -> bool:
    tokens_new = set(new_content.lower().split())
    for msg in reversed(self.history[-20:]):
        tokens_old = set(msg.content.lower().split())
        if not tokens_old:
            continue
        intersection = tokens_new & tokens_old
        union = tokens_new | tokens_old
        similarity = len(intersection) / len(union)
        if similarity >= threshold:
            return True
    return False
```

Aynı ajan son 20 turda %70+ kelime tekrarı yapıyorsa, mesaj iptal edilir ve "pas" muamelesi görür. Bu, LLM'lerin döngüye girmesini önler.

## Token Optimizasyonu

Toplam token bütçesi tipik bir turda:

```
Sistem promptu:    ~250 token
  - Ajan kimliği:   100
  - Hafıza:         150

Kullanıcı promptu: ~1500 token
  - Bağlam (8 msg): 1000
  - Direktifler:    200
  - Konu:           100
  - Sistem yönergesi: 200

Tamamlama:        ~300 token
─────────────────────────
Toplam:           ~2050 token
```

`max_tokens=300` tamamlama için, `temperature=0.7` yaratıcılık için.

## Yapılandırma

```python
MemoryManager(
    context_window_size=8,        # bağlamdaki son mesaj sayısı
    summary_interval=20,          # kaç turda bir özet
    memory_update_interval=5,     # kaç turda bir ajan hafızası güncelle
    max_agent_memory_items=20,    # ajan başına maks not
)
```

TUI'dan değiştirmek:

```
/config context_window_size 12
```

## Sınırlamalar

- **Çapraz oturum hafıza yok** — her oturum sıfırdan başlar (kasıtlı)
- **Vektör tabanlı arama yok** — semantik arama gerekirse eklenebilir
- **Özet kalitesi LLM'e bağlı** — kötü özet, hafıza kalitesini düşürür

## Sonraki Adım

- [API Katmanı](api.md) — LLM çağrısının kendisi
- [Komut Sistemi](commands.md) — hafızayı kullanıcıya açan komutlar
