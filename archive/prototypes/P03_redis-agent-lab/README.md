---
title: Redis-for-Agent Lab — 八章可运行示例工程
aliases: [Redis Agent Lab, redis-agent-lab]
tags: [prototype, redis, agent, lab, hands-on]
date: 2026-04-24
category: 实验验证
status: in-progress
related:
  - "[Redis在Agent中的应用与替代方案综合对比](../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)"
  - "[大规模知识库检索方案调研](../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md)"
  - "[RAG从入门到生产落地完全指南](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Redis-for-Agent Lab 🧪

> **统一管理的 Redis × Agent 示例工程集**
> 八章对应主报告 [Redis在Agent中的应用与替代方案综合对比](../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) 的六大模式 + 两个新增量主题。每章独立可跑，共享 Docker Redis 和 LLM 客户端。

---

## 设计原则

| 原则 | 体现 |
|------|------|
| **统一基础设施** | 一个 `docker-compose.yml` 起 Redis 8（含 RediSearch + Vector Set），所有章节共用 |
| **每章独立可跑** | 每个 `0X_*/main.py` 都是自包含的，进入子目录就能跑 |
| **共享 LLM 客户端** | `_common/llm.py` 用 OpenAI 兼容 API（默认 Qwen/DashScope），所有章节复用 |
| **递进式难度** | 00 速通 → 01-05 六大模式 → 06-07 进阶新增量 |
| **README + Code 双轨** | 每章一份 README 讲 Why + 跑法 + 预期输出，一份 main.py 实现 |

---

## 快速开始（5 分钟）

### 1. 起 Redis

```powershell
cd prototypes/redis-agent-lab
docker compose up -d
# 验证：访问 http://localhost:8001 看 RedisInsight 控制台
```

### 2. 配置环境

```powershell
copy .env.example .env
# 编辑 .env，填入你的 DashScope API Key（或任何 OpenAI 兼容服务）
```

### 3. 装依赖

```powershell
cd ../..  # 回到工作区根
.\.venv\Scripts\Activate.ps1
pip install -r prototypes/redis-agent-lab/requirements.txt
```

### 4. 跑 Hello World

```powershell
cd prototypes/redis-agent-lab
python 00_hello_redis/main.py
# 预期看到 5 大数据结构演示输出
```

---

## 章节索引

| # | 章节 | 对应主报告 | 状态 | 核心收获 |
|---|------|-----------|------|---------|
| **00** | [hello_redis](00_hello_redis/) | §一 核心概念速通 | ✅ 完整可跑 | String/Hash/List/Stream/Pub-Sub 五大结构 + TTL |
| **01** | [checkpoint](01_checkpoint/) | §2.1 状态持久化 | ⏭️ README + 完整参考代码 | LangGraph + Redis Checkpoint 断点续跑（**需真 Redis 8.0**，fakeredis 不支持 langgraph-checkpoint-redis）|
| **02** | [chat_memory](02_chat_memory/) | §2.2 对话记忆 | ✅ 完整可跑 | List 短期 + Hash 长期 + LTRIM 自动淘汰 |
| **03** | [semantic_cache](03_semantic_cache/) | §2.3 语义缓存 ⭐ | ✅ 完整可跑 | cosine 阈值 + 命中率/降本测量（mock embed fallback）|
| **04** | [vector_rag](04_vector_rag/) | §2.4 向量检索 | ✅ 完整可跑 | 双路径：真 Redis 走 redisvl HNSW / fakeredis 走手写 cosine |
| **05** | [tool_cache](05_tool_cache/) | §2.5 工具缓存 | ✅ 完整可跑 | L1+L2 缓存链 + 幂等 key + Lua 击穿防护（5 并发→1 真调）|
| **06** | [multi_agent_pubsub](06_multi_agent_pubsub/) | §2.6 多 Agent 通信 ⭐🆕 | ✅ 完整可跑 | Pub/Sub vs Streams + **Redis vs Kafka 取舍**（新增量）|
| **07** | [distributed_lock](07_distributed_lock/) | 主报告未覆盖 🆕 | ✅ 完整可跑 | 互斥锁 + 误释放防护 + Leader Election 接任演示 |

