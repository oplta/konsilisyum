# Mimari Genel Bakış

Konsilisyum beş katmanlı bir mimariye sahiptir. Bu sayfa büyük resmi verir; detaylar ilgili sayfalara bağlanır.

## Katmanlar

```
┌──────────────────────────────────────────────────────────┐
│                    TUI  (Textual/Rich)                    │  ← Sunum
├──────────────────────────────────────────────────────────┤
│              Command Handler  (28+ komut)                │  ← Etkileşim
├──────────────────────────────────────────────────────────┤
│   Orchestrator   │   Memory Manager   │   Session Mgr    │  ← Çekirdek
├──────────────────────────────────────────────────────────┤
│  LLM Abstraction  │  KeyPool  │  Provider Clients         │  ← API
├──────────────────────────────────────────────────────────┤
│         Models  (Agent, Message, Session, Topic)         │  ← Veri
└──────────────────────────────────────────────────────────┘
```

### 1. Veri Katmanı

**Modül:** `konsilisyum/core/models.py`

Tüm domain varlıklarının dataclass'ları. Saf veri, davranışsız.

- `Agent`, `Message`, `Topic`, `Summary`, `Session`, `APIKey`

### 2. API Katmanı

**Modül:** `konsilisyum/api/`

LLM sağlayıcılarını soyutlar. Hangi modeli kullandığını çekirdek bilmez.

- `BaseLLMClient` — arayüz
- `MistralClient`, `OpenAIClient`, `AnthropicClient`, `OllamaClient` — somut
- `KeyPool` — API anahtarı rotasyonu ve rate limit yönetimi

### 3. Çekirdek Katman

**Modüller:** `konsilisyum/core/orchestrator.py`, `memory.py`, `session.py`

Asıl iş mantığı:

- **Orchestrator:** Sıradaki ajanı seçer, prompt inşa eder, yanıtı işler
- **MemoryManager:** Bağlam penceresi, ajan hafızası, tekrar algılama
- **SessionManager:** Oturum kaydet/yükle, export

### 4. Etkileşim Katmanı

**Modül:** `konsilisyum/commands/`

Kullanıcı komutlarını çekirdek eylemlere eşler. Her komut izole bir fonksiyondur.

- `/pause`, `/resume`, `/topic`, `/add-agent`, `/export`, ...

### 5. Sunum Katmanı

**Modül:** `konsilisyum/tui/`

Terminal arayüzü. Rich + Textual. Kullanıcı girişi alır, çekirdekten gelen olayları renderlar.

## İstek Akışı

Bir tur şu şekilde işlenir:

```
1. Kullanıcı prompt'a mesaj yazar
        ↓
2. TUI girdiyi Command Handler'a iletir
        ↓
3. Komut parse edilir
        ↓
4. Eğer "send" → Orchestrator._user_message_pending ayarlanır
   Eğer "/topic" → Session.current_topic güncellenir
        ↓
5. Orchestrator.execute_turn() çağrılır
        ↓
6. select_speaker() — puan tabanlı seçim
        ↓
7. _build_system_prompt() — ajanın kişiliği + hafıza
        ↓
8. _build_user_prompt() — bağlam + direktifler
        ↓
9. api_client.complete_with_retry() — LLM çağrısı
        ↓
10. Yanıt: pas mı, tekrar mı, geçerli mi?
        ↓
11. Message oluşturulup Session.messages'a eklenir
        ↓
12. MemoryManager.add_message() ile hafıza güncellenir
        ↓
13. TUI yeniden render edilir
```

## Olay Akışı

Asenkron olay tabanlı bir yapı kullanılır:

```python
# asyncio event loop
event = await queue.get()
match event.type:
    case EventType.AGENT_SPEAK:
        tui.render_message(event.payload)
    case EventType.STATUS_CHANGE:
        tui.update_status(event.payload)
    case EventType.SESSION_SAVED:
        log.info("Snapshot alındı")
```

## Veri Akışı

```
Session
  ├── Agents[] ──> Orchestrator.select_speaker()
  ├── Topics[] ──> Prompt'a konu metni
  ├── Messages[] ─> MemoryManager.build_context_window()
  └── current_turn ─> Orchestrator.increment()
```

## Tek Sorumluluk Prensibi

Her modülün **tek** bir işi vardır:

| Modül                | Tek Sorumluluk                |
|----------------------|--------------------------------|
| `models.py`          | Veri şekli                    |
| `llm.py`             | LLM arayüzü + retry           |
| `mistral.py`         | Mistral API çağrısı            |
| `keypool.py`         | Anahtar rotasyonu             |
| `orchestrator.py`    | Tur döngüsü, konuşmacı seçimi  |
| `memory.py`          | Bağlam + hafıza yönetimi       |
| `session.py`         | Kalıcılık + export             |
| `commands/handler.py`| Komut ayrıştırma               |
| `commands/<cmd>.py`  | Tek bir komut                  |
| `tui/`               | Render + girdi                 |

Bu ayrım sayesinde:

- **Test edilebilirlik:** her katman izole test edilir
- **Değiştirilebilirlik:** yeni LLM sağlayıcısı eklemek `api/providers.py`'ye bir sınıf
- **Anlaşılabilirlik:** dosya adı ne yaptığını söyler

## Sonraki Adımlar

- [Orkestratör](orchestrator.md) — puan tabanlı seçim ve tur döngüsü
- [Hafıza](memory.md) — üç katmanlı hafıza mimarisi
- [API](api.md) — provider soyutlaması
- [Komutlar](commands.md) — komut eşleme mimarisi
