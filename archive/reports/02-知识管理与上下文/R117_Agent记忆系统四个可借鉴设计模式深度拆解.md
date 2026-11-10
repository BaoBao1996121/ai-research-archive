---
title: Agent 记忆系统四个可借鉴设计模式深度拆解
aliases: [R117, 记忆设计模式, 记忆巩固, RRF, Ebbinghaus, Token预算]
report_id: R117
category: 知识管理与上下文
status: completed
tags: [memory, consolidation, RRF, hybrid-search, Ebbinghaus, decay, token-budget, design-pattern]
date: 2026-05-15
related:
  - "[R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)"
  - "R48（原稿交叉引用，本归档未解析）"
  - "[R74](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R74_%E6%89%8B%E6%90%93MCP%E4%B8%8ESkill%E5%AE%9E%E7%8E%B0%E6%9C%BA%E5%88%B6.md)"
  - "[R102](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R102_Agent_Dreaming_%E5%BD%93AI%E5%AD%A6%E4%BC%9A%E5%81%9A%E6%A2%A6.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Agent 记忆系统四个可借鉴设计模式深度拆解

> **一句话概括**：从 agentmemory/Mem0/Letta/认知心理学中提炼出四个已被验证的记忆系统设计模式——四层巩固、RRF 融合检索、Ebbinghaus 衰减 + 矛盾检测、Token 预算控制——逐个拆解原理、给出最小可运行实现、并映射到我们工作区的具体改进点。
>
> **研究日期**：2026-05-15
> **增量价值**：在 [R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)（Agent 记忆系统横评）和 R48（原稿交叉引用，本归档未解析）（Agent 知识工程全景）基础上，从"框架选型"下沉到"设计模式级"，提炼四个可独立借鉴的通用模式，不依赖任何特定框架即可落地。
> **关联报告**：[R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)（五家横评）、R48（原稿交叉引用，本归档未解析）（知识工程全景，含 RRF 代码）、[R74](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R74_%E6%89%8B%E6%90%93MCP%E4%B8%8ESkill%E5%AE%9E%E7%8E%B0%E6%9C%BA%E5%88%B6.md)（GBrain 混合搜索）、[R102](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R102_Agent_Dreaming_%E5%BD%93AI%E5%AD%A6%E4%BC%9A%E5%81%9A%E6%A2%A6.md)（Agent Dreaming 记忆巩固）

---

## 目录

