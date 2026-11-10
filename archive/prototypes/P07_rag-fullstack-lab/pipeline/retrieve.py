"""⑤ Retrieve 环节：从一个或多个索引中召回 top-k。

可选模式：
- dense: 仅向量检索
- bm25: 仅词袋检索
- hybrid_rrf: 二者并跑，用 RRF (Reciprocal Rank Fusion) 融合
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .ingest import Chunk
from .index import Index
from .embed import Embedder


@dataclass
class RetrievalResult:
    chunk: Chunk
    score: float
    source_method: str = ""


def reciprocal_rank_fusion(
    rankings: list[list[tuple[Chunk, float]]],
    *,
    k: int = 60,
) -> list[tuple[Chunk, float]]:
    """RRF：score = Σ 1/(k + rank_i)。k=60 是 Cormack et al. 2009 的经典默认值。

    为什么 RRF 这么强：它只看排名不看绝对分数。dense 和 bm25 的分数尺度完全不同
    （dense 是 [0,1] 余弦，bm25 是 [0, +∞]），直接加权会被尺度大的一方吞掉。
    RRF 把分数压成「我在这个排序里第几名」再相加，自然抹平尺度差异。
    """
    fused: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, (chunk, _score) in enumerate(ranking):
            fused[chunk.id] += 1.0 / (k + rank + 1)
            chunk_map[chunk.id] = chunk
    sorted_ids = sorted(fused.keys(), key=lambda i: -fused[i])
    return [(chunk_map[i], fused[i]) for i in sorted_ids]


def retrieve(
    queries: list[str],
    *,
    mode: str,
    dense_index: Index | None = None,
    bm25_index: Index | None = None,
    embedder: Embedder | None = None,
    k: int = 20,
) -> list[tuple[Chunk, float]]:
    """主入口。queries 可能是多个改写后的查询，结果会跨 queries 再次 RRF 融合。"""
    all_dense_rankings: list[list[tuple[Chunk, float]]] = []
    all_bm25_rankings: list[list[tuple[Chunk, float]]] = []

    for q in queries:
        if mode in ("dense", "hybrid_rrf"):
            assert dense_index is not None
            all_dense_rankings.append(dense_index.query(q, k=k, embedder=embedder))
        if mode in ("bm25", "hybrid_rrf"):
            assert bm25_index is not None
            all_bm25_rankings.append(bm25_index.query(q, k=k))

    if mode == "dense":
        return reciprocal_rank_fusion(all_dense_rankings)[:k] if len(queries) > 1 else all_dense_rankings[0][:k]
    if mode == "bm25":
        return reciprocal_rank_fusion(all_bm25_rankings)[:k] if len(queries) > 1 else all_bm25_rankings[0][:k]
    if mode == "hybrid_rrf":
        return reciprocal_rank_fusion(all_dense_rankings + all_bm25_rankings)[:k]
    raise ValueError(f"未知 retrieve mode={mode}")
