"""
Production RAG — Hybrid Search & Reranking (PRD Section 50).

All methods are FREE:
    - BM25: scikit-learn TfidfVectorizer (no paid APIs)
    - Dense: numpy cosine similarity (no paid embedding APIs)
    - RRF: pure Python implementation
    - Hybrid: combines BM25 + Dense via RRF

In production:
    - BM25 uses OpenSearch or Elasticsearch (free, self-hosted)
    - Dense uses Qdrant or pgvectorscale (free, open source)
    - Embeddings from BGE-large (free, open source model)
    - Reranking from BGE-reranker (free, open source model)

References:
    - PRD Section 50 (Production RAG — Hybrid Search & Reranking)
    - PRD Section 84.2 (Cosine Similarity formula)
    - PRD Section 84.4 (BM25 formula)
    - PRD Section 84.6 (RRF formula)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine


class BM25Search:
    """BM25 sparse retrieval using scikit-learn TF-IDF (FREE).

    Uses TF-IDF with cosine similarity as a BM25 approximation.
    In production, this uses OpenSearch's BM25 algorithm (free, self-hosted).

    Usage:
        bm25 = BM25Search()
        bm25.add_documents(["doc1 text", "doc2 text"])
        results = bm25.search("query text", top_k=5)
    """

    def __init__(self) -> None:
        self._documents: list[str] = []
        self._source_urls: list[str] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def add_documents(
        self,
        documents: list[str],
        source_urls: list[str] | None = None,
    ) -> None:
        """Add documents to the BM25 index.

        Args:
            documents: List of document texts.
            source_urls: Optional list of source URLs (same length).
        """
        self._documents.extend(documents)
        if source_urls:
            self._source_urls.extend(source_urls)
        else:
            self._source_urls.extend([""] * len(documents))
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the TF-IDF index."""
        if not self._documents:
            return
        self._vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        self._matrix = self._vectorizer.fit_transform(self._documents)

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Search for documents matching the query.

        Args:
            query: Search query.
            top_k: Maximum results.

        Returns:
            List of result dicts with: id, content, score, source_url.
        """
        if not self._documents or self._vectorizer is None or self._matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = sklearn_cosine(query_vec, self._matrix).flatten()

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[dict[str, Any]] = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "id": f"doc_{idx}",
                    "content": self._documents[idx],
                    "score": float(scores[idx]),
                    "source_url": self._source_urls[idx] if idx < len(self._source_urls) else "",
                    "rank": len(results) + 1,
                })
        return results


class DenseSearch:
    """Dense vector retrieval using numpy cosine similarity (FREE).

    Uses numpy for vector operations — no GPU required, no paid APIs.
    In production, this uses Qdrant or pgvectorscale with HNSW index.

    Usage:
        dense = DenseSearch(dim=768)
        dense.add_documents(["doc1", "doc2"], [emb1, emb2])
        results = dense.search(query_embedding, top_k=5)
    """

    def __init__(self, dim: int = 768) -> None:
        self._dim = dim
        self._documents: list[str] = []
        self._embeddings: np.ndarray | None = None
        self._source_urls: list[str] = []

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        source_urls: list[str] | None = None,
    ) -> None:
        """Add documents with their embeddings.

        Args:
            documents: List of document texts.
            embeddings: List of embedding vectors (same length).
            source_urls: Optional source URLs.
        """
        self._documents.extend(documents)
        new_embs = np.array(embeddings, dtype=np.float32)
        if self._embeddings is None:
            self._embeddings = new_embs
        else:
            self._embeddings = np.vstack([self._embeddings, new_embs])
        if source_urls:
            self._source_urls.extend(source_urls)
        else:
            self._source_urls.extend([""] * len(documents))

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search by vector similarity.

        Args:
            query_embedding: Query embedding vector.
            top_k: Maximum results.

        Returns:
            List of result dicts with: id, content, score, source_url.
        """
        if self._embeddings is None or not self._documents:
            return []

        query_vec = np.array(query_embedding, dtype=np.float32)
        # Normalize for cosine similarity
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        doc_norms = self._embeddings / (
            np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-10
        )
        scores = doc_norms @ query_norm

        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[dict[str, Any]] = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "id": f"vec_{idx}",
                    "content": self._documents[idx],
                    "score": float(scores[idx]),
                    "source_url": self._source_urls[idx] if idx < len(self._source_urls) else "",
                    "rank": len(results) + 1,
                })
        return results


