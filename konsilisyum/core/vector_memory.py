"""Vector memory for cross-session semantic search.

Lightweight implementation using sqlite3 + numpy.
Embeddings are generated via LLM provider API.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class VectorSearchResult:
    message_id: str
    content: str
    speaker: str
    session_id: str
    similarity: float


class VectorMemory:
    """Stores message embeddings and provides semantic search."""

    def __init__(self, db_path: str = "data/vector_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session ON embeddings(session_id)
        """)
        self._conn.commit()

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    async def add_message(
        self,
        message_id: str,
        session_id: str,
        speaker: str,
        content: str,
        embed_fn,
    ):
        """Add a message with its embedding.

        Args:
            message_id: Unique message identifier
            session_id: Session identifier
            speaker: Speaker name
            content: Message content
            embed_fn: Async function that takes text and returns embedding vector
        """
        embedding = await embed_fn(content)
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

        self._conn.execute(
            "INSERT OR REPLACE INTO embeddings (id, session_id, speaker, content, embedding) VALUES (?, ?, ?, ?, ?)",
            (message_id, session_id, speaker, content, embedding_bytes),
        )
        self._conn.commit()

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        session_id: str | None = None,
        min_similarity: float = 0.7,
    ) -> list[VectorSearchResult]:
        """Search for semantically similar messages.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            session_id: Filter by session (None = all sessions)
            min_similarity: Minimum similarity threshold
        """
        query_vec = np.array(query_embedding, dtype=np.float32)

        if session_id:
            rows = self._conn.execute(
                "SELECT id, session_id, speaker, content, embedding FROM embeddings WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, session_id, speaker, content, embedding FROM embeddings"
            ).fetchall()

        results: list[tuple[float, VectorSearchResult]] = []
        for row in rows:
            msg_id, sid, speaker, content, emb_bytes = row
            emb_vec = np.frombuffer(emb_bytes, dtype=np.float32)
            sim = self._cosine_similarity(query_vec, emb_vec)
            if sim >= min_similarity:
                results.append((sim, VectorSearchResult(
                    message_id=msg_id,
                    content=content,
                    speaker=speaker,
                    session_id=sid,
                    similarity=sim,
                )))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]

    def delete_session(self, session_id: str):
        """Remove all embeddings for a session."""
        self._conn.execute(
            "DELETE FROM embeddings WHERE session_id = ?",
            (session_id,),
        )
        self._conn.commit()

    def get_stats(self) -> dict:
        """Return database statistics."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM embeddings"
        ).fetchone()[0]
        sessions = self._conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM embeddings"
        ).fetchone()[0]
        return {"total_messages": total, "total_sessions": sessions}

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
