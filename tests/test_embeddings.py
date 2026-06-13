"""Tests for the embedding client."""

import httpx
import pytest
import respx

from konsilisyum.api.embeddings import EmbeddingClient

MISTRAL_EMBED_URL = "https://api.mistral.ai/v1/embeddings"
OPENAI_EMBED_URL = "https://api.openai.com/v1/embeddings"


def mock_embedding_response(vector: list[float]) -> dict:
    return {
        "data": [{"embedding": vector, "index": 0, "object": "embedding"}],
        "model": "mistral-embed",
        "object": "list",
        "usage": {"prompt_tokens": 10, "total_tokens": 10},
    }


class TestEmbeddingClient:
    @pytest.mark.asyncio
    @respx.mock
    async def test_embed_mistral(self):
        vector = [0.1, 0.2, 0.3]
        respx.post(MISTRAL_EMBED_URL).mock(
            return_value=httpx.Response(200, json=mock_embedding_response(vector))
        )
        client = EmbeddingClient(api_key="test-key", provider="mistral")
        result = await client.embed(["hello world"])
        assert len(result) == 1
        assert result[0] == vector

    @pytest.mark.asyncio
    @respx.mock
    async def test_embed_openai(self):
        vector = [0.4, 0.5, 0.6]
        respx.post(OPENAI_EMBED_URL).mock(
            return_value=httpx.Response(200, json=mock_embedding_response(vector))
        )
        client = EmbeddingClient(api_key="test-key", provider="openai")
        result = await client.embed(["hello world"])
        assert len(result) == 1
        assert result[0] == vector

    @pytest.mark.asyncio
    async def test_embed_unsupported_provider(self):
        client = EmbeddingClient(api_key="test-key", provider="anthropic")
        with pytest.raises(ValueError, match="does not support embeddings"):
            await client.embed(["hello"])
