from __future__ import annotations

from konsilisyum.api.llm import (
    AuthError,
    BaseLLMClient,
    CompletionResult,
    RateLimitError,
    ServerError,
)
from konsilisyum.core.logging import get_logger

logger = get_logger(__name__)


class MistralClient(BaseLLMClient):
    BASE_URL = "https://api.mistral.ai/v1"

    def __init__(
        self,
        model: str = "mistral-small-latest",
        max_tokens: int = 4096,
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
        choice = data["choices"][0]
        content = choice["message"]["content"]
        finish_reason = choice.get("finish_reason", "stop")
        usage = data.get("usage", {})

        if finish_reason == "length":
            logger.warning(
                "yanit_kesildi",
                model=self.model,
                tokens_out=usage.get("completion_tokens", 0),
                max_tokens=self.max_tokens,
            )

        return CompletionResult(
            content=content.strip(),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            model=data.get("model", self.model),
            finish_reason=finish_reason,
        )
