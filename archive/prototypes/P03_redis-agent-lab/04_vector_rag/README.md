> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# 04 · Vector RAG — RediSearch HNSW 向量检索

> **状态**：⚡ 骨架 + README（推荐用 `redis-vl` 的高级封装，比手写省 80% 代码）

## Why 这一章

03 章的语义缓存底层是 O(n) 全量扫描——< 1 万条还行，更多就慢。本章用 **RediSearch HNSW 索引**做 RAG 检索，O(log n) 级别，百万向量也快。

## 跑法

```powershell
python 04_vector_rag/main.py
```

## 核心代码骨架（用 redis-vl）

```python
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.schema import IndexSchema
from _common.llm import embed, EMBEDDING_DIM, REDIS_URL

# 1. 定义索引 schema
schema = IndexSchema.from_dict({
    "index": {"name": "docs", "prefix": "doc:", "storage_type": "hash"},
    "fields": [
        {"name": "title", "type": "text"},
        {"name": "content", "type": "text"},
        {"name": "category", "type": "tag"},  # 用于过滤
        {"name": "embedding", "type": "vector", "attrs": {
            "dims": EMBEDDING_DIM,
            "algorithm": "hnsw",        # vs "flat"，hnsw 是近似但快
            "datatype": "float32",
            "distance_metric": "cosine",
            "m": 16,                    # HNSW 参数
            "ef_construction": 200,
        }},
    ],
})

index = SearchIndex(schema, redis_url=REDIS_URL)
index.create(overwrite=True)

# 2. 灌数据
docs = [
    {"title": "退货政策", "content": "7 天无理由退货...", "category": "policy"},
    {"title": "运费规则", "content": "满 99 包邮...", "category": "policy"},
    # ... N 条
]
for doc in docs:
    doc["embedding"] = embed(doc["content"])  # 生成 embedding
index.load(docs)

# 3. 查询
query_vec = embed("怎么退货")
query = VectorQuery(
    vector=query_vec,
    vector_field_name="embedding",
    return_fields=["title", "content"],
    num_results=3,
    filter_expression="@category:{policy}",  # 元数据过滤
)
results = index.query(query)
for r in results:
    print(r["title"], r["vector_distance"])
```

## HNSW vs FLAT 索引选择

| 算法 | 召回率 | 查询速度 | 内存 | 何时选 |
|------|-------|---------|------|-------|
| FLAT | 100%（精确） | 慢（O(n)） | 小 | < 1 万条，要求精确 |
| HNSW | 95-99%（近似） | 快（O(log n)） | 大 | > 1 万条，可接受小误差 |

## Hybrid Search（向量 + 关键词）

```python
from redisvl.query.filter import Tag, Text

filter_exp = (Text("title") % "退货") & Tag("category") == "policy"
query.set_filter(filter_exp)
```

## 关键参数调优

| 参数 | 作用 | 推荐 |
|------|------|------|
| `m` | HNSW 每个节点的连接数 | 16（默认），密集向量调大 |
| `ef_construction` | 建索引时探索深度 | 200（质量优先） |
| `ef_runtime` | 查询时探索深度 | 10-100（速度 vs 召回平衡） |

## 与专业向量库对比

| 维度 | RediSearch HNSW | Milvus | Qdrant |
|------|----------------|--------|--------|
| 数据规模上限 | ~百万级（全内存） | 十亿级 | 亿级 |
| 查询延迟 | < 1ms | 1-10ms | 1-10ms |
| 过滤能力 | 基础（Tag/Text） | 复杂表达式 | 复杂表达式 |
| 部署复杂度 | ⭐ 简单 | ⭐⭐⭐⭐ 复杂 | ⭐⭐ 中等 |

详见主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §三 + [大规模知识库检索方案调研](../../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md)。

## TODO

- [ ] 完整端到端：灌入一份真实 FAQ → RAG 问答
- [ ] 加入 Reranker（向量召回 Top-20 → BGE-reranker 精排 Top-3）
- [ ] 测试 Hybrid Search 召回率提升

## 关联

- 主报告 §2.4
- [大规模知识库检索方案调研](../../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md)
- [RAG从入门到生产落地完全指南](../../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)
