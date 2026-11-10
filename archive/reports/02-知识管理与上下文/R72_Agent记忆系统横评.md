---
title: Agent 记忆系统横评：Mem0 / Letta / Zep / LangMem / 自建五家对比
aliases: [R72, Agent记忆系统横评, 记忆框架对比]
report_id: R72
category: 知识管理与上下文
prev_path: reports/02-知识管理与上下文/R72_Agent记忆系统横评.md
status: completed
tags: [memory, agent, mem0, letta, memgpt, zep, langmem, comparison]
date: 2026-04-25
tokens: 15000
related:
  - "[R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)"
  - "[R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)"
  - "[R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)"
  - "[R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md)"
  - "[R48](R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Agent 记忆系统横评：Mem0 / Letta / Zep / LangMem / 自建五家对比

> **一句话概括**：2025-2026 年 Agent 记忆赛道已从「VectorStore + 时间戳」初级形态分化为四个流派——**事实抽取派 (Mem0) / 自我编辑派 (Letta-MemGPT) / 时序图谱派 (Zep) / Store 原语派 (LangMem)**，加上「Redis + Embedding + Recency 自建」第五条路。选型铁律：**会话短 + 单 Agent → LangMem；多用户长记忆 + 不想自运维 → Mem0 Cloud；状态化角色扮演 + Agent 自我学习 → Letta；事实关系频繁演变（CRM/医疗/客服）→ Zep；< 1 万用户、想完全可控 → 自建 Redis 方案**。
>
> **研究日期**：2026-04-25
> **研究类型**：学习向调研（双轨并行：定位透镜 + 五家技术拆解 + 五段 Hello World + 自建 200 行最小实现）
> **增量价值**：在 [R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)（Copilot 五层指令记忆）和 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)（Redis 六大应用模式）基础上，**首次系统横评 Agent 专用记忆框架**，把 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §六.D 一句带过的 Mem0/Letta 展开成产品级选型指南；填补"记忆系统专题"知识空白
> **关联报告**：[R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)（Copilot 全局记忆架构 — 分层指令记忆范式）、[R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)（Redis 在 Agent 中的应用 — 自建路线技术底座）、[R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)（RAG 从入门到生产 — 检索技术骨架）、[R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md)（长效 AgentHarness 工程化 — 长会话场景）、[R48](R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md)（Agent 知识工程全景）

---

## TL;DR 速查卡

**30 秒结论**：

- 🥇 **不想造轮子、要最快上线** → **Mem0**（54k⭐，managed cloud + 自托管 OSS 双轨；2026-04 新算法在 LongMemEval 拿到 93.4 分，比上版 +26 分）
- 🥈 **想要"会自己写小作文"的 stateful 角色 Agent** → **Letta**（formerly MemGPT，22.3k⭐；memory_blocks + archival + sleep-time agents；学术血统 UC Berkeley）
- 🥉 **业务事实会随时间演变（如客户续费状态、医疗诊断更新）** → **Zep**（4.5k⭐；Graphiti 时序知识图谱；fact invalidation；< 200ms p95；**注意 Community Edition 已弃用，仅剩 Cloud**）
- 🎯 **已经在 LangGraph 生态、要 vendor-neutral 原语** → **LangMem**（1.4k⭐，MIT；BaseStore API；hot-path tool vs background manager 双模式）
- 🔧 **< 1 万用户 / 内网部署 / 完全可控** → **自建 Redis + Embedding + Recency 加权**（200 行 Python 起步，参考 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §二.C）

**关键数字**：

| 框架      | Stars | License             | 部署形态                 | 核心抽象                             | 学术依据                    |
| ------- | ----- | ------------------- | -------------------- | -------------------------------- | ----------------------- |
| Mem0    | 54.0k | Apache 2.0          | OSS + Cloud          | User/Session/Agent 三类记忆          | arXiv:2504.19413 (2025) |
| Letta   | 22.3k | Apache 2.0          | OSS + Cloud          | Memory Blocks + Archival         | MemGPT NeurIPS'23       |
| Zep     | 4.5k  | Apache 2.0 (legacy) | **仅 Cloud**（OSS 已弃用） | Knowledge Graph + Temporal Facts | Graphiti 论文 2024        |
| LangMem | 1.4k  | MIT                 | Library              | LangGraph BaseStore + Tools      | LangChain 系（无独立论文）      |
| 自建      | —     | 自定                  | 自托管                  | Redis + Embedding + Recency      | 工程实践                    |

**一句话推荐表**：

| 你的场景 | 选这个 |
|---------|------|
| 客服机器人 / SaaS 产品个性化 | Mem0 Cloud |
| 角色扮演 / 个人助理 / 长任务 Agent | Letta |
| 数据频繁变更的业务（CRM / 医疗 / 法务）| Zep |
| 已用 LangGraph，想轻量集成 | LangMem |
| 国产化 / 数据合规要求高 / 要省钱 | 自建（Redis + 国产 Embedding）|
| 不需要持久记忆，对话 < 20 轮 | **不要用任何记忆系统，直接塞 ChatHistory** |

---

## 目录

