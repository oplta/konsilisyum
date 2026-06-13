# Mimari Genel Bakış

Konsilisyum altı katmanlı bir mimariye sahiptir. Bu sayfa büyük resmi verir; detaylar ilgili sayfalara bağlanır.

## Katmanlar

```
┌──────────────────────────────────────────────────────────┐
│              Web UI  (Next.js + React)                    │  ← Sunum (Web)
├──────────────────────────────────────────────────────────┤
│              TUI  (Textual/Rich)                          │  ← Sunum (Terminal)
├──────────────────────────────────────────────────────────┤
│              WebSocket / REST API  (FastAPI)              │  ← İletişim
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

- `BaseLLMClient` — arayüz (finish_reason desteği)
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

- `/pause`, `/resume`, `/topic`, `/spawn`, `/export`, ...

### 5. İletişim Katmanı

**Modüller:** `konsilisyum/web/routes.py`, `websocket.py`

FastAPI ile REST API ve WebSocket desteği.

- `POST /api/sessions` — yeni oturum oluştur
- `GET /api/sessions` — oturumları listele
- `WS /ws/session/{id}` — gerçek zamanlı iletişim

### 6. Sunum Katmanı

#### Web (Next.js)

**Modül:** `web/`

Klasik Meclis temalı modern arayüz. Playfair Display + Source Serif 4 fontları.

- `components/AgentCards.tsx` — 5 ajan kartı
- `components/MessageStream.tsx` — mesaj akışı
- `components/MessageCard.tsx` — Markdown destekli mesaj kartı
- `components/BackstagePanel.tsx` — kontrol paneli
- `hooks/useWebSocket.ts` — WebSocket yönetimi
- `stores/sessionStore.ts` — Zustand state yönetimi

#### Terminal (Textual)

**Modül:** `konsilisyum/tui/`

Terminal arayüzü. Rich + Textual. Kullanıcı girişi alır, çekirdekten gelen olayları renderlar.

## İstek Akışı

### Web Akışı

```
1. Tarayıcı → POST /api/sessions
        ↓
2. FastAPI → AppBootstrapper.initialize()
        ↓
3. WebSocket bağlantısı kurulur
        ↓
4. session_state mesajı (5 ajan) gönderilir
        ↓
5. Orchestrator.execute_turn() otomatik başlar
        ↓
6. agent_message WebSocket ile gönderilir
        ↓
7. Tarayıcı mesajı render eder
```

### Terminal Akışı

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
| `web/app.py`         | FastAPI uygulaması             |
| `web/routes.py`      | REST API endpointleri          |
| `web/websocket.py`   | WebSocket handler              |
| `tui/`               | Render + girdi                 |
| `web/`               | Next.js frontend               |

Bu ayrım sayesinde:

- **Test edilebilirlik:** her katman izole test edilir
- **Değiştirilebilirlik:** yeni LLM sağlayıcısı eklemek `api/providers.py`'ye bir sınıf
- **Anlaşılabilirlik:** dosya adı ne yaptığını söyler

## Sonraki Adımlar

- [Orkestratör](orchestrator.md) — puan tabanlı seçim ve tur döngüsü
- [Hafıza](memory.md) — üç katmanlı hafıza mimarisi
- [API](api.md) — provider soyutlaması
- [Komutlar](commands.md) — komut eşleme mimarisi
