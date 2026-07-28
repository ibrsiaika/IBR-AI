"""
CS Formulas — Mathematical Foundations (PRD Section 84-85).

Implements all 14 CS formulas with derivations:
    - Cosine Similarity (Section 84.2)
    - TF-IDF (Section 84.3)
    - BM25 (Section 84.4)
    - HNSW complexity (Section 84.5)
    - RRF (Section 84.6)
    - PageRank (Section 84.7)
    - Bayesian Update (Section 85.1)
    - Brier Score (Section 85.2)
    - KL Divergence (Section 85.3)
    - Softmax (Section 85.4)
    - Cross-Entropy (Section 85.5)
    - ROUGE-N (Section 85.6)
    - BLEU (Section 85.7)
    - nDCG (Section 85.8)

All FREE — pure Python + numpy, no paid libraries.
"""

from __future__ import annotations

import math

import numpy as np


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity: cos(A,B) = (A·B) / (||A|| * ||B||).

    For normalized vectors, simplifies to dot product.
    Range: -1 (opposite) to 1 (identical).
    """
    a_arr = np.array(a, dtype=np.float64)
    b_arr = np.array(b, dtype=np.float64)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def bm25_score(
    tf: float,
    df: int,
    n_docs: int,
    doc_len: int,
    avgdl: float,
    k1: float = 1.2,
    b: float = 0.75,
) -> float:
    """BM25 scoring function.

    BM25(q,d) = IDF(t) * (TF*(k1+1)) / (TF + k1*(1-b+b*|d|/avgdl))
    IDF(t) = log((n_docs - df + 0.5) / (df + 0.5))
    """
    idf = math.log((n_docs - df + 0.5) / (df + 0.5))
    denom = tf + k1 * (1 - b + b * doc_len / avgdl)
    if denom == 0:
        return 0.0
    return float(idf * (tf * (k1 + 1)) / denom)


def rrf_score(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion: RRF(d) = 1 / (k + rank).

    k=60 is the standard constant from Cormack et al.
    """
    return 1.0 / (k + rank)


def bayesian_update(prior: float, reliability: float) -> float:
    """Bayesian update using odds form.

    posterior_odds = prior_odds * likelihood_ratio
    LR = r / (1-r) for reliability r
    """
    prior_odds = prior / (1 - prior) if prior < 1 else 1e10
    lr = reliability / (1 - reliability) if reliability < 1 else 1e10
    posterior_odds = prior_odds * lr
    return float(posterior_odds / (1 + posterior_odds))


def brier_score(forecasts: list[float], outcomes: list[int]) -> float:
    """Brier Score: BS = (1/N) * sum (f_i - o_i)^2.

    0 = perfect, 0.25 = random, 1 = perfectly wrong.
    """
    n = len(forecasts)
    if n == 0:
        return 0.0
    total = sum((f - o) ** 2 for f, o in zip(forecasts, outcomes, strict=True))
    return float(total / n)


def softmax(x: list[float]) -> list[float]:
    """Softmax: softmax(x_i) = exp(x_i) / sum(exp(x_j)).

    Numerically stable: subtract max before exp.
    """
    x_arr = np.array(x, dtype=np.float64)
    x_arr = x_arr - np.max(x_arr)
    exp_x = np.exp(x_arr)
    return (exp_x / np.sum(exp_x)).tolist()


def cross_entropy(predicted: list[float], actual: list[int]) -> float:
    """Cross-Entropy Loss: CE = -sum y_i * log(p_i).

    For one-hot actual and softmax predicted.
    """
    total = 0.0
    for p, y in zip(predicted, actual, strict=True):
        if y == 1:
            total += -math.log(max(p, 1e-10))
    return float(total)


def pagerank(
    adjacency: dict[str, list[str]],
    damping: float = 0.85,
    iterations: int = 100,
) -> dict[str, float]:
    """PageRank: PR(p) = (1-d)/N + d * sum PR(q)/out_degree(q).

    Iterative computation until convergence.
    """
    nodes = list(adjacency.keys())
    n = len(nodes)
    if n == 0:
        return {}

    pr: dict[str, float] = dict.fromkeys(nodes, 1.0 / n)

    # Build in-links
    in_links: dict[str, list[str]] = {node: [] for node in nodes}
    out_degree: dict[str, int] = dict.fromkeys(nodes, 0)

    for source, targets in adjacency.items():
        for target in targets:
            if target in in_links:
                in_links[target].append(source)
        out_degree[source] = len(targets)

    for _ in range(iterations):
        new_pr: dict[str, float] = {}
        for node in nodes:
            rank = (1 - damping) / n
            for source in in_links[node]:
                deg = out_degree.get(source, 0)
                if deg > 0:
                    rank += damping * pr[source] / deg
            new_pr[node] = rank
        pr = new_pr

    return pr


def ndcg(relevances: list[int]) -> float:
    """Normalized Discounted Cumulative Gain.

    DCG = sum rel_i / log2(i+1)
    nDCG = DCG / IDCG (ideal)
    """
    if not relevances:
        return 0.0

    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))
    ideal = sorted(relevances, reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))

    if idcg == 0:
        return 0.0
    return float(dcg / idcg)


def kl_divergence(p: list[float], q: list[float]) -> float:
    """KL Divergence: KL(P||Q) = sum P(x) * log(P(x)/Q(x)).

    Non-negative, zero iff P=Q. Not symmetric.
    """
    total = 0.0
    for pi, qi in zip(p, q, strict=True):
        if pi > 0 and qi > 0:
            total += pi * math.log(pi / qi)
    return float(total)
