"""
RAG pipeline for AutoStream knowledge base.

Uses ChromaDB (in-memory) with sentence-transformers embeddings to retrieve
relevant product/policy context for user queries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Optional


class AutoStreamRAG:
    """Thin wrapper around ChromaDB for the AutoStream knowledge base."""

    _instance: Optional["AutoStreamRAG"] = None  # singleton

    def __init__(self, kb_path: Optional[Path] = None):
        import chromadb
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )
        from config import EMBEDDING_MODEL, KB_PATH

        self._kb_path = kb_path or KB_PATH

        self._ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        self._client = chromadb.Client()  # ephemeral / in-memory
        self._collection = self._client.get_or_create_collection(
            name="autostream_kb",
            embedding_function=self._ef,
        )
        self._load()

    # ── Singleton so we don't re-load on every Streamlit rerun ────────────────
    @classmethod
    def get(cls) -> "AutoStreamRAG":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Ingestion ─────────────────────────────────────────────────────────────
    def _load(self) -> None:
        if self._collection.count() > 0:
            return  # already loaded

        data = json.loads(self._kb_path.read_text(encoding="utf-8"))
        docs, metas, ids = [], [], []

        for item in data["documents"]:
            docs.append(item["content"])
            metas.append({"category": item["category"], "title": item["title"]})
            ids.append(item["id"])

        self._collection.add(documents=docs, metadatas=metas, ids=ids)

    # ── Retrieval ─────────────────────────────────────────────────────────────
    def retrieve(self, query: str, n: int = 3) -> List[Dict]:
        """Return top-n most relevant documents with metadata and distance."""
        n = min(n, self._collection.count())
        results = self._collection.query(query_texts=[query], n_results=n)

        retrieved = []
        for i, doc in enumerate(results["documents"][0]):
            retrieved.append(
                {
                    "content": doc,
                    "title": results["metadatas"][0][i]["title"],
                    "category": results["metadatas"][0][i]["category"],
                    "score": round(1 - results["distances"][0][i], 4),  # cosine sim
                }
            )
        return retrieved

    def get_context(self, query: str, n: int = 3) -> str:
        """Return a formatted context string ready for LLM injection."""
        docs = self.retrieve(query, n)
        if not docs:
            return "No relevant information found in the knowledge base."

        lines = []
        for doc in docs:
            lines.append(f"### {doc['title']} (relevance: {doc['score']:.2f})\n{doc['content']}")
        return "\n\n".join(lines)

    def get_all_docs(self) -> List[Dict]:
        """Return every document — useful for debug / UI display."""
        result = self._collection.get()
        return [
            {"id": result["ids"][i], "content": result["documents"][i], **result["metadatas"][i]}
            for i in range(len(result["ids"]))
        ]
