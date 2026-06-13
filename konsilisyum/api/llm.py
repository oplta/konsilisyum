from __future__ import annotations

import abc
from dataclasses import dataclass

import httpx

from konsilisyum.core.errors import KonsilisyumError


@dataclass
class CompletionResult:
    content: str
    tokens_in: int
    tokens_out: int
    model: str


class LLMError(KonsilisyumError):
    pass


class RateLimitError(LLMError):
    def __init__(self, message: str = "Rate limit", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthError(LLMError):
    pass


class ServerError(LLMError):
    pass


class LLMClient(abc.ABC):
    @abc.abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
    ) -> CompletionResult:
        pass

    @abc.abstractmethod
    async def complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        get_key,
        max_retries: int = 3,
    ) -> CompletionResult:
        pass

    @property
    @abc.abstractmethod
    def model(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def provider(self) -> str:
        pass


class BaseLLMClient(LLMClient):
    def __init__(
        self,
        model: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ):
        self._model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider(self) -> str:
        return self.__class__.__name__.replace("Client", "").lower()

    async def complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        get_key,
        max_retries: int = 3,
    ) -> CompletionResult:
        import asyncio

        last_error: Exception | None = None
        for attempt in range(max_retries):
            api_key = get_key()
            try:
                return await self.complete(system_prompt, user_prompt, api_key)
            except RateLimitError as e:
                last_error = e
                wait = e.retry_after or (2**attempt)
                await asyncio.sleep(wait)
            except AuthError as e:
                last_error = e
                continue
            except (ServerError, TimeoutError) as e:
                last_error = e
                await asyncio.sleep(2**attempt)

        raise last_error or ServerError("Bilinmeyen hata")
