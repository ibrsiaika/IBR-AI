"""Tests for Section 84-85 — CS Formulas module."""
from __future__ import annotations
import math
import pytest
import numpy as np


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        from ibr_platform.utils.formulas import cosine_similarity
        v = [1.0, 0.0, 0.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        from ibr_platform.utils.formulas import cosine_similarity
        assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-6

    def test_opposite_vectors(self) -> None:
        from ibr_platform.utils.formulas import cosine_similarity
        assert abs(cosine_similarity([1, 0], [-1, 0]) - (-1.0)) < 1e-6


class TestBM25:
    def test_bm25_importable(self) -> None:
        from ibr_platform.utils.formulas import bm25_score
        assert callable(bm25_score)

    def test_bm25_returns_float(self) -> None:
        from ibr_platform.utils.formulas import bm25_score
        score = bm25_score(tf=2, df=10, N=1000, doc_len=100, avgdl=200)
        assert isinstance(score, float)

    def test_bm25_rare_term_higher_score(self) -> None:
        from ibr_platform.utils.formulas import bm25_score
        common = bm25_score(tf=2, df=900, N=1000, doc_len=100, avgdl=200)
        rare = bm25_score(tf=2, df=10, N=1000, doc_len=100, avgdl=200)
        assert rare > common


class TestRRF:
    def test_rrf_importable(self) -> None:
        from ibr_platform.utils.formulas import rrf_score
        assert callable(rrf_score)

    def test_rrf_rank_1_higher_than_rank_10(self) -> None:
        from ibr_platform.utils.formulas import rrf_score
        s1 = rrf_score(rank=1, k=60)
        s10 = rrf_score(rank=10, k=60)
        assert s1 > s10

    def test_rrf_formula(self) -> None:
        from ibr_platform.utils.formulas import rrf_score
        # RRF = 1/(k + rank), k=60, rank=1 → 1/61
        assert abs(rrf_score(rank=1, k=60) - 1.0/61.0) < 1e-6


class TestBayesianUpdate:
    def test_importable(self) -> None:
        from ibr_platform.utils.formulas import bayesian_update
        assert callable(bayesian_update)

    def test_prior_05_with_reliable_source(self) -> None:
        from ibr_platform.utils.formulas import bayesian_update
        posterior = bayesian_update(prior=0.5, reliability=0.9)
        assert posterior > 0.9  # Strong evidence → high posterior

    def test_prior_05_with_unreliable_source(self) -> None:
        from ibr_platform.utils.formulas import bayesian_update
        posterior = bayesian_update(prior=0.5, reliability=0.6)
        assert 0.5 < posterior < 0.9  # Weak evidence → moderate posterior

    def test_multiple_sources(self) -> None:
        from ibr_platform.utils.formulas import bayesian_update
        posterior = 0.5
        for _ in range(3):
            posterior = bayesian_update(posterior, 0.9)
        assert posterior > 0.99  # 3 reliable sources → very high


class TestBrierScore:
    def test_perfect_prediction(self) -> None:
        from ibr_platform.utils.formulas import brier_score
        forecasts = [1.0, 0.0, 1.0]
        outcomes = [1, 0, 1]
        assert abs(brier_score(forecasts, outcomes) - 0.0) < 1e-6

    def test_random_prediction(self) -> None:
        from ibr_platform.utils.formulas import brier_score
        forecasts = [0.5, 0.5]
        outcomes = [1, 0]
        assert abs(brier_score(forecasts, outcomes) - 0.25) < 1e-6


class TestSoftmax:
    def test_importable(self) -> None:
        from ibr_platform.utils.formulas import softmax
        assert callable(softmax)

    def test_sums_to_one(self) -> None:
        from ibr_platform.utils.formulas import softmax
        result = softmax([1.0, 2.0, 3.0])
        assert abs(sum(result) - 1.0) < 1e-6

    def test_all_positive(self) -> None:
        from ibr_platform.utils.formulas import softmax
        result = softmax([1.0, 2.0, 3.0])
        assert all(r > 0 for r in result)


class TestPageRank:
    def test_importable(self) -> None:
        from ibr_platform.utils.formulas import pagerank
        assert callable(pagerank)

    def test_simple_graph(self) -> None:
        from ibr_platform.utils.formulas import pagerank
        # A → B → C → A (cycle)
        adjacency = {"A": ["B"], "B": ["C"], "C": ["A"]}
        pr = pagerank(adjacency, iterations=100)
        assert len(pr) == 3
        # All should have equal PageRank in a cycle
        assert abs(pr["A"] - pr["B"]) < 0.01

    def test_hub_node_higher_rank(self) -> None:
        from ibr_platform.utils.formulas import pagerank
        # A is pointed to by B and C
        adjacency = {"A": [], "B": ["A"], "C": ["A"]}
        pr = pagerank(adjacency, iterations=100)
        assert pr["A"] > pr["B"]
        assert pr["A"] > pr["C"]


class TestCrossEntropy:
    def test_perfect_prediction(self) -> None:
        from ibr_platform.utils.formulas import cross_entropy
        # Perfect: predicted 1.0 for true class
        loss = cross_entropy(predicted=[0.0, 1.0, 0.0], actual=[0, 1, 0])
        assert loss < 0.01

    def test_worst_prediction(self) -> None:
        from ibr_platform.utils.formulas import cross_entropy
        # Worst: predicted 0.0 for true class
        loss = cross_entropy(predicted=[1.0, 0.0, 0.0], actual=[0, 1, 0])
        assert loss > 10  # Very high loss


class TestNDCG:
    def test_importable(self) -> None:
        from ibr_platform.utils.formulas import ndcg
        assert callable(ndcg)

    def test_perfect_ranking(self) -> None:
        from ibr_platform.utils.formulas import ndcg
        # Perfect: most relevant first
        relevances = [3, 2, 1, 0]
        score = ndcg(relevances)
        assert abs(score - 1.0) < 1e-6

    def test_worst_ranking(self) -> None:
        from ibr_platform.utils.formulas import ndcg
        # Worst: least relevant first
        relevances = [0, 1, 2, 3]
        score = ndcg(relevances)
        assert score < 1.0
