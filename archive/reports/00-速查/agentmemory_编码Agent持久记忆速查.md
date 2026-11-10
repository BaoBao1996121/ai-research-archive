> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# agentmemory 速查卡 — AI 编码 Agent 的持久记忆引擎

> **调研日期**：2026-05-15
> **项目**：[rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) · 9,070⭐ · Apache-2.0 · TypeScript
> **一句话**：给 Claude Code / Cursor / Codex 等编码 Agent 加装跨会话记忆——自动捕获、语义检索、注入上下文，不改一行 Agent 代码。
> **关联**：[R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)（Agent 记忆系统横评——通用框架赛道），[R46](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R46_%E5%A4%96%E9%83%A8%E8%B5%84%E8%AE%AF%E5%90%8C%E6%AD%A5_Agent%E6%8C%81%E7%BB%AD%E5%AD%A6%E4%B9%A0%E4%B8%89%E5%B1%82%E8%8C%83%E5%BC%8F.md)（外部资讯同步——claude-mem）

---

## 定位透镜

### 纵轴 · 它是怎么来的

| 时间线 | 事件 |
|--------|------|
| 2025 中 | Karpathy 提出 "LLM Wiki" 概念（给 LLM 长期记忆），rohitg00 写了一个 1,200⭐ 的 Gist 扩展该思路 |
| 2026 Q1 | 发布 agentmemory v0.1，定位"Claude Code 插件级记忆"，基于 iii 引擎（同一作者关联项目） |
| 2026-04-18 | v0.9.0：独立官网 agent-memory.dev、fs-watcher、standalone MCP |
| 2026-05 | 9K⭐ 爆发增长，GitHub Trending 首页，支持 16+ Agent 平台 |

**生命周期**：上升期（社区爆发增长中，但工程成熟度待观察——pinned iii-engine v0.11.2、Windows 支持需手动装二进制）

### 横轴 · 它和谁竞争

agentmemory 不在 R72 横评的赛道里。R72 覆盖的是**通用 Agent 记忆框架**（Mem0/Letta/Zep/LangMem），面向的是"你自己写的 Agent 需要记忆层"。agentmemory 面向的是**已有编码 Agent（Claude Code、Cursor 等）的外挂记忆增强**。

| | agentmemory | claude-mem (64K⭐) | 内置记忆 (CLAUDE.md/.cursorrules) | Mem0 (54K⭐) |
|---|---|---|---|---|
| 定位 | 编码 Agent 外挂记忆 | Claude Code 持久记忆插件 | 各 Agent 自带 | 通用记忆 API 层 |
| 集成方式 | MCP server + Hooks | Claude Code Hooks + SQLite+Chroma | 文件/配置 | SDK `add()`/`search()` |
| 搜索 | BM25 + Vector + Graph（RRF 融合） | Vector + BM25 | 全文加载进 context | Vector + Graph |
| 外部依赖 | **iii-engine**（Rust 二进制，Elastic License 2.0） | SQLite + Chroma | 无 | Qdrant / pgvector |
| 多 Agent 共享 | MCP + REST + leases + signals | 否 | 否 | API |
| Token 效率 | ~1,900 tokens/session（号称） | 待验证 | 22K+ tokens（240 obs 时） | 因集成而异 |
| 自部署 | 本地优先 | 本地 | 本地 | OSS + Cloud |

### 交叉判断

agentmemory 的独特价值是**零侵入集成**——不改 Agent 代码，通过 Hook 自动捕获 + MCP 暴露 51 个工具。但它绑定了 **iii-engine**（一个 Elastic License 2.0 的 Rust 运行时），这是最大的架构耦合点。

---

## 核心架构

```
PostToolUse hook 触发
  → SHA-256 去重 (5min 窗口)
  → 隐私过滤 (剥离 secrets/API keys)
  → 存储原始 observation
  → LLM 压缩 → 结构化 facts + concepts + narrative
  → 向量 embedding (6 种 provider + 本地)
  → 索引到 BM25 + Vector

Stop/SessionEnd hook 触发
  → 会话摘要
  → 知识图谱抽取 (可选)
  → Slot 反思 (可选)

SessionStart hook 触发
  → 加载项目 profile
  → 混合搜索 (BM25 + Vector + Graph)
  → Token 预算控制 (默认 2000 tokens)
  → 注入到对话
```

**四层记忆巩固**（仿人脑睡眠巩固模型）：

| 层级 | 内容 | 类比 |
|------|------|------|
| Working | 原始 tool use 观察 | 短期记忆 |
| Episodic | 压缩的会话摘要 | "发生了什么" |
| Semantic | 提取的事实和模式 | "我知道什么" |
| Procedural | 工作流和决策模式 | "怎么做" |

记忆按 Ebbinghaus 遗忘曲线衰减，高频访问的记忆增强，过时记忆自动驱逐，矛盾检测并解决。

---

