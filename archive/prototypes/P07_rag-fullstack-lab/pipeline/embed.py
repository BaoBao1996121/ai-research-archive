"""② Embed 环节：把文本编码成向量。

默认本地 sentence-transformers（bge-m3 中文最强 baseline 之一）。
可扩展：bge-large-zh / Qwen3-Embedding / OpenAI 兼容 API。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import numpy as np


class Embedder:
    """统一接口。所有 embedding 实现都暴露 encode(texts) -> np.ndarray (N, D)。"""

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError

    @property
    def dim(self) -> int:
        raise NotImplementedError


class SentenceTransformerEmbedder(Embedder):
    """本地 sentence-transformers。首次调用会自动下载模型。"""

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str | None = None, batch_size: int = 32):
        from sentence_transformers import SentenceTransformer  # 延迟导入
        self.model_name = model_name
        self.batch_size = batch_size
        print(f"[embed] 加载本地模型 {model_name}（首次运行会下载，~2GB）...")
        self.model = SentenceTransformer(model_name, device=device)
        self._dim = self.model.get_sentence_embedding_dimension()
        print(f"[embed] 模型加载完成，维度={self._dim}")

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        return self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
            normalize_embeddings=True,  # bge 系列推荐归一化，配合内积=余弦
        ).astype(np.float32)

    @property
    def dim(self) -> int:
        return self._dim


class OpenAICompatEmbedder(Embedder):
    """OpenAI 兼容 embedding 接口（含 SiliconFlow / Ollama embedding model）。"""

    def __init__(self, model_name: str, base_url: str, api_key: str, batch_size: int = 16):
        from openai import OpenAI
        self.model_name = model_name
        self.batch_size = batch_size
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        # 探测维度：先发一条
        probe = self.client.embeddings.create(model=model_name, input=["probe"])
        self._dim = len(probe.data[0].embedding)
        print(f"[embed] 远程模型 {model_name} @ {base_url}, dim={self._dim}")

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        out = []
        for i in range(0, len(texts), self.batch_size):
            batch = list(texts[i:i + self.batch_size])
            resp = self.client.embeddings.create(model=self.model_name, input=batch)
            out.extend([d.embedding for d in resp.data])
        arr = np.array(out, dtype=np.float32)
        # 归一化，与本地 bge 行为一致
        norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9
        return arr / norms

    @property
    def dim(self) -> int:
        return self._dim


@lru_cache(maxsize=4)
def _build_embedder_cached(kind: str, model: str, base_url: str | None, api_key: str | None) -> Embedder:
    if kind == "sentence_transformer":
        return SentenceTransformerEmbedder(model_name=model)
    if kind == "openai_compat":
        return OpenAICompatEmbedder(model_name=model, base_url=base_url, api_key=api_key)
    raise ValueError(f"未知 embedder kind={kind}")


def build_embedder(cfg: dict) -> Embedder:
    """配置 → embedder。
    cfg 例：{kind: sentence_transformer, model: BAAI/bge-m3}
    或：    {kind: openai_compat, model: bge-m3, base_url: ..., api_key: ...}
    """
    return _build_embedder_cached(
        cfg.get("kind", "sentence_transformer"),
        cfg.get("model", "BAAI/bge-m3"),
        cfg.get("base_url"),
        cfg.get("api_key"),
    )
