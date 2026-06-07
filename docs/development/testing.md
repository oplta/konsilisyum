# Test

Konsilisyum 50+ test ile birlikte gelir: birim, entegrasyon ve özellik testleri.

## Test Çalıştırma

```bash
# Tüm testler
uv run pytest

# veya
pytest

# Sadece birim
pytest tests/unit/

# Sadece entegrasyon
pytest tests/test_integration.py

# Belirli bir test
pytest tests/test_integration.py::TestMistralIntegration::test_rate_limit_handling

# Verbose
pytest -v

# İlk hatada dur
pytest -x

# Coverage raporu
pytest --cov=konsilisyum --cov-report=term-missing
```

## Test Yapısı

```
tests/
├── test_integration.py      # 17 entegrasyon testi
├── test_models.py           # veri modelleri
├── test_orchestrator.py     # orkestratör
├── test_memory.py           # hafıza
├── test_session.py          # oturum yönetimi
├── test_keypool.py          # anahtar havuzu
├── test_commands.py         # komut sistemi
└── ...
```

## Entegrasyon Testleri

`tests/test_integration.py` API sağlayıcılarını `respx` ile mock'layarak test eder:

```python
import httpx
import respx
import pytest

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


@pytest.mark.asyncio
@respx.mock
async def test_successful_completion():
    respx.post(MISTRAL_URL).mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "Test yanıt"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        })
    )
    client = MistralClient()
    result = await client.complete("system", "user", "key")
    assert result.content == "Test yanıt"
    assert result.tokens_in == 10
```

### Kapsam

- **Mistral** — başarı, 429 rate limit, 401 auth, 500 server
- **OpenAI** — başarı
- **Anthropic** — başarı
- **Ollama** — başarı
- **Orchestrator** — tam tur döngüsü, pas, max-turns, hata kurtarma
- **SessionManager** — kaydet/yükle/listele, md ve jsonl export

## Birim Testler

Her modülün kendi test dosyası var.

### `test_orchestrator.py`

```python
def test_select_speaker_prefers_pending_reply():
    session = make_session(agents=[A, B])
    orch = Orchestrator(session, ...)
    orch.set_pending_reply("B")
    assert orch.select_speaker().name == "B"
```

### `test_memory.py`

```python
def test_detect_repetition_returns_true_for_similar():
    mem = MemoryManager()
    mem.add_message(Message(content="Kurallar net olmalı"))
    assert mem.detect_repetition("Kurallar net ve açık olmalı")
```

### `test_keypool.py`

```python
def test_pool_returns_available_key():
    keys = [APIKey(id="1", is_pool=True), APIKey(id="2", is_pool=True)]
    pool = KeyPool(keys)
    assert pool.get_key().id in ["1", "2"]
```

## Test Yazma

### Yeni Komut İçin

```python
# tests/test_commands.py
from konsilisyum.commands.handler import CommandHandler


def test_topic_command_changes_topic():
    ctx = make_test_context()
    result = CommandHandler.dispatch("/topic", ["YZ", "etiği"], ctx)
    assert "Konu değiştirildi" in result
    assert ctx.session.current_topic.content == "YZ etiği"


def test_unknown_command_shows_help_hint():
    ctx = make_test_context()
    result = CommandHandler.dispatch("/nonexistent", [], ctx)
    assert "Bilinmeyen komut" in result
```

### Yeni Provider İçin

```python
@respx.mock
async def test_cohere_completion():
    respx.post(COHERE_URL).mock(
        return_value=httpx.Response(200, json={"text": "yanıt"})
    )
    client = CohereClient()
    result = await client.complete("sys", "user", "key")
    assert result.content == "yanıt"
```

## Fixture'lar

`tests/conftest.py` ortak fixture'ları sağlar:

```python
@pytest.fixture
def sample_session():
    agents = [
        Agent(name="Atlas", role="Stratejist", ...),
        Agent(name="Mira", role="Etikçi", ...),
    ]
    topic = Topic(content="Test")
    return Session(agents=agents, current_topic=topic)


@pytest.fixture
def tmp_sessions_dir(tmp_path):
    return str(tmp_path / "sessions")
```

## Mock Stratejisi

- **HTTP** → `respx`
- **Dosya sistemi** → `tmp_path` fixture
- **Zaman** → `freezegun` (gerektiğinde)
- **LLM yanıtları** → gerçek sağlayıcı yerine mock

Asla gerçek API'ye istek atma. CI'da kesinlikle çalışmamalı.

## Coverage Hedefi

```
konsilisyum/api/llm.py           ~95%
konsilisyum/api/mistral.py       ~90%
konsilisyum/api/providers.py     ~85%
konsilisyum/api/keypool.py       ~90%
konsilisyum/core/orchestrator.py ~85%
konsilisyum/core/memory.py       ~80%
konsilisyum/core/session.py      ~80%
konsilisyum/core/models.py       ~70%
konsilisyum/commands/            ~70%
konsilisyum/tui/                 ~50%  (zor test edilir)
```

Coverage düşüşünü CI yakalar.

## Sürekli Entegrasyon

`.github/workflows/ci.yml` her push'ta:

```yaml
- name: Test
  run: |
    uv sync
    uv run pytest --cov=konsilisyum --cov-fail-under=70
```

Detaylar: [CI Konfigürasyonu](contributing.md#ci-cd).

## Lint ve Format

```bash
# Ruff (lint + format)
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy konsilisyum/
```

CI bunları da çalıştırır.

## Test İpuçları

!!! tip "async test"
    `pytest-asyncio` otomatik modda. `@pytest.mark.asyncio` ile işaretle.

!!! tip "Hızlı test"
    Network çağrısı yapma. Her şeyi mock'la.

!!! tip "İzolasyon"
    Her test bağımsız olmalı. Global state'den kaçın.

!!! tip "Anlamlı isim"
    `test_api_returns_error_on_401` > `test_api_error`.
