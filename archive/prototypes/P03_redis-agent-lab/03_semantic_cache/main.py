"""
03 · Semantic Cache — 语义缓存（最有 AI 特色的章节 ⭐）

核心思想：
  传统缓存按 key 精确匹配，"退货政策" ≠ "怎么退货" → cache miss
  语义缓存按 embedding 向量相似度匹配，意思一样就命中

本 demo 不依赖 redis-vl 或 langgraph，自己手写一个最小语义缓存，
让你看清楚 4 个核心动作：embed → search → similarity check → store

跑法：
    python 03_semantic_cache/main.py

预期输出：
  Q1: 退货政策是什么？               [MISS] 调 LLM, 耗时 1.8s
  Q2: 怎么退货？                     [HIT ] 命中, 耗时 0.05s, 相似度 0.91
  Q3: 退货流程怎么走？               [HIT ] 命中, 耗时 0.04s, 相似度 0.88
  Q4: 北京天气怎么样？               [MISS] 调 LLM, 耗时 1.5s
  Q5: Beijing weather today?         [HIT ] 命中, 耗时 0.05s, 相似度 0.86

  📊 命中率: 60% (3/5)
  💰 估算节省 LLM 调用: 3 次
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import (
    EMBEDDING_DIM,
    chat,
    cosine_similarity,
    embed,
    redis_client,
    redis_text_client,
    to_bytes,
)


# ---------- 语义缓存类 ----------

class SemanticCache:
    """最小可用的语义缓存

    实现思路（教学版，未做工业级优化）：
    1) 每条 cache entry 存为 Hash:  cache:{id} = {q, a, ts}
    2) 向量单独存为 String:         cache:vec:{id} = float32 bytes
    3) 用一个 Set 维护所有 id:      cache:ids
    4) 查询时遍历所有 id，逐个算 cosine 相似度

    ⚠️ 这种"全量扫描"方式只适合学习。生产用 RediSearch HNSW 索引（见 04 章）
       或 redis-vl 的 SemanticCache，都是 O(log n) 级别。
    """

    def __init__(
        self,
        namespace: str = "demo",
        threshold: float = 0.85,
        ttl_seconds: int = 3600,
    ):
        self.r = redis_client()             # bytes 模式（向量需要）
        self.rt = redis_text_client()       # 文本模式（普通字段方便）
        self.ns = namespace
        self.threshold = threshold
        self.ttl = ttl_seconds

    # --- key 命名约定 ---
    def _ids_key(self) -> str:
        return f"cache:{self.ns}:ids"

    def _entry_key(self, eid: str) -> str:
        return f"cache:{self.ns}:entry:{eid}"

    def _vec_key(self, eid: str) -> str:
        return f"cache:{self.ns}:vec:{eid}"

    # --- 核心 API ---
    def lookup(self, query: str) -> Optional[tuple[str, float]]:
        """查询：找到相似度 ≥ threshold 的最佳条目，返回 (answer, similarity)"""
        q_vec = embed(query)
        best_sim, best_answer = -1.0, None

        ids = self.rt.smembers(self._ids_key())
        for eid in ids:
            raw = self.r.get(self._vec_key(eid))
            if raw is None:
                # 向量过期了但 id 还在 set 里，顺手清理
                self.rt.srem(self._ids_key(), eid)
                continue
            cached_vec = np.frombuffer(raw, dtype=np.float32).tolist()
            sim = cosine_similarity(q_vec, cached_vec)
            if sim > best_sim:
                best_sim = sim
                best_answer = self.rt.hget(self._entry_key(eid), "a")

        if best_answer is not None and best_sim >= self.threshold:
            return best_answer, best_sim
        return None

    def store(self, query: str, answer: str) -> None:
        """存入：query+answer 作为新条目"""
        eid = uuid.uuid4().hex[:8]
        q_vec = embed(query)

        pipe = self.r.pipeline()
        pipe.set(self._vec_key(eid), to_bytes(q_vec), ex=self.ttl)
        pipe.execute()

        self.rt.hset(self._entry_key(eid), mapping={"q": query, "a": answer, "ts": int(time.time())})
        self.rt.expire(self._entry_key(eid), self.ttl)
        self.rt.sadd(self._ids_key(), eid)
        self.rt.expire(self._ids_key(), self.ttl)

    def clear(self) -> None:
        """清空当前 namespace 的所有缓存（demo 用）"""
        ids = self.rt.smembers(self._ids_key())
        if ids:
            keys = [self._entry_key(i) for i in ids] + [self._vec_key(i) for i in ids]
            self.rt.delete(*keys)
        self.rt.delete(self._ids_key())


# ---------- 带缓存的 LLM 调用 ----------

def cached_chat(cache: SemanticCache, question: str) -> tuple[str, str, float, float]:
    """返回 (answer, status, latency_seconds, similarity_or_zero)"""
    t0 = time.time()
    hit = cache.lookup(question)
    if hit is not None:
        ans, sim = hit
        return ans, "HIT ", time.time() - t0, sim

    # Miss：调 LLM 并存入缓存
    answer = chat(
        [
            {"role": "system", "content": "You are a helpful customer service assistant. Answer in 1-2 sentences."},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    cache.store(question, answer)
    return answer, "MISS", time.time() - t0, 0.0


# ---------- 主流程：跑一组测试问题 ----------

def main():
    from _common.llm import USE_MOCK_LLM
    print("初始化语义缓存（threshold=0.85, ttl=3600s）...")
    if USE_MOCK_LLM:
        print("⚠️  当前未配置 OPENAI_API_KEY，embed 走 mock（hash 伪向量）。")
        print("   后果：同义但用词不同的问题不会命中（mock 抓不到语义）。")
        print("   配 key 后重跑可看到真实 80%+ 跨语言命中率。")

    cache = SemanticCache(namespace="demo_03", threshold=0.85, ttl_seconds=3600)
    cache.clear()  # 确保 demo 从空状态开始

    # 5 个测试问题：1/4 是新问题，2/3/5 应命中前面的语义
    # Q6 故意复用 Q1 原文，证明缓存框架本身 work（即便 mock 模式）
    questions = [
        "退货政策是什么？",          # 新问题 → MISS
        "怎么退货？",                # 与 Q1 同义 → 真 embed: HIT, mock: MISS
        "退货流程怎么走？",          # 与 Q1 同义 → 真 embed: HIT, mock: MISS
        "北京天气怎么样？",          # 新问题 → MISS
        "Beijing weather today?",    # 与 Q4 同义（跨语言）→ 真 embed: HIT, mock: MISS
        "退货政策是什么？",          # ★ 与 Q1 完全相同 → 任何模式都 HIT
    ]

    hits = 0
    print("\n" + "=" * 70)
    for i, q in enumerate(questions, 1):
        ans, status, latency, sim = cached_chat(cache, q)
        sim_str = f"sim={sim:.2f}" if status.strip() == "HIT" else "          "
        if status.strip() == "HIT":
            hits += 1
        print(f"Q{i}: {q}")
        print(f"    [{status}] 耗时 {latency:5.2f}s {sim_str}  → {ans[:60]}...")
        print()

    print("=" * 70)
    print(f"📊 命中率: {hits}/{len(questions)} = {hits/len(questions)*100:.0f}%")
    print(f"💰 估算节省 LLM 调用: {hits} 次")
    print()
    print("💡 调参建议：")
    print("   - threshold 太低（<0.80）：会把不相关问题也命中，返回错答案")
    print("   - threshold 太高（>0.95）：几乎不命中，缓存形同虚设")
    print("   - 建议 0.85-0.92 之间，按业务测一遍 false-positive 再定")


if __name__ == "__main__":
    main()
