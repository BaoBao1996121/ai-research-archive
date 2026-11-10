"""
04 · Vector RAG — 向量召回 + 生成

本章演示生产级向量检索的两条路径：
  - 路径 A（真 Redis 8.0+）：用 redisvl + RediSearch HNSW 索引，O(log n) 近似最近邻
  - 路径 B（fakeredis fallback）：手写全表 cosine 暴扫，O(n)，仅用于本机演示

无 OPENAI_API_KEY 时 embed 走 mock（hash 伪向量），仍能跑通管道但语义召回不准。

跑法：
    python 04_vector_rag/main.py

检索流程（RAG）：
    用户 query → embed → 向量检索 top-k → 把 chunks 塞进 prompt → LLM 生成答案
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import (
    EMBEDDING_DIM,
    USE_FAKEREDIS,
    USE_MOCK_LLM,
    chat,
    cosine_similarity,
    embed,
    redis_client,
    redis_text_client,
    to_bytes,
)


# ---------- 知识库（教学用 mini 文档集） ----------

DOCS = [
    {"id": "doc1", "title": "退货政策", "text": "公司支持 7 天无理由退货。商品需保持原包装完好，购物凭证齐全。退款将在 3-5 个工作日内退回原支付账户。"},
    {"id": "doc2", "title": "运费规则", "text": "订单满 99 元包邮。偏远地区（新疆、西藏、青海）需补 15 元运费。海外订单需联系客服报价。"},
    {"id": "doc3", "title": "会员等级", "text": "VIP 会员分为银卡、金卡、黑卡三级。累计消费 5000 元升金卡，2 万元升黑卡。黑卡会员享受专属客服与生日礼。"},
    {"id": "doc4", "title": "积分规则", "text": "每消费 1 元积 1 分，1000 分可抵扣 10 元。积分有效期为 1 年，过期自动清零。"},
    {"id": "doc5", "title": "客服时间", "text": "在线客服服务时间为每天 9:00-22:00。电话客服 7×24 小时。复杂问题建议工单提交，24 小时内回复。"},
    {"id": "doc6", "title": "支付方式", "text": "支持微信、支付宝、银联卡、Apple Pay。企业用户可申请对公转账，需提供营业执照。"},
    {"id": "doc7", "title": "发票申请", "text": "电子发票订单完成后 48 小时内自动发送至预留邮箱。需要纸质发票的请在订单备注，运费 5 元由买家承担。"},
    {"id": "doc8", "title": "商品保修", "text": "电子产品保修 1 年（厂家保修），支持上门服务。非人为损坏免费维修，人为损坏酌情收取材料费。"},
]


# ---------- 路径 A：redisvl + RediSearch HNSW（真 Redis 用） ----------

def _build_index_redisvl():
    from redisvl.index import SearchIndex
    from redisvl.schema import IndexSchema

    schema = IndexSchema.from_dict({
        "index": {"name": "rag_demo", "prefix": "rag:", "storage_type": "hash"},
        "fields": [
            {"name": "title", "type": "text"},
            {"name": "text", "type": "text"},
            {"name": "vec", "type": "vector",
             "attrs": {"dims": EMBEDDING_DIM, "algorithm": "hnsw",
                       "distance_metric": "cosine", "datatype": "float32",
                       "m": 16, "ef_construction": 200}},
        ],
    })
    idx = SearchIndex(schema, redis_client=redis_client())
    idx.create(overwrite=True, drop=True)
    return idx


def _ingest_redisvl(idx, docs):
    vecs = embed([d["text"] for d in docs])
    payload = []
    for d, v in zip(docs, vecs):
        payload.append({
            "id": d["id"],
            "title": d["title"],
            "text": d["text"],
            "vec": to_bytes(v),
        })
    idx.load(payload, id_field="id")


def _search_redisvl(idx, query: str, top_k: int = 3) -> List[Tuple[dict, float]]:
    from redisvl.query import VectorQuery
    qv = embed(query)
    q = VectorQuery(vector=qv, vector_field_name="vec",
                    return_fields=["title", "text"], num_results=top_k)
    results = idx.query(q)
    out = []
    for r in results:
        # redisvl 返回 vector_distance（cosine 距离 = 1 - 相似度）
        sim = 1.0 - float(r.get("vector_distance", 0))
        out.append(({"title": r["title"], "text": r["text"]}, sim))
    return out


# ---------- 路径 B：fakeredis 手写 cosine 暴扫 ----------

def _ingest_manual(docs):
    r = redis_client()
    rt = redis_text_client()
    rt.delete("rag:doc_ids")
    for d in docs:
        v = embed(d["text"])
        r.set(f"rag:vec:{d['id']}", to_bytes(v))
        rt.hset(f"rag:doc:{d['id']}", mapping={"title": d["title"], "text": d["text"]})
        rt.sadd("rag:doc_ids", d["id"])


def _search_manual(query: str, top_k: int = 3) -> List[Tuple[dict, float]]:
    r = redis_client()
    rt = redis_text_client()
    qv = embed(query)
    scores = []
    for did in rt.smembers("rag:doc_ids"):
        raw = r.get(f"rag:vec:{did}")
        if raw is None:
            continue
        v = np.frombuffer(raw, dtype=np.float32).tolist()
        sim = cosine_similarity(qv, v)
        meta = rt.hgetall(f"rag:doc:{did}")
        scores.append((meta, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# ---------- 统一对外 API：自动选路径 ----------

class VectorRAG:
    def __init__(self):
        # fakeredis 不支持 RediSearch → 走手写 cosine
        self.use_redisvl = not USE_FAKEREDIS
        self.idx = None

    def ingest(self, docs):
        if self.use_redisvl:
            self.idx = _build_index_redisvl()
            _ingest_redisvl(self.idx, docs)
        else:
            _ingest_manual(docs)

    def search(self, query: str, top_k: int = 3):
        if self.use_redisvl:
            return _search_redisvl(self.idx, query, top_k)
        return _search_manual(query, top_k)

    def ask(self, query: str, top_k: int = 3) -> dict:
        t0 = time.time()
        hits = self.search(query, top_k)
        retrieve_ms = (time.time() - t0) * 1000

        ctx = "\n\n".join(f"[{i+1}] 《{h[0]['title']}》: {h[0]['text']}" for i, h in enumerate(hits))
        prompt = (
            "你是客服助理。仅基于下面的知识片段回答用户问题。"
            "如果片段中没有答案，请直接说\"知识库中没有相关信息\"。\n\n"
            f"【知识片段】\n{ctx}\n\n【用户问题】{query}"
        )

        t1 = time.time()
        answer = chat([{"role": "user", "content": prompt}], temperature=0.2)
        gen_ms = (time.time() - t1) * 1000

        return {
            "query": query,
            "answer": answer,
            "retrieved": [(h[0]["title"], round(h[1], 3)) for h in hits],
            "retrieve_ms": round(retrieve_ms, 1),
            "gen_ms": round(gen_ms, 1),
        }


# ---------- 主流程 ----------

def main():
    print("=" * 70)
    print("04 · Vector RAG")
    print("=" * 70)
    print(f"  Redis 后端: {'fakeredis（手写 cosine 暴扫，O(n)）' if USE_FAKEREDIS else 'redisvl + HNSW，O(log n)'}")
    print(f"  Embedding: {'mock（hash 伪向量，语义召回有限）' if USE_MOCK_LLM else '真 DashScope text-embedding-v3'}")
    print(f"  LLM: {'mock 回复（仅演示流程）' if USE_MOCK_LLM else '真 LLM'}")

    rag = VectorRAG()
    print(f"\n📚 入库 {len(DOCS)} 篇文档...")
    t0 = time.time()
    rag.ingest(DOCS)
    print(f"   完成，耗时 {(time.time()-t0)*1000:.0f}ms")

    queries = [
        "我想退货怎么办？",          # 应召回 doc1
        "买到 100 元用不用付运费？",  # 应召回 doc2
        "怎么成为黑卡会员？",         # 应召回 doc3
        "积分会过期吗？",             # 应召回 doc4
    ]

    print("\n" + "=" * 70)
    for q in queries:
        res = rag.ask(q, top_k=3)
        print(f"\n❓ {res['query']}")
        print(f"   召回: {res['retrieved']}")
        print(f"   耗时: 检索 {res['retrieve_ms']}ms + 生成 {res['gen_ms']}ms")
        print(f"   答案: {res['answer'][:80]}...")

    print("\n" + "=" * 70)
    print("💡 关键观察：")
    if USE_FAKEREDIS:
        print("   - 当前用 fakeredis 走 O(n) 暴扫，8 篇文档无感")
        print("   - 文档量到 1 万级建议切真 Redis 8.0 + HNSW，召回从 50ms 降到 <5ms")
    if USE_MOCK_LLM:
        print("   - mock embed 召回是 hash 决定的，不反映真语义")
        print("   - 配 DashScope key 后，'我想退货' 应能稳定召回《退货政策》")
    print("   - 生产 RAG 还需：chunk 切分策略、重排序（rerank）、混合检索（BM25+向量）")


if __name__ == "__main__":
    main()
