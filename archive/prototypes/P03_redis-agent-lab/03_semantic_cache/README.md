> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# 03 · Semantic Cache — 语义缓存 ⭐

> **本 Lab 最有 AI 特色的章节**。Redis 在 AI 领域的"差异化王牌"，官方推出了 LangCache 托管服务。

## Why 这一章

传统缓存按 key 精确匹配——"退货政策" ≠ "怎么退货"，全是 cache miss。
**语义缓存按 embedding 相似度匹配，意思一样就命中**。

收益数据（来自主报告 §2.3）：
- LLM 调用成本可降 **50%+**
- 命中延迟 **5-20ms**（vs LLM 调用 1-5 秒，**100x 加速**）
- TTL 策略：FAQ 类 24h，产品描述 1-4h，价格库存 5-15min

## Why 自己手写而不是用 redis-vl

教学目的：让你看清 4 个核心动作。一旦理解了原理，再切到 `redis-vl` 的 `SemanticCache` 类（生产用 HNSW 索引，O(log n) 而非本 demo 的 O(n)）只是 5 行代码替换。

## 跑法

```powershell
# 前置：docker compose up -d + .env 配好 DashScope key
python 03_semantic_cache/main.py
```

## 预期输出（示例）

```
初始化语义缓存（threshold=0.85, ttl=3600s）...

======================================================================
Q1: 退货政策是什么？
    [MISS] 耗时  1.85s            → 我们的退货政策是 7 天无理由退货...

Q2: 怎么退货？
    [HIT ] 耗时  0.04s sim=0.91  → 我们的退货政策是 7 天无理由退货...

Q3: 退货流程怎么走？
    [HIT ] 耗时  0.04s sim=0.88  → 我们的退货政策是 7 天无理由退货...

Q4: 北京天气怎么样？
    [MISS] 耗时  1.62s            → 抱歉，我无法获取实时天气...

Q5: Beijing weather today?
    [HIT ] 耗时  0.05s sim=0.86  → 抱歉，我无法获取实时天气...

======================================================================
📊 命中率: 3/5 = 60%
💰 估算节省 LLM 调用: 3 次
```

> Q5 是否命中**取决于 embedding 模型的跨语言能力**。`text-embedding-v3` 跨中英效果不错；`text-embedding-ada-002` 可能 miss。

## 调参指南（生产关键）

| 参数 | 推荐值 | 调高的代价 | 调低的代价 |
|------|-------|-----------|-----------|
| `threshold` | 0.85-0.92 | 命中率下降 | False positive：返回错答案 |
| `ttl_seconds` | 取决于数据时效 | 旧数据滞留 | 命中率低 |
| Embedding 维度 | 1024（v3） | 内存增、查询慢 | 召回质量降 |

## 升级到生产

本 demo 是 O(n) 全量扫描，**不超过 1 万条 entries 都没问题**。超过就要换索引：

```python
# 生产推荐：用 redis-vl，底层是 RediSearch HNSW
from redisvl.extensions.cache.llm import SemanticCache as RVL_Cache

cache = RVL_Cache(
    name="prod_cache",
    redis_url="redis://localhost:6379",
    distance_threshold=0.15,  # cosine distance（注意是 distance 不是 similarity）
    ttl=3600,
)
```

## 停下来想一想 🤔

1. 为什么 threshold 用 cosine **similarity** 而非 cosine **distance**？两者关系是什么？
   - 答：distance = 1 - similarity，redis-vl 用 distance（小=更像），手写时常用 similarity（大=更像），别搞混
2. 如果用户问"今天的退货政策"和"昨天的退货政策"，会都命中同一个缓存——这是 bug 还是 feature？
   - 答：这是**业务语义模糊**问题。语义缓存的根本假设是"语义相同 → 答案相同"，时效性强的领域要么调高阈值要么不缓存
3. 怎么测试 false-positive 率？
   - 答：构造一组"看起来像但实际不同"的问题对（如"退货" vs "退款"），跑一遍统计错命中率

## 关联

- 主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §2.3
- Redis 官方 LangCache 商业产品：托管版本，不用自己运维
- 04 章 vector_rag 用同样的向量索引做 RAG 检索
