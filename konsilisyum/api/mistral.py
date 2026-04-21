from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


@dataclass
class CompletionResult:
    content: str
    tokens_in: int
    tokens_out: int
    model: str


class RateLimitError(Exception):
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthError(Exception):
    pass


class ServerError(Exception):
    pass


class MistralClient:
    BASE_URL = "https://api.mistral.ai/v1"
    TIMEOUT = 30.0

    def __init__(self, model: str = "mistral-small-latest",
                 max_tokens: int = 300, temperature: float = 0.7):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

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

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
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
            raise AuthError("Gecersiz API anahtari")
        if response.status_code >= 500:
            raise ServerError(f"Sunucu hatasi: {response.status_code}")
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

    async def complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        get_key,  # callable -> str
        max_retries: int = 3,
    ) -> CompletionResult:
        last_error: Exception | None = None
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
                continue
            except (ServerError, httpx.TimeoutException) as e:
                last_error = e
                await asyncio.sleep(2 ** attempt)

        raise last_error or ServerError("Bilinmeyen hata")
