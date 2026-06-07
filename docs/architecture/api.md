# API Katmanı

Konsilisyum hangi LLM sağlayıcısını kullandığını bilmez. Sadece `BaseLLMClient` arayüzünü bilir. Bu sayede yeni sağlayıcı eklemek trivial'dir.

## Arayüz

```python
class LLMClient(Protocol):
    @property
    def model(self) -> str: ...
    @property
    def provider(self) -> str: ...

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
    ) -> CompletionResult: ...

    async def complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        get_key: Callable[[], str],
        max_retries: int = 3,
    ) -> CompletionResult: ...
```

## Somut Sağlayıcılar

```
BaseLLMClient
  ├── MistralClient       (https://api.mistral.ai/v1)
  ├── OpenAIClient        (https://api.openai.com/v1)
  ├── AnthropicClient     (https://api.anthropic.com/v1)
  └── OllamaClient        (http://localhost:11434)
```

### MistralClient

```python
class MistralClient(BaseLLMClient):
    BASE_URL = "https://api.mistral.ai/v1"

    async def complete(self, system_prompt, user_prompt, api_key):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
        # ... hata yönetimi ...
        return CompletionResult(...)
```

### OpenAIClient

OpenAI uyumlu API'ler (Together, Groq, OpenRouter) için aynı şablon kullanılır; sadece `BASE_URL` değişir.

```python
class OpenAIClient(BaseLLMClient):
    BASE_URL = "https://api.openai.com/v1"
    # OpenAI-uyumlu API'ler için subclass yapılabilir
```

### AnthropicClient

Anthropik'in API şeması biraz farklı:

```python
class AnthropicClient(BaseLLMClient):
    BASE_URL = "https://api.anthropic.com/v1"

    async def complete(self, system_prompt, user_prompt, api_key):
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "system": system_prompt,  # system ayrı alan
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.max_tokens,
        }
```

### OllamaClient

Yerel çalışan Ollama için API yine OpenAI-uyumlu:

```python
class OllamaClient(BaseLLMClient):
    BASE_URL = "http://localhost:11434/api"

    async def complete(self, system_prompt, user_prompt, api_key):
        # api_key genelde boş string
        payload = {
            "model": self.model,
            "messages": [...],
            "stream": False,
        }
```

## Hata Yönetimi

Üç özel hata sınıfı:

```python
class RateLimitError(Exception):
    def __init__(self, message: str, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(message)

class AuthError(Exception):
    """401 — geçersiz API anahtarı"""

class ServerError(Exception):
    """5xx — sağlayıcı hatası"""
```

Durum kodlarına göre:

| Kod | Eylem                                |
|-----|---------------------------------------|
| 200 | `CompletionResult` döndür             |
| 401 | `AuthError` raise                     |
| 429 | `RateLimitError(retry_after=...)`     |
| 5xx | `ServerError` raise                   |
| diğer | `ServerError` raise                  |

## Retry Mekanizması

`BaseLLMClient.complete_with_retry()` üst seviye retry mantığı sağlar:

```python
async def complete_with_retry(self, system_prompt, user_prompt, get_key, max_retries=3):
    last_error = None
    for attempt in range(max_retries):
        api_key = get_key()
        try:
            return await self.complete(system_prompt, user_prompt, api_key)
        except RateLimitError as e:
            last_error = e
            wait = e.retry_after or (2 ** attempt)
            await asyncio.sleep(wait)
        except AuthError as e:
            last_error = e
            continue  # sıradaki anahtar
        except (ServerError, TimeoutError) as e:
            last_error = e
            await asyncio.sleep(2 ** attempt)
    raise last_error or ServerError("Bilinmeyen hata")
```

Strateji:

- **Rate limit** → sağlayıcının `retry-after` başlığına uy, yoksa üstel bekle
- **Auth error** → aynı anahtarı bir daha deneme, sıradakine geç
- **Server error** → üstel geri çekilme (1s, 2s, 4s)
- **3 deneme sonrası** → istisna fırlat, orkestratör oturumu duraklatır

## KeyPool

Birden fazla API anahtarını yönetir. Her ajan için ya atanmış bir anahtar ya da havuz:

```python
class KeyPool:
    def __init__(self, keys: list[APIKey]):
        self.keys: dict[str, APIKey] = {k.id: k for k in keys}

    def get_key(self, agent: Agent | None = None) -> APIKey:
        # Ajanın atanmış anahtarı varsa onu kullan
        if agent and agent.api_key_id:
            key = self.keys.get(agent.api_key_id)
            if key and self._is_available(key):
                return key
        # Yoksa havuzdan sıradaki boşta
        pool_keys = [k for k in self.keys.values() if k.is_pool and self._is_available(k)]
        if not pool_keys:
            raise NoAvailableKeyError("Tüm anahtarlar tükenmiş")
        return pool_keys[0]

    def _is_available(self, key: APIKey) -> bool:
        return key.status == KeyStatus.ACTIVE
```

Rate limit'e düşen anahtar 60 saniye `COOLING` durumuna geçer:

```python
def mark_rate_limited(self, key_id: str, duration: int = 60):
    self.keys[key_id].status = KeyStatus.COOLING
    self.keys[key_id].cooldown_until = datetime.now() + timedelta(seconds=duration)
```

## Yeni Sağlayıcı Eklemek

1. `konsilisyum/api/providers.py` içinde yeni sınıf:

```python
class CohereClient(BaseLLMClient):
    BASE_URL = "https://api.cohere.ai/v1"

    def __init__(self, model: str = "command-r-plus", **kwargs):
        super().__init__(model, **kwargs)

    async def complete(self, system_prompt, user_prompt, api_key):
        # Cohere API'sine özel implementasyon
        ...
```

2. `konsilisyum/config/providers.py` kayıt:

```python
PROVIDERS = {
    "mistral": MistralClient,
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "ollama": OllamaClient,
    "cohere": CohereClient,  # yeni
}
```

3. Yapılandırmaya ekle:

```yaml
provider: cohere
model: command-r-plus
api_key_env: COHERE_API_KEY
```

Başka hiçbir dosyada değişiklik gerekmez.

## Test

`respx` ile mock'lanan HTTP katmanı:

```python
@respx.mock
async def test_mistral_completion():
    respx.post(MISTRAL_URL).mock(
        return_value=httpx.Response(200, json=mock_mistral_response())
    )
    client = MistralClient()
    result = await client.complete("sys", "user", "key")
    assert result.content == "..."
```

Detaylar: [API Referansı: Sağlayıcılar](../api/providers.md), [Test](../development/testing.md).
