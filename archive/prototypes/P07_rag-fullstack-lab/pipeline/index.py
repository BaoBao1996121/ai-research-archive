"""③ Index 环节：把 chunks 灌入索引。

支持：
- chroma: 本地持久化向量库（默认）
- faiss: 纯 numpy + 暴力 IP 检索（无外部依赖，演示用）
- bm25: 词袋稀疏索引（rank_bm25 + jieba 中文分词）

所有索引实现统一接口：build(chunks, embedder) / query(text, k) / load() / save()
"""
from __future__ import annotations

import json
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import numpy as np

from .ingest import Chunk
from .embed import Embedder


# ----------------------- 通用基类 -----------------------

class Index:
    name: str = "base"

    def build(self, chunks: list[Chunk], embedder: Embedder | None = None) -> None:
        raise NotImplementedError

    def query(self, text: str, k: int = 10, *, embedder: Embedder | None = None) -> list[tuple[Chunk, float]]:
        raise NotImplementedError

    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...


# ----------------------- Chroma -----------------------

class ChromaIndex(Index):
    name = "chroma"

    def __init__(self, persist_dir: str = "./chroma_db", collection: str = "rag_lab"):
        import chromadb
        self.persist_dir = persist_dir
        self.collection_name = collection
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.col = None

    def build(self, chunks: list[Chunk], embedder: Embedder | None = None) -> None:
        assert embedder is not None, "Chroma 需要 embedder"
        # 重建集合
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.col = self.client.create_collection(self.collection_name, metadata={"hnsw:space": "cosine"})
        # 批量入库（避免过大 payload）
        BATCH = 64
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            embeds = embedder.encode([c.text for c in batch])
            self.col.add(
                ids=[c.id for c in batch],
                embeddings=embeds.tolist(),
                documents=[c.text for c in batch],
                metadatas=[{"source": c.source, **{k: str(v) for k, v in c.metadata.items()}} for c in batch],
            )
        print(f"[index/chroma] 已索引 {len(chunks)} chunks 到 {self.persist_dir}")

    def query(self, text: str, k: int = 10, *, embedder: Embedder | None = None) -> list[tuple[Chunk, float]]:
        if self.col is None:
            self.col = self.client.get_collection(self.collection_name)
        q_vec = embedder.encode([text])[0]
        res = self.col.query(query_embeddings=[q_vec.tolist()], n_results=k)
        out = []
        for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            chunk = Chunk(id=cid, text=doc, source=meta.get("source", ""), metadata=meta)
            score = 1.0 - float(dist)  # cosine distance -> similarity
            out.append((chunk, score))
        return out


# ----------------------- 简单 FAISS-like 暴力检索 -----------------------

class NumpyIndex(Index):
    """纯 numpy 暴力 IP 检索。无外部依赖，演示「向量检索本质」用。"""
    name = "numpy"

    def __init__(self):
        self.matrix: np.ndarray | None = None
        self.chunks: list[Chunk] = []

    def build(self, chunks: list[Chunk], embedder: Embedder | None = None) -> None:
        assert embedder is not None
        self.chunks = chunks
        self.matrix = embedder.encode([c.text for c in chunks])
        print(f"[index/numpy] 矩阵 shape={self.matrix.shape}")

    def query(self, text: str, k: int = 10, *, embedder: Embedder | None = None) -> list[tuple[Chunk, float]]:
        q = embedder.encode([text])[0]
        # 已归一化 → 内积 = 余弦
        sims = self.matrix @ q
        top = np.argsort(-sims)[:k]
        return [(self.chunks[i], float(sims[i])) for i in top]

    def save(self, path: str):
        Path(path).mkdir(parents=True, exist_ok=True)
        np.save(f"{path}/matrix.npy", self.matrix)
        with open(f"{path}/chunks.pkl", "wb") as f:
            pickle.dump([asdict(c) for c in self.chunks], f)

    def load(self, path: str):
        self.matrix = np.load(f"{path}/matrix.npy")
        with open(f"{path}/chunks.pkl", "rb") as f:
            self.chunks = [Chunk(**d) for d in pickle.load(f)]


# ----------------------- BM25 -----------------------

def _tokenize_zh(text: str) -> list[str]:
    """中文 jieba + 英文小写。BM25 必须分词。"""
    import jieba
    import re
    text = text.lower()
    # 先 jieba 分中文
    tokens = list(jieba.cut_for_search(text))
    # 过滤纯空白和单字符标点
    return [t for t in tokens if re.sub(r"\s+", "", t) and t not in "，。、；：！？.,;:!?\"'"]


class BM25Index(Index):
    name = "bm25"

    def __init__(self):
        self.bm25 = None
        self.chunks: list[Chunk] = []
        self.tokens: list[list[str]] = []

    def build(self, chunks: list[Chunk], embedder: Embedder | None = None) -> None:
        from rank_bm25 import BM25Okapi
        self.chunks = chunks
        self.tokens = [_tokenize_zh(c.text) for c in chunks]
        self.bm25 = BM25Okapi(self.tokens)
        print(f"[index/bm25] 已建索引，{len(chunks)} chunks，平均 token 数={sum(len(t) for t in self.tokens)/max(len(self.tokens),1):.1f}")

    def query(self, text: str, k: int = 10, *, embedder: Embedder | None = None) -> list[tuple[Chunk, float]]:
        q_tokens = _tokenize_zh(text)
        scores = self.bm25.get_scores(q_tokens)
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in top]

    def save(self, path: str):
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(f"{path}/bm25.pkl", "wb") as f:
            pickle.dump({"chunks": [asdict(c) for c in self.chunks], "tokens": self.tokens}, f)

    def load(self, path: str):
        from rank_bm25 import BM25Okapi
        with open(f"{path}/bm25.pkl", "rb") as f:
            data = pickle.load(f)
        self.chunks = [Chunk(**d) for d in data["chunks"]]
        self.tokens = data["tokens"]
        self.bm25 = BM25Okapi(self.tokens)


# ----------------------- 工厂 -----------------------

def build_index(kind: str, **kwargs) -> Index:
    if kind == "chroma":
        return ChromaIndex(**kwargs)
    if kind == "numpy":
        return NumpyIndex()
    if kind == "bm25":
        return BM25Index()
    raise ValueError(f"未知 index kind={kind}")