> **状态说明**：
> - ✅ **完整可跑**：本机已用 fakeredis 端到端验证（详见 [VALIDATION.md](VALIDATION.md)）
> - ⏭️ **待真 Redis 验证**：代码完整，但依赖 fakeredis 不支持的特性
> - 标 ⭐ 表示**最有价值的章节**，建议优先跑
> - 标 🆕 表示**主报告未深入的新增量**

---

## 学习路径建议

### Path A：30 分钟看懂 Redis 在 Agent 里干啥

```
00 (5 min) → 03 (15 min) → 06 (10 min)
```

跑完你会理解：基础数据 → 最有价值的 AI 模式（语义缓存）→ 多 Agent 通信范式。

### Path B：一个下午把六大模式过一遍

```
00 → 01 → 02 → 03 → 04 → 05 → 06
```

按主报告 §二 顺序，每章 30-60 分钟。

### Path C：进阶——新增量探索

```
06 (Redis vs Kafka 取舍) → 07 (分布式锁/Leader Election)
```

主报告未深入的工业级模式，适合已经熟悉基础后想搞生产级方案的人。

---

## 共享文件说明

| 文件 | 作用 |
|------|------|
| `docker-compose.yml` | Redis 8.0+ 单节点 + RedisInsight 8.0 控制台 |
| `requirements.txt` | redis、redis-vl、openai、numpy、tiktoken 等共享依赖 |
| `.env.example` | API Key/模型名/Redis URL 配置模板 |
| `_common/llm.py` | OpenAI 兼容客户端 + Embedding 接口（所有章节 import 这个） |

---

## 与已有产物的关系

- 与 `prototypes/multi-agent-demo/`（D26）正交：那个示范"Agent 之间如何编排"，本 Lab 示范"Redis 如何作为底层基础设施"
- 与 `experiments/learning/iter*.py`（D45）正交：那个示范"Agent 自身如何从 30 行到 1000 行演进"，本 Lab 不关心 Agent 内部，只关心外围基础设施
- 与主报告 [Redis在Agent中的应用与替代方案综合对比](../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)：本 Lab 是主报告的**实战配套工程**，主报告讲 Why 和对比，Lab 讲 How

---

## 避坑速查（共享）

| 坑 | 原因 | 解法 |
|----|------|------|
| `MODULE redisearch not loaded` | 用了官方 `redis:latest`（无模块） | 用 `redis:8` 或 `redis/redis-stack` |
| Embedding 维度不匹配报错 | 创建索引时维度 ≠ embedding 实际维度 | DashScope `text-embedding-v3` 是 1024 维，`v2` 是 1536 维 |
| 中文向量召回率低 | 用了 `text-embedding-ada-002`（英文优化） | 中文用 `text-embedding-v3`（DashScope）或 `bge-m3`（HF） |
| `WRONGTYPE` 错误 | 同一个 key 被当不同类型用 | 命名加前缀：`cache:xxx`、`queue:xxx`、`mem:xxx` |
| Pub/Sub 消息丢失 | Pub/Sub 是 fire-and-forget，订阅者没在线就丢 | 不能丢的用 Streams（带持久化和消费组） |
| `langgraph-checkpoint-redis` 装失败 | 它要 Redis ≥ 8.0 | 用 docker-compose 里的 `redis:8`，不要用本机老 Redis |

---

## TODO（欢迎贡献）

- [ ] 01/02/04/05 章节从骨架升级到完整可跑
- [ ] 加入 K6/locust 压力测试脚本，量化语义缓存的降本数据
- [ ] 补充 Redis Cluster 模式下各章节的注意事项
- [ ] 加入 Redis Sentinel 高可用部署示例