## 关键数字

| 指标 | 数值 | 说明 |
|------|------|------|
| 检索 R@5 | 95.2% | LongMemEval-S (ICLR 2025, 500题) |
| 检索 R@10 | 98.6% | 同上 |
| Token/年 | ~170K (~$10) | 对比全量粘贴 19.5M+ |
| MCP 工具数 | 51 | core 8 + extended 43 |
| Hook 数 | 12 | 全自动，零手动 |
| 测试数 | 827 | ~1.7s 运行 |
| 代码量 | 118 文件 / ~21,800 LOC | |
| 支持 Agent | 16+ | Claude Code/Cursor/Codex/Gemini CLI/... |

---

## 本地可用性评估

### Windows 部署路径

三个选项，从易到难：

| 方案 | 步骤 | 限制 |
|------|------|------|
| **C: MCP only**（最简） | `npx -y @agentmemory/mcp` | 无 REST API、无 viewer、无 cron |
| **A: 预构建二进制** | 下载 iii-engine v0.11.2 Windows 二进制 → 加 PATH → `npx @agentmemory/agentmemory` | 必须 pin v0.11.2，v0.11.6+ 不兼容 |
| **B: Docker Desktop** | 装 Docker Desktop → `npx @agentmemory/agentmemory` | 需要 Docker 常驻 |

### 与我们工作区的关系

我们的工作区**已经有一套自建的持久记忆体系**：
- `/memories/` 三层记忆（User / Session / Repo）
- `KNOWLEDGE_INDEX.md` + `DELIVERABLES_INDEX.md` 知识索引
- `RECENT.md` 自动刷新
- 交互日志 `sessions/interaction-log/`
- agent.md 中的完整研究方法论

agentmemory 解决的问题（跨会话记忆、语义检索、自动捕获）和我们的体系有**部分重叠但定位不同**：
- 我们的体系是**知识管理驱动**（面向研究沉淀和方法论复用）
- agentmemory 是**编码会话驱动**（面向"上次改了什么文件、用了什么方案"的即时回忆）

### 值不值得装

**结论：现阶段不建议引入。** 理由：

1. **iii-engine 耦合是硬伤**：核心运行时 Elastic License 2.0（不是纯 OSS），且 Windows 支持是二等公民（无 installer、无 scoop/winget）。引擎版本 pin 在 v0.11.2 而最新已 v0.11.6+，说明 agentmemory 追不上 iii 的迭代速度。
2. **我们的场景不是它的甜蜜区**：agentmemory 最大价值是"多人团队、频繁切换编码会话、不同 Agent 间共享记忆"。我们是单人研究场景，VS Code Copilot 的 memory 机制 + 我们的 KNOWLEDGE_INDEX 已经覆盖了核心需求。
3. **benchmark 需要打折**：95.2% R@5 在 LongMemEval-S 上的分数是自测自报，对比基线是 BM25-only 和 grep，没有与 Mem0/Letta 在**同一 benchmark** 上的公开第三方对照。
4. **复杂度收益比不划算**：为了"Agent 自动记住上次改了哪个文件"，需要跑一个 Rust 运行时 + MCP server + SQLite + 向量索引——杀鸡用牛刀。

**什么时候重新评估**：
- 当我们开始用 Claude Code CLI（非 VS Code Copilot）做重度编码，且会话频繁中断重启
- 当 agentmemory 脱离 iii-engine 依赖，或 iii Windows 支持成熟
- 当出现独立第三方 benchmark 验证其检索质量

---

## 值得借鉴的设计思路

即使不装 agentmemory，它的几个设计值得记住：

1. **四层记忆巩固**（Working→Episodic→Semantic→Procedural）—— 我们的三层记忆可以参考这个分类（目前缺 Procedural 层）
2. **RRF 融合检索**（BM25 + Vector + Graph，Reciprocal Rank Fusion k=60）—— 比纯 vector 或纯 BM25 更鲁棒
3. **Token 预算控制**（默认 2000 tokens/session）—— 硬约束注入上下文的量，避免信息过载
4. **Ebbinghaus 衰减 + 矛盾检测**—— 记忆不是只增不减，需要主动遗忘和冲突解决

---

📌 **来源清单**
- [rohitg00/agentmemory README](https://github.com/rohitg00/agentmemory) — 2026-05-15 获取 — 项目文档和 benchmark 数据
- [rohitg00 GitHub profile](https://github.com/rohitg00?tab=repositories&sort=stargazers) — 2026-05-15 — 作者项目全景
- [iii-hq/iii](https://github.com/iii-hq/iii) — 15.7K⭐ — 底层运行时引擎信息
- 本工作区 [R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md) Agent 记忆系统横评 — 竞品格局参照

⚖️ 来源一致性：基本一致（信息主要来自项目官方文档，缺乏独立第三方验证）
📅 时效性声明：以上信息获取于 2026-05-15
