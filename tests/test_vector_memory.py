"""Tests for core/vector_memory.py."""

import numpy as np
import pytest

from konsilisyum.core.vector_memory import VectorMemory, VectorSearchResult


class TestVectorMemory:
    @pytest.fixture
    def vm(self, tmp_path):
        db = tmp_path / "test_vec.db"
        v = VectorMemory(str(db))
        yield v
        v.close()

    @pytest.fixture
    def mock_embed_fn(self):
        async def _embed(text):
            # Deterministic fake embedding based on text length
            vec = np.zeros(10, dtype=np.float32)
            vec[len(text) % 10] = 1.0
            return vec.tolist()
        return _embed

    @pytest.mark.asyncio
    async def test_add_and_search(self, vm, mock_embed_fn):
        await vm.add_message("m1", "s1", "Atlas", "Strategy is key", mock_embed_fn)
        await vm.add_message("m2", "s1", "Mira", "Ethics matter", mock_embed_fn)

        # Search with query matching first message length
        query = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]  # len("Strategy is key") = 15, 15 % 10 = 5
        results = vm.search(query, top_k=2, min_similarity=0.5)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_by_session(self, vm, mock_embed_fn):
        await vm.add_message("m1", "session-a", "Atlas", "Content A", mock_embed_fn)
        await vm.add_message("m2", "session-b", "Mira", "Content B", mock_embed_fn)

        query = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # len("Content A") = 9, 9 % 10 = 9 -> wait, len("Content A")=9
        # Let's use a more reliable approach
        query = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # index 0
        results = vm.search(query, session_id="session-a", min_similarity=0.0)
        assert all(r.session_id == "session-a" for r in results)

    @pytest.mark.asyncio
    async def test_delete_session(self, vm, mock_embed_fn):
        await vm.add_message("m1", "del-session", "Atlas", "X", mock_embed_fn)
        vm.delete_session("del-session")

        query = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        results = vm.search(query, min_similarity=0.0)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_stats(self, vm, mock_embed_fn):
        await vm.add_message("m1", "s1", "A", "X", mock_embed_fn)
        await vm.add_message("m2", "s2", "B", "Y", mock_embed_fn)

        stats = vm.get_stats()
        assert stats["total_messages"] == 2
        assert stats["total_sessions"] == 2

    def test_cosine_similarity_identical(self, vm):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0, 3.0])
        assert vm._cosine_similarity(a, b) == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self, vm):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert vm._cosine_similarity(a, b) == pytest.approx(0.0)

    def test_cosine_similarity_zero(self, vm):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 2.0])
        assert vm._cosine_similarity(a, b) == 0.0

    def test_context_manager(self, tmp_path):
        db = tmp_path / "cm.db"
        with VectorMemory(str(db)) as vm:
            assert vm.get_stats()["total_messages"] == 0
