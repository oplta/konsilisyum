# LLM Sağlayıcıları

Konsilisyum dört LLM sağlayıcısını destekler. Tümü aynı `BaseLLMClient` arayüzünü uygular.

## Desteklenen Sağlayıcılar

| Sağlayıcı      | Sınıf              | BASE_URL                          |
|----------------|---------------------|-----------------------------------|
| Mistral AI     | `MistralClient`     | `https://api.mistral.ai/v1`        |
| OpenAI         | `OpenAIClient`      | `https://api.openai.com/v1`        |
| Anthropic      | `AnthropicClient`   | `https://api.anthropic.com/v1`     |
| Ollama (yerel) | `OllamaClient`      | `http://localhost:11434/api`       |

## Ortak Yapılandırma

Tüm sağlayıcılar `BaseLLMClient`'dan miras alır:

```python
class BaseLLMClient(LLMClient):
    def __init__(
        self,
        model: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ): ...
```

### Parametreler

| Parametre     | Varsayılan | Açıklama                          |
|---------------|------------|-----------------------------------|
| `model`       | (gerekli)  | Sağlayıcıya özel model adı       |
| `max_tokens`  | 300        | Tamamlama için maksimum token     |
| `temperature` | 0.7        | Yaratıcılık (0.0–1.0)            |
| `timeout`     | 30.0       | HTTP timeout (saniye)             |

## Mistral AI

**Sınıf:** `konsilisyum.api.mistral.MistralClient`

### Modeller

| Model                    | Bağlam  | Fiyat (giriş/çıkış $/1M) |
|--------------------------|---------|--------------------------|
| `mistral-small-latest`   | 32K     | 0.2 / 0.6                |
| `mistral-medium-latest`  | 32K     | 2.7 / 8.1                |
| `mistral-large-latest`   | 128K    | 2.0 / 6.0                |
| `open-mistral-7b`        | 32K     | 0.25 / 0.25              |
| `open-mixtral-8x7b`      | 32K     | 0.7 / 0.7                |

### Kullanım

```python
from konsilisyum.api.mistral import MistralClient

client = MistralClient(
    model="mistral-small-latest",
    max_tokens=300,
    temperature=0.7,
)

result = await client.complete(
    system_prompt="Sen Atlas'sın, stratejistsin.",
    user_prompt="Yeni ürün lansmanı için fikir ver.",
    api_key=os.environ["MISTRAL_API_KEY"],
)

print(result.content)
print(f"Tokens: {result.tokens_in} in, {result.tokens_out} out")
```

## OpenAI

**Sınıf:** `konsilisyum.api.providers.OpenAIClient`

### Modeller

| Model              | Bağlam  | Fiyat (giriş/çıkış $/1M) |
|--------------------|---------|--------------------------|
| `gpt-4o-mini`      | 128K    | 0.15 / 0.6               |
| `gpt-4o`           | 128K    | 5.0 / 15.0               |
| `gpt-4-turbo`      | 128K    | 10.0 / 30.0              |
| `gpt-3.5-turbo`    | 16K     | 0.5 / 1.5                |

### Kullanım

```python
from konsilisyum.api.providers import OpenAIClient

client = OpenAIClient(model="gpt-4o-mini")
result = await client.complete(system, user, api_key)
```

### OpenAI-Uyumlu API'ler

OpenAI uyumlu API veren servisler (Together, Groq, OpenRouter) için subclass:

```python
class TogetherClient(OpenAIClient):
    BASE_URL = "https://api.together.xyz/v1"

client = TogetherClient(model="meta-llama/Llama-3-70b-chat-hf")
result = await client.complete(system, user, api_key)
```

## Anthropic

**Sınıf:** `konsilisyum.api.providers.AnthropicClient`

### Modeller

| Model                  | Bağlam  | Fiyat (giriş/çıkış $/1M) |
|------------------------|---------|--------------------------|
| `claude-3-haiku-...`   | 200K    | 0.25 / 1.25              |
| `claude-3-sonnet-...`  | 200K    | 3.0 / 15.0               |
| `claude-3-opus-...`    | 200K    | 15.0 / 75.0              |
| `claude-3-5-sonnet-...`| 200K    | 3.0 / 15.0               |

### Kullanım

```python
from konsilisyum.api.providers import AnthropicClient

client = AnthropicClient(model="claude-3-haiku-20240307")
result = await client.complete(system, user, api_key)
```

### Farklar

- System prompt ayrı alan (`payload["system"]`)
- Mesajlar `messages` içinde sadece user/assistant
- `x-api-key` başlığı, `Authorization` değil
- `anthropic-version` başlığı zorunlu

## Ollama (Yerel)

**Sınıf:** `konsilisyum.api.providers.OllamaClient`

### Modeller

Yerel olarak indirdiğiniz her model:

```bash
ollama pull llama3.1
ollama pull mistral
ollama pull codellama
```

### Kullanım

```python
from konsilisyum.api.providers import OllamaClient

client = OllamaClient(model="llama3.1")
# api_key genelde boş string; yerel çalışır
result = await client.complete(system, user, "")
```

### Avantajlar

- Veri dışarı çıkmaz
- Maliyet sıfır
- Offline çalışır

### Dezavantajlar

- GPU gerekir (veya yavaş CPU)
- Küçük modeller ajan kişiliğini korumakta zorlanabilir

## CompletionResult

Tüm sağlayıcılar aynı sonuç tipini döndürür:

```python
@dataclass
class CompletionResult:
    content: str           # asıl yanıt metni
    tokens_in: int         # giriş token sayısı
    tokens_out: int        # çıkış token sayısı
    model: str             # kullanılan model
    metadata: dict = {}    # sağlayıcıya özel ek veri
```

## Hata Tipleri

```python
from konsilisyum.api.llm import (
    AuthError,        # 401
    RateLimitError,   # 429
    ServerError,      # 5xx
    TimeoutError,     # ağ zaman aşımı
)

# RateLimitError özel olarak:
except RateLimitError as e:
    print(f"Bekleniyor: {e.retry_after}s")
```

## Yapılandırma

### Ortam Değişkenleri

```bash
export MISTRAL_API_KEY="sk-xxx"
export OPENAI_API_KEY="sk-xxx"
export ANTHROPIC_API_KEY="sk-ant-xxx"
```

### `~/.konsilisyum/config.yaml`

```yaml
provider: mistral
model: mistral-small-latest
max_tokens: 300
temperature: 0.7
timeout: 30

api_keys:
  - env: MISTRAL_API_KEY
    is_pool: true
  - env: MISTRAL_API_KEY_2
    is_pool: true
```

Detaylar: [Yapılandırma](config.md).
