---
title: Agent 主流技术栈搭配速查手册
aliases: [R65, Agent技术栈搭配, Agent主流配置扫盲]
tags: [stack, ecosystem, embedding, vector-db, rerank, fine-tuning, inference, lookup]
date: 2026-04-25
category: 工具与生态
report_id: R65
tokens: 13000
status: completed
related:
  - "[R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)"
  - "[R47](R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)"
  - "[R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R53](R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)"
  - "[R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)"
  - "[R45](R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Agent 主流技术栈搭配速查手册

> **一句话概括**：Agent 开发中 90% 的技术选型其实只在 6 个组件上做选择——Embedding、向量库、Rerank、微调框架、推理引擎、Agent 框架。每个组件主流玩家就 3-5 个，搭配套路也就 4-5 套。本报告把它们一次性铺平在一张速查图上。
> **研究日期**：2026-04-25
> **关联报告**：[R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)（RAG 落地，Embedding/向量库深度章节）、[R47](R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)（Redis 与 7 个向量库横评）、[R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)（微调框架横评）、[R53](R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)（Rerank 蒸馏与基座）、[R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)（推理引擎横评）、[R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)（服务化与网关）、[R45](R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md)（Agent 编排框架）
> **增量声明**：本报告**不重复**上述 7 篇深度报告的内容，**只做横向汇总**——把散落在各报告里的组件选型整合为"主流搭配速查 + 经典套餐"，作为新人扫盲入口和老兵的速查卡。需要任一组件深度时，跳转到对应报告。

---

## 📋 TL;DR 速查卡（30 秒抓核心）

> 想立刻动手的人，看完这一页就够了。其余章节是"为什么"的展开。

**核心结论**：

1. **2026 年 Agent 主流栈已收敛**——Embedding 选 BGE-M3，向量库选 Milvus 或 pgvector，Rerank 选 bge-reranker-v2-m3，微调用 LLaMA-Factory 或 Unsloth，推理用 vLLM，框架用 LangGraph 或 OpenAI SDK。**90% 场景按这个走不会出错**。
2. **闭源 vs 开源 = "省心 vs 可控"二选一**：API 路线（OpenAI Embedding + Cohere Rerank + GPT-4 + AssistantsAPI）开发周期 1 周但单价高；自托管路线（BGE + Milvus + bge-reranker + Qwen + vLLM）准入门槛 1 张 4090 但调优周期 1-2 月。
3. **新手最容易踩坑的不是"选错组件"，而是"中途换 Embedding 模型导致全量重建索引"**——第一次就选对，比反复横跳成本低十倍。

**默认推荐配置（中文场景，无脑抄）**：

| 组件 | 推荐 | 理由 |
|------|------|------|
| Embedding | **BGE-M3**（BAAI，1024 维，免费） | 中文 MTEB 前 5、多语言、query/doc 不对称、本地部署 |
| 向量库 | **Milvus**（生产）或 **pgvector**（已有 PG） | 混合检索内置、千万级稳、Stars 33K+ |
| Rerank | **bge-reranker-v2-m3**（568M 参数） | 中文标杆，月下载 814 万+，比 Cohere 免费 |
| 微调框架 | **LLaMA-Factory**（学习 / 100+ 模型）或 **Unsloth**（单卡极致） | 70.6K⭐ 零代码 / 62.8K⭐ 2× 速度 |
| 微调方法 | **QLoRA**（4bit + LoRA） | 7B=6GB / 30B=24GB / 70B=48GB，效果差 < 2% |
| 推理引擎 | **vLLM**（生产）或 **Ollama**（本地） | 综合第一 / 一行命令跑模型 |
| LLM 基座 | **Qwen2.5/3 系列**（中文）或 **Llama 3.1**（英文） | 开源模型主力，覆盖 0.5B-72B 全谱 |
| Agent 框架 | **LangGraph**（多 Agent / 复杂状态）或 **OpenAI SDK**（单 Agent） | 29.2K⭐ 事实标准 / 最简起点 |

**最常踩的坑（按发生频率排）**：

| 坑 | 症状 | 解法 |
|----|------|------|
| Embedding 中途换模型 | 整个向量库失效，必须全量重建 | 第一次就用 MTEB Leaderboard 选好，**绑定一个版本** |
| 微调用了全量 SFT | 单卡爆显存 / 成本爆炸 | 默认上 QLoRA，除非有充分理由全参 |
| Cross-Encoder Rerank 太慢 | Top-100 重排一次 2-3 秒 | 用 `bge-reranker-v2-m3` 而不是 large；或蒸成 MiniLM-6L |
| Chat Template 没对上 | 微调完模型胡言乱语 | 训练和推理用**同一个模板**，LLaMA-Factory 会强制校验 |
| 推理把全精度模型直接上 | 显存翻倍、吞吐减半 | 默认 W4A16（GPTQ/AWQ），效果差 < 1% 但显存省 75% |

