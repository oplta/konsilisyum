"""Embedding generation using LLM provider APIs."""

from __future__ import annotations

import httpx

from konsilisyum.api.llm import BaseLLMClient


class EmbeddingClient:
    """Lightweight embedding client using provider APIs."""

    def __init__(self, api_key: str, provider: str = "mistral"):
        self.api_key = api_key
        self.provider = provider.lower()
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if self.provider == "mistral":
            return await self._embed_mistral(texts)
        elif self.provider == "openai":
            return await self._embed_openai(texts)
        else:
            raise ValueError(f"Provider '{self.provider}' does not support embeddings")

    async def _embed_mistral(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mistral-embed",
            "input": texts,
        }
        response = await self.client.post(
            "https://api.mistral.ai/v1/embeddings",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    async def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": texts,
        }
        response = await self.client.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
