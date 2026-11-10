"""配置 → 完整 pipeline 工厂。

让 run.py 和 eval/run_eval.py 都通过这个统一入口构建 pipeline。
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import ingest as ingest_mod
from .embed import build_embedder, Embedder
from .index import build_index, Index
from .llm import build_llm, LLMClient
from .query_transform import transform_query
from .retrieve import retrieve
from .rerank import build_reranker, Reranker
from .compress import compress
from .generate import generate


def _resolve_env(obj):
    """递归把 ${ENV} 占位符替换成实际环境变量。"""
    if isinstance(obj, dict):
        return {k: _resolve_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env(v) for v in obj]
    if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        return os.environ.get(obj[2:-1], "")
    return obj


def load_config(path: str) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return _resolve_env(cfg)


def config_fingerprint(cfg: dict) -> str:
    """配置指纹：用于命名 chroma collection / 缓存目录。
    只包含影响索引的字段（ingest + embed + index）。
    """
    relevant = {
        "corpus": cfg.get("corpus"),
        "ingest": cfg.get("ingest"),
        "embed": cfg.get("embed"),
        "index": cfg.get("index"),
    }
    s = json.dumps(relevant, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(s.encode()).hexdigest()[:10]


@dataclass
class Pipeline:
    cfg: dict
    embedder: Embedder
    dense_index: Index | None
    bm25_index: Index | None
    reranker: Reranker
    llm: LLMClient
    transform_llm: LLMClient

    def answer(self, question: str, *, k: int = 20, top_n: int = 5, return_trace: bool = False) -> dict:
        # ④ Query transform
        q_mode = self.cfg.get("query", {}).get("transform", "none")
        queries = transform_query(question, mode=q_mode, llm=self.transform_llm)

        # ⑤ Retrieve
        r_mode = self.cfg.get("retrieve", {}).get("mode", "dense")
        candidates = retrieve(
            queries,
            mode=r_mode,
            dense_index=self.dense_index,
            bm25_index=self.bm25_index,
            embedder=self.embedder,
            k=k,
        )

        # ⑥ Rerank
        reranked = self.reranker.rerank(question, candidates, top_n=top_n)

        # ⑦ Compress
        c_mode = self.cfg.get("compress", {}).get("mode", "topk")
        max_chars = self.cfg.get("compress", {}).get("max_chars", 8000)
        context = compress(reranked, mode=c_mode, llm=self.llm, max_chars=max_chars)

        # ⑧ Generate
        prompt_tmpl = self.cfg.get("generate", {}).get("prompt", "standard")
        max_tokens = self.cfg.get("generate", {}).get("max_tokens", 1024)
        answer = generate(question, context, llm=self.llm, prompt_template=prompt_tmpl, max_tokens=max_tokens)

        result = {"question": question, "answer": answer, "retrieved_docs": [c.source for c, _ in reranked]}
        if return_trace:
            result["trace"] = {
                "queries": queries,
                "candidates_count": len(candidates),
                "reranked_top": [{"source": c.source, "score": s, "preview": c.text[:120]} for c, s in reranked],
                "context_chars": len(context),
            }
        return result


def build_pipeline(cfg: dict, *, build_indices: bool = True) -> Pipeline:
    """从配置构建完整 pipeline。
    build_indices=False 用于「索引已存在直接加载」场景（eval 时跑多 case 不重建）。
    """
    embedder = build_embedder(cfg["embed"])

    fp = config_fingerprint(cfg)
    persist_root = Path(cfg.get("persist_dir", "./data")) / fp
    persist_root.mkdir(parents=True, exist_ok=True)

    # 索引
    dense_index = None
    bm25_index = None
    r_mode = cfg.get("retrieve", {}).get("mode", "dense")
    needs_dense = r_mode in ("dense", "hybrid_rrf")
    needs_bm25 = r_mode in ("bm25", "hybrid_rrf")

    if build_indices:
        chunks = ingest_mod.ingest(
            cfg["corpus"]["dirs"],
            strategy=cfg["ingest"]["strategy"],
            **{k: v for k, v in cfg["ingest"].items() if k != "strategy"},
        )
    else:
        chunks = []

    if needs_dense:
        idx_kind = cfg["index"].get("backend", "chroma")
        if idx_kind == "chroma":
            dense_index = build_index("chroma", persist_dir=str(persist_root / "chroma"), collection=f"col_{fp}")
        else:
            dense_index = build_index(idx_kind)
        if build_indices:
            dense_index.build(chunks, embedder=embedder)
        else:
            # Chroma 自动从 persist_dir 加载；NumpyIndex 需要显式 load
            if idx_kind != "chroma":
                dense_index.load(str(persist_root / "numpy"))

    if needs_bm25:
        bm25_index = build_index("bm25")
        if build_indices:
            bm25_index.build(chunks)
            bm25_index.save(str(persist_root / "bm25"))
        else:
            bm25_index.load(str(persist_root / "bm25"))

    # LLM
    llm = build_llm(cfg["generate"])
    transform_llm = build_llm(cfg.get("query", {}).get("llm", cfg["generate"]))

    # Reranker
    reranker = build_reranker(cfg.get("rerank"), llm=llm)

    return Pipeline(
        cfg=cfg,
        embedder=embedder,
        dense_index=dense_index,
        bm25_index=bm25_index,
        reranker=reranker,
        llm=llm,
        transform_llm=transform_llm,
    )
