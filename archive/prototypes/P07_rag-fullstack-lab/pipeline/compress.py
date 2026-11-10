"""⑦ Compress 环节：把 top-N chunks 压成最终送给 LLM 的上下文。

可选：
- topk: 直接拼 top-k
- parent_doc: 检索的是子 chunk，但喂给 LLM 的是父级章节（小召回大上下文）
- llm_summary: 用 LLM 把每个 chunk 摘要后再拼

设计意图：
- topk 简单粗暴，适合 chunk 本身就够大的场景
- parent_doc 解决"子 chunk 太碎"问题：召回精度高，但回答时给完整章节
- llm_summary 适合 chunk 长且冗余的场景，代价是慢一倍（多一轮 LLM 调用）
"""
from __future__ import annotations

from .ingest import Chunk
from .llm import LLMClient


def compress_topk(chunks: list[tuple[Chunk, float]], *, max_chars: int = 8000, **_) -> str:
    out = []
    used = 0
    for c, _ in chunks:
        snippet = f"\n\n--- 来源: {c.source} ---\n{c.text}"
        if used + len(snippet) > max_chars:
            break
        out.append(snippet)
        used += len(snippet)
    return "".join(out).strip()


SUMMARIZE_PROMPT = """请把下面的段落压缩成 50-100 字的精炼摘要，保留所有关键事实和数字。
直接输出摘要，不要任何前言。

段落：
{c}

摘要："""


def compress_llm_summary(chunks: list[tuple[Chunk, float]], *, llm: LLMClient, max_chars: int = 8000, **_) -> str:
    out = []
    used = 0
    for c, _ in chunks:
        try:
            summary = llm.complete(SUMMARIZE_PROMPT.format(c=c.text[:2000]), max_tokens=200).strip()
        except Exception:
            summary = c.text[:300]
        snippet = f"\n\n--- 来源: {c.source} ---\n{summary}"
        if used + len(snippet) > max_chars:
            break
        out.append(snippet)
        used += len(snippet)
    return "".join(out).strip()


def compress(chunks: list[tuple[Chunk, float]], *, mode: str = "topk", llm: LLMClient | None = None, max_chars: int = 8000) -> str:
    if mode == "topk":
        return compress_topk(chunks, max_chars=max_chars)
    if mode == "llm_summary":
        assert llm is not None
        return compress_llm_summary(chunks, llm=llm, max_chars=max_chars)
    if mode == "parent_doc":
        # MVP 简化：直接用 source 文件作为父文档（去重后拼）。生产版应建立 child→parent 映射。
        # 这里因为 markdown_header 切片已含 header_path，可以用同 header_path 的 chunks 合并
        seen_sources = set()
        out = []
        used = 0
        for c, _ in chunks:
            key = c.metadata.get("header_path") or c.source
            if key in seen_sources:
                continue
            seen_sources.add(key)
            snippet = f"\n\n--- {c.source} | {key} ---\n{c.text}"
            if used + len(snippet) > max_chars:
                break
            out.append(snippet)
            used += len(snippet)
        return "".join(out).strip()
    raise ValueError(f"未知 compress mode={mode}")