---

## 目录

- [一、全景搭配地图：一张图看懂整个栈](#一全景搭配地图)
- [二、组件横评](#二组件横评)
  - [2.1 Embedding 模型](#21-embedding-模型)
  - [2.2 向量数据库](#22-向量数据库)
  - [2.3 Rerank 模型](#23-rerank-模型)
  - [2.4 微调框架与基座](#24-微调框架与基座)
  - [2.5 推理引擎](#25-推理引擎)
  - [2.6 LLM 基座（开源模型）](#26-llm-基座开源模型)
  - [2.7 Agent 编排框架](#27-agent-编排框架)
- [三、经典搭配套餐](#三经典搭配套餐)
- [四、决策树速查](#四决策树速查)
- [五、避坑指南](#五避坑指南)
- [六、关联阅读地图](#六关联阅读地图)

---

## 一、全景搭配地图

> **先建立坐标系**：Agent 系统按数据流动方向看，就是从用户提问 → 检索知识 → 调模型 → 返回结果。下图把每一层的主流玩家全列出来——选型时挑一个就够了。

```
┌─────────────────────────────────────────────────────────────────────┐
│                  用户请求                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ① Agent 框架层（编排 / 状态 / 工具调度）                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ LangGraph  │ │ OpenAI SDK │ │  CrewAI    │ │ Claude SDK │       │
│  │ 29.2K⭐ 标杆│ │ 单 Agent 起点│ │ 角色编排   │ │ 黑盒最强   │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ② 检索层（RAG / 知识库）                                              │
│   ┌──────────┐    ┌────────────┐    ┌──────────┐                   │
│   │ Embedding│───▶│ 向量数据库   │───▶│  Rerank  │                   │
│   ├──────────┤    ├────────────┤    ├──────────┤                   │
│   │ BGE-M3   │    │ Milvus     │    │bge-rerank│                   │
│   │ OpenAI-3 │    │ Qdrant     │    │ Cohere   │                   │
│   │ Jina v3  │    │ pgvector   │    │ Jina     │                   │
│   │ Voyage   │    │ Chroma     │    │ MiniLM-6 │                   │
│   └──────────┘    │ Weaviate   │    └──────────┘                   │
│                   └────────────┘                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ③ 模型层（LLM 调用）                                                  │
│   ┌────────────────┐         ┌─────────────────┐                   │
│   │   API 路线      │   或者  │  自托管路线      │                   │
│   ├────────────────┤         ├─────────────────┤                   │
│   │ GPT-5 / o系列  │         │ Qwen2.5/3 系列  │                   │
│   │ Claude Sonnet/ │         │ Llama 3.1/3.3   │                   │
│   │   Opus 4.x     │         │ DeepSeek V3/R1  │                   │
│   │ Gemini 2.x     │         │ Mistral/Mixtral │                   │
│   │ DeepSeek API   │         │ + vLLM/SGLang   │                   │
│   └────────────────┘         │ + 量化(GPTQ/AWQ)│                   │
│                              └─────────────────┘                   │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ④ 可选：微调层（让基座学私有知识 / 改风格）                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│   │LLaMA-Factory │  │   Unsloth    │  │   Axolotl    │             │
│   │ 零代码 WebUI │  │ 单卡 2× 速度│  │ YAML 驱动     │             │
│   │ 70.6K⭐      │  │ 62.8K⭐     │  │ 11.7K⭐       │             │
│   └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                    │
│   方法：QLoRA（默认）/ LoRA / DPO / GRPO                             │
└─────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ⑤ 基础设施层（缓存 / 网关 / 监控）                                    │
│   Redis (语义缓存) / LiteLLM (路由 fallback) / Langfuse (观测)       │
└─────────────────────────────────────────────────────────────────────┘
```

**怎么用这张图**：从上到下，每一层挑一个——不需要每层都用最贵的。比如做内部知识库问答，可以是「OpenAI SDK + BGE-M3 + pgvector + bge-reranker-v2-m3 + GPT-4o-mini API + 不微调 + Redis 缓存」，这就是一个完整的搭配。

---

## 二、组件横评

### 2.1 Embedding 模型

**Embedding 是干啥的**：把"文字"变成 768 / 1024 / 3072 维的向量，让计算机能算"两段话有多像"。是 RAG 的入口。

| 模型 | 维度 | 中文 MTEB | 多语言 | 部署 | 单价/1M tokens | 适合 |
|------|------|----------|--------|------|---------------|------|
| **BGE-M3**（BAAI）⭐ | 1024 | 前 5 | **极好** | 本地/API | 免费 | 中文/多语言生产首选 |
| **BGE-large-zh-v1.5** | 1024 | 前 10 | 仅中文 | 本地 | 免费 | 纯中文场景 |
| **OpenAI text-embedding-3-large** | 3072 | 前 10 | 好 | 仅 API | $0.13 | 不想运维、英文为主 |
| **OpenAI text-embedding-3-small** | 1536 | 前 20 | 好 | 仅 API | $0.02 | 性价比 API 选项 |
| **Jina-embeddings-v3** | 1024 | 前 10 | 好 | 本地/API | 免费/付费 | 想要 LoRA 适配头 |
| **GTE-Qwen2-7B**（阿里达摩院） | 3584 | **第 1** | 好 | 本地 | 免费 | 中文绝对榜首、显存吃 |
| **Voyage-3** | 1024 | - | 好 | 仅 API | $0.06 | 欧美技术圈认可 |

**怎么选**（对照 [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) §6.2 决策树）：

- **中文为主、要免费、要好用** → **BGE-M3**（默认推荐，覆盖 90% 场景）
- **不想自己部署、英文为主** → OpenAI text-embedding-3-small（成本低）
- **想要 SOTA 中文效果、显存够** → GTE-Qwen2-7B（榜首但部署贵）
- **多语言（10+ 语言）** → BGE-M3 是专门为这个设计的

**优劣对比**：

| 路线 | 优势 | 劣势 |
|------|------|------|
| **BGE 系列**（开源本地） | 免费、可微调、隐私可控 | 自己运维 GPU，需要 16-32GB 显存 |
| **OpenAI 系列**（API） | 零运维、`dimensions` 参数可截断维度省存储 | 数据出境合规、长期成本高 |
| **GTE-Qwen2-7B** | 中文榜首 | 7B 模型部署贵，吞吐低，性价比差 |

> 完整选型陷阱（query/doc 不对称、维度截断、换模型必重建索引）见 [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)。

---

### 2.2 向量数据库

**向量库是干啥的**：存 Embedding 向量、提供"找最近的 100 个"这种近似最近邻（ANN）搜索能力。Agent 的"长期记忆"和"知识库"都靠它。

| 向量库 | 类型 | 混合检索 | 集群 | Stars | 核心场景 |
|--------|------|---------|------|-------|---------|
| **Milvus** | 专用 | ✅ 内置 BM25 | ✅ | 33K | 生产级首选、千万级以上 |
| **Qdrant** | 专用（Rust 写） | ✅ | ✅ | 23K | 高性能、Payload Filter 强 |
| **Weaviate** | 专用 | ✅ | ✅ | 14K | GraphQL 生态、模块化 |
| **pgvector** | PostgreSQL 扩展 | ✅（配 pg_trgm） | ✅ | 14K | 已有 PG 团队、要事务 |
| **Chroma** | 专用（轻量） | ❌ | ❌ | 18K | 原型/小规模/嵌入式 |
| **Elasticsearch** | 搜索引擎 | ✅ | ✅ | 72K | 已有 ES 团队、关键词强 |
| **Redis Stack** | KV+向量 | ⚠️ 一般 | ✅ | 74K | 缓存+向量一体、< 500 万规模 |

**怎么选**（对照 [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) §7.3 + [R47](R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §3.1）：

- **原型阶段**（< 10 万文档） → **Chroma**（pip install 就用）
- **生产 < 100 万文档** → **pgvector**（已有 PG）或 **Qdrant**（性能更好）
- **生产 > 100 万文档** → **Milvus**（专为大规模设计）
- **缓存 + 向量一体** → **Redis 8.0+**（Vector Set beta）但**> 500 万条会内存爆炸**
- **已有 Elasticsearch** → 直接用 ES 8.x 的向量搜索

**优劣对比**（这个表是用户最容易混淆的部分，重点看）：

| 库 | 优势 | 劣势 | 不适合 |
|----|------|------|--------|
| **Milvus** | 大规模王者、混合检索原生、3.0 后云原生架构 | 部署复杂（需要 etcd/pulsar）、< 100 万规模杀鸡用牛刀 | 个人项目 |
| **Qdrant** | Rust 写性能最快、单二进制部署简单、Payload Filter 强 | 集群版商业化、文档不如 Milvus 全 | 国内合规要求严的金融场景 |
| **pgvector** | 数据一致性、SQL 生态、HNSW 索引 | < 1000 万条性能可、再大就吃力 | 千万级以上 ANN |
| **Chroma** | 几行代码起跑、API 极简 | 单机、生产级稳定性差、社区小 | 任何要扩展的场景 |
| **Redis** | 一站式（缓存+会话+向量）、运维简单 | 全数据驻内存、向量 > 500 万条经济性垮 | 大规模 RAG |

> 7 库 × 8 维度完整对比矩阵见 [R47](R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)。

---

### 2.3 Rerank 模型

**Rerank 是干啥的**：向量检索是"大网捞鱼"（百万→100 条粗筛），Rerank 是"精挑细选"（100→5 条精排）。原理是用 **Cross-Encoder**（query 和 doc 拼一起喂模型）算精确相关性，比 Embedding 的 Bi-Encoder（两边分别 encode）准但慢。

| 模型 | 基座 | 参数量 | 中文 | 部署 | 月下载量 | 推荐度 |
|------|------|--------|------|------|---------|--------|
| **bge-reranker-v2-m3** ⭐ | XLM-RoBERTa | 568M | **极好** | 本地 | 814 万+ | 中文默认首选 |
| **bge-reranker-large** | XLM-RoBERTa | 560M | 好 | 本地 | 高 | 老版本，建议升 v2 |
| **bge-reranker-v2.5-gemma2-lightweight** | Gemma2 | 蒸馏后小 | 好 | 本地 | 中 | 2026 新出，主打速度 |
| **Cohere Rerank 3.5** | 闭源 | 未公开 | 好 | 仅 API | - | 商业 SaaS、英文标杆 |
| **Jina Reranker v2** | 自研 | 278M | 好 | 本地/API | 中 | 多语言、轻量 |
| **MiniLM-L6-v2 cross-encoder** | BERT 蒸馏 | 22M | 弱 | 本地 | 高 | 极致延迟、英文场景 |
| **bge-reranker-v2-gemma** | Gemma2 9B | 9B | 极好 | 本地 | 低 | 极致精度、不在乎速度 |

**怎么选**（对照 [R53](R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) §7.D）：

- **中文 / 多语言、生产默认** → **bge-reranker-v2-m3**（无脑选）
- **要 API、不想自部署** → Cohere Rerank 3.5
- **延迟要求 < 100ms / 100 docs** → MiniLM-L6 蒸馏版（bge-reranker 蒸馏出来的小模型）
- **追求极致精度、可以慢** → bge-reranker-v2-gemma 9B

**优劣对比**：

| 路线 | 优势 | 劣势 |
|------|------|------|
| **bge-reranker-v2-m3**（568M XLM-RoBERTa） | 中文最强、免费、月下载 814 万验证可靠 | CPU 上 100 docs 要 2-3 秒、GPU 才能进生产 |
| **Cohere API** | 零运维、英文质量稳 | 中文相对弱、单价高、合规问题 |
| **MiniLM-6L 蒸馏版** | CPU 上 100 docs < 100ms | 质量比 bge-large 低 5-10% |

**关键认知**：Cross-Encoder 的"基座"主流就两条路——**XLM-RoBERTa（多语言之王）**和 **Gemma/Qwen 等 LLM 用作 Reranker（精度榜首但慢）**。看到 "bge-reranker-vXX-XX" 命名，前面的 vXX 是 BAAI 的版本号，后面的 XX 是基座（base/large/m3=XLM-R / gemma/qwen=LLM as Reranker）。

> Rerank 蒸馏（把 large 蒸成 6L 跑 CPU）的实操代码见 [R53](R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)。

---

### 2.4 微调框架与基座

**微调是干啥的**：让通用模型学到你公司的数据/口风/业务知识。但 **微调不是首选——优先 RAG，RAG 解决不了再微调**（[R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 反复强调的核心结论）。

#### 微调框架横评

| 框架 | 定位 | Stars | 适合 | 核心卖点 |
|------|------|-------|------|---------|
| **LLaMA-Factory** ⭐ | 零代码 WebUI | 70.6K | 学习者 / 快速验证 | **100+ 模型 Day-0 支持**、Gradio UI、硬件需求表清晰 |
| **Unsloth** ⭐ | 性能优化器 | 62.8K | 单卡 / 小团队 | **2× 速度，70% VRAM 节省**、免费 Colab 可跑 |
| **Axolotl** | YAML 驱动 | 11.7K | 研究 / 实验 | 配置即代码、多 GPU 友好 |
| **TRL**（HuggingFace） | 底层库 | 11K+ | 工程师 / 集成 | 官方 SFT/DPO/PPO/GRPO 标准实现 |
| **PEFT**（HuggingFace） | 底层库 | - | 被上述工具引用 | LoRA/QLoRA/DoRA/LoftQ 标准实现 |
| **verl**（字节） | 工业级 RL | 中 | 严肃 RL（671B 实战） | 大规模 RLHF/GRPO 唯一选择 |

**怎么选**：

- **第一次玩、想快速跑通** → **LLaMA-Factory**（WebUI 零代码）
- **单卡 4090 / 想极致省显存** → **Unsloth**（2× 速度、70% 显存省）
- **多卡集群、要可复现性** → Axolotl（YAML 配置）
- **要做 RL（GRPO/PPO）** → TRL（学习）/ verl（生产）

#### 微调方法横评（PEFT 家族）

| 方法 | VRAM 节省 | 效果差距 | 适合场景 |
|------|-----------|---------|---------|
| **全参 SFT** | 0% | baseline | 老师领域 / 数据 > 1M / 显存够 |
| **LoRA** | 70% | -1~2% | 标准选择 |
| **QLoRA** ⭐ | **90%** | -2~3% | **单卡跑大模型默认选** |
| **DoRA** | 同 LoRA | +1% | 想榨性能 |
| **LoftQ** | 同 QLoRA | +1~2% | QLoRA 升级版 |

**典型硬件门槛（QLoRA 4bit）**：
- 7B 模型 → **6GB 显存**（任何 GPU）
- 13B → 10GB（3060 12G 起）
- 30B → 24GB（4090 / 3090 单卡）
- 70B → 48GB（A100 / 双 4090）

#### 后训练方法演进（按学习顺序排）

| 方法 | 干啥 | 何时用 |
|------|------|--------|
| **SFT** | 模仿示范数据 | 教模型新格式/新领域知识、入门必学 |
| **DPO** ⭐ | 对齐人类偏好 | 替代 RLHF/PPO 的默认对齐方法（2024 已成主流） |
| **GRPO** | 强化推理能力 | DeepSeek-R1 同款、做推理模型必学 |
| **PPO** | 经典 RLHF | 已被 DPO 取代，除非要研究底层、否则跳过 |

**核心结论**（来自 [R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)）：**2026 年个人最优学习路径 = "SFT → LoRA → DPO → GRPO"，跳过 PPO 完全合理。**

#### 适合微调的开源基座（按规模分）

| 规模 | 推荐基座 | 理由 |
|------|---------|------|
| 0.5B-3B | Qwen2.5-1.5B / Llama 3.2-1B | 边缘 / 端侧 / 蒸馏老师选小模型 |
| 7B-8B | **Qwen2.5-7B / Llama 3.1-8B** ⭐ | 最经典甜点、社区资源最多 |
| 13B-14B | Qwen2.5-14B | 中文场景 |
| 30B-32B | Qwen2.5-32B / Mistral 22B | 单 4090/A100 极限 |
| 70B+ | Llama 3.3-70B / Qwen2.5-72B | 多卡或租云 |

> 完整训练成本表 + Chat Template 等避坑见 [R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)。

---

### 2.5 推理引擎

**推理引擎是干啥的**：把训练好的 LLM 高效跑起来。同样的模型 + 显卡，用对引擎吞吐能差 5-10 倍。

| 引擎 | 主战场 | Stars | 一句话定位 |
|------|--------|-------|-----------|
| **vLLM** ⭐ | 生产服务 | 36K+ | **综合第一**、PagedAttention 鼻祖 |
| **SGLang** | 极致吞吐 | 12K+ | **RadixAttention 前缀缓存王**、Agent 多轮场景神器 |
| **TensorRT-LLM** | NVIDIA 极限 | 中 | 榨干 NVIDIA GPU，配置复杂 |
| **llama.cpp** ⭐ | 本地 / CPU / 边缘 | 80K+ | **GGUF 格式王**、纯 C++ 跨平台 |
| **Ollama**（基于 llama.cpp） | 一行命令本地跑 | 130K+ | 个人电脑跑模型最简、`ollama run llama3` |
| **TGI** | (已归档) | - | **不要选** ⚠️ HF 已停止积极开发 |

**怎么选**（对照 [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)）：

- **本地玩 / Mac 跑 / 一行命令** → **Ollama**
- **生产 GPU 服务、综合最稳** → **vLLM**（无脑选）
- **多轮对话、Agent 场景、前缀复用率高** → **SGLang**（RadixAttention 命中可省 80% prefill）
- **NVIDIA H100 极限优化** → TensorRT-LLM
- **CPU/边缘** → llama.cpp + GGUF Q4_K_M

#### 量化格式速查

| 格式 | 位宽 | 适用 | 主流场景 |
|------|------|------|---------|
| **W4A16**（GPTQ/AWQ）⭐ | 权重 4bit、激活 16bit | vLLM/SGLang | **生产甜点**，吞吐高、效果损失 < 1% |
| **FP8** | 8bit 浮点 | TensorRT-LLM、vLLM 新版 | H100+ 专属、精度最接近 FP16 |
| **GGUF Q4_K_M** | 4bit 混合 | llama.cpp/Ollama | **本地 & 边缘首选** |
| **INT8** | 8bit 整数 | 各引擎 | 兼容性好但已被 W4A16 取代 |

> 5 引擎 × 8 维度对比 + 7B/14B/32B/72B 在不同量化档下的 GPU 选型表见 [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)。

---

### 2.6 LLM 基座（开源模型）

> 闭源 API（GPT-5 / Claude / Gemini）这里不展开——都很强、按预算选就行。下表只列**开源主流**，能下载下来自己跑的。

| 系列 | 厂商 | 规模 | 中文 | 推理能力 | 工具调用 | 主战场 |
|------|------|------|------|---------|---------|--------|
| **Qwen2.5 / 3** ⭐ | 阿里 | 0.5B-72B 全谱 | **极好** | 强 | 强 | **中文场景默认** |
| **Llama 3.1 / 3.3** ⭐ | Meta | 8B / 70B / 405B | 一般 | 强 | 强 | **英文场景标杆** |
| **DeepSeek V3 / R1** | DeepSeek | 671B MoE（激活 37B） | 极好 | **极强**（R1 是推理专家） | 强 | 推理任务 / API 极便宜 |
| **Mistral / Mixtral** | Mistral AI | 7B / 8x7B / 8x22B | 弱 | 中 | 强 | 欧洲技术圈、MoE 经典 |
| **Phi-3 / Phi-4** | Microsoft | 3.8B / 14B | 中 | 强（小模型推理强） | 中 | 端侧 / 教育领域 |
| **Gemma 2 / 3** | Google | 2B / 9B / 27B | 中 | 中 | 中 | Google 生态 |
| **Yi / GLM / Baichuan** | 国内厂商 | 各种 | 极好 | 中 | 中 | 国内合规 / 兜底备份 |

**怎么选**：

- **中文 Agent 第一选择** → **Qwen2.5 / Qwen3**（按能跑的最大尺寸选，7B/14B/32B 都行）
- **英文 / 国际化** → Llama 3.1-8B（甜点）/ Llama 3.3-70B（旗舰）
- **要推理能力（数学/代码）** → DeepSeek-R1（API 超便宜）或 R1-Distill-Qwen 系列
- **想省钱用 API** → DeepSeek-V3 API（< GPT-4o-mini 价格的 1/3）
- **端侧 / 手机 / 树莓派** → Phi-3-mini / Qwen2.5-1.5B

> 五家厂商横评（DeepSeek 工程创新最强）见 [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)。

---

### 2.7 Agent 编排框架

| 框架 | 派别 | Stars | 一句话定位 |
|------|------|-------|-----------|
| **LangGraph** ⭐ | 图编排派 | 29.2K | **事实标准**、多 Agent / 复杂状态首选 |
| **OpenAI Agents SDK** | 轻量 SDK | 中 | **单 Agent 起步最简**、官方钦点 |
| **Microsoft Agent Framework** | 图编排派 | 9.4K | AutoGen 接班人（AutoGen 已维护模式） |
| **CrewAI** | 角色编排派 | 27K+ | 多 Agent 协作、像组队打副本 |
| **Pydantic AI** | 轻量 SDK | 7K+ | 类型安全、Python 工程师友好 |
| **ADK**（Google） | 图编排派 | 中 | 五模式设计、Gemini 生态 |
| **Claude Agent SDK** | 黑盒 | 中 | 用 Claude Code 引擎、不开源但最强 |

**怎么选**（对照 [R45](R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md)）：

- **从零开始、单 Agent 任务** → **OpenAI SDK** 或 Pydantic AI（简单优先）
- **多 Agent / 复杂状态 / HITL** → **LangGraph**（无脑选）
- **想要"角色扮演"式协作** → CrewAI（市场/产品/工程组队那种）
- **黑盒最强、不在乎开源** → Claude Agent SDK
- **AutoGen 用户** → 迁移到 Microsoft Agent Framework

> 9 框架 × 12 维度对比矩阵见 [R45](R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) 和 [R27](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R27_ClaudeAgentSDK%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md)。

---

## 三、经典搭配套餐

> 把上述组件组合起来，2026 年市面上 90% 的 Agent 系统就是下面这 5 个套餐之一。

### 套餐 A：API 极简快速起步（适合 0→1 验证）

```
LangGraph 或 OpenAI SDK
   + OpenAI text-embedding-3-small ($0.02/1M)
   + Chroma（嵌入式向量库）
   + Cohere Rerank（API）
   + GPT-4o-mini 或 Claude 3.5 Haiku（API）
   + 不微调
   + Redis 做语义缓存
```

- **优势**：1 周可上线、无运维、按用量付费
- **劣势**：单价高、数据出境、长期成本爆炸
- **成本估算**：日均 1k 次查询，月成本 $50-200
- **适合**：MVP / Demo / 内部小工具

### 套餐 B：自托管中文标准栈（最常见的生产选择）

```
LangGraph
   + BGE-M3（本地 GPU）
   + Milvus 或 pgvector
   + bge-reranker-v2-m3
   + Qwen2.5-32B + vLLM + W4A16 量化
   + 微调（可选）：LLaMA-Factory + QLoRA
   + Redis 缓存 + LiteLLM 网关 + Langfuse 监控
```

- **优势**：数据不出境、长期成本低、可微调可控
- **劣势**：GPU 投入（至少 1 张 A10/4090）、运维复杂、上线周期 1-2 月
- **成本估算**：单机 4090 ≈ ¥15K + 电费，月运营成本 ¥500-2000
- **适合**：中文企业内部知识库 / 客服 / 合规要求高的场景

### 套餐 C：边缘 / 离线场景

```
单机 Python / Go
   + bge-small-zh-v1.5（CPU 即可）
   + SQLite / Chroma
   + MiniLM-6L 蒸馏 reranker（CPU < 100ms）
   + Qwen2.5-1.5B / Phi-3-mini + Ollama / llama.cpp（GGUF Q4）
   + 不微调（要也是 LoRA + 合并）
```

- **优势**：完全离线、隐私 100%、笔记本能跑
- **劣势**：模型小能力有限、复杂任务搞不定
- **适合**：手机 App / 政企内网 / IoT 设备

### 套餐 D：极致性能 / 高并发

```
LangGraph + 自研路由
   + GTE-Qwen2-7B（榜首 Embedding）
   + Milvus 集群
   + bge-reranker-v2-gemma 9B（精度优先）
   + Llama 3.3-70B + SGLang + RadixAttention + FP8（H100）
   + 微调：Axolotl + 多卡 / verl 做 GRPO
```

- **优势**：吞吐顶配、效果天花板
- **劣势**：基础设施投入巨大（多张 H100）、团队需要 5+ 工程师
- **成本**：起步 ¥100K+ 硬件，月运营 ¥10K+
- **适合**：日均百万级请求的 To C 产品

### 套餐 E：研究 / 教学（学习路线推荐）

```
单机 Colab 或 4090
   + LangGraph 或 OpenAI SDK（教学用）
   + BGE-M3 + Chroma（最简）
   + bge-reranker-base
   + Qwen2.5-7B + Ollama（本地跑）
   + LLaMA-Factory（点鼠标做微调实验）
```

- **目的**：用最低成本走完全流程，建立完整心智模型
- **学习路径**：先跑通 OpenAI SDK Hello World → 接 RAG → 加 Rerank → 试微调 → 换框架体验
- **关联**：完整 12 章学习路径见 `tutorial/` 目录、路线图见 [R54](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md)

---

## 四、决策树速查

```
我要建一个 Agent 系统...
│
├─ 用户提问需要查私有知识？
│   ├─ 是 → 上 RAG（套餐 A 或 B）
│   │   ├─ 数据出境合规无障碍 + 想快速验证 → 套餐 A
│   │   └─ 中文 / 合规 / 长期 → 套餐 B
│   └─ 否 → 直接调 LLM API 或 vLLM
│
├─ 模型不够准、回答风格不对？
│   ├─ 先试 Prompt 工程（[R55](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md)）
│   ├─ 再试 RAG 增强检索质量
│   ├─ 再试 Few-Shot
│   └─ 都不行才微调（默认 QLoRA + LLaMA-Factory）
│
├─ 检索召回不行？
│   ├─ 单纯向量不够 → 加 BM25 做混合检索（[R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)）
│   ├─ 召回多但精度低 → 加 Rerank（bge-reranker-v2-m3）
│   ├─ 文档质量本身差 → 改分块策略 / 加元数据
│   └─ 都不行 → 检查 Embedding 模型选错没
│
├─ 推理太慢 / 太贵？
│   ├─ API 路线 → 上 Prompt Cache（[R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)）+ 语义缓存（Redis）
│   ├─ 自托管 → 量化（W4A16）+ 换 vLLM/SGLang
│   ├─ Reranker 慢 → 换 v2-m3（不要 large）或蒸馏
│   └─ 都不行 → 用更小的模型 + 微调
│
└─ 多 Agent 协作 / 复杂状态？
    ├─ 单 Agent 多工具 → OpenAI SDK 够用
    ├─ 状态机式工作流 → LangGraph
    ├─ 角色扮演式协作 → CrewAI
    └─ 工业级长效守护 → 参考 [R36](R36_OpenClaw%E6%9E%B6%E6%9E%84%E8%B0%83%E7%A0%94%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%99%E4%B9%88%E7%81%AB.md) OpenClaw 范式
```

---

## 五、避坑指南

| 坑 | 症状 | 原因 | 解法 |
|----|------|------|------|
| **换 Embedding 模型** | 上线 3 个月后想换模型，发现整个向量库废了 | 不同模型向量空间不同，不能混用 | 第一次就选好（推 BGE-M3），**绑定版本号** |
| **维度选太大** | 向量库存储 / 检索都慢 | 3072 维比 1024 维占 3 倍空间 | OpenAI 用 `dimensions=1024` 截断、BGE 用 1024 默认 |
| **query/doc 不区分** | 召回率低 | 用户 query 短、doc 长，应该用不同 prefix | BGE 用 `encode_queries` 和 `encode_corpus` 分开调用 |
| **不做 Rerank** | LLM 看到的 Top-5 有噪声 | 向量检索精度有限 | 召回 50-100 → Rerank → Top-5（[R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)）|
| **Cross-Encoder 用错型号** | Rerank 100 docs 要 3 秒 | 用了 large 而不是 v2-m3 | 中文用 v2-m3、要更快蒸成 6L |
| **微调直接全参 SFT** | 单卡 4090 爆显存 | 7B 全参要 80GB+ | 默认上 QLoRA，效果差 < 2% |
| **Chat Template 没对** | 微调完输出乱码 / 不停 | 训练和推理用了不同模板 | LLaMA-Factory 强制校验、Hugging Face 用 `apply_chat_template` |
| **微调学习率太大** | 灾难性遗忘 | 沿用了预训练学习率 | SFT 全参 2e-5、LoRA 1e-4 起步 |
| **推理不量化** | 显存翻倍、吞吐减半 | 直接用 FP16 上线 | 默认 W4A16（GPTQ/AWQ），效果差 < 1% |
| **选了 TGI** | 部署后发现没人维护 | HuggingFace 已归档 | 换 vLLM 或 SGLang |
| **Redis 当主向量库** | 数据涨到 500 万条内存爆炸 | Redis 全数据驻内存 | 超过 100 万条规划迁 Milvus/pgvector |
| **微调当 RAG 用** | 灌了 100GB 知识进模型，召回率反而下降 | SFT 改不了知识上限（[R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) 核心结论） | 知识用 RAG、风格/格式才用 SFT |
| **Top-K 取太大** | LLM 上下文塞满垃圾，回答质量下降 | "多多益善"思维错了 | Rerank 后取 Top-3-5 足够、Lost-in-the-Middle 是真的 |

---

## 六、关联阅读地图

> 本报告是"组件汇总速查"。每个组件深度内容在以下专题报告：

| 想深挖什么 | 跳转到 |
|----------|--------|
| RAG 完整流程 + Embedding 选型陷阱 + 分块策略 | [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) RAG 从入门到生产落地 |
| 7 个向量库 × 8 维度横评 + Redis 应用模式 | [R47](R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) Redis 在 Agent 中的应用与替代方案 |
| 微调框架 + 方法 + 硬件门槛 + DPO/GRPO | [R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 模型训练与微调技术全景 |
| Rerank 蒸馏 + Cross-Encoder 工程化 | [R53](R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 模型蒸馏技术全景 |
| 推理引擎 + 量化格式 + GPU 选型 | [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) LLM 推理部署工程指南 |
| KV Cache + FlashAttention + 投机解码 | [R59](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) LLM 推理优化技术 |
| 服务化 / 监控 / 网关 / SLA / 成本 | [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) LLM 服务化生产部署 |
| Agent 框架横评（LangGraph/CrewAI/...） | [R45](R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) 现代智能体编排框架深度调研 |
| LangChain/LangGraph 入门到实战 | [R27](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R27_ClaudeAgentSDK%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md) LangChain 与 LangGraph |
| 完整 LLM 学习路线 | [R54](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md) LLM 从业者学习路线总览 |
| Prompt 工程系统化方法 | [R55](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) Prompt Engineering 系统化调研 |
| 预训练 / 数据墙 / Scaling Law | [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) LLM 预训练全景 |

> **核心阅读路径建议**：
> - **新手入门** → 本报告（R65）→ [R54](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md) 路线图 → 跟着 `tutorial/` 一章一章跑
> - **选型决策** → 本报告 → 对应组件深度报告 → 决策
> - **遇到具体坑** → 直接查本报告 §五 避坑表 → 跳到对应深度报告

---

## 📌 来源清单

> 本报告**不引入新外部信息**，是对工作区已有报告的横向汇总。所有数据来源标注如下：

| 信息块 | 来源报告 | 数据日期 |
|--------|---------|---------|
| Embedding 模型对比表 | [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) §6.2 | 2026-04 |
| 向量数据库对比表 | [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) §7.3 + [R47](R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §3.1 | 2026-04 |
| Rerank 模型 + 蒸馏数据 | [R53](R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) §7.D + 月下载量来自 HuggingFace | 2026-04 |
| 微调框架横评 + Stars | [R52](R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) §2.1 | 2026-04 |
| 推理引擎横评 | [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) | 2026-04 |
| Agent 框架横评 | [R45](R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) + [R27](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R27_ClaudeAgentSDK%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md) | 2026-04 |
| LLM 基座对比 | [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) + [R54](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md) | 2026-04 |

⚖️ **来源一致性**：本报告作为汇总报告，与各原始报告的数据保持一致；如发现矛盾，以原报告（更深度）为准。
📅 **时效性声明**：信息汇总于 2026-04-25，原始报告 2026-04 期间陆续完成。
🎯 **本报告的诚实声明**：因为是"汇总性"报告，**不涉及新的实验或一手数据**——它的价值在"地图"和"速查表"，不在"新发现"。如果你已经读完上面 7 篇深度报告，这份速查表对你的边际价值有限；如果你还没读过任何一篇，这份是最好的入口。
