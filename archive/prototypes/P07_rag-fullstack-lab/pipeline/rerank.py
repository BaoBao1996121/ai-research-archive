"""⑥ Rerank 环节：用更贵更准的模型对 top-N 重新排序。

可选：
- none: 不重排
- bge_reranker: bge-reranker-v2-m3，cross-encoder 型，强但需 GPU
- llm_judge: 用 LLM 当 judge 给每对 (q, chunk) 打 0-10 分。慢但灵活，且能给出原因。

为什么需要 Rerank：
- 双塔（dense embedding）召回快但精度有限——它把 query 和 doc 分开编码，无法精细交互
- Cross-encoder 把 (query, doc) 拼在一起进 BERT，能算出"逐 token 注意力"，精度高但慢
- 因此最佳实践：召回 K=50（双塔粗筛）→ Rerank 取 top-5（cross-encoder 精排）
"""
from __future__ import annotations

from typing import Sequence

from .ingest import Chunk
from .llm import LLMClient


class Reranker:
    name: str = "base"

    def rerank(self, query: str, candidates: list[tuple[Chunk, float]], top_n: int = 5) -> list[tuple[Chunk, float]]:
        raise NotImplementedError


class NoOpReranker(Reranker):
    name = "none"

    def rerank(self, query, candidates, top_n=5):
        return candidates[:top_n]


class BGEReranker(Reranker):
    """bge-reranker-v2-m3 - 中英文 cross-encoder SOTA。首次需下载 ~600MB。"""
    name = "bge_reranker"

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str | None = None):
        from sentence_transformers import CrossEncoder
        print(f"[rerank] 加载 cross-encoder {model_name}（首次会下载）...")
        self.model = CrossEncoder(model_name, device=device, max_length=512)

    def rerank(self, query, candidates, top_n=5):
        if not candidates:
            return []
        pairs = [[query, c.text] for c, _ in candidates]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
        return [(c, float(s)) for (c, _orig), s in ranked[:top_n]]


LLM_JUDGE_PROMPT = """请评估"候选段落"对"用户问题"的相关性。只输出一个 0 到 10 的整数分数，10 分表示完全相关、能直接回答问题，0 分表示完全无关。

用户问题：{q}

候选段落：
{c}

分数（只输出数字）："""


class LLMReranker(Reranker):
    name = "llm_judge"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def rerank(self, query, candidates, top_n=5):
        scored = []
        for c, _ in candidates:
            try:
                out = self.llm.complete(LLM_JUDGE_PROMPT.format(q=query, c=c.text[:1500]), max_tokens=10).strip()
                # 抠出第一个数字
                num = "".join(ch for ch in out.split()[0] if ch.isdigit() or ch == ".")
                score = float(num) if num else 0.0
            except Exception:
                score = 0.0
            scored.append((c, score))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_n]


def build_reranker(cfg: dict | None, llm: LLMClient | None = None) -> Reranker:
    if not cfg or cfg.get("model") in (None, "none", ""):
        return NoOpReranker()
    model = cfg["model"]
    if model == "bge_reranker":
        return BGEReranker(model_name=cfg.get("model_name", "BAAI/bge-reranker-v2-m3"))
    if model == "llm_judge":
        assert llm is not None, "llm_judge reranker 需要 llm"
        return LLMReranker(llm)
    raise ValueError(f"未知 rerank model={model}")
