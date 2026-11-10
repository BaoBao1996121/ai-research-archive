"""
Redis-for-Agent Lab 共享 LLM/Embedding 客户端

设计原则：
- 所有章节统一从这里 import，避免每个章节重复初始化
- 走 OpenAI 兼容协议，可以无感切换 OpenAI / DashScope / Moonshot / Doubao
- 默认 DashScope（Qwen 系列），因为它对中文友好且价格便宜

用法：
    from _common.llm import chat, embed, redis_client
    answer = chat([{"role": "user", "content": "你好"}])
    vec = embed("hello world")
    r = redis_client()
"""
from __future__ import annotations

# === 强制 stdout/stderr 走 UTF-8（Windows GBK 终端会被 emoji 噎死） ===
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    _sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Union

import numpy as np
from dotenv import load_dotenv
import redis

# 自动从项目根加载 .env（无论从哪个章节子目录跑）
_LAB_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAB_ROOT / ".env")

# OpenAI 延迟导入，避免未装时报错
try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

# fakeredis 延迟导入
try:
    import fakeredis  # type: ignore
except ImportError:  # pragma: no cover
    fakeredis = None  # type: ignore


# ---------- 配置 ----------

LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5-plus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_FAKEREDIS = os.getenv("USE_FAKEREDIS", "0") in ("1", "true", "True")


# ---------- 客户端单例 ----------

@lru_cache(maxsize=1)
def _openai_client():
    if OpenAI is None:
        raise RuntimeError("openai 包未装：pip install openai")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not api_key or api_key.startswith("EXAMPLE_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY 未配置。请 copy .env.example .env 并填入 key。"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


# fakeredis 单例（跨 client 共享同一个虚拟服务器）
_FAKE_SERVER = None


def _make_redis_client(decode: bool) -> redis.Redis:
    if USE_FAKEREDIS:
        if fakeredis is None:
            raise RuntimeError("fakeredis 未装：pip install 'fakeredis[lua]'")
        global _FAKE_SERVER
        if _FAKE_SERVER is None:
            _FAKE_SERVER = fakeredis.FakeServer(version=(7,))
        return fakeredis.FakeRedis(server=_FAKE_SERVER, decode_responses=decode)
    return redis.Redis.from_url(REDIS_URL, decode_responses=decode)


@lru_cache(maxsize=1)
def redis_client() -> redis.Redis:
    """返回共享 Redis 客户端（decode_responses=False，原始 bytes，向量场景必需）"""
    return _make_redis_client(decode=False)


@lru_cache(maxsize=1)
def redis_text_client() -> redis.Redis:
    """返回字符串模式的 Redis 客户端（自动 decode，文本场景方便）"""
    return _make_redis_client(decode=True)


def _has_real_llm() -> bool:
    api_key = os.getenv("OPENAI_API_KEY", "")
    return bool(api_key) and not api_key.startswith("EXAMPLE_API_KEY")


# 模式标记：USE_MOCK_LLM=1 强制走 mock；无 key 也自动走 mock
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "0") in ("1", "true", "True") or not _has_real_llm()


def _mock_embed(text: str) -> List[float]:
    """确定性 hash-based 伪向量。
    
    设计：把文本拆词 → 每个词 sha256 → 摘要 N 个 float bucket → 累加 → L2 归一化。
    保证：同义词命中率有限（取决于词重叠度），但「同一句子」每次结果完全相同。
    用途：无真 embedding key 时，让管道能跑通；真 key 时自动切回真模型。
    """
    import hashlib
    vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
    # 简单 unigram + bigram，捕获一点语义
    tokens = list(text.lower())
    tokens += [text.lower()[i:i+2] for i in range(len(text)-1)]
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        # 把 32 字节摘要均匀洒到 EMBEDDING_DIM 个槽里
        for i, b in enumerate(h):
            vec[(i * 31) % EMBEDDING_DIM] += (b - 128) / 128.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


# ---------- 高层 API ----------

def chat(
    messages: List[dict],
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs,
) -> str:
    """简化的 chat 接口，返回 assistant 的 content 字符串"""
    if USE_MOCK_LLM:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"[mock-llm] 收到「{last_user[:60]}」（无 OPENAI_API_KEY，走 mock 回复）"
    resp = _openai_client().chat.completions.create(
        model=model or LLM_MODEL,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    return resp.choices[0].message.content or ""


def embed(text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
    """嵌入接口。单字符串返回单向量，列表返回向量列表。

    无 OPENAI_API_KEY 时自动走 mock embed（确定性 hash 伪向量），
    保证管道能跑通；有 key 时走真 DashScope text-embedding-v3。
    """
    single = isinstance(text, str)
    inputs = [text] if single else text

    if USE_MOCK_LLM:
        all_vecs = [_mock_embed(t) for t in inputs]
        return all_vecs[0] if single else all_vecs

    BATCH = 25
    all_vecs: List[List[float]] = []
    for i in range(0, len(inputs), BATCH):
        batch = inputs[i : i + BATCH]
        resp = _openai_client().embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_vecs.extend([d.embedding for d in resp.data])

    return all_vecs[0] if single else all_vecs


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """余弦相似度，结果范围 [-1, 1]，越大越相似"""
    av = np.asarray(a, dtype=np.float32)
    bv = np.asarray(b, dtype=np.float32)
    return float(np.dot(av, bv) / (np.linalg.norm(av) * np.linalg.norm(bv)))


def to_bytes(vec: List[float]) -> bytes:
    """把向量转成 Redis 向量索引需要的 float32 bytes"""
    return np.asarray(vec, dtype=np.float32).tobytes()


# ---------- 健康检查 ----------

def healthcheck() -> dict:
    """快速检查 Redis 和 LLM 是否都通"""
    result = {"redis": "❌", "llm": "❌", "embedding": "❌"}
    try:
        redis_text_client().ping()
        result["redis"] = "✅"
    except Exception as e:
        result["redis_err"] = str(e)

    try:
        chat([{"role": "user", "content": "ping"}], temperature=0)
        result["llm"] = "✅"
    except Exception as e:
        result["llm_err"] = str(e)

    try:
        v = embed("test")
        result["embedding"] = f"✅ (dim={len(v)})"
    except Exception as e:
        result["embedding_err"] = str(e)

    return result


if __name__ == "__main__":
    print("Redis-for-Agent Lab 健康检查：")
    for k, v in healthcheck().items():
        print(f"  {k}: {v}")
