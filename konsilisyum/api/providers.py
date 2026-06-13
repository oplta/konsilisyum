from __future__ import annotations

from konsilisyum.api.llm import (
    AuthError,
    BaseLLMClient,
    CompletionResult,
    RateLimitError,
    ServerError,
)


class OpenAIClient(BaseLLMClient):
    BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_tokens: int = 300,
        temperature: float = 0.7,
    ):
        super().__init__(model, max_tokens, temperature)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
    ) -> CompletionResult:
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

        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                "Rate limit",
                retry_after=int(retry_after) if retry_after else None,
            )
        if response.status_code == 401:
            raise AuthError("Geçersiz API anahtarı")
        if response.status_code >= 500:
            raise ServerError(f"Sunucu hatası: {response.status_code}")
        if response.status_code != 200:
            raise ServerError(f"Beklenmeyen hata: {response.status_code} - {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return CompletionResult(
            content=content.strip(),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            model=data.get("model", self.model),
        )


class AnthropicClient(BaseLLMClient):
    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 300,
        temperature: float = 0.7,
    ):
        super().__init__(model, max_tokens, temperature)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
    ) -> CompletionResult:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": self.API_VERSION,
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        response = await self.client.post(
            f"{self.BASE_URL}/messages",
            headers=headers,
            json=payload,
        )

        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                "Rate limit",
                retry_after=int(retry_after) if retry_after else None,
            )
        if response.status_code == 401:
            raise AuthError("Geçersiz API anahtarı")
        if response.status_code >= 500:
            raise ServerError(f"Sunucu hatası: {response.status_code}")
        if response.status_code != 200:
            raise ServerError(f"Beklenmeyen hata: {response.status_code} - {response.text}")

        data = response.json()
        content = data["content"][0]["text"]
        usage = data.get("usage", {})

        return CompletionResult(
            content=content.strip(),
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            model=data.get("model", self.model),
        )


class OllamaClient(BaseLLMClient):
    BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        model: str = "llama3.1",
        max_tokens: int = 300,
        temperature: float = 0.7,
        base_url: str = "http://localhost:11434",
    ):
        super().__init__(model, max_tokens, temperature)
        self.base_url = base_url

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,  # Ollama doesn't use API key
    ) -> CompletionResult:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
            "stream": False,
        }

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            headers=headers,
            json=payload,
        )

        if response.status_code >= 500:
            raise ServerError(f"Sunucu hatası: {response.status_code}")
        if response.status_code != 200:
            raise ServerError(f"Beklenmeyen hata: {response.status_code} - {response.text}")

        data = response.json()
        content = data["message"]["content"]
        usage = data.get("eval_count", 0), data.get("prompt_eval_count", 0)

        return CompletionResult(
            content=content.strip(),
            tokens_in=usage[1] if isinstance(usage, tuple) else 0,
            tokens_out=usage[0] if isinstance(usage, tuple) else 0,
            model=self.model,
        )