class RRFFusion:
    """Reciprocal Rank Fusion (PRD Section 50.2, 84.6).

    Combines multiple ranked lists into a single fused ranking.
    Formula: RRF(d) = sum 1/(k + rank(d)), k=60.

    FREE — pure Python implementation, no external dependencies.

    Usage:
        rrf = RRFFusion(k=60)
        fused = rrf.fuse([bm25_results, dense_results], top_k=10)
    """

    def __init__(self, k: int = 60) -> None:
        self._k = k

    def fuse(
        self,
        ranked_lists: list[list[dict[str, Any]]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Fuse multiple ranked lists using RRF.

        Args:
            ranked_lists: List of ranked result lists.
            top_k: Maximum results to return.

        Returns:
            Fused and re-ranked list of results.
        """
        if not ranked_lists:
            return []

        scores: dict[str, float] = {}
        docs: dict[str, dict[str, Any]] = {}

        for ranked_list in ranked_lists:
            for rank, result in enumerate(ranked_list):
                doc_id = result.get("id", str(rank))
                rrf_score = 1.0 / (self._k + rank + 1)
                scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
                if doc_id not in docs:
                    docs[doc_id] = result.copy()

        # Sort by fused score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results: list[dict[str, Any]] = []
        for doc_id in sorted_ids[:top_k]:
            result = docs[doc_id].copy()
            result["fused_score"] = scores[doc_id]
            result["rank"] = len(results) + 1
            results.append(result)

        return results


class HybridSearch:
    """Hybrid search combining BM25 + Dense + RRF (PRD Section 50.2).

    Combines sparse (BM25) and dense (vector) retrieval via Reciprocal
    Rank Fusion. This is the production RAG pattern validated in PRD
    Section 50 with 15-30% nDCG improvement over dense-only.

    All components are FREE:
        - BM25: scikit-learn TF-IDF
        - Dense: numpy cosine similarity
        - RRF: pure Python

    Usage:
        hs = HybridSearch(dim=768)
        hs.add_documents(docs, embeddings)
        results = hs.search("query", query_embedding=emb, top_k=10)
    """

    def __init__(self, dim: int = 768, rrf_k: int = 60) -> None:
        self._bm25 = BM25Search()
        self._dense = DenseSearch(dim=dim)
        self._rrf = RRFFusion(k=rrf_k)
        self._dim = dim

    @property
    def document_count(self) -> int:
        return self._bm25.document_count

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        source_urls: list[str] | None = None,
    ) -> None:
        """Add documents to both BM25 and Dense indices.

        Args:
            documents: List of document texts.
            embeddings: List of embedding vectors.
            source_urls: Optional source URLs.
        """
        self._bm25.add_documents(documents, source_urls)
        self._dense.add_documents(documents, embeddings, source_urls)

    def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        top_k: int = 10,
        bm25_weight: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Hybrid search combining BM25 and Dense via RRF.

        Args:
            query: Text query for BM25.
            query_embedding: Embedding for dense search (None = BM25 only).
            top_k: Maximum results.
            bm25_weight: Weight for BM25 results (0-1).

        Returns:
            Fused and re-ranked list of results.
        """
        ranked_lists: list[list[dict[str, Any]]] = []

        # BM25 search
        bm25_results = self._bm25.search(query, top_k=top_k * 2)
        if bm25_results:
            ranked_lists.append(bm25_results)

        # Dense search (if embedding provided)
        if query_embedding is not None:
            dense_results = self._dense.search(query_embedding, top_k=top_k * 2)
            if dense_results:
                ranked_lists.append(dense_results)

        # Fuse via RRF
        return self._rrf.fuse(ranked_lists, top_k=top_k)

    def __repr__(self) -> str:
        return f"<HybridSearch(docs={self.document_count}, dim={self._dim})>"
