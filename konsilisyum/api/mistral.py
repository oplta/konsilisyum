from __future__ import annotations

import httpx

from konsilisyum.api.llm import (
    AuthError,
    BaseLLMClient,
    CompletionResult,
    RateLimitError,
    ServerError,
)


class MistralClient(BaseLLMClient):
    BASE_URL = "https://api.mistral.ai/v1"

    def __init__(
        self,
        model: str = "mistral-small-latest",
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
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
