"""
Tests for Section 50 — Production RAG (Hybrid Search & Reranking).

All methods are FREE — using scikit-learn for BM25/TF-IDF and numpy
for vector similarity. No paid APIs.

Run: pytest tests/unit/test_rag.py -v
"""
from __future__ import annotations


class TestBM25Search:
    """Test BM25 sparse retrieval (free, using scikit-learn TF-IDF)."""

    def test_bm25_importable(self) -> None:
        """BM25Search is importable."""
        from ibr_platform.platform.rag import BM25Search
        assert BM25Search is not None

    def test_bm25_add_documents(self) -> None:
        """BM25Search can add documents to the index."""
        from ibr_platform.platform.rag import BM25Search
        bm25 = BM25Search()
        bm25.add_documents([
            "machine learning basics",
            "database optimization techniques",
            "web security best practices",
        ])
        assert bm25.document_count == 3

    def test_bm25_search_returns_results(self) -> None:
        """BM25Search returns relevant results."""
        from ibr_platform.platform.rag import BM25Search
        bm25 = BM25Search()
        bm25.add_documents([
            "Python is a programming language",
            "Java is also a programming language",
            "The weather is nice today",
        ])
        results = bm25.search("programming language", top_k=2)
        assert len(results) == 2
        assert "programming" in results[0]["content"].lower()

    def test_bm25_search_empty_index(self) -> None:
        """BM25Search returns empty list for empty index."""
        from ibr_platform.platform.rag import BM25Search
        bm25 = BM25Search()
        results = bm25.search("test", top_k=5)
        assert len(results) == 0


class TestDenseSearch:
    """Test dense vector retrieval (free, using numpy cosine similarity)."""

    def test_dense_importable(self) -> None:
        """DenseSearch is importable."""
        from ibr_platform.platform.rag import DenseSearch
        assert DenseSearch is not None

    def test_dense_add_documents(self) -> None:
        """DenseSearch can add documents with embeddings."""
        import numpy as np

        from ibr_platform.platform.rag import DenseSearch
        dense = DenseSearch(dim=4)
        docs = ["doc1", "doc2", "doc3"]
        embeddings = np.random.randn(3, 4).tolist()
        dense.add_documents(docs, embeddings)
        assert dense.document_count == 3

    def test_dense_search_returns_results(self) -> None:
        """DenseSearch returns relevant results by similarity."""
        import numpy as np

        from ibr_platform.platform.rag import DenseSearch
        dense = DenseSearch(dim=4)
        docs = ["machine learning", "database design", "web scraping"]
        embeddings = np.array([
            [1, 0, 0, 0],  # ML
            [0, 1, 0, 0],  # DB
            [0, 0, 1, 0],  # Web
        ], dtype=np.float32)
        dense.add_documents(docs, embeddings.tolist())
        # Query close to ML
        results = dense.search([1, 0.1, 0, 0], top_k=2)
        assert len(results) == 2
        assert "machine learning" in results[0]["content"]


class TestRRFFusion:
    """Test Reciprocal Rank Fusion (PRD Section 50.2)."""

    def test_rrf_importable(self) -> None:
        """RRFFusion is importable."""
        from ibr_platform.platform.rag import RRFFusion
        assert RRFFusion is not None

    def test_rrf_fuses_two_lists(self) -> None:
        """RRFFusion combines two ranked lists."""
        from ibr_platform.platform.rag import RRFFusion
        rrf = RRFFusion(k=60)
        bm25_results = [
            {"id": "doc1", "content": "A"},
            {"id": "doc2", "content": "B"},
            {"id": "doc3", "content": "C"},
        ]
        dense_results = [
            {"id": "doc2", "content": "B"},
            {"id": "doc1", "content": "A"},
            {"id": "doc4", "content": "D"},
        ]
        fused = rrf.fuse([bm25_results, dense_results], top_k=3)
        assert len(fused) == 3
        # doc1 and doc2 appear in both lists, should rank higher
        ids = [r["id"] for r in fused]
        assert "doc1" in ids
        assert "doc2" in ids

    def test_rrf_empty_lists(self) -> None:
        """RRFFusion handles empty lists."""
        from ibr_platform.platform.rag import RRFFusion
        rrf = RRFFusion()
        fused = rrf.fuse([], top_k=5)
        assert len(fused) == 0


class TestHybridSearch:
    """Test hybrid search combining BM25 + Dense + RRF (PRD Section 50.2)."""

    def test_hybrid_importable(self) -> None:
        """HybridSearch is importable."""
        from ibr_platform.platform.rag import HybridSearch
        assert HybridSearch is not None

    def test_hybrid_instantiable(self) -> None:
        """HybridSearch can be instantiated."""
        from ibr_platform.platform.rag import HybridSearch
        hs = HybridSearch()
        assert hs is not None

    def test_hybrid_add_documents(self) -> None:
        """HybridSearch can add documents."""
        import numpy as np

        from ibr_platform.platform.rag import HybridSearch
        hs = HybridSearch(dim=4)
        docs = ["machine learning", "database design"]
        embeddings = np.random.randn(2, 4).tolist()
        hs.add_documents(docs, embeddings)
        assert hs.document_count == 2

    def test_hybrid_search(self) -> None:
        """HybridSearch returns combined results."""
        import numpy as np

        from ibr_platform.platform.rag import HybridSearch
        hs = HybridSearch(dim=4)
        docs = [
            "Python machine learning tutorial",
            "Java database programming",
            "web scraping with Python",
        ]
        embeddings = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0.5, 0, 0.5, 0],
        ], dtype=np.float32)
        hs.add_documents(docs, embeddings.tolist())
        results = hs.search("Python", query_embedding=[1, 0.1, 0.3, 0], top_k=2)
        assert len(results) <= 2
        assert len(results) > 0


class TestSourceTracking:
    """Test source tracking for citations (PRD Section 50.4)."""

    def test_source_tracking_in_results(self) -> None:
        """Search results include source metadata."""
        from ibr_platform.platform.rag import BM25Search
        bm25 = BM25Search()
        bm25.add_documents(["test document"], source_urls=["https://example.com/doc1"])
        results = bm25.search("test", top_k=1)
        assert len(results) == 1
        assert "source_url" in results[0]
        assert results[0]["source_url"] == "https://example.com/doc1"
