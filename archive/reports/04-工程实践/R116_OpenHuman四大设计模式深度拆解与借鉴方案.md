> 脱敏公开版 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../ARCHIVE_POLICY.md)。

# R116 · OpenHuman 四大设计模式深度拆解与借鉴方案

> 一句话概括：拆解 OpenHuman 中 Memory Tree 双写、TokenJuice 压缩、hint-based 模型路由、auto-fetch 定时拉取四个设计模式的内部机制，并给出在我们自己的 Agent 项目中落地的具体方案
> 研究日期：2026-05-15
> 关联报告：OpenHuman 速查卡（reports/00-速查/OpenHuman_个人AI助手速查.md）、R20 Obsidian Wiki 知识库方案、R09 大规模知识库检索方案

---

## 目录

- [定位透镜](#定位透镜)
- [模式一：Memory Tree — 分层压缩记忆](#模式一memory-tree--分层压缩记忆)
- [模式二：TokenJuice — 工具输出压缩](#模式二tokenjuice--工具输出压缩)
- [模式三：hint-based 模型路由](#模式三hint-based-模型路由)
- [模式四：auto-fetch 定时拉取](#模式四auto-fetch-定时拉取)
- [四个模式的交叉关系](#四个模式的交叉关系)
- [结论与优先级建议](#结论与优先级建议)
- [开放问题](#开放问题)

---

## 定位透镜

**这四个模式不是 OpenHuman 发明的**——它们是 Agent 工程领域里几个独立演化的工程模式。OpenHuman 的贡献是把它们整合到了一个产品里。拆解它们的价值在于：每个模式都可以独立采用，不需要买 OpenHuman 的整套方案。

**纵轴**：这四个模式分别来自不同的技术谱系——Memory Tree 来自知识图谱 + 摘要树研究；TokenJuice 来自 Agent 终端输出优化社区（vincentkoc/tokenjuice 是独立开源项目）；模型路由来自 LLM Gateway/Proxy 领域；auto-fetch 来自数据同步/ETL 领域。

**横轴**：每个模式都有现成的替代方案和开源实现，不必从零造轮子。报告会对每个模式标注"最小实现成本"和"现成可用的工具"。

---

## 模式一：Memory Tree — 分层压缩记忆

### 它解决什么问题

LLM 是无状态的。每次对话上下文窗口塞满后，旧信息就丢了。现有的"记忆"方案要么是聊天级的（Claude/ChatGPT 记住几个 bullet point），要么是 RAG 级的（向量检索，没有层次结构，检索质量不稳定）。

Memory Tree 的核心洞察：**记忆不只是"什么和这个查询相似"，还需要回答"今天发生了什么""这个人最近怎么样""上周二那件事的细节"**。向量搜索只解决了第一个，后面几个需要结构化的层级摘要。

### 架构拆解

```
source adapters (email/chat/doc)
        │
        ▼
   canonicalize     → 标准化为 Markdown + 元数据
        │
        ▼
     chunker        → 确定性 ID（内容寻址），≤3k token
        │
        ▼
   content_store    → 原子 .md 文件落盘（Obsidian vault）
        │
        ▼
     store          → SQLite 持久化（chunks/scores/summaries/jobs）
        │
        ▼
     score          → 嵌入 + 实体抽取 + 信号评分
        │
        ▼
  三棵摘要树        → Source Tree / Topic Tree / Global Tree
        │
        ▼
   retrieval        → search / drill_down / topic / global / fetch
```

**关键设计决策**：

1. **确定性分块**：Chunk ID 是内容寻址的（content-addressed），重复 ingest 不会产生重复行。这消除了"同一封邮件被处理两次"的问题。
2. **双写**：同一份数据同时写 SQLite（Agent 查询用，快、结构化）和 `.md` 文件（人类用 Obsidian 浏览、可编辑）。人类的编辑会在下次 ingest 时被 Agent 感知。
3. **三棵树**：
   - **Source Tree**：按数据源（Gmail、Slack、GitHub）分别维护，有 L0→L1→L2 的逐级摘要。L0 缓冲区满了就 seal 成 L1 摘要，L1 满了 seal 成 L2
   - **Topic Tree**：按实体（人名、项目名）聚合，热度驱动——出现越多的实体，其 Topic Tree 越深
   - **Global Tree**：每天一个全局摘要节点，回答"今天发生了什么"
4. **Leaf 生命周期状态机**：`pending_extraction → admitted → buffered → sealed`（或 `→ dropped`），保证 chunk 不会卡在中间态
5. **后台 Worker 池**：嵌入生成、实体抽取、摘要构建等重活交给后台 Worker（默认 3 个），共享信号量限制并发 LLM 调用

### 值得借鉴的核心点

| 要素 | 值得抄 | 不值得抄 |
|------|--------|---------|
| 确定性分块 + 内容寻址 ID | ✅ 消除重复，幂等性好 | — |
| SQLite + Markdown 双写 | ✅ Agent 可查 + 人类可读 | — |
| 三棵树的分层摘要 | ⚠️ Source Tree 和 Global Tree 有价值 | Topic Tree 的"热度驱动"在小数据量下过度工程 |
| 后台 Worker 池 + 持久任务队列 | ✅ 防止 ingest 阻塞前端 | Rust 实现复杂度高，Python 版更合适 |
| Leaf 状态机 | ⚠️ 大规模数据有意义 | 数据量小时直接同步写即可 |

### 如何在我们的 Agent 项目中借鉴

**最小可用方案（Python，~200 行核心代码）**：

```python
# 思路骨架，非完整实现

import hashlib, json, sqlite3
from pathlib import Path
from datetime import date

class MemoryTree:
    def __init__(self, workspace: Path):
        self.db_path = workspace / "memory.db"
        self.vault_path = workspace / "wiki"
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def ingest(self, source: str, content: str, metadata: dict):
        """确定性分块 + 双写"""
        chunks = self._chunk(content, max_tokens=3000)
        for chunk in chunks:
            chunk_id = self._content_hash(chunk)
            # SQLite 写入（Agent 用）
            self._upsert_chunk(chunk_id, source, chunk, metadata)
            # Markdown 写入（人类用）
            self._write_md(source, chunk_id, chunk, metadata)

    def _content_hash(self, text: str) -> str:
        """内容寻址：相同内容 = 相同 ID → 幂等"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _chunk(self, text: str, max_tokens: int) -> list[str]:
        """按段落/句子边界分块，每块 ≤ max_tokens"""
        # 实现略：按 \n\n 分段，超长段落再按句号切
        ...

    def summarize_source(self, source: str) -> str:
        """L0 chunks → L1 摘要（可用 LLM 或提取式）"""
        chunks = self._get_chunks_by_source(source)
        # 当 chunks 数量超过阈值，调用 LLM 做摘要
        ...

    def daily_digest(self) -> str:
        """全局日摘要：今天所有新 chunk 的一句话概括"""
        today = date.today().isoformat()
        chunks = self._get_chunks_by_date(today)
        # 调用 LLM："用 3-5 句话概括今天的信息"
        ...
```

**现成替代方案对比**：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| 直接用我们的 Obsidian 知识库 | 已有，零成本 | 没有 SQLite 查询层、没有分层摘要 | 已经在用 |
| mem0（开源记忆层） | API 简单、支持多 LLM | 黑盒向量存储、无层级结构 | 快速接入 |
| 自建 Memory Tree（如上） | 完全可控、理解透彻 | 需要自己写和维护 | 需要深度定制时 |
| Zep（开源 Agent 记忆） | 支持对话+事实记忆 | 需要部署服务端 | 多用户场景 |

**我的建议**：我们已经在用 Obsidian vault 做知识库管理（KNOWLEDGE_INDEX 就是这个角色），最有价值的增量是**加一个 SQLite 索引层**让 Agent 能快速检索，而不是重建整个 Memory Tree。Source Tree 的 L0→L1 摘要机制值得在自动化报告归档时采用。

---

## 模式二：TokenJuice — 工具输出压缩

### 它解决什么问题

Agent 调用工具（shell 命令、API 请求、网页抓取）后，工具输出经常是一大坨噪声——`git status` 的冗余头部、`pnpm test` 的进度条、HTML 页面的导航栏。这些噪声进入 LLM 上下文窗口后：
- **浪费 Token**（= 浪费钱）
- **稀释有效信息**（LLM 在噪声中找关键信息的能力会下降）
- **挤占上下文空间**（留给后续推理的 token 更少了）

### TokenJuice 的实际架构

TokenJuice 不是 OpenHuman 独有的——它是 [vincentkoc/tokenjuice](https://github.com/vincentkoc/tokenjuice) 独立开源项目（211 Stars，MIT 协议，TypeScript 实现），已经集成了 Claude Code、Cursor、Copilot CLI、VS Code Copilot Chat 等 15+ 编码 Agent。

```
工具调用结果
      │
      ▼
TokenJuice（classify → match rule → reduce）
      │
      ▼
LLM 上下文
```

**核心机制：规则驱动的确定性压缩**（不是 LLM 摘要，是正则+规则）

```json
// 一条规则的结构示例（git/status 规则）
{
  "id": "git/status",
  "family": "git-status",
  "match": {
    "argv0": ["git"],
    "gitSubcommands": ["status"]
  },
  "transforms": {
    "stripAnsi": true,           // 去 ANSI 颜色码
    "dedupeAdjacent": true,      // 去相邻重复行
    "trimEmptyEdges": true       // 去首尾空行
  },
  "filters": {
    "skipPatterns": [             // 丢弃匹配的行
      "^On branch ",
      "^Your branch is "
    ]
  },
  "summarize": {
    "head": 10,                  // 保留前 10 行
    "tail": 4                    // 保留后 4 行
  },
  "failure": {
    "preserveOnFailure": true,   // 失败时保留更多
    "head": 12,
    "tail": 12
  },
  "counters": [                  // 计数器摘要
    { "name": "modified", "pattern": "modified:" }
  ]
}
```

**三层规则覆盖**：
1. **内置规则**（`src/rules/`）：git、npm/pnpm、docker、cargo 等常见命令
2. **用户全局规则**（`~/.config/tokenjuice/rules/`）：个人偏好
3. **项目级规则**（`.tokenjuice/rules/`）：项目特定

**设计哲学**——引用原作者的话："prefer deterministic reducers over vague summaries"。这不是用 LLM 做摘要（那会引入延迟和幻觉），而是用规则做确定性裁剪。

### 值得借鉴的核心点

| 要素 | 值得抄 | 不值得抄 |
|------|--------|---------|
| 规则驱动 + 确定性裁剪 | ✅ 无延迟、无幻觉、可审计 | — |
| 三层规则覆盖（内置→用户→项目） | ✅ 灵活且不需 fork | — |
| 失败时保留更多上下文 | ✅ 关键洞察：出错时信息更重要 | — |
| 计数器摘要 | ✅ "3 files modified" 比原始输出信息密度高 | — |
| 完整的 CLI 工具链 | ⚠️ 如果用 Claude Code/Copilot 可直接集成 | 如果自建 Agent 不需要 CLI |

### 如何在我们的 Agent 项目中借鉴

**方案 A：直接用 TokenJuice（推荐，成本最低）**

```powershell
# 安装
npm install -g tokenjuice

# 集成到 VS Code Copilot Chat
tokenjuice install vscode-copilot

# 集成到 Claude Code
tokenjuice install claude-code

# 验证安装
tokenjuice doctor hooks
```

安装后，Agent 的工具调用输出会自动经过 TokenJuice 压缩，你什么都不用改。

**方案 B：在自建 Agent 中实现类似逻辑**

如果你在构建自己的 Agent，可以在工具调用的 postprocess 阶段加一个压缩层：

```python
import re
from dataclasses import dataclass

@dataclass
class CompressRule:
    """工具输出压缩规则"""
    command_pattern: str           # 匹配哪个命令
    skip_patterns: list[str]       # 删掉匹配的行
    head: int = 20                 # 保留前 N 行
    tail: int = 10                 # 保留后 N 行
    strip_ansi: bool = True        # 去 ANSI 颜色码
    failure_head: int = 40         # 失败时保留更多
    failure_tail: int = 40

# 内置规则示例
RULES = [
    CompressRule(
        command_pattern=r"^git\s+status",
        skip_patterns=[r"^On branch ", r"^Your branch is "],
        head=15, tail=5
    ),
    CompressRule(
        command_pattern=r"^(npm|pnpm|yarn)\s+test",
        skip_patterns=[r"^\s*$", r"^>"],
        head=10, tail=20  # 测试输出尾部更重要
    ),
]

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

def compress_tool_output(command: str, output: str, exit_code: int) -> str:
    """在工具输出进入 LLM 上下文之前压缩"""
    rule = _match_rule(command)
    if not rule:
        return _fallback_compress(output)

    lines = output.splitlines()
    if rule.strip_ansi:
        lines = [ANSI_RE.sub("", l) for l in lines]
    lines = [l for l in lines
             if not any(re.search(p, l) for p in rule.skip_patterns)]

    is_failure = exit_code != 0
    h = rule.failure_head if is_failure else rule.head
    t = rule.failure_tail if is_failure else rule.tail

    if len(lines) <= h + t:
        return "\n".join(lines)

    omitted = len(lines) - h - t
    return "\n".join(
        lines[:h]
        + [f"\n... ({omitted} lines omitted) ...\n"]
        + lines[-t:]
    )
```

**方案 C：仅做 HTML→Markdown 压缩（针对 RAG/网页抓取场景）**

OpenHuman 的 TokenJuice 在 RAG 场景中的最大价值是 HTML→Markdown 转换。如果你的 Agent 做网页抓取，加这一层能立刻降 60-80% 的 Token 消耗。现成工具：`html2text`（Python）、`turndown`（JS）。

**我的建议**：方案 A 是**此刻就能做**的事——装个 TokenJuice 到 VS Code Copilot/Claude Code 上，零代码改动就能享受压缩。方案 B 留给自建 Agent 项目。

---

## 模式三：hint-based 模型路由

### 它解决什么问题

一个 Agent 在执行过程中需要做各种不同重量级的任务：
- 判断"这封邮件是不是垃圾邮件" → 小模型就够
- "帮我重构这段 500 行的代码" → 需要强推理模型
- "这张图片里是什么" → 需要视觉模型

如果所有任务都走同一个大模型，**成本高、延迟大**。如果让用户手动切换模型，**认知负担大、容易选错**。

### OpenHuman 的路由机制

```rust
// src/openhuman/providers/router.rs（简化版）
fn resolve(&self, model: &str) -> (usize, String) {
    if let Some(hint) = model.strip_prefix("hint:") {
        // hint:reasoning → 路由到 Claude Opus / GPT-4o
        // hint:fast       → 路由到 Claude Haiku / GPT-4o-mini
        // hint:vision     → 路由到有视觉能力的模型
        if let Some((idx, resolved_model)) = self.routes.get(hint) {
            return (*idx, resolved_model.clone());
        }
    }
    // 没有 hint 前缀 → 直接用指定模型
    (self.default_index, model.to_string())
}
```

**hint 类型表**：

| Hint | 典型路由目标 | 使用场景 |
|------|-------------|---------|
| `hint:reasoning` | Claude Opus / GPT-4o | 复杂推理、代码重构、方案设计 |
| `hint:agentic` | Claude Sonnet / GPT-4o | Agent loop 主循环 |
| `hint:coding` | Claude Sonnet / GPT-4o | 代码生成与编辑 |
| `hint:fast` | Claude Haiku / GPT-4o-mini | 分类、格式化、情感分析 |
| `hint:vision` | Claude Sonnet(vision) / GPT-4o | 图像理解 |
| `hint:summarize` | 本地 Gemma 或云端 Haiku | 摘要生成 |
| `hint:tool_lite` | 本地或 Haiku | 轻量工具调用响应 |

**关键设计决策**：
1. **hint 是 Agent loop 自己发出的**，不是用户选的。Agent 根据当前要做的事自动标注 hint
2. **路由表可运行时重映射**，无需重启
3. **有本地 AI 时，轻量 hint 优先路由到 Ollama**，重度 hint 始终走云端
4. **一个订阅覆盖多供应商**——路由器在后端代理层工作，用户无需各自申请 API Key

### 值得借鉴的核心点

| 要素 | 值得抄 | 不值得抄 |
|------|--------|---------|
| hint 前缀约定 | ✅ 简洁优雅，易扩展 | — |
| Agent 自动标注 hint | ✅ 用户无感知 | — |
| 路由表可配置可覆盖 | ✅ 灵活性好 | — |
| 一个订阅覆盖多供应商 | ❌ 这是商业模式不是技术 | 我们用 BYO Key 更灵活 |
| 健康检查 + 降级 | ✅ Ollama 挂了自动回退云端 | — |

### 如何在我们的 Agent 项目中借鉴

**Python 实现骨架**：

```python
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class ModelRoute:
    provider: str   # "anthropic" / "openai" / "ollama"
    model: str      # "claude-sonnet-4" / "gpt-4o-mini" / "gemma3:1b"

# 路由表——可从配置文件/环境变量加载
DEFAULT_ROUTES: dict[str, ModelRoute] = {
    "reasoning": ModelRoute("anthropic", "claude-sonnet-4"),
    "fast":      ModelRoute("openai", "gpt-4o-mini"),
    "coding":    ModelRoute("anthropic", "claude-sonnet-4"),
    "vision":    ModelRoute("openai", "gpt-4o"),
    "embedding": ModelRoute("ollama", "all-minilm:latest"),
    "summarize": ModelRoute("ollama", "gemma3:1b-it-qat"),
}

class ModelRouter:
    def __init__(self, routes: Optional[dict] = None):
        self.routes = routes or DEFAULT_ROUTES

    def resolve(self, model_or_hint: str) -> ModelRoute:
        """hint:reasoning → 路由；直接模型名 → 透传"""
        if model_or_hint.startswith("hint:"):
            hint = model_or_hint[5:]
            if hint in self.routes:
                return self.routes[hint]
        # fallback：当具体模型名传入
        return ModelRoute("anthropic", model_or_hint)

    def is_local_available(self, hint: str) -> bool:
        """检查本地模型是否可用"""
        route = self.routes.get(hint)
        if route and route.provider == "ollama":
            # 实际检查 Ollama 健康
            ...

# Agent loop 中使用
router = ModelRouter()

# 分类任务 → 自动选小模型
route = router.resolve("hint:fast")
# → ModelRoute(provider='openai', model='gpt-4o-mini')

# 推理任务 → 自动选大模型
route = router.resolve("hint:reasoning")
# → ModelRoute(provider='anthropic', model='claude-sonnet-4')
```

**现成替代方案**：

| 方案 | Stars | 特点 | 适用场景 |
|------|-------|------|---------|
| LiteLLM | 17k+ | 统一 API 代理 100+ 模型 | BYO Key 多模型切换 |
| OpenRouter | 商业 | 一个 API 调多家模型 | 快速接入不想管多个 Key |
| 自建路由表（如上） | — | 轻量、完全可控 | Agent 内部决策 |

**我的建议**：如果你已经在用 LiteLLM 或类似代理，hint→model 的映射可以作为一层薄 wrapper 加在上面。关键价值不在路由器本身（代码很简单），而在 **Agent prompt 中让 Agent 学会自己标注 hint**——这需要在 system prompt 中教它："当你要做分类/格式化等轻量任务时，用 hint:fast；当你要做推理/代码生成时，用 hint:reasoning"。

---

## 模式四：auto-fetch 定时拉取

### 它解决什么问题

大多数 AI 助手是**被动的**：你问了才查。OpenHuman 的 auto-fetch 让 Agent 变成**主动的**：每 20 分钟自动从所有连接的数据源拉取新数据，Agent "已经有了明天的上下文"。

说白了：**这不是 AI 的创新，这是 ETL/数据同步的老思路**，只是把目标从"数据仓库"换成了"Agent 的记忆库"。

### 机制拆解

```
每 20 分钟全局 tick
    │
    ▼
遍历每个 active connection（Gmail, Notion, GitHub, ...）
    │
    ├── 检查 sync_state（上次同步时间、每日预算、去重集、游标）
    │
    └── 如果间隔已过 → provider.sync()
            │
            ├── 成功 → record_sync_success(timestamp)
            └── 失败 → 记日志，吞掉错误，下次再试
```

**关键设计决策**：

1. **一个全局定时器，不是每个 connection 一个**：简单、可维护。connection 数量不多（个人用户通常 5-20 个），不需要复杂调度
2. **状态按 `(toolkit, connection_id)` 隔离**：每个连接有独立的游标（cursor）、去重集（dedup set）、每日预算（daily budget）、最后同步时间
3. **错误吞掉不 panic**："scheduler must never panic out of its loop"——一个 connection 挂了不影响其他 connection
4. **Event-driven 同步和定时同步共享状态**：如果 webhook 已经触发了同步，定时器不会重复拉取
5. **每日预算**：防止 API 用量失控。比如 Gmail API 有每日配额，auto-fetch 不会打满

### 值得借鉴的核心点

| 要素 | 值得抄 | 不值得抄 |
|------|--------|---------|
| 定时 + 增量同步模式 | ✅ 让 Agent 有"先见之明" | — |
| 每个 source 独立游标/状态 | ✅ 断了一个不影响其他 | — |
| 每日预算限制 | ✅ 防止 API 打满 | — |
| 错误吞掉不崩 | ✅ 定时任务的铁律 | — |
| 20 分钟 tick 间隔 | ⚠️ 可配置更好 | 固定 20 分钟可能太频或太疏 |
| 118+ OAuth 集成 | ❌ 这是产品层面的工作量 | 按需接几个就够 |

### 如何在我们的 Agent 项目中借鉴

**适用场景判断**——先问一个问题：你的 Agent **需要主动感知外部变化**吗？

- 如果 Agent 只是回答问题（如 Copilot）→ **不需要** auto-fetch
- 如果 Agent 需要"早上打开就知道昨晚发生了什么"→ **需要**
- 如果 Agent 需要监控某些数据源（如 Jira ticket 状态、Git 仓库提交）→ **需要**

**最小实现（Python + APScheduler）**：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class SyncState:
    last_sync: datetime | None = None
    cursor: str | None = None       # 增量拉取游标
    daily_count: int = 0
    daily_budget: int = 100          # 每日最多调 100 次 API

class AutoFetcher:
    def __init__(self, memory_tree, interval_minutes: int = 20):
        self.memory_tree = memory_tree
        self.sources: dict[str, dict] = {}  # source_id → config
        self.states: dict[str, SyncState] = {}
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            self._tick,
            'interval',
            minutes=interval_minutes
        )

    def register_source(self, source_id: str, provider, config: dict):
        self.sources[source_id] = {
            "provider": provider, "config": config
        }
        self.states[source_id] = SyncState()

    def start(self):
        self.scheduler.start()

    def _tick(self):
        """全局 tick：遍历所有 source，逐个同步"""
        for source_id, source in self.sources.items():
            try:
                state = self.states[source_id]
                if state.daily_count >= state.daily_budget:
                    logger.info(f"{source_id}: daily budget exhausted")
                    continue

                new_items = source["provider"].fetch_since(
                    cursor=state.cursor
                )
                if new_items:
                    for item in new_items:
                        self.memory_tree.ingest(
                            source=source_id,
                            content=item["content"],
                            metadata=item["metadata"]
                        )
                    state.cursor = new_items[-1].get("cursor")
                    state.daily_count += 1
                state.last_sync = datetime.now()

            except Exception as e:
                # 关键：吞掉错误，不影响其他 source
                logger.error(f"{source_id} sync failed: {e}")
```

**我的建议**：auto-fetch 的价值取决于你有多少需要持续监控的数据源。如果只是"每天看看邮件"，手动触发就够了。如果项目需要持续感知多个工具的状态变化，就值得实现。**先从一个 source 开始**（比如飞书文档变更或 Git 仓库提交），验证模式后再扩展。

---

## 四个模式的交叉关系

这四个模式不是互相独立的——它们是一条数据流上的不同环节：

```
数据源（邮件、代码、文档）
    │
    ▼
auto-fetch（定时拉取增量数据）      ← 模式四
    │
    ▼
TokenJuice（压缩噪声，降低处理成本）← 模式二
    │
    ▼
Memory Tree（分块、评分、构建摘要树）← 模式一
    │
    ▼
Agent Loop（需要时从记忆树检索）
    │
    └──→ hint-based 路由（按任务选模型） ← 模式三
```

**关键交叉点**：
- TokenJuice 让 auto-fetch 在经济上可行——不压缩的话，每 20 分钟全量灌数据进 LLM 做摘要，Token 成本会爆炸
- Memory Tree 让 auto-fetch 有地方存东西——不只是存，还要能查、能摘要
- hint-based 路由让 Memory Tree 的后台 Worker 能用便宜模型做摘要，贵模型留给前台推理

如果只取一个，**TokenJuice 的 ROI 最高**——装一行命令就能降低现有 Agent 的 Token 消耗。如果取两个，再加**Memory Tree 的 SQLite 索引层**。

---

## 结论与优先级建议

| 优先级 | 模式 | 行动 | 成本 | 预期收益 |
|--------|------|------|------|---------|
| **P0 · 今天就做** | TokenJuice | `npm i -g tokenjuice && tokenjuice install vscode-copilot` | 5 分钟 | Agent 工具输出 Token 降 30-60% |
| **P1 · 本周** | hint-based 路由 | 在 Agent prompt 中加 hint 约定 + 轻量路由表 | 半天 | 轻量任务成本降 70%+，延迟降低 |
| **P2 · 需要时** | Memory Tree 双写 | 给 Obsidian 知识库加 SQLite 索引层 | 1-2 天 | Agent 检索速度和准确率提升 |
| **P3 · 有具体场景时** | auto-fetch | 先接一个数据源验证模式 | 2-3 天 | Agent 从"被动回答"变"主动感知" |

---

## 开放问题

1. **TokenJuice 在 Windows 上的兼容性**——官方文档显示部分 host integration 有 "native Windows shell interception is intentionally blocked for now" 的限制，需要实测
2. **Memory Tree 的 SQLite 索引和现有 KNOWLEDGE_INDEX.md 如何共存**——是替代还是补充？当前的 Markdown 索引对人类友好但不适合程序化查询
3. **hint-based 路由需要 Agent 有"任务分类能力"**——如果 Agent 自己标错 hint（把推理任务标成 fast），路由反而会降质。需要验证 Agent 的自标注准确率
4. **auto-fetch 的 daily budget 该设多少**——取决于 API 成本和数据量，需要实际跑几天数据来调参

---

> 📌 来源清单
> - [OpenHuman Memory Tree 文档](https://tinyhumans.gitbook.io/openhuman/features/obsidian-wiki/memory-tree) — 2026-05-11 更新 — 完整管道架构和三棵树设计
> - [OpenHuman Obsidian Wiki 文档](https://tinyhumans.gitbook.io/openhuman/features/obsidian-wiki) — 2026-05-10 更新 — vault 结构和双写机制
> - [OpenHuman Auto-fetch 文档](https://tinyhumans.gitbook.io/openhuman/features/obsidian-wiki/auto-fetch) — 2026-05-10 更新 — 定时同步机制
> - [OpenHuman Model Routing 文档](https://tinyhumans.gitbook.io/openhuman/features/model-routing) — 2026-05-10 更新 — hint 路由和 router.rs
> - [OpenHuman Token Compression 文档](https://tinyhumans.gitbook.io/openhuman/features/token-compression) — 2026-05-10 更新 — TokenJuice 集成
> - [vincentkoc/tokenjuice GitHub](https://github.com/vincentkoc/tokenjuice) — 211 Stars, MIT, v0.7.0 — 独立开源的 Token 压缩工具
> - [TokenJuice Rules Spec](https://github.com/vincentkoc/tokenjuice/blob/main/docs/rules.md) — 规则格式和编写指南
> - [TokenJuice Core Spec](https://github.com/vincentkoc/tokenjuice/blob/main/docs/spec.md) — 架构设计和 host adapter 协议
>
> ⚖️ 来源一致性：多源一致（OpenHuman 文档与 TokenJuice 独立仓库信息吻合）
> 📅 时效性声明：以上信息获取于 2026-05-15