1. [🔭 定位透镜：从 Buffer 到 Knowledge Graph 的演化](#-定位透镜从-buffer-到-knowledge-graph-的演化)
2. [📚 研究分析](#-研究分析)
   - 2.1 记忆三层模型：Working / Episodic / Semantic
   - 2.2 五家横评矩阵
   - 2.3 关键能力对比表
   - 2.4 与已有报告交叉引用
3. [🚀 上手实战](#-上手实战)
   - 3.1 五家各自的 Hello World（同段对话喂入对比）
   - 3.2 自建最小记忆系统（≈200 行）
4. [🕳️ 避坑指南](#-避坑指南)
5. [💰 成本速算](#-成本速算)
6. [🎯 决策速查](#-决策速查)
7. [📌 来源清单](#-来源清单)

---

## 🔭 定位透镜：从 Buffer 到 Knowledge Graph 的演化

### 纵轴 · 演化脉络（"Agent 记忆是怎么走到今天的"）

```
2022 ───  LangChain ConversationBufferMemory（朴素拼接 chat_history）
  │       └─ 痛点：超 token 就崩，无任何"提炼"
  │
2023.01 ─ ConversationSummaryMemory / VectorStoreRetrieverMemory
  │       └─ 用 LLM 总结 + 向量检索补救，但策略硬编码
  │
2023.10 ─ MemGPT 论文 (UC Berkeley, Packer et al., NeurIPS'23) 🌟
  │       └─ 关键转折：第一次把记忆当"操作系统的虚拟内存"管理
  │          引入 main_context (RAM) + archival_storage (Disk) + 自我编辑工具
  │
2024.Q1 ─ Mem0 v0 发布（YC S24）
  │       └─ 商业化路线：把"自动事实抽取 + 三类记忆"做成 SaaS
  │
2024.Q2 ─ Zep 引入 Graphiti（temporal knowledge graph）
  │       └─ 从 chat-summary 转向"事实级别的关系图 + 时间戳"
  │
2024.Q4 ─ MemGPT 重新品牌化为 Letta
  │       └─ 从「记忆是核心」扩展为「stateful agent 平台」
  │
2025.01 ─ LangMem 发布 (LangChain-AI)
  │       └─ 不做"框架"，做"原语"——和 LangGraph BaseStore 深度绑定
  │
2025.04 ─ Mem0 v3 算法：single-pass ADD-only + entity linking + 多信号检索
          └─ 在 LongMemEval 跑到 93.4，确立"自动抽取 + 多信号融合"主流派
```

**生命周期判断**：

- ⚠️ **赛道还在快速演化**——2025 年至少 3 篇里程碑论文（Mem0 / MemoryBank / A-MEM）；不要押注"五年不变"
- ✅ **基础抽象已收敛**：「事实抽取 + 检索 + 遗忘策略」三件套是大家共识，差异在实现路线
- 🔮 **下一波趋势**：① 多模态记忆（图像/语音/视频片段）② 记忆共享/联邦（多 Agent 间）③ 主动遗忘（dropout-style）

### 横轴 · 竞争格局（"五家在江湖中的位置"）

```
                  ┌─────────────────────────────────────────────────┐
                  │                  设计哲学坐标系                   │
                  └─────────────────────────────────────────────────┘
   高
   ↑
"自动化"     ┌──────────────┐                ┌──────────────┐
（Agent      │   Mem0       │                │   Zep         │
 不用关心    │ 自动事实抽取  │                │ 自动构图      │
 怎么存/找）│ 三类记忆     │                │ 时序图谱      │
            └──────────────┘                └──────────────┘

            ┌──────────────┐
            │   Letta      │
            │ 半自动+      │
            │ Agent自我编辑 │
            └──────────────┘

                              ┌──────────────┐    ┌──────────────┐
                              │   LangMem    │    │   自建 Redis  │
                              │ 显式 tool    │    │ 完全手写      │
                              │ 由 Agent 决定 │    │              │
                              └──────────────┘    └──────────────┘
   ↓
"控制力"   ←─────────────────────────────────────────────────→
（你完全               中                              高
 决定每一步）
```

**设计哲学差异**（不比功能清单，比"为什么各自走了不同的路"）：

| 流派 | 代表 | 核心信念 | 适合什么人 |
|------|-----|---------|---------|
| **事实抽取派** | Mem0 | "记忆 = 一组小事实，自动抽自动存" | 不想关心存储细节、要快速上线的 SaaS 团队 |
| **自我编辑派** | Letta (MemGPT) | "Agent 应该像人一样自己决定记什么、改什么" | 想做 stateful 角色扮演 / 长任务执行的研究者 |
| **时序图谱派** | Zep | "记忆的本质是关系网，且关系会随时间变化" | 业务事实复杂、关系频繁演变的企业（CRM/医疗）|
| **Store 原语派** | LangMem | "不要给我框架，给我 read/write/search 三个原语" | 已在 LangGraph 生态、想保持架构一致性的 LangChain 用户 |
| **手写派** | 自建 Redis | "我的场景很简单，框架抽象都是负担" | 数据合规严苛 / 内网部署 / < 1 万用户的小团队 |

### 交叉判断（独立结论，不是"大家都在用所以选谁"）

1. **Mem0 是当前赛道流量第一**（54k⭐、YC S24、商业化最成熟），但**它有 vendor lock-in 风险**——OSS 版本与 Cloud 版本特性差距持续拉大（dashboard / 高级功能仅 Cloud）
2. **Letta 在"Agent 自学习"方向独一档**——sleep-time agents（Agent 在用户离线时自己整理记忆）+ MemFS（git-tracked memory）是其它家没有的
3. **Zep 押对了"知识图谱"方向**，但**Community Edition 已正式弃用**（2025 年），现在是纯商业产品——选 Zep = 选 Cloud，要做好预算
4. **LangMem 不是"框架"而是"装在 LangGraph 里的工具组"**——独立用价值有限，但如果你已经 all-in LangGraph，加它几乎零成本（参考 [R26](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R26_LangChain%E4%B8%8ELangGraph%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md) LangChain/LangGraph 入门）
5. **自建路线被严重低估**：< 1 万用户 + 简单场景下，Redis + 文本 embedding + 简单 recency 加权打 60 分，**而上面四家给你 80 分但要付 5-20× 的运维/订阅成本**

> 💡 **诚实的不确定性**：本横评数据采集于 2026-04-25。Mem0 的 LoCoMo / LongMemEval 分数来自其官方 GitHub README（2026-04 算法升级），未独立复现；Zep 的 < 200ms 延迟来自 getzep.com 官方声明，未压测验证。这些数字仅作"量级参考"，不要作为合同 SLA 引用。

---

## 📚 研究分析

### 2.1 记忆三层模型：Working / Episodic / Semantic

> **类比**：这套分层直接抄自认知心理学（Tulving, 1972）。如果你修过心理学课，跳过这段；如果没有，3 分钟读一下，整篇报告会清晰很多。

```
┌──────────────────────────────────────────────────────────┐
│  Working Memory（工作记忆）                                │
│  ─ 当前对话窗口里的内容（几分钟到几小时）                    │
│  ─ 实现：直接放在 LLM context window                       │
│  ─ 例子：用户刚才说"我要订上海到北京的票"                   │
│                                                          │
│  ↓（什么值得"沉下去"成为长期记忆？）                       │
│                                                          │
│  Episodic Memory（情景记忆）                               │
│  ─ 具体事件 + 时间戳（"什么时候发生了什么"）               │
│  ─ 实现：带 metadata 的向量库（content + timestamp）       │
│  ─ 例子：2026-04-23 用户订了一张机票                       │
│                                                          │
│  ↓（多次情景中能否抽象出规律？）                            │
│                                                          │
│  Semantic Memory（语义记忆）                               │
│  ─ 抽象事实 / 规则 / 偏好（"是什么"）                       │
│  ─ 实现：结构化事实库（user_prefers_aisle_seat=true）      │
│  ─ 例子：用户偏好靠过道的座位                              │
└──────────────────────────────────────────────────────────┘
```

**五家对这三层的处理**：

| 层级 | Mem0 | Letta | Zep | LangMem | 自建 Redis |
|------|------|-------|-----|---------|----------|
| Working | 框架不管，靠 context window | core memory blocks（human/persona）| Context Block 自动注入 | 短期靠 LangGraph state | 自己拼 prompt |
| Episodic | 自动抽取，存到 user/session memory | archival storage | 自动建图谱节点 + edge | manage_memory_tool 显式调用 | Redis Stream 或 ZSET |
| Semantic | entity linking + 多信号融合 | 由 Agent 自我编辑总结 | 节点属性 + 关系类型 | 用户用 Pydantic schema 定义 | 自己写抽取 prompt |

**关键洞见**：**Mem0 和 Zep 把 Episodic→Semantic 自动化了，Letta 让 Agent 自己做这件事，LangMem 把决定权交给 Agent 工具调用**。这是流派分化的根源。

### 2.2 五家横评矩阵

#### A. Mem0：自动事实提取 + 三类记忆

**核心抽象**：

```python
# 三类记忆 namespace
memory.add(messages, user_id="alice")       # User: 跨会话稳定的用户事实
memory.add(messages, run_id="session-42")   # Session: 单会话内的临时事实
memory.add(messages, agent_id="travel-bot") # Agent: Agent 自己的状态
```

**架构图**：

```
┌──────────────┐
│ 对话流入     │
│ messages[]   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Fact Extraction Layer                │
│ ─ LLM Call 1: 抽取候选事实           │
│ ─ Single-pass ADD-only (v3 算法)     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Storage Layer                        │
│ ─ Vector Store (Qdrant/Chroma 等)    │
│ ─ Entity Index（实体表）             │
│ ─ BM25 Keyword Index                 │
└──────┬───────────────────────────────┘
       │（检索时）
       ▼
┌──────────────────────────────────────┐
│ Multi-Signal Retrieval (v3 新增)     │
│ ─ Semantic (cosine)  ┐               │
│ ─ BM25 (keyword)     ├─ Score Fusion │
│ ─ Entity Match       ┘               │
└──────────────────────────────────────┘
```

**v3 算法（2026-04 发布）核心变化**：

| 维度 | v2 | v3 |
|------|----|----|
| 抽取策略 | ADD/UPDATE/DELETE 多阶段 | **Single-pass ADD-only**（不删不改，只追加）|
| 检索 | 纯 semantic | **Semantic + BM25 + Entity 三路融合** |
| LongMemEval 分数 | 67.8 | **93.4**（+26 分）|
| LoCoMo 分数 | 71.4 | **91.6**（+20 分）|
| 单次延迟 | 7.0K tokens / 0.88s | 6.8K tokens / 1.09s（略增）|

**优势**：
- ✅ **学习曲线最低**：5 行代码起步
- ✅ **OSS + Cloud 双轨**，可平滑过渡
- ✅ **多 LLM 支持**：OpenAI / Anthropic / 国产模型 / 本地 Ollama
- ✅ **生态最活跃**：54k⭐、~313 contributors、月度发版

**短板**：
- ❌ **每次 add 都要调 LLM**（成本敏感场景下要警惕，见 §5）
- ❌ OSS 版本与 Cloud 版本特性鸿沟在拉大
- ❌ 抽取 prompt 是黑盒，定制需改源码

#### B. Letta（formerly MemGPT）：分层记忆 + 自我编辑

**核心抽象**：`memory_blocks` 是 first-class citizen。

```python
agent_state = client.agents.create(
    model="openai/gpt-5.2",
    memory_blocks=[
        {"label": "human",   "value": "Name: Alice. Likes: 历史小说"},
        {"label": "persona", "value": "I am a literary assistant."},
    ],
)
# Agent 在对话中自己调 core_memory_replace / core_memory_append 工具
# 长出来的细节 → archival_storage（无限大向量库）
```

**架构图**（直接对应 MemGPT 论文）：

```
┌─────────────────────────────────────────┐
│  Main Context (≈ RAM)                   │
│  ┌────────────────────────────────────┐ │
│  │ System Instructions (固定)          │ │
│  │ Core Memory (human + persona)       │ │
│  │   ↑↓ Agent 自己调工具修改           │ │
│  │ FIFO Recent Messages                │ │
│  └────────────────────────────────────┘ │
└──────┬──────────────────────────────────┘
       │ 溢出 / 主动归档
       ▼
┌─────────────────────────────────────────┐
│  External Context (≈ Disk)              │
│  ─ Recall Storage（旧消息检索）         │
│  ─ Archival Storage（向量库）           │
│  ─ MemFS（git-tracked，2025 新增）      │
└─────────────────────────────────────────┘
```

**独家特性**：

1. **Sleep-time Agents**：用户离线时，Agent 自己跑后台任务整理记忆（业内首创）
2. **MemFS**：把记忆当文件系统管理，每次修改有 git diff，可回滚
3. **AgentFile (.af)**：把整个 Agent 状态序列化为单文件，跨平台迁移

**优势**：
- ✅ **学术血统硬**（NeurIPS'23 论文）
- ✅ **状态可序列化**，做角色扮演 / 长期任务的天然选择
- ✅ **Agent 自我编辑** — 不像 Mem0 那样"被动被抽取"

**短板**：
- ❌ **学习曲线陡**：要理解 memory blocks / archival / recall 三层
- ❌ Agent 的工具调用次数显著增加（→ Token 成本上去）
- ❌ Python 99.5%，TypeScript 支持不如 Mem0

#### C. Zep：知识图谱 + 时序事实

**核心抽象**：用户的所有交互 → 一张随时间演化的知识图谱。

```
节点（Node）：实体
  ─ 类型：User / Person / Place / Event / 自定义...
边（Edge）：事实
  ─ 例：(Alice) --likes--> (Sci-Fi)
  ─ valid_at:    2025-03-12   ← 事实何时成立
  ─ invalid_at:  2026-01-08   ← 事实何时失效（Fact Invalidation）
```

**Fact Invalidation 实战例子**（这是 Zep 真正的杀手锏）：

```
2025-03-12  user: "我最喜欢科幻小说"
            → Edge:  (Alice) --likes--> (Sci-Fi)
                     valid_at = 2025-03-12

2026-01-08  user: "现在我更喜欢历史类"
            → Zep 自动:
              ① Edge1.invalid_at = 2026-01-08
              ② 新建 Edge2: (Alice) --likes--> (History)
                  valid_at = 2026-01-08

2026-04-25  你查询"Alice 喜欢什么":
            → Zep 只返回 valid 的事实: Alice likes History
            → 但保留历史: 之前喜欢过 Sci-Fi（这点比 Mem0 强）
```

**架构图**：

```
对话/业务事件 ──→ Graphiti Pipeline ──→ Knowledge Graph
                  ┌────────────────┐    ┌──────────────┐
                  │ 1. Entity ER   │    │  Nodes       │
                  │ 2. Relation    │    │  Edges       │
                  │    Extract     │    │   ├ valid_at │
                  │ 3. Conflict    │    │   └invalid_at│
                  │    Resolution  │    └──────────────┘
                  └────────────────┘            │
                                                ▼
                                       ┌──────────────┐
                                       │ Context Block│
                                       │ 拼好的 prompt │
                                       │（< 200ms p95）│
                                       └──────────────┘
```

**优势**：
- ✅ **时序处理是行业最强**——valid_at / invalid_at 是其它家没有的
- ✅ **关系-aware 检索**：可以查"Alice 的同事的偏好"这种二跳问题
- ✅ **延迟低**（官方声明 < 200ms p95，但需自行验证）

**短板**：
- 🚨 **Community Edition 2025 年正式弃用**——OSS 路线断了，**只能用 Cloud**
- ❌ 学习曲线最陡：要理解图谱建模、自定义 ontology
- ❌ 价格不透明（按节点/边计费），小团队压力大

#### D. LangMem：LangGraph 原生 + Store API

**核心抽象**：不做记忆框架，做"装在 LangGraph 里的工具"。

```python
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

# Store 是 LangGraph 原生抽象
store = InMemoryStore(index={"dims": 1536, "embed": "openai:text-embedding-3-small"})

# 把记忆操作做成 Agent 工具
tools = [
    create_manage_memory_tool(namespace=("memories",)),  # add/update/delete
    create_search_memory_tool(namespace=("memories",)),  # search
]
agent = create_react_agent("anthropic:claude-3-5-sonnet", tools=tools, store=store)
```

**两种工作模式**（这是 LangMem 文档的核心区分）：

| 模式 | 何时记忆 | 由谁触发 | 优缺点 |
|------|---------|---------|------|
| **Hot Path**（热路径）| 对话进行时 | Agent 主动调工具 | ✅ 实时；❌ 增加每轮 Token |
| **Background Manager** | 对话结束后批处理 | 后台任务 | ✅ 不影响对话延迟；❌ 复杂度高 |

**优势**：
- ✅ **MIT License**（五家中最宽松）
- ✅ 与 LangGraph Platform 零摩擦集成
- ✅ "原语而非框架"——你完全控制何时记忆、记什么
- ✅ 支持 Pydantic schema 定义 semantic memory 结构

**短板**：
- ❌ **强依赖 LangGraph 生态**——不是 LangChain 用户慎入
- ❌ 1.4k⭐，社区比 Mem0 小一个数量级
- ❌ 没有现成的"事实抽取" pipeline，要自己写

#### E. 自建：Redis + Embedding + Recency 加权

**何时该自建**（参考 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)：Redis 在 Agent 中的应用）：

- 用户量 < 1 万，记忆条数 < 100 万
- 数据合规要求严格（医疗/金融），记忆不能出本地
- 已有 Redis 基础设施，运维路径熟悉
- 场景明确，不需要"通用智能记忆"

**最小架构**：

```
┌────────────────────────────────────────────┐
│  Application Layer                         │
│  ─ extract_facts(messages) → List[fact]   │
│  ─ retrieve(query, user_id) → top-K facts │
└──────┬─────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────┐
│  Redis Stack                               │
│  ┌──────────────────────────────────────┐ │
│  │ HASH  user:{uid}:fact:{fid}          │ │
│  │   ├ content                          │ │
│  │   ├ embedding (binary, 1536 floats)  │ │
│  │   ├ timestamp                        │ │
│  │   └ access_count                     │ │
│  ├──────────────────────────────────────┤ │
│  │ FT.SEARCH (RediSearch + 向量索引)    │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

**评分公式**（合并 semantic + recency）：

$$
\text{score}(f) = \alpha \cdot \cos(\vec{q}, \vec{f}) + \beta \cdot e^{-\lambda \cdot \Delta t} + \gamma \cdot \log(1 + \text{access\_count})
$$

经验值：$\alpha=0.7, \beta=0.2, \gamma=0.1$，$\lambda$ 取 1/(7\*86400)（半衰期 7 天）。

**优缺点**：

| 维度 | 自建 | 框架 |
|------|------|------|
| 启动成本 | 200 行 Python | `pip install` 一行 |
| 运行成本 | 极低（仅 Redis + Embedding API）| 中等（含框架调度 LLM）|
| 灵活性 | 完全可控 | 受限于框架 |
| 演化成本 | 你自己重写 | 跟着上游升级 |
| 适合规模 | < 10 万用户 | 10 万以上 |

### 2.3 关键能力对比表

| 能力 | Mem0 | Letta | Zep | LangMem | 自建 Redis |
|------|------|-------|-----|---------|----------|
| **自动事实提取** | ✅ 强（v3 single-pass）| ⚠️ 半自动（Agent 主动调工具）| ✅ 强（自动建图谱）| ❌ 需 Agent 显式调用 | 🔧 自己写 prompt |
| **语义检索** | ✅ Multi-signal（sem+BM25+entity）| ✅ archival storage | ✅ Graph traversal | ✅ vector | ✅ FT.SEARCH |
| **时序处理** | ⚠️ 仅 timestamp | ⚠️ FIFO + recall | ✅✅ valid_at/invalid_at | ⚠️ metadata | 🔧 自己实现 |
| **冲突解决** | v3 接受冲突共存 | Agent 自己用工具改 | ✅ 自动 invalidate | ❌ 无 | 🔧 自己实现 |
| **遗忘策略** | UPDATE/DELETE API | archive | invalidation 不删 | tool 调用删 | TTL / LRU |
| **多模态** | ❌ 仅文本 | ❌ 仅文本 | ⚠️ 有限（实验中）| ❌ 仅文本 | 🔧 可扩展 |
| **多 Agent 共享** | ✅ 跨 agent_id | ⚠️ 需 AgentFile 导出 | ✅ 共享图谱 | ✅ 共享 store | 🔧 共享 Redis 实例 |
| **可观测性** | Cloud Dashboard | Letta Dashboard | Cloud Dashboard | LangSmith 集成 | 🔧 自建 |
| **私有化部署** | ✅ Docker Compose | ✅ Docker | ❌ Cloud only | ✅ 纯库 | ✅ 完全可控 |

> **图例**：✅ 原生强支持 / ⚠️ 部分支持 / ❌ 不支持 / 🔧 需自己实现

### 2.4 与已有报告交叉引用

| 已有报告 | 关联点 | 本报告新增的部分 |
|---------|-------|---------------|
| [R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md) Copilot 全局记忆架构 | "分层指令 + 三层运行时记忆"是另一种记忆范式 | 本报告聚焦"Agent 框架级记忆"，与 R19 的"IDE/CLI 级指令记忆"互补 |
| [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) Redis 在 Agent 中的应用 | §六.D 一句带过 Mem0/Letta | 本报告把 §2.2 和 §3.2 完整展开，是 R47 §六的"深入版" |
| [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) RAG 从入门到生产 | 检索技术（embedding + ANN）是记忆系统的底座 | 本报告的"自建" §2.2.E 直接复用 R30 的 embedding 选型结论 |
| [R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) 长效 AgentHarness 工程化 | "长会话场景"是记忆系统的核心战场 | 本报告 §6 决策速查给出"长任务场景应选 Letta"的明确推荐 |
| [R48](R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md) Agent 知识工程全景 | 知识 vs 记忆边界讨论 | 本报告补充："记忆是用户/会话级的、知识是组织/全局级的" |

**新确立的范式**（建议添加到 KNOWLEDGE_INDEX §三）：

- **P-Mem-1：记忆三层模型（Working/Episodic/Semantic）** — 直接借鉴认知心理学，五家框架都用此分层，已成行业共识
- **P-Mem-2：Hot Path vs Background Manager 二元工作模式** — LangMem 提出后被业界广泛采用，决定了记忆系统的延迟/成本权衡
- **P-Mem-3：Fact Invalidation 而非 Fact Deletion** — Zep 提出的"事实失效但不删除"范式，对审计/可追溯场景至关重要

---

## 🚀 上手实战

### 3.1 五家各自的 Hello World（同段对话喂入）

**测试对话**（喂给五家做对比）：

```
[Turn 1] user: "你好，我叫 Alice，住在上海，是一名软件工程师。"
[Turn 2] user: "我喜欢科幻小说，最喜欢刘慈欣的《三体》。"
[Turn 3] user: "对了，我现在搬到北京了。"
[Turn 4] user: "我现在更喜欢历史类的书了。"

[查询] "Alice 住在哪？喜欢什么书？"
```

**期望理想答案**：住在北京（不是上海，事实更新）；喜欢历史类（保留"曾经喜欢科幻"为 invalid 事实）。

#### Hello World A：Mem0

```python
# pip install mem0ai
import os
from mem0 import Memory

os.environ["OPENAI_API_KEY"] = "sk-..."
memory = Memory()  # 默认用 OpenAI text-embedding-3-small + gpt-5-mini

uid = "alice"
turns = [
    "你好，我叫 Alice，住在上海，是一名软件工程师。",
    "我喜欢科幻小说，最喜欢刘慈欣的《三体》。",
    "对了，我现在搬到北京了。",
    "我现在更喜欢历史类的书了。",
]
for t in turns:
    memory.add([{"role": "user", "content": t}], user_id=uid)

# 查询
results = memory.search(query="Alice 住在哪？喜欢什么书？", user_id=uid, limit=5)
for r in results["results"]:
    print(f"- {r['memory']}")

# 期望输出（具体行可能略有不同）：
# - User lives in Beijing
# - User prefers history books
# - User is a software engineer
# - User likes Liu Cixin's Three-Body Problem (older fact)
```

**注意点**：v3 算法是 **ADD-only**——"上海"和"北京"会**共存**，靠检索分数排序（北京时间戳更新，分数更高）。如果你需要严格"事实失效"，请用 Zep。

#### Hello World B：Letta（MemGPT）

```python
# pip install letta-client
from letta_client import Letta
import os

client = Letta(api_key=os.getenv("LETTA_API_KEY"))

agent = client.agents.create(
    model="openai/gpt-5.2",
    memory_blocks=[
        {"label": "human",   "value": "Unknown user."},
        {"label": "persona", "value": "I am a helpful assistant who remembers users."},
    ],
)

for t in turns:
    client.agents.messages.create(agent_id=agent.id, input=t)
    # Agent 会自己调 core_memory_replace / archival_memory_insert

# 查询
resp = client.agents.messages.create(agent_id=agent.id, input="我住在哪？喜欢什么书？")
for m in resp.messages:
    print(m)

# 关键观察：
#  ─ "human" block 会被 Agent 自己改写成: "Name: Alice. Lives in Beijing. SW Engineer. Likes history books."
#  ─ archival_storage 里保存了"曾经住上海""曾喜欢科幻"的历史
```

**注意点**：Letta 每次对话都可能消耗 5-10 倍 Token（Agent 多次工具调用），成本敏感场景慎用。

#### Hello World C：Zep

```python
# pip install zep-cloud
from zep_cloud.client import Zep
import os

client = Zep(api_key=os.getenv("ZEP_API_KEY"))

# 1. 注册用户（必须）
client.user.add(user_id="alice", first_name="Alice")

# 2. 创建 thread（对话线程）
thread_id = "alice-chat-001"
client.thread.create(thread_id=thread_id, user_id="alice")

# 3. 喂入对话
for t in turns:
    client.thread.add_messages(
        thread_id=thread_id,
        messages=[{"role": "user", "content": t, "name": "Alice"}],
    )

# 4. 查询：Zep 自动构建图谱并产出 Context Block
ctx = client.thread.get_user_context(thread_id=thread_id)
print(ctx.context)

# 期望输出（节选）：
# FACTS:
#   - Alice lives in Beijing  (valid_at: 2026-04-25)
#   - Alice's previous location was Shanghai  (valid_at: 2026-04-25, invalid_at: 2026-04-25)
#   - Alice prefers history books (valid_at: 2026-04-25)
#   - Alice previously preferred sci-fi (valid_at: ..., invalid_at: 2026-04-25)
```

**注意点**：Zep Cloud **必须有 API Key**，无 OSS 替代。新账户有少量免费额度，超出后按 token/节点计费。

#### Hello World D：LangMem

```python
# pip install langmem langgraph "langgraph-prebuilt"
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

store = InMemoryStore(index={"dims": 1536, "embed": "openai:text-embedding-3-small"})

agent = create_react_agent(
    "anthropic:claude-3-5-sonnet-latest",
    tools=[
        create_manage_memory_tool(namespace=("memories", "{user_id}")),
        create_search_memory_tool(namespace=("memories", "{user_id}")),
    ],
    store=store,
)

config = {"configurable": {"user_id": "alice"}}
for t in turns:
    agent.invoke({"messages": [{"role": "user", "content": t}]}, config=config)

# 查询
resp = agent.invoke(
    {"messages": [{"role": "user", "content": "我住在哪？喜欢什么书？"}]},
    config=config,
)
print(resp["messages"][-1].content)

# 注意点：LangMem 默认走 Hot Path，Agent 自己决定何时调 manage_memory / search_memory
# 遗忘旧事实需要 Agent 主动调 manage_memory_tool 的 update/delete
```

#### Hello World E：自建 Redis（最小骨架）

详见 §3.2，约 200 行可跑通。

---

### 3.2 自建最小记忆系统（≈200 行）

**目标**：演示自建路线的核心逻辑——事实抽取 + 多信号检索 + recency 加权 + 简单遗忘。

**前置要求**：
- Redis 7.4+（含 Redis Stack 或安装 RediSearch 模块）
- Python 3.10+
- 一个 OpenAI 兼容的 API（用 OpenAI 也可换成 Qwen/DeepSeek/本地 Ollama）

**依赖**：

```bash
pip install redis==5.2.1 openai==1.59.3 numpy==2.2.1
# Redis 启动（Docker）：
docker run -d -p 6379:6379 redis/redis-stack:7.4.0-v0
```

**完整代码**（保存为 `experiments/single/E13_minimal_memory.py`，约 180 行）：

```python
"""E13_minimal_memory.py — 自建最小记忆系统
─ Redis Hash 存事实 + RediSearch 向量检索
─ Recency 加权 + 简单冲突解决
"""
import os
import time
import json
import struct
import math
from typing import List, Dict, Any
import numpy as np
import redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from openai import OpenAI

# ───────────── 配置 ─────────────
DIM = 1536
INDEX_NAME = "idx:facts"
KEY_PREFIX = "fact:"
TOP_K = 5
ALPHA, BETA, GAMMA = 0.7, 0.2, 0.1            # semantic / recency / popularity
HALF_LIFE_DAYS = 7                              # recency 半衰期

oa = OpenAI()
r = redis.Redis(host="localhost", port=6379, decode_responses=False)


# ───────────── 索引初始化（幂等）─────────────
def ensure_index():
    try:
        r.ft(INDEX_NAME).info()
        return
    except redis.ResponseError:
        pass
    schema = (
        TextField("content"),
        TextField("user_id"),
        NumericField("ts"),
        NumericField("access_count"),
        VectorField("embedding", "HNSW", {
            "TYPE": "FLOAT32", "DIM": DIM, "DISTANCE_METRIC": "COSINE"
        }),
    )
    r.ft(INDEX_NAME).create_index(
        schema,
        definition=IndexDefinition(prefix=[KEY_PREFIX], index_type=IndexType.HASH),
    )


# ───────────── Embedding ─────────────
def embed(text: str) -> bytes:
    v = oa.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
    return np.asarray(v, dtype=np.float32).tobytes()


# ───────────── 事实抽取（一次 LLM 调用）─────────────
EXTRACT_PROMPT = """你是事实抽取助手。从下面对话中提取关于用户的稳定事实。
要求：
- 每条事实一行，不超过 20 字
- 只提取明确的、可追溯的事实
- 用第三人称（"用户喜欢..."）
- 不确定的不提取
- 输出 JSON 数组，例: ["用户住在北京", "用户喜欢历史书"]

对话内容:
{text}

输出 JSON："""

def extract_facts(text: str) -> List[str]:
    resp = oa.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": EXTRACT_PROMPT.format(text=text)}],
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    try:
        data = json.loads(raw)
        # 支持 {"facts": [...]} 或 [...] 两种返回
        if isinstance(data, dict):
            return data.get("facts") or list(data.values())[0]
        return data
    except Exception:
        return []


# ───────────── 写入 ─────────────
def add_memory(user_id: str, message: str):
    facts = extract_facts(message)
    now = time.time()
    for f in facts:
        fid = f"{KEY_PREFIX}{user_id}:{int(now*1000)}:{hash(f) & 0xffff}"
        r.hset(fid, mapping={
            "content": f,
            "user_id": user_id,
            "ts": now,
            "access_count": 0,
            "embedding": embed(f),
        })
    return facts


# ───────────── 检索（多信号融合）─────────────
def search_memory(user_id: str, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    q_vec = embed(query)
    # 1) 向量检索（多取一些再 rerank）
    knn_q = (
        Query(f"(@user_id:{user_id})=>[KNN {top_k*3} @embedding $vec AS sem_score]")
        .sort_by("sem_score").return_fields("content", "ts", "access_count", "sem_score")
        .dialect(2).paging(0, top_k * 3)
    )
    res = r.ft(INDEX_NAME).search(knn_q, query_params={"vec": q_vec})
    now = time.time()
    scored = []
    for d in res.docs:
        sem = 1 - float(d.sem_score)        # cosine distance → similarity
        age_days = (now - float(d.ts)) / 86400
        recency = math.exp(-age_days / HALF_LIFE_DAYS)
        pop = math.log1p(int(d.access_count))
        score = ALPHA * sem + BETA * recency + GAMMA * pop
        scored.append({"content": d.content, "score": score, "ts": float(d.ts)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]
    # 命中后增加 access_count（异步会更好，这里同步示例）
    for d in res.docs[: top_k]:
        r.hincrby(d.id, "access_count", 1)
    return top


# ───────────── 简易冲突解决：同实体 + 时间更新 → 旧事实 TTL ─────────────
# （留作练习——可加 LLM 二阶段：抽取主语，比对历史，发现矛盾就给旧条目设 TTL）

# ───────────── Demo ─────────────
if __name__ == "__main__":
    ensure_index()
    uid = "alice"
    turns = [
        "你好，我叫 Alice，住在上海，是一名软件工程师。",
        "我喜欢科幻小说，最喜欢刘慈欣的《三体》。",
        "对了，我现在搬到北京了。",
        "我现在更喜欢历史类的书了。",
    ]
    for t in turns:
        added = add_memory(uid, t)
        print(f"+ added: {added}")

    print("\n查询：Alice 住在哪？喜欢什么书？")
    for hit in search_memory(uid, "Alice 住在哪？喜欢什么书？"):
        print(f"  [{hit['score']:.3f}] {hit['content']}")
```

**预期输出**（运行后大致样子）：

```
+ added: ['用户名为 Alice', '用户住在上海', '用户是软件工程师']
+ added: ['用户喜欢科幻小说', '用户最喜欢《三体》']
+ added: ['用户搬到北京']
+ added: ['用户现在更喜欢历史类的书']

查询：Alice 住在哪？喜欢什么书？
  [0.812] 用户搬到北京
  [0.798] 用户现在更喜欢历史类的书
  [0.621] 用户住在上海
  [0.587] 用户喜欢科幻小说
  [0.502] 用户名为 Alice
```

**关键观察**：北京/历史的分数高于上海/科幻——**recency 项让最新事实自动浮上来**，但**旧事实没被删除**（这是与 Zep 的 invalidation 不同的设计——它保留了"用户曾经"的历史）。

**进阶练习**（让你的自建系统接近 Mem0 v3 水平）：

1. 加 BM25 关键词通道（RediSearch 原生支持 `FT.SEARCH @content:"...":xxx` 语法）
2. 加实体抽取（用 spaCy 或 LLM JSON mode）和实体索引
3. 加冲突检测：抽取主语 + 谓语，如果存在历史条目同主谓但宾语不同 → 标记 `invalid_at`
4. 加后台 Manager：用 cron 定期合并相似事实、删除低分事实

---

## 🕳️ 避坑指南

> 这是 GitHub Issues + Reddit + 实战凝结的高频坑，看完能少踩 80% 的雷。

| # | 坑 | 原因 | 解法 |
|---|----|----|------|
| 1 | **记忆冲突——新旧事实并存导致回答自相矛盾** | Mem0 v3 是 ADD-only；自建若没冲突解决也会发生 | Zep 选 invalidation；自建则定期跑 conflict resolution；或用主语+谓语+TTL 兜底 |
| 2 | **隐私泄露——把记忆塞进 prompt 后被另一个用户看到** | 没做严格的 user_id namespace 隔离 | 所有检索 API 必须强制传 user_id；中间件层加白名单校验 |
| 3 | **过度记住——把废话也存了，检索质量被拖垮** | 抽取 prompt 写得太宽松 | 抽取时加"只提取稳定的、可追溯的"；定期低分清理；设最大记忆条数上限 |
| 4 | **跨会话污染——同 user 的不同业务场景互相干扰**（如同一个 user 既问健身又问代码）| 没做 session_id / agent_id 二级隔离 | 用三元 namespace `(user_id, agent_id, session_id)`；Mem0 原生支持，自建要加 |
| 5 | **Mem0 v2 → v3 升级数据不兼容** | 算法从 ADD/UPDATE/DELETE 变 ADD-only，UPDATE 历史丢失 | 升级前看官方 migration guide；先在小流量验证一周 |
| 6 | **Letta 工具调用爆炸——每轮 5-10 次工具调用** | Agent 自己决定记什么，遇到长对话每条都要思考 | 限制 max_tool_calls 或换更轻的 LLM；用 sleep-time agent 把整理放到离线 |
| 7 | **Zep Community Edition 还在用** | 2025 年已正式弃用，没安全更新 | 立即迁 Cloud 或迁移到自建 + Graphiti（Graphiti OSS 仍维护）|
| 8 | **LangMem 不设 namespace 导致全局共享** | 默认 `("memories",)` 是单 namespace | 用 `("memories", "{user_id}")` + LangGraph config 注入 user_id |
| 9 | **embedding 模型混用导致检索失效** | 写入用 `text-embedding-3-small`，检索时换了 `text-embedding-3-large` | 严格固定一个模型；版本写入元数据，检索前校验 |
| 10 | **过度依赖框架 add() 的 LLM 调用，成本失控** | 每条消息都触发 fact extraction = 一次 LLM 调用 | 批量化（攒 5-10 条再 add）；或在前置过滤层用规则跳过寒暄类消息 |
| 11 | **Hot Path 模式拖慢主对话** | 每轮 Agent 都要决定记不记，先想再答 | 切到 Background Manager 模式；或用 LangMem 的 `delayed_processing` |
| 12 | **没有"主动遗忘"机制，记忆库无限膨胀** | 框架默认只追加 | 设 TTL（自建 Redis 直接用）；或定期跑低分清理 |
| 13 | **自建系统没考虑 Embedding 漂移** | 一年后想升级 embedding 模型，全库要重算 | 写入时存原文 + embedding 双份；升级时后台 reindex |
| 14 | **多 Agent 共享记忆没做权限隔离** | 一个 Agent 写的记忆所有 Agent 都看到 | 分 namespace；或加 ACL 字段 `visible_to: [agent_a, agent_b]` |

---

## 💰 成本速算

> 假设：日活 1000 用户，每人每天 20 轮对话，平均每轮 200 tokens，按 OpenAI gpt-4o-mini 定价（2026-04 实时）。

### 月度运行成本估算（USD）

| 方案 | LLM 调用成本 | 存储成本 | 平台/订阅 | 月总成本 | 备注 |
|------|----------|--------|----------|--------|------|
| **不要记忆**（基线）| $0（直接拼 history）| $0 | $0 | $0 | 但 token 浪费 + 上下文窗口压力 |
| **Mem0 OSS** | ≈ $180（每次 add 一次抽取）| $20（Qdrant 自托管 4GB）| $0 | **≈ $200** | 需自运维 |
| **Mem0 Cloud** | ≈ $180（仍走 LLM）| 平台内含 | $99-499（按 tier）| **$280-680** | 零运维 |
| **Letta OSS** | ≈ $360（工具调用 ~2x）| $20 | $0 | **≈ $380** | 工具调用消耗大 |
| **Zep Cloud** | $0（包月）| 平台内含 | **$200-1500+**（按节点数）| **$200-1500+** | OSS 无 |
| **LangMem** | ≈ $90（仅 Hot Path 调用）| $5（Postgres 小实例）| $0（含在 LangGraph Platform 内）| **≈ $95** | 配 LangGraph 用 |
| **自建 Redis** | ≈ $90（仅抽取 LLM）| $30（Redis Cloud 5GB 或自建）| $0 | **≈ $120** | 加你的开发/运维人力 |

> ⚠️ **以上仅为量级参考**。实际成本受抽取频率、记忆条数、Embedding 模型、平台计费规则影响极大。**实际预算前必须按你自己的对话密度做一周压测**。

### Token 成本三板斧（参考 [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) §6 LLM 服务化）

不论选哪家，记忆系统都额外消耗 token。降本三招：

1. **批量化抽取**：攒 5-10 轮再调一次 add，而非每轮调（省 50-80% 抽取成本）
2. **小模型抽取**：用 gpt-4o-mini / Qwen2.5-7B 做抽取，省 10× 成本
3. **检索结果压缩**：检索后只把 top-3 摘要塞进 prompt，而非塞 top-10 原文

### ROI 临界点

| 用户量级 | 推荐方案 | 月成本量级 | 理由 |
|---------|---------|----------|------|
| < 100 | 不上记忆 | $0 | 拼 history 够用 |
| 100 - 10k | LangMem 或自建 | $50-300 | 自托管划算 |
| 10k - 100k | Mem0 OSS / 自建升级版 | $300-2k | 平衡运维成本 |
| 100k - 1M | Mem0 Cloud / Zep | $2k-20k | 平台优势开始体现 |
| > 1M | 自建 + 团队（5+ 人）| 因人而异 | 此规模下 vendor lock-in 风险大于成本 |

---

## 🎯 决策速查

### 决策树（按你的场景从上到下走）

```
你需要持久跨会话记忆吗？
├── 否 → 直接用 ChatHistory，不要引入记忆系统（最大避坑）
├── 是 →
    │
    ├── 业务事实会随时间频繁演变？（CRM/医疗/合规审计）
    │   └── 是 → Zep（接受 Cloud-only + 预算）；否则 Graphiti OSS 自建
    │
    ├── 已经在 LangGraph 生态里？
    │   └── 是 → LangMem（最低摩擦）
    │
    ├── 要做 stateful 角色扮演 / 长任务执行 Agent？
    │   └── 是 → Letta（独家 sleep-time + MemFS）
    │
    ├── 数据合规严格 / 内网部署 / 用户量 < 1 万？
    │   └── 是 → 自建 Redis 路线（参考 §3.2）
    │
    └── 都不是 → Mem0 是默认选择
        ├── 不想运维 → Mem0 Cloud
        └── 要私有化 → Mem0 OSS + 自托管 dashboard
```

### 何时用 / 何时不用 / 何时换

| 信号 | 行动 |
|------|------|
| 用户抱怨"AI 总忘记我说过的偏好" | 该上记忆系统了 |
| 你的 prompt 已经 > 30k tokens 全是 chat_history | 上记忆系统能省 50%+ 成本 |
| 业务非常窄（如单轮工具调用机器人）| 不要上，复杂度溢出 |
| 数据合规说"用户数据不能出本地" | 排除 Zep / Mem0 Cloud；自建或 Letta OSS |
| 你已经用 Mem0 OSS 半年，每次 add 卡 1-2 秒 | 该升 v3 / 切批量化 / 切自建 |
| Letta 项目工具调用次数失控 | 切 Mem0（让框架接管而非 Agent 自己决定）|

### 范式选择速查

| 范式 | 何时优先 | 何时不要 |
|-----|---------|--------|
| 事实抽取派（Mem0）| 用户量大、对话密集 | 事实结构强类型化（用图谱）|
| 自我编辑派（Letta）| 角色扮演、长任务、Agent 要"自学" | 简单 QA 机器人 |
| 时序图谱派（Zep）| 关系复杂 + 时序敏感 | 简单偏好/事实场景（杀鸡用牛刀）|
| Store 原语派（LangMem）| 已用 LangGraph + 想要灵活控制 | 没用 LangGraph 的项目 |
| 自建 | 简单场景 + 合规严格 + 团队有人 | 通用智能记忆需求 |

---

## 📌 来源清单

> **时效性声明**：以下信息获取于 2026-04-25。框架版本/分数/价格随时变化，签合同前请核实最新数据。

### 一手来源（官方）

- [Mem0 GitHub](https://github.com/mem0ai/mem0) — 2026-04-25 — README 含 v3 算法 benchmark（LongMemEval 93.4 / LoCoMo 91.6）
- [Mem0 Docs](https://docs.mem0.ai) — 2026-04-25 — 概念、API、Cloud vs OSS 对比
- [Mem0 Paper (arXiv:2504.19413)](https://arxiv.org/abs/2504.19413) — 2025-04 — Chhikara et al., "Building Production-Ready AI Agents with Scalable Long-Term Memory"
- [Letta GitHub](https://github.com/letta-ai/letta) — 2026-04-25 — formerly MemGPT，22.3k⭐
- [Letta Docs](https://docs.letta.com) — 2026-04-25 — memory_blocks / archival / sleep-time agents
- [MemGPT Paper (arXiv:2310.08560)](https://arxiv.org/abs/2310.08560) — 2023-10 — Packer et al., NeurIPS'23
- [Zep GitHub](https://github.com/getzep/zep) — 2026-04-25 — 已转向 Cloud，Community Edition 在 `legacy/`
- [Zep Docs](https://help.getzep.com/concepts) — 2026-04-25 — Knowledge Graph + Fact Invalidation
- [Graphiti GitHub](https://github.com/getzep/graphiti) — 2026-04-25 — Zep 底层图谱框架（仍 OSS）
- [LangMem GitHub](https://github.com/langchain-ai/langmem) — 2026-04-25 — 1.4k⭐，MIT
- [LangMem Docs](https://langchain-ai.github.io/langmem/) — 2026-04-25 — Hot Path / Background 双模式

### 工作区交叉引用

- [R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md) Copilot 全局记忆架构 — 五层指令 + 三层运行时记忆
- [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) Redis 在 Agent 中的应用 — §六.D 简介 Mem0/Letta，本报告是其深化版
- [R30](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) RAG 从入门到生产 — Embedding 选型、向量检索基础
- [R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) 长效 AgentHarness 工程化 — 长会话场景
- [R48](R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md) Agent 知识工程全景 — 知识 vs 记忆边界
- [R26](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R26_LangChain%E4%B8%8ELangGraph%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md) LangChain 与 LangGraph 入门到实战 — LangMem 的 LangGraph 前置知识
- [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) LLM 服务化生产部署 — Token 成本控制方法

### 来源一致性

⚖️ **多源一致**：

- 五家产品均有官方 GitHub + 官方文档双源验证
- Mem0 v3 benchmark 数字仅有官方来源，未独立复现 → 标"参考量级"
- Zep Community Edition 弃用：GitHub README + 官方博客双源确认

⚠️ **未充分验证**：

- 各方案 token 成本估算基于公开定价 + 假设的对话密度，**实际 ROI 必须自己压测**
- Zep < 200ms p95 来自官方声明，本报告未独立压测

---

## 后续追踪

- [ ] **跑一次跨框架 benchmark**：把同一段 100 轮真实对话喂入五家，量化对比检索 P@5 / 延迟 / 成本（值得做成 `E14` 或 `P05` 实验，候选编号）
- [ ] **跟踪 Mem0 v4 / Letta 后续 release**（赛道演进太快，6 个月后本报告需要复审）
- [ ] **多模态记忆专题**：图像 / 语音 / 视频片段如何融入这套体系（目前五家几乎都是纯文本）
- [ ] **联邦记忆**：多 Agent 在隐私保护前提下共享记忆（差分隐私 / TEE 路线）

---

> **报告锻造审视**（PSEV - Forge 阶段）：
>
> 本报告产出过程中识别到若干可固化模式：
>
> 1. ✅ "**框架横评矩阵**"模板（同段对话喂入 + 能力维度对比表）已在 R45 / R47 / R52 / R67 复用 4 次 → **建议固化为 `wiki/templates/横评报告模板.md`**
> 2. ⏸️ "**Hello World 同输入对比法**"思路已用 2 次（R47 也用过类似手法）→ 累计 3 次后再固化
> 3. ✅ 决策树 + 何时用/何时换 表 在 R45 / R52 / R67 都出现 → 建议提到 `tech-selector` Skill（D30）作为标准产物
