"""① Ingest 环节：把原始语料切成 chunks。

可选策略：
- fixed: 固定字符数窗口（最暴力的 baseline）
- markdown_header: 按 # ## ### 层级切，保留标题路径作为元数据
- semantic: TODO（按段落语义边界）
- contextual: TODO（Anthropic Contextual Retrieval：每个 chunk 前加 LLM 生成的上下文）
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Chunk:
    """统一的 chunk 数据结构。所有切片策略都返回 Chunk 列表。"""
    id: str
    text: str
    source: str  # 原文件相对路径
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "metadata": self.metadata,
        }


# ----------------------- 策略：fixed -----------------------

def chunk_fixed(text: str, source: str, *, size: int = 512, overlap: int = 64) -> list[Chunk]:
    """固定字符数滑动窗口。中文按字符算，简单暴力。"""
    chunks = []
    step = size - overlap
    for i, start in enumerate(range(0, len(text), step)):
        seg = text[start:start + size].strip()
        if not seg:
            continue
        chunks.append(Chunk(
            id=f"{source}::{i}",
            text=seg,
            source=source,
            metadata={"strategy": "fixed", "start": start, "size": size},
        ))
    return chunks


# ----------------------- 策略：markdown_header -----------------------

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def chunk_markdown_header(text: str, source: str, *, max_size: int = 1500) -> list[Chunk]:
    """按 markdown 标题切分，保留标题层级路径作为元数据。
    超长段落继续 fixed 切，避免单 chunk 太大。
    """
    # 找出所有标题位置
    headers = [(m.start(), len(m.group(1)), m.group(2).strip()) for m in _HEADER_RE.finditer(text)]
    if not headers:
        return chunk_fixed(text, source, size=max_size)

    chunks: list[Chunk] = []
    header_path: list[str] = []  # 当前各级标题
    boundaries = [(0, "ROOT")] + [(pos, title) for pos, _, title in headers] + [(len(text), "EOF")]

    for idx, (pos, _, title) in enumerate(headers):
        next_pos = headers[idx + 1][0] if idx + 1 < len(headers) else len(text)
        level = len(re.match(r"^#+", text[pos:next_pos]).group(0))
        # 维护标题路径栈
        header_path = header_path[:level - 1] + [title]
        section_text = text[pos:next_pos].strip()
        if not section_text:
            continue
        # 太大就再切
        if len(section_text) > max_size:
            sub_chunks = chunk_fixed(section_text, source, size=max_size, overlap=100)
            for j, c in enumerate(sub_chunks):
                c.id = f"{source}::md::{idx}::{j}"
                c.metadata.update({
                    "strategy": "markdown_header",
                    "header_path": " > ".join(header_path),
                    "level": level,
                })
                chunks.append(c)
        else:
            chunks.append(Chunk(
                id=f"{source}::md::{idx}",
                text=section_text,
                source=source,
                metadata={
                    "strategy": "markdown_header",
                    "header_path": " > ".join(header_path),
                    "level": level,
                },
            ))
    return chunks


# ----------------------- 入口：ingest 文件夹 -----------------------

def load_corpus(corpus_dirs: list[str], *, glob: str = "**/*.md") -> Iterable[tuple[str, str]]:
    """遍历语料目录，yield (相对路径, 内容)。"""
    for d in corpus_dirs:
        root = Path(d).resolve()
        if not root.exists():
            print(f"[ingest] 警告：语料目录不存在 {root}")
            continue
        for f in root.glob(glob):
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[ingest] 跳过 {f}: {e}")
                continue
            rel = f.relative_to(root.parent if root.parent.exists() else root)
            yield str(rel).replace("\\", "/"), content


def ingest(corpus_dirs: list[str], *, strategy: str = "fixed", **kwargs) -> list[Chunk]:
    """主入口：根据策略切片所有语料。"""
    all_chunks: list[Chunk] = []
    for source, content in load_corpus(corpus_dirs):
        if strategy == "fixed":
            all_chunks.extend(chunk_fixed(content, source, **kwargs))
        elif strategy == "markdown_header":
            all_chunks.extend(chunk_markdown_header(content, source, **kwargs))
        else:
            raise NotImplementedError(f"切片策略 {strategy} 还没实现，欢迎贡献")
    print(f"[ingest] 策略={strategy} 共 {len(all_chunks)} chunks，来自 {len(set(c.source for c in all_chunks))} 个文件")
    return all_chunks