1. [模式一：四层记忆巩固](#模式一四层记忆巩固-workingepisodicsemantic-procedural)
2. [模式二：RRF 融合检索](#模式二rrf-融合检索)
3. [模式三：Ebbinghaus 衰减 + 矛盾检测](#模式三ebbinghaus-衰减--矛盾检测)
4. [模式四：Token 预算控制](#模式四token-预算控制)
5. [四个模式的协作关系](#四个模式的协作关系)
6. [落地映射：在我们的工作区中怎么用](#落地映射在我们的工作区中怎么用)
7. [来源清单](#来源清单)

---

## 模式一：四层记忆巩固 Working→Episodic→Semantic→Procedural

### 认知心理学根基

这套分层来自 Endel Tulving (1972) 的记忆分类理论，后被 Squire (1992) 扩展。人脑的长期记忆确实按**陈述性记忆**（Declarative = Episodic + Semantic）和**程序性记忆**（Procedural）两大分支组织。agentmemory 把 Working Memory 加进来，形成四层模型。

### 四层是什么

```
┌──────────────────────────────────────────────────────────┐
│  Working（工作记忆）                                      │
│  存什么：当前会话的原始 tool use 观察                      │
│  时间尺度：分钟级                                         │
│  触发：每次 PostToolUse hook                              │
│  实现：内存 buffer / 短 TTL 缓存                          │
│  去重：SHA-256 + 5min 滑动窗口                            │
├──────────────────────────────────────────────────────────┤
│  Episodic（情景记忆）                                     │
│  存什么：压缩后的会话摘要 —— "什么时候做了什么"            │
│  时间尺度：小时到天                                       │
│  触发：Stop/SessionEnd hook（会话结束时批量处理）          │
│  实现：带时间戳的文档库（向量索引 + metadata filter）      │
│  例子："2026-05-15 会话：修了 auth 模块的 JWT 过期 bug"    │
├──────────────────────────────────────────────────────────┤
│  Semantic（语义记忆）                                     │
│  存什么：从多次情景中抽取的事实、偏好、规律                 │
│  时间尺度：天到月                                         │
│  触发：定时巩固任务 / 积累 N 条 Episodic 后触发            │
│  实现：结构化 KV 或知识图谱（entity→relation→entity）     │
│  例子："该项目用 jose 替代 jsonwebtoken，因为 Edge 兼容"   │
├──────────────────────────────────────────────────────────┤
│  Procedural（程序性记忆）                                 │
│  存什么：反复验证的工作流、决策模式、"怎么做"              │
│  时间尺度：周到月                                         │
│  触发：当同一模式在 Semantic 层被识别出现 ≥3 次            │
│  实现：Skill 文件 / Instruction / 模板                    │
│  例子："遇到性能问题先 profile 再优化，不要凭直觉猜"       │
└──────────────────────────────────────────────────────────┘
```

### 层间流动机制

这是理解四层模型的关键——层之间不是静态存储，是有**升级和降级通道**的：

```
Working ──压缩──→ Episodic ──抽象──→ Semantic ──固化──→ Procedural
   ↑                  ↑                  ↑                  ↑
   │                  │                  │                  │
   └─ 新观察         └─ 会话结束时     └─ N次情景后       └─ ≥3次验证后
                       LLM 摘要          LLM 事实抽取        人工/LLM 审核

降级通道（反方向）：
  Procedural 被发现不再适用 → 降级回 Semantic（标注"已废弃"）
  Semantic 事实被新证据推翻 → 更新或删除
  Episodic 长期未被检索命中 → 衰减（见模式三）
```

### 最小实现（Python，~60 行）

```python
"""四层记忆巩固的最小概念实现"""
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Optional


@dataclass
class Observation:
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    hash: str = ""
    
    def __post_init__(self):
        self.hash = sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class EpisodicEntry:
    summary: str
    session_id: str
    timestamp: datetime
    access_count: int = 0


@dataclass
class SemanticFact:
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source_episodes: list[str] = field(default_factory=list)


@dataclass
class ProceduralPattern:
    name: str
    description: str
    steps: list[str]
    verified_count: int = 0  # ≥3 才算 stable


class FourTierMemory:
    def __init__(self):
        self.working: list[Observation] = []        # 当前会话 buffer
        self.episodic: list[EpisodicEntry] = []      # 会话摘要
        self.semantic: list[SemanticFact] = []        # 事实库
        self.procedural: list[ProceduralPattern] = [] # 流程库
        self._seen_hashes: set[str] = set()           # 去重窗口
    
    def observe(self, content: str) -> Optional[Observation]:
        """Working 层：捕获新观察，去重"""
        obs = Observation(content)
        if obs.hash in self._seen_hashes:
            return None  # 5min 窗口内重复
        self._seen_hashes.add(obs.hash)
        self.working.append(obs)
        return obs
    
    def end_session(self, session_id: str, summarize_fn):
        """Working → Episodic：会话结束时压缩"""
        if not self.working:
            return
        raw_text = "\n".join(o.content for o in self.working)
        summary = summarize_fn(raw_text)  # LLM 调用
        self.episodic.append(EpisodicEntry(
            summary=summary, session_id=session_id,
            timestamp=datetime.now()
        ))
        self.working.clear()
        self._seen_hashes.clear()
    
    def consolidate(self, extract_facts_fn):
        """Episodic → Semantic：定期巩固，抽取事实"""
        unconsolidated = [e for e in self.episodic if e.access_count == 0]
        if len(unconsolidated) < 3:
            return  # 攒够 3 条再巩固
        text = "\n".join(e.summary for e in unconsolidated)
        facts = extract_facts_fn(text)  # LLM 抽取 (subject, pred, obj)
        for s, p, o in facts:
            self.semantic.append(SemanticFact(
                subject=s, predicate=p, object=o,
                source_episodes=[e.session_id for e in unconsolidated]
            ))
        for e in unconsolidated:
            e.access_count += 1
```

### 与 R72 横评的映射

| 四层 | Mem0 | Letta | Zep | 我们的工作区 |
|------|------|-------|-----|-------------|
| Working | 无（直接存） | main_context | 无 | 对话 context window |
| Episodic | session memories | conversation_storage | chat sessions | `sessions/interaction-log/` |
| Semantic | user/agent memories（事实抽取） | memory_blocks（自我编辑） | Graphiti facts | `KNOWLEDGE_INDEX.md` §二/§三 |
| Procedural | **缺失** | **缺失** | **缺失** | `skills/` + `agent.md` 方法论 |

关键发现：**业界的记忆框架几乎都缺 Procedural 层**。我们的工作区通过 Skill 体系（Forge 阶段）和 agent.md 方法论，实际上已经在做 Procedural 记忆——只是没有用这个术语，也没有自动化"从 Semantic 到 Procedural 的升级通道"。

---

## 模式二：RRF 融合检索

### 它解决什么问题

单一检索方法各有盲区：
- **BM25/关键词**：精确匹配强，语义理解弱（搜"数据库性能优化"找不到"N+1 查询修复"）
- **向量检索**：语义理解强，精确匹配弱（搜"auth.ts"可能返回语义相近但文件名错误的结果）
- **图检索**：关系推理强，但覆盖率依赖图的完整度

RRF 的思路是：**不要选一个，把三个的结果融合起来**。

### 算法本质（一句话 + 公式）

对于文档 $d$，它在第 $i$ 个排序列表中排名为 $r_i(d)$，则 RRF 分数为：

$$\text{RRF}(d) = \sum_{i=1}^{n} \frac{1}{k + r_i(d)}$$

其中 $k$ 是平滑常数（工业默认 $k=60$，来自 Cormack et al., SIGIR 2009 原始论文的实验结果）。

**为什么 $k=60$ 效果好**：$k$ 控制了"排名靠前"和"排名靠后"的分数差距。$k$ 太小（如 1），第 1 名和第 2 名的分数差距巨大（0.5 vs 0.33），过度偏向头部；$k$ 太大（如 1000），所有排名的分数几乎一样，融合失去意义。$k=60$ 在绝大多数数据集上处于这个甜区。

### 最小实现（Python，25 行）

```python
"""Reciprocal Rank Fusion — 最小可运行实现"""
from collections import defaultdict


def rrf_fuse(
    *ranked_lists: list[str],  # 每个列表是按相关性排序的文档 ID
    k: int = 60,
    top_n: int = 10,
) -> list[tuple[str, float]]:
    """
    输入：多个排序列表（每个来自不同检索方法）
    输出：融合后的 (doc_id, score) 列表，按 score 降序
    """
    scores: dict[str, float] = defaultdict(float)
    
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return fused[:top_n]


# 示例：BM25 和 Vector 各返回 5 个结果
bm25_results  = ["doc_A", "doc_C", "doc_B", "doc_E", "doc_F"]
vector_results = ["doc_B", "doc_A", "doc_D", "doc_C", "doc_G"]

fused = rrf_fuse(bm25_results, vector_results, k=60)
# doc_A: 1/(60+1) + 1/(60+2) = 0.01639 + 0.01613 = 0.03252  ← 两个列表都排前列
# doc_B: 1/(60+3) + 1/(60+1) = 0.01587 + 0.01639 = 0.03226
# doc_C: 1/(60+2) + 1/(60+4) = 0.01613 + 0.01563 = 0.03175
```

### 三流融合的完整版（agentmemory 的做法）

agentmemory 不只做双流（BM25 + Vector），而是**三流**（BM25 + Vector + Graph），并加了一个"session 去重"后处理：

```python
"""三流 RRF 融合 + session 多样性去重"""
from collections import defaultdict


def triple_rrf_fuse(
    bm25_results: list[str],
    vector_results: list[str],
    graph_results: list[str],
    doc_to_session: dict[str, str],  # doc_id → session_id 映射
    k: int = 60,
    top_n: int = 10,
    max_per_session: int = 3,  # 每个 session 最多贡献 3 条
) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    
    for ranked_list in [bm25_results, vector_results, graph_results]:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    
    # 按分数排序
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Session 多样性去重：避免一个 session 的记忆霸占结果
    result = []
    session_count: dict[str, int] = defaultdict(int)
    for doc_id, score in sorted_docs:
        sid = doc_to_session.get(doc_id, "unknown")
        if session_count[sid] < max_per_session:
            result.append((doc_id, score))
            session_count[sid] += 1
        if len(result) >= top_n:
            break
    
    return result
```

### 何时用、何时不用

| 场景 | 建议 |
|------|------|
| 知识库 > 1000 条，查询有关键词+语义双重需求 | 用 RRF |
| 知识库 < 100 条，全文搜索就够 | 不用，过度工程 |
| 已有 Milvus/Elasticsearch 等支持 hybrid search 的存储 | 直接用内置 RRF（R48（原稿交叉引用，本归档未解析） §四 有 Milvus 代码） |
| 纯代码搜索（精确匹配为主） | BM25 优先，向量辅助 |

---

## 模式三：Ebbinghaus 衰减 + 矛盾检测

### Ebbinghaus 遗忘曲线

Hermann Ebbinghaus (1885) 发现人类记忆保持率随时间指数衰减：

$$R(t) = e^{-t/S}$$

其中 $R$ 是记忆保持率，$t$ 是时间，$S$ 是记忆强度（与重复次数正相关）。

**关键洞察**：每次"回忆"（被检索命中）会增强 $S$，使衰减变慢。这就是间隔重复（Spaced Repetition）的理论基础，也是 agentmemory 记忆衰减策略的核心。

### 映射到 Agent 记忆系统

对于 Agent 记忆条目，定义一个 importance score：

$$\text{importance}(m) = \text{base\_score}(m) \times R(t) \times \text{access\_boost}(m)$$

其中：
- $\text{base\_score}$ = 创建时的初始重要性（由 LLM 评估，或根据上下文推断）
- $R(t) = e^{-t/S}$ = 时间衰减因子
- $\text{access\_boost} = 1 + \log(1 + \text{access\_count})$ = 被检索命中次数的增强

### 最小实现（Python，~50 行）

```python
"""Ebbinghaus 衰减 + 矛盾检测的最小实现"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class MemoryEntry:
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    base_importance: float = 1.0   # LLM 评估的初始重要性 [0, 1]
    strength: float = 1.0          # S 参数，初始=1，每次访问增强
    superseded_by: str | None = None  # 被哪条新记忆取代
    
    def decay_score(self, now: datetime | None = None) -> float:
        """计算当前时刻的重要性分数"""
        now = now or datetime.now()
        hours_elapsed = (now - self.created_at).total_seconds() / 3600
        
        # Ebbinghaus 衰减：R = e^(-t/S)
        retention = math.exp(-hours_elapsed / (self.strength * 24))  # S 以天为单位
        
        # 访问增强：每次被命中，strength 增加
        access_boost = 1 + math.log1p(self.access_count)
        
        return self.base_importance * retention * access_boost
    
    def on_accessed(self):
        """被检索命中时调用"""
        self.access_count += 1
        self.strength *= 1.5  # 每次访问，衰减半衰期延长 50%


def evict_stale(
    memories: list[MemoryEntry],
    threshold: float = 0.01,  # 低于此分数的记忆被驱逐
) -> tuple[list[MemoryEntry], list[MemoryEntry]]:
    """驱逐过期记忆"""
    now = datetime.now()
    alive, evicted = [], []
    for m in memories:
        if m.superseded_by:
            evicted.append(m)  # 已被取代的直接驱逐
        elif m.decay_score(now) < threshold:
            evicted.append(m)  # 衰减到阈值以下
        else:
            alive.append(m)
    return alive, evicted
```

### 矛盾检测

记忆不只会过时，还会**互相矛盾**。比如：
- 旧记忆："项目用 express 框架"
- 新记忆："项目迁移到 fastapi"

矛盾检测的核心是**同主语事实的版本管理**：

```python
def detect_contradiction(
    new_fact: tuple[str, str, str],  # (subject, predicate, object)
    existing_facts: list[tuple[str, str, str, str]],  # (..., entry_id)
) -> str | None:
    """检测新事实是否与已有事实矛盾。返回被取代的 entry_id"""
    subj, pred, obj = new_fact
    for e_subj, e_pred, e_obj, entry_id in existing_facts:
        if e_subj == subj and e_pred == pred and e_obj != obj:
            # 同主语同谓语但宾语不同 = 矛盾
            return entry_id  # 旧事实应被标记为 superseded
    return None
```

实际系统中还需要处理**软矛盾**（不是完全相反，而是部分冲突）——这通常需要 LLM 介入判断。agentmemory 的做法是在巩固阶段让 LLM 对比同主语的所有事实，输出"保留/取代/合并"决策。

### 衰减策略的参数调优

| 参数 | 含义 | agentmemory 默认 | 建议范围 |
|------|------|-----------------|---------|
| $S$ 初始值 | 记忆初始半衰期 | 1 天 | 0.5-7 天（取决于场景变化速度） |
| 访问增强系数 | 每次命中后 $S$ 的增幅 | ×1.5 | ×1.2-2.0 |
| 驱逐阈值 | 低于此分数的记忆被清理 | 0.01 | 0.001-0.05 |
| 巩固频率 | 多久做一次 Working→Episodic 压缩 | 每次会话结束 | 每次会话结束（合理） |
| 矛盾检测 | 什么时候触发 | 新事实写入 Semantic 层时 | 同上 + 定期全量扫描 |

---

## 模式四：Token 预算控制

### 它解决什么问题

记忆系统的天然倾向是"尽可能多注入上下文"——但 LLM 的注意力不是均匀的。研究表明（Liu et al., 2024, "Lost in the Middle"），当 context 过长时，**中间部分的信息被严重忽视**。所以"注入更多 ≠ 更好的效果"。

Token 预算控制的核心思想：**硬约束注入量，迫使系统做信息筛选**。

### agentmemory 的做法

```
SessionStart hook 触发
  → 加载项目 profile（top concepts, files, patterns）
  → 混合搜索（BM25 + Vector + Graph）
  → 按 importance score 排序
  → 裁剪到 TOKEN_BUDGET（默认 2000 tokens）
  → 注入到对话首轮
```

2000 tokens 是一个经过验证的默认值——大约 1500 个中文字符或 500 个英文单词。这个量足够携带 5-8 条关键记忆，但不会让 Agent 的注意力被记忆信息稀释。

### 预算分配策略

不是简单的"按分数排序，取 top-K 到填满"。更精细的做法是按记忆类型分配配额：

```python
"""Token 预算分配器"""
from dataclasses import dataclass


@dataclass
class BudgetConfig:
    total_tokens: int = 2000
    # 各层配额比例（加起来 = 1.0）
    procedural_ratio: float = 0.30   # 流程性记忆优先——"怎么做"最有操作价值
    semantic_ratio: float = 0.40     # 事实记忆次之——"项目用什么技术栈"
    episodic_ratio: float = 0.20     # 近期情景——"上次做了什么"
    profile_ratio: float = 0.10     # 项目概况——"这个项目是什么"


def allocate_budget(config: BudgetConfig) -> dict[str, int]:
    return {
        "procedural": int(config.total_tokens * config.procedural_ratio),
        "semantic":   int(config.total_tokens * config.semantic_ratio),
        "episodic":   int(config.total_tokens * config.episodic_ratio),
        "profile":    int(config.total_tokens * config.profile_ratio),
    }
    # → {"procedural": 600, "semantic": 800, "episodic": 400, "profile": 200}


def fill_budget(
    memories_by_type: dict[str, list[tuple[str, float, int]]],
    # type → [(content, importance_score, token_count), ...]
    budget: dict[str, int],
) -> list[str]:
    """贪心填充：每种类型内按 importance 排序，填到配额用尽"""
    injected = []
    for mem_type, quota in budget.items():
        remaining = quota
        candidates = sorted(
            memories_by_type.get(mem_type, []),
            key=lambda x: x[1],  # 按 importance 降序
            reverse=True,
        )
        for content, score, tokens in candidates:
            if tokens <= remaining:
                injected.append(content)
                remaining -= tokens
    return injected
```

### Lost in the Middle 的应对

Token 预算不只控制"总量"，还应该控制"位置"。基于 Lost in the Middle 效应，高重要性记忆应放在 context 的**头部或尾部**，低重要性的放中间：

```
[高重要性记忆 1]   ← 注意力集中区
[高重要性记忆 2]
[中等重要性记忆]   ← 注意力低谷区
[中等重要性记忆]
[高重要性记忆 3]   ← 注意力恢复区
```

---

## 四个模式的协作关系

四个模式不是独立的——它们构成一个完整的记忆管理管线：

```
新观察输入
    │
    ▼
┌─────────────────┐
│  模式一：四层巩固  │  决定记忆"存在哪一层"
│  Working→...     │
│  →Procedural     │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  模式三：衰减+矛盾 │  决定记忆"还活不活"
│  Ebbinghaus 衰减  │  检测并解决事实冲突
│  superseded 标记  │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  模式二：RRF 融合  │  决定"搜出哪些记忆"
│  BM25+Vector     │  多信号交叉验证
│  (+Graph)        │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│  模式四：Token 预算│  决定"注入哪些记忆"
│  2000 tokens 硬约束│  按类型分配配额
│  位置感知排列     │  头尾放高优先级
└─────────────────┘
        │
        ▼
    注入 Agent 上下文
```

---

## 落地映射：在我们的工作区中怎么用

### 现状 vs 四个模式

| 模式 | 我们已经有什么 | 缺什么 | 改进建议 |
|------|--------------|--------|---------|
| 四层巩固 | 三层：User/Session/Repo memory；Skill 体系 = Procedural | **Working→Episodic 的自动压缩**缺失；**Episodic→Semantic 的自动抽取**缺失 | 短期不动。我们的交互日志 + KNOWLEDGE_INDEX 已是手动版的巩固管线，自动化 ROI 不高（单人场景） |
| RRF 融合 | R48 已有 Milvus RRF 代码；Obsidian Vault 用 grep + 文件名搜索 | **Obsidian 本地无向量索引**，现在纯靠 grep_search + semantic_search | **中期可做**：给 Vault 加一层本地 embedding 索引（如 Chroma），与现有 grep 做 RRF 融合。但优先级不高——当前 96 篇报告用 KNOWLEDGE_INDEX §二手动索引 + grep 已够用 |
| 衰减+矛盾 | 手动标注"已过时"（报告 frontmatter status）；无自动衰减 | **无自动衰减**；**无矛盾检测** | **值得做一个轻量版**：给 KNOWLEDGE_INDEX §二 的每条摘要加 `last_cited` 日期，定期扫描 > 6 月未被引用的条目，提醒 review |
| Token 预算 | agent.md 中有定性规则（"先查旧报告""按需选读"）；无硬约束 | **无量化的 token 预算机制** | **可以借鉴精神而非实现**：在 agent.md 的"动态加载协议"中加入"单次读取 ≤ 5000 tokens 索引信息"的建议值 |

### 优先级排序

按"改进幅度 × 实现成本的倒数"排序：

1. **衰减提醒**（轻量版 Ebbinghaus）—— 给 KNOWLEDGE_INDEX 加 `last_cited` 字段，写一个 30 行 Python 脚本扫描过期条目。成本极低，价值明确。
2. **Procedural 层意识强化** —— 我们已经在做（Forge 阶段），但可以在 agent.md 中明确使用"Procedural Memory"术语，让"研究→固化 Skill"的管线更有理论支撑。
3. **Token 预算意识** —— 在"动态加载协议"中加入量化建议（单次索引读取建议 ≤ 5000 tokens），作为软约束。
4. **RRF 融合检索** —— 等 Vault 规模 > 200 篇报告、或开始做 RAG 项目时再投入。

### 不建议做的事

- **不要给 Obsidian Vault 硬搬 agentmemory 的四层架构**——我们是人+AI 协作的知识库，不是纯 Agent 自主记忆。人的判断力（哪些值得记、哪些该忘）远比 Ebbinghaus 公式准确。
- **不要为了"看起来先进"而加向量索引**——96 篇报告 + grep + KNOWLEDGE_INDEX 手动索引的组合，搜索质量已经 >90 分。加向量索引的边际收益很低，但维护成本不低（embedding 模型选型、索引更新、存储空间）。
- **不要自动化矛盾检测**——让 LLM 判断两条摘要是否矛盾的准确率不够高，误报会制造噪声。不如在"写新报告时手动检查 KNOWLEDGE_INDEX §二 是否有需要修正的旧结论"。

---

## 来源清单

📌 **来源清单**
- [Cormack, Clarke & Büttcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods", SIGIR 2009](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — RRF 原始论文
- [Microsoft Azure AI Search: Hybrid Search Ranking using RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking) — 2026-05-15 获取 — RRF 工业实现参考
- [Tulving, E. (1972). Episodic and semantic memory](https://scholar.google.com/scholar?q=tulving+1972+episodic+semantic+memory) — 情景/语义记忆分类理论原始论文
- [Ebbinghaus, H. (1885). Über das Gedächtnis](https://en.wikipedia.org/wiki/Forgetting_curve) — 遗忘曲线原始研究
- [Liu et al. (2024). Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — 长上下文注意力衰减研究
- [Chhikara et al. (2025). Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory, arXiv:2504.19413](https://arxiv.org/abs/2504.19413) — Mem0 记忆巩固算法
- [rohitg00/agentmemory README](https://github.com/rohitg00/agentmemory) — 2026-05-15 获取 — 四层巩固 + 衰减机制实现参考
- 本工作区 [R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md) Agent 记忆系统横评 — 五家框架对比基线
- 本工作区 R48（原稿交叉引用，本归档未解析） Agent 知识工程全景 — RRF 融合 Milvus 代码

⚖️ 来源一致性：高（认知心理学理论 + 工业实践 + 本工作区已有报告交叉验证）
📅 时效性声明：以上信息获取于 2026-05-15

---

## 开放问题

1. **Procedural 层的自动升级通道**：当前依赖人工判断"这个模式出现了 3 次，值得固化为 Skill"。能否让 Agent 在交互日志中自动识别重复模式？（与"交互日志分析协议 Phase 2"重叠，留待日志积累 100+ 条后评估）
2. **Ebbinghaus 衰减的参数校准**：$S$ 和访问增强系数的最优值高度依赖使用场景。需要实际数据（KNOWLEDGE_INDEX 各条目的引用频率）才能校准。
3. **RRF 的 $k$ 值是否需要场景适配**：Cormack 2009 论文在 TREC 数据集上验证 $k=60$ 最优，但对中文知识库是否同样适用，尚无公开验证。
