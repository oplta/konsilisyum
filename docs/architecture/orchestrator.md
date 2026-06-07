# Orkestratör

Orkestratör Konsilisyum'un kalbi. Her turda hangi ajanın konuşacağını, ona ne söyleneceğini ve gelen yanıtın nasıl işleneceğini belirler.

## Sınıf

```python
class Orchestrator:
    def __init__(
        self,
        session: Session,
        memory: MemoryManager,
        api_client: BaseLLMClient,
        key_pool: KeyPool,
        turn_delay: float = 2.0,
        max_auto_turns: int = 50,
    ): ...
```

## execute_turn()

Bir tur döngüsünün tam akışı:

```python
async def execute_turn(self) -> TurnResult:
    if self.session.auto_turns_since_user >= self.max_auto_turns:
        self.pause()
        return TurnResult(error="max_auto_turns")

    agent = self.select_speaker()                    # 1. Kim konuşacak?
    system_prompt = self._build_system_prompt(agent) # 2. Kimliği hazırla
    user_prompt = self._build_user_prompt(agent)     # 3. Direktifi hazırla

    try:
        result = await self.api_client.complete_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            get_key=lambda: self.key_pool.get_raw_key(agent),
        )
    except Exception as e:
        self.pause()
        return TurnResult(error=str(e))

    content = result.content

    is_pas = content.strip().lower() == "pas"
    if is_pas:
        agent.last_turn = self.session.current_turn
        return TurnResult(message=None, is_pas=True)

    if self.memory.detect_repetition(content):
        agent.last_turn = self.session.current_turn
        return TurnResult(message=None, is_pas=True, error="tekrar_tespit")

    if len(content.split()) > 500:
        content = " ".join(content.split()[:500]) + " [...kesildi]"

    msg = Message(
        turn=self.session.current_turn,
        speaker=agent.name,
        content=content,
        speaker_type=SpeakerType.AGENT,
        topic=self.session.current_topic.content,
        metadata={...},
    )
    self.session.messages.append(msg)
    self.memory.add_message(msg)
    self.session.current_turn += 1
    self.session.auto_turns_since_user += 1
    return TurnResult(message=msg)
```

## Konuşmacı Seçimi

`select_speaker()` puan tabanlı bir sistem kullanır. Her aday için:

```python
score = 0.0

# +5.0: Doğrudan kendisine sorulmuş
if self._pending_reply_to and agent.name == self._pending_reply_to:
    score += 5.0

# +1.0: Kullanıcı mesajı varsa herkes eşit aday
if self._user_message_pending:
    score += 1.0

# +0.5 * turns_silent (max +2.0): Ne kadar uzun süredir konuşmadı
turns_silent = self.session.current_turn - agent.last_turn
score += min(turns_silent * 0.5, 2.0)

# -3.0: Son konuşan o ise
if last_speaker == agent.name:
    score -= 3.0

# +0..0.5: küçük rastgelelik — sıra deterministik olmasın
score += random.uniform(0, 0.5)
```

Kazanan en yüksek puanlı ajan. Bu tasarım:

- Sona yakın konuşanlar kısa süre dinlenir
- Tüm ajanlar fırsat eşitliği alır
- Direkt sorular öncelik kazanır

## Prompt İnşası

### Sistem Promptu

```
Sen {name}, bir {role}.

Amacın: {goal}
Kör noktan: {blind_spot}
Konuşma üslubun: {style}
Tetikleyici koşulun: {trigger}

Senin hafıza defterin:
{memory}

Kurallar:
- Pas geçmek istiyorsan sadece "Pas" yaz
- Maksimum 500 kelime
- Net ve karakterine uygun konuş
```

### Kullanıcı Promptu

```
{context_window}

---
Konu: {topic}

{direktifler}
```

Direktifler dinamik eklenir:

- "Kullanıcı bir mesaj bıraktı: ..."
- "{ajan} sana direkt sordu. Cevap ver."
- "Uzun süredir konuşmadın. Görüşünü belirt."
- "Bu tartışmanın ilk turu. Perspektifini ortaya koy."

## Tekrar Algılama

`MemoryManager.detect_repetition()` Jaccard benzerliği kullanır:

```python
def detect_repetition(self, new_content: str, threshold: float = 0.7) -> bool:
    tokens_new = set(new_content.lower().split())
    for msg in reversed(self.history[-20:]):
        if msg.speaker_type != SpeakerType.AGENT:
            continue
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

%70 eşleşme eşiği aşılırsa mesaj `tekrar_tespit` hatasıyla iptal edilir.

## Max Auto Turns

Kullanıcı araya girmeden art arda 50 tur çalışırsa oturum otomatik duraklatılır. Bu, LLM maliyetini kontrol altında tutar ve "boş yere dönen" tartışmaları önler.

```python
if self.session.auto_turns_since_user >= self.max_auto_turns:
    self.pause()
    return TurnResult(error="max_auto_turns")
```

## Hata Yönetimi

API hatalarında:

1. **Rate limit** (429): `KeyPool` sıradaki anahtarı dener
2. **Auth error** (401): Anahtarı pasif yapar, sıradakine geçer
3. **Server error** (5xx): 3 deneme, üstel geri çekilme
4. **Network error:** 30 sn timeout, sonra duraklat

Tüm bu hatalar `TurnResult.error` olarak TUI'ye bildirilir.

## Asenkronluk

`async/await` yapısı:

```python
async def main_loop():
    while not orchestrator.is_paused():
        result = await orchestrator.execute_turn()
        if result.message:
            await tui.render(result.message)
        await asyncio.sleep(turn_delay)
```

`turn_delay` (varsayılan 2 sn) ajanların "düşünme" hissi yaratır ve rate limit'e saygı gösterir.

## Test

Orkestratör için 17+ entegrasyon testi var (`tests/test_integration.py`):

```python
@respx.mock
async def test_full_turn_cycle(self):
    respx.post(MISTRAL_URL).mock(return_value=httpx.Response(200, json=...))
    result = await orchestrator.execute_turn()
    assert result.message is not None
```

Detaylar: [Test](../development/testing.md).
