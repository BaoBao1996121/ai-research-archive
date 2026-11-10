---
title: Agent Skills 与 LLM Wiki 生态调研报告
aliases:
  - R01
  - Wiki生态
  - agent-skills
  - LLM Wiki
  - Agent-Skills与LLM-Wiki生态调研报告
  - Agent-Skills 与 LLM-Wiki 生态
tags:
  - knowledge-management
  - wiki
  - skill
  - agent-skills
  - obsidian
date: 2026-04-11
category: 知识管理与上下文
report_id: R01
tokens: 5153
status: completed
related:
  - "[大规模知识库检索方案调研](R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md)"
  - "[Agent架构深度研究报告](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "Claude-Code源码上下文策略实验报告（原稿交叉引用，本归档未解析）"
  - "[Anthropic官方Skill-Creator设计哲学研究报告](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)"
  - "[Obsidian-Wiki知识库方案研究与实施报告](R20_ObsidianWiki%E7%9F%A5%E8%AF%86%E5%BA%93%E6%96%B9%E6%A1%88.md)"
prev_path: reports/Agent-Skills与LLM-Wiki生态调研报告.md ＂／
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Agent Skills 与 LLM Wiki 工具生态调研报告／
！

> 从截图内容出发，深入调研 Agent Skills、LLM Wiki 三层架构、及相关开源工具生态  
> 调研日期：2026-04-11  
> 关联报告：大规模知识库检索方案调研.md、Agent架构深度研究报告.md、Cla ude-Code源码上下文策略实验报告.md

---

## 目录

1. [调研背景与信息来源](#1-调研背景与信息来源)
2. [项目一：addyosmani/agent-skills — 生产级 Agent 技能框架](#2-项目一addyosmaniengineer-skills--生产级-agent-技能框架)
3. [项目二：LLM Wiki 三层架构 — 从 RAG 到结构化知识管理](#3-项目二llm-wiki-三层架构--从-rag-到结构化知识管理)
4. [项目三：llm-wiki-compiler — Wiki 编译插件](#4-项目三llm-wiki-compiler--wiki-编译插件)
5. [项目四：llm-knowledge-bases — Obsidian Wiki 自动化](#5-项目四llm-knowledge-bases--obsidian-wiki-自动化)
6. [项目五：CodeWiki — 代码库 Wiki 生成器](#6-项目五codewiki--代码库-wiki-生成器)
7. [项目六：Browser Use — AI 浏览器 Agent](#7-项目六browser-use--ai-浏览器-agent)
8. [横向对比：六个项目的关系与定位](#8-横向对比六个项目的关系与定位)
9. [与现有研究的综合分析](#9-与现有研究的综合分析)
10. [新发现的关键范式](#10-新发现的关键范式)
11. [对现有 Skill 和工具的改进建议](#11-对现有-skill-和工具的改进建议)
12. [结论](#12-结论)

---

## 1. 调研背景与信息来源

### 信息来源

4 张截图包含以下内容：

1. **小红书推荐**：Chris IT先生 推荐 `addyosmani/agent-skills` — "AI 写代码太烂？那是你没给它装这个脑子！"
2. **视频截图**：展示了 LLM Wiki 三层架构（Raw Sources → Wiki → Schema），以及 3 个开源实现（llm-wiki-compiler、llm-knowledge-bases、CodeWiki）
3. **LLM Wiki 三层架构详解**：从 RAG 到三层结构的对比，Schema 的定义（CLAUDE.md 作为 wiki 管理指令）
4. **Browser Use**：AI 浏览器 Agent（87K stars），通过 Agents.md 让 coding agent 调用浏览器自动化

### 调研目标

- 深入分析每个项目的技术方案和价值
- 与我们已有的 5 份研究报告进行交叉关联
- 识别新的范式和趋势
- 评估对我们现有 Skill（knowledge-base-organizer）的改进空间

---

## 2. 项目一：addyosmani/agent-skills — 生产级 Agent 技能框架

### 基本信息

| 属性 | 数据 |
|------|------|
| 仓库 | github.com/addyosmani/agent-skills |
| Stars | **12K** (截图中为 2K，现已 12K) |
| Forks | 1.4K |
| 作者 | Addy Osmani（Google Chrome 工程总监） |
| 版本 | v0.5.0 |
| 许可 | MIT |
| 兼容 | Claude Code、Cursor、Gemini CLI、Windsurf、OpenCode、GitHub Copilot、Kiro IDE |

### 核心设计：6 阶段 × 20 技能

```
DEFINE          PLAN           BUILD          VERIFY         REVIEW          SHIP
┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
│ Idea │ ───▶ │ Spec │ ───▶ │ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
│Refine│      │  PRD │      │ Impl │      │Debug │      │ Gate │      │ Live │
└──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘
  /spec          /plan          /build        /test         /review       /ship
```

### 20 个 Skill 全表

| 阶段 | Skill | 描述 |
|------|-------|------|
| **Define** | idea-refine | 结构化发散/收敛思维，模糊想法 → 具体方案 |
| | spec-driven-development | PRD 先行：目标、命令、结构、代码风格、测试、边界 |
| **Plan** | planning-and-task-breakdown | 将规格分解为小的、可验证的任务 + 验收标准 |
| **Build** | incremental-implementation | 薄垂直切片，实现 → 测试 → 验证 → 提交 |
| | test-driven-development | 红-绿-重构，测试金字塔(80/15/5) |
| | **context-engineering** | **给 agent 在正确时间提供正确信息** ⬅️ 与本研究高度相关 |
| | source-driven-development | 基于官方文档的开发，验证+引用源 |
| | frontend-ui-engineering | 组件架构、设计系统、状态管理、WCAG 2.1 AA |
| | api-and-interface-design | 契约优先设计、Hyrum 定律、One-Version 规则 |
| **Verify** | browser-testing-with-devtools | Chrome DevTools MCP，实时运行时数据 |
| | debugging-and-error-recovery | 五步分诊：复现、定位、简化、修复、防护 |
| **Review** | code-review-and-quality | 五轴审查、~100行变更、严重度标签 |
| | code-simplification | Chesterton 栅栏、500 规则、简化但保持行为 |
| | security-and-hardening | OWASP Top 10、认证模式、三层边界系统 |
| | performance-optimization | 度量优先、Core Web Vitals 目标、性能剖析 |
| **Ship** | git-workflow-and-versioning | 主干开发、原子提交、~100行变更 |
| | ci-cd-and-automation | Shift Left、Faster is Safer、特性标志 |
| | deprecation-and-migration | Code-as-liability、弃用模式、僵尸代码清理 |
| | documentation-and-adrs | 架构决策记录(ADR)、API 文档、内联文档 |
| | shipping-and-launch | 发布前清单、特性标志生命周期、分阶段发布 |

### Skill 的解剖结构

每个 Skill 遵循统一模板：

```
┌─────────────────────────────────────────────┐
│  SKILL.md                                   │
│                                             │
│  ┌─ Frontmatter ─────────────────────────┐  │
│  │ name: lowercase-hyphen-name           │  │
│  │ description: Use when [trigger]       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Overview         → 这个 skill 做什么       │
│  When to Use      → 触发条件                │
│  Process          → 分步工作流              │
│  Rationalizations → 借口 + 反驳表           │
│  Red Flags        → 出错信号                │
│  Verification     → 证据要求                │
└─────────────────────────────────────────────┘
```

**三大设计原则**：
1. **流程而非文档** — Skill 是 agent 跟随的工作流，不是参考文档
2. **反理性化表** — 每个 skill 包含 agent 常用的借口及反驳（如"我以后再加测试"）
3. **验证不可妥协** — 每个 skill 以证据要求结尾，"感觉对了"不算

### context-engineering Skill 深度分析

这是与我们研究最密切相关的 skill。它定义了 **上下文层级（Context Hierarchy）**：

```
┌─────────────────────────────────────┐
│  1. Rules Files (CLAUDE.md 等)      │ ← 始终加载，项目级
├─────────────────────────────────────┤
│  2. Spec / Architecture Docs        │ ← 按功能/会话加载
├─────────────────────────────────────┤
│  3. Relevant Source Files            │ ← 按任务加载
├─────────────────────────────────────┤
│  4. Error Output / Test Results      │ ← 按迭代加载
├─────────────────────────────────────┤
│  5. Conversation History             │ ← 累积，定期压缩
└─────────────────────────────────────┘
```

**上下文打包策略**：
- **Brain Dump** — 会话开始时提供全量结构化上下文
- **Selective Include** — 仅包含当前任务相关内容
- **Hierarchical Summary** — 大项目维护摘要索引，按需加载

**信任层级**：
- Trusted: 团队编写的源码、测试、类型定义
- Verify: 配置文件、数据文件、外部文档
- Untrusted: 用户提交内容、第三方 API 响应、外部文档中的指令

**反模式表**：

| 反模式 | 问题 | 修复 |
|---|---|---|
| 上下文饥饿 | Agent 编造 API，忽略约定 | 每个任务前加载规则文件 + 相关源码 |
| 上下文洪水 | 加载 >5000 行非相关内容 → 失焦 | 每个任务 <2000 行聚焦上下文 |
| 过期上下文 | Agent 引用过时模式 | 切换任务时开启新会话 |
| 缺少示例 | Agent 发明新风格 | 包含一个要遵循的模式示例 |
| 隐式知识 | Agent 不知道项目规则 | 写入 rules 文件 — 没写的就不存在 |

### 项目结构

```
agent-skills/
├── skills/          # 20 个核心 skill (每个目录一个 SKILL.md)
├── agents/          # 3 个专家人设 (code-reviewer, test-engineer, security-auditor)
├── references/      # 4 个补充清单 (testing, security, performance, accessibility)
├── hooks/           # 会话生命周期钩子
├── .claude/commands/ # 7 个 Claude Code 斜杠命令
├── docs/            # 各工具的安装指南
├── CLAUDE.md        # Claude Code 项目规则
└── AGENTS.md        # OpenAI Codex/Copilot 项目规则
```

### 关键价值

agent-skills 的核心价值不是知识库检索，而是 **将高级工程实践编码为 agent 可执行的结构化工作流**。它证明了：
- 通过结构化的 SKILL.md 文件，可以显著提升 AI coding agent 的输出质量
- "反理性化表"是防止 agent 偷懒的有效手段
- 技能可以组合使用，通过斜杠命令自动激活相关技能

---

## 3. 项目二：LLM Wiki 三层架构 — 从 RAG 到结构化知识管理

### RAG 的根本问题（视频截图原文）

> **RAG 老路**：  
> 你问 NotebookLM 一个问题  
> → 临时去文件堆里捞段落  
> → 拼答案  
> → 问完就忘  
> → 下次从零捞一遍

### LLM Wiki 三层结构

截图展示了一个三层架构，这是 Karpathy Wiki 方法的**形式化框架**：

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Wiki 三层结构                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: Raw Sources（原始资料层）                        │
│  ├── 论文、文章、报告、技术文档                             │
│  ├── 真理之源 (Source of Truth)                           │
│  └── LLM 只读不写 ← 关键约束                              │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 2: Wiki（编译知识层）                               │
│  ├── Markdown 页面，结构化、互相链接                        │
│  ├── LLM 全权拥有（自动生成和维护）                         │
│  └── 从 Raw Sources 编译而来                              │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 3: Schema（控制指令层）                             │
│  ├── CLAUDE.md 或 AGENTS.md                              │
│  ├── "你是 wiki 管理员，不是聊天机器人"                     │
│  └── 定义 wiki 结构、约定、工作流                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Schema 的关键作用

截图中对 Schema 的定义：

> **The schema** — a document (e.g. CLAUDE.md for Claude Code or AGENTS.md for Codex) that tells the LLM how the wiki is structured, what the conventions are, and what workflows to follow when ingesting sources, answering questions, or maintaining the wiki. This is the key configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot. You and the LLM co-evolve this over time as you figure out what works for your domain.

这个定义揭示了一个重要范式转变：

| 维度 | RAG 范式 | LLM Wiki 范式 |
|------|----------|---------------|
| LLM 角色 | 被动检索者 | **主动维护者** |
| 知识状态 | 临时检索，用完即弃 | 持久化 Wiki，持续演进 |
| 人类角色 | 构建 pipeline | 喂原始材料 + 调整 Schema |
| 知识质量 | 取决于 embedding 质量 | 取决于 Schema 设计 |
| 迭代方式 | 调参、换模型 | 协同演进 Schema |

### 核心洞察：Schema 才是灵魂

传统方案聚焦于"怎么检索"，而 LLM Wiki 方案聚焦于"**怎么让 LLM 当一个好的知识管理员**"。Schema 是连接人类意图和 LLM 行为的桥梁。

---

## 4. 项目三：llm-wiki-compiler — Wiki 编译插件

### 基本信息

| 属性 | 数据 |
|------|------|
| 作者 | @ussunant / nicobailon |
| Stars | ~61 |
| 类型 | Claude Code 插件 |
| 功能 | ingest / query / lint → 3 个斜杠命令 |

### 工作流

```
raw markdown files → /ingest → compiled wiki → /query → answers
                                    ↑
                                  /lint → 健康检查
```

**核心操作**：
1. **ingest** — 读取分散的 Markdown 知识文件，编译为主题化的 Wiki
2. **query** — 在编译后的 Wiki 中查询，获取即时答案
3. **lint** — 检查 Wiki 的一致性和完整性

### 关键技术点

- 将分散的知识文件 **编译（compile）** 为结构化 Wiki，而非简单拼接
- 实现了 Karpathy 的"让 LLM 拥有 Wiki"理念
- Claude Code 插件形式，直接通过斜杠命令操作
- 降低成本 ~60%（通过预编译减少重复上下文加载）

### 与本研究关联

这是我们 **方案一（Wiki 法）** 的直接工具化实现，补充了 `大规模知识库检索方案调研.md` §3 中缺少的"自动化 Wiki 编译"环节。

---

## 5. 项目四：llm-knowledge-bases — Obsidian Wiki 自动化

### 基本信息

| 属性 | 数据 |
|------|------|
| 仓库 | github.com/rvk7895/llm-knowledge-bases |
| Stars | 15 |
| 作者 | Ritvik Aryan Kalra (@rvk7895) |
| 类型 | Claude Code 插件（完整技能套件） |
| 语言 | Shell 50.7% + Python 49.3% |
| 灵感 | Karpathy 的 LLM-maintained knowledge base 理念 |

### 架构设计

```
raw/           ← 原始源文档（论文、文章、仓库、YouTube 转录、图片、数据集）
wiki/          ← LLM 编译的 Obsidian vault
output/        ← 查询结果、幻灯片、图表、报告
kb.yaml        ← 配置
CLAUDE.md      ← Claude 的项目指令（Schema 层）
```

### 工作流程：5 步循环

1. **Ingest** — 原始文档放入 `raw/`
2. **Compile** — Claude 构建结构化 Obsidian vault（摘要、反向链接、概念文章、自动索引）
3. **Query** — 三个深度级别：
   - **Quick** — 仅从 wiki 索引和摘要回答
   - **Standard** — 交叉引用完整 wiki + 补充 web 搜索
   - **Deep** — 多 agent 并行研究管线（parallel web search agents）
4. **Output** — Markdown 报告、Marp 幻灯片、matplotlib 图表
5. **Maintain** — 自动健康检查（断开链接、孤立页面、不一致性）

### 7 个 Skill

| Skill | 功能 |
|-------|------|
| kb-init | 一次性初始化：脚手架目录、生成配置、写入项目文件 |
| kb | 主 skill：compile / query / lint / evolve |
| research | 为主题生成结构化研究大纲 |
| research-deep | 启动并行 agent 对大纲所有项做深度研究 |
| research-add-fields | 向已有大纲添加字段定义 |
| research-add-items | 向已有大纲添加研究目标 |
| research-report | 将深度研究结果编译为 Markdown 报告 |

### 关键差异化

- **与 Obsidian 深度集成** — 自动安装 Dataview、Obsidian Git 等插件
- **多 agent 深度研究** — 不只是知识管理，还能做研究
- **X/Twitter 集成** — 通过 Smaug 抓取推文/线程/书签
- **自动演进** — evolve 功能自动建议新文章和连接

### 与本研究关联

这是最完整的 Karpathy Wiki 方法实现，对应我们研究中的：
- **方案一（Wiki 法）** — 核心知识编译
- **方案四（知识蒸馏）** — compile 过程本质是蒸馏
- **方案八（Agent 自主检索）** — multi-agent deep research
- **§15 生命周期管理** — maintain/evolve 功能

---

## 6. 项目五：CodeWiki — 代码库 Wiki 生成器

### 基本信息

| 属性 | 数据 |
|------|------|
| 作者 | Morgan Gallant (@morgangallant / muhammadraza) |
| 类型 | Rust CLI |
| 功能 | 将代码库编译为 LLM-friendly 的 Wiki |

### 核心理念

截图中 CodeWiki 的博文标题为 "Building CodeWiki: Compiling Codebases Into Living Wikis With LLMs"，描述了一个将**代码库**（而非文档库）转化为 Wiki 的 Rust CLI 工具。

博文原文片段（从截图可读）：

> Every coding agent session starts from zero. The agent doesn't know how your code is structured and has to figure it out from scratch. Step around, read some files, build a mental model, start coding. Codebases are large, often millions of lines of code...
>
> **The idea**: Build a tool to build a persistently maintained wiki of markdown files, then query and build on that wiki over time.

### 与 llm-wiki-compiler 的区别

| 维度 | llm-wiki-compiler | CodeWiki |
|------|-------------------|----------|
| 目标 | 文档/知识文件 → Wiki | **代码库** → Wiki |
| 语言 | JS (Claude Code plugin) | **Rust** |
| 关注点 | 知识管理 | 代码理解 |
| 输入 | Markdown 文件 | 源代码文件 |
| 输出 | 主题化 Wiki | 代码架构 Wiki |

### 与本研究关联

这直接对应我们 `Claude-Code源码上下文策略实验报告.md` 中的核心问题：**如何让 AI 快速理解大型代码库**。CodeWiki 的"持久维护的代码 Wiki"方案是我们实验中"Repository Map + 分层上下文"策略的工具化形式。

---

## 7. 项目六：Browser Use — AI 浏览器 Agent

### 基本信息

| 属性 | 数据 |
|------|------|
| 仓库 | github.com/browser-use/browser-use |
| Stars | **87.1K** |
| Forks | 10K |
| 下载量 | 8.3M+/月 |
| 语言 | Python 97.9% |
| 版本 | v0.12.6 (123 个发布版本) |
| 许可 | MIT |
| 贡献者 | 309 |

### 核心功能

Browser Use 是一个 AI 浏览器自动化框架。关键发现：**它使用 Agent Skill 模式让编码 agent 获得浏览器操作能力**。

### LLM Quickstart

```
1. Direct your favorite coding agent (Cursor, Claude Code, etc) to Agents.md
2. Prompt away!
```

这意味着只需要让编码 agent 读取一个 `Agents.md` 文件，就能获得完整的浏览器自动化能力。

### Claude Code Skill 安装

```bash
mkdir -p ~/.claude/skills/browser-use
curl -o ~/.claude/skills/browser-use/SKILL.md \
  https://raw.githubusercontent.com/browser-use/browser-use/main/skills/browser-use/SKILL.md
```

### CLI 接口

```bash
browser-use open https://example.com    # 导航到 URL
browser-use state                       # 查看可点击元素
browser-use click 5                     # 按索引点击元素
browser-use type "Hello"                # 输入文本
browser-use screenshot page.png         # 截图
browser-use close                       # 关闭浏览器
```

### 架构中的关键文件

| 文件 | 作用 |
|------|------|
| CLAUDE.md | Claude Code 项目指令 |
| AGENTS.md | Codex/通用 agent 指令 |
| skills/browser-use/SKILL.md | 浏览器自动化技能定义 |

### 与本研究关联

Browser Use 展示了 **Skill 模式在非知识管理领域的应用**：通过一个 SKILL.md 文件，让编码 agent 获得全新的能力域（浏览器操作）。这验证了 Skill 作为**能力注入**机制的通用性。

---

## 8. 横向对比：六个项目的关系与定位

### 生态位分析

```
                        知识管理                          开发流程
                    ◄─────────────────────────────────────────────►
                    
  文档/知识 ─┬── llm-wiki-compiler ──── Wiki 编译 (文档 → Wiki)
  知识库     │
             ├── llm-knowledge-bases ── 完整知识管线 (Obsidian + 多agent)
             │
  代码库 ────┼── CodeWiki ───────────── 代码 Wiki 生成 (代码 → Wiki)
             │
  Schema ────┤   ↑ 三者都遵循 LLM Wiki 三层架构
  (控制层)   │
             │
  技能框架 ──┼── agent-skills ──────── 20 个工程技能 (开发全流程)
             │
  浏览器 ────┴── browser-use ──────── 浏览器自动化能力注入
```

### 关键指标对比

| 项目 | Stars | 目标 | 形式 | 核心文件 |
|------|-------|------|------|----------|
| agent-skills | 12K | 工程技能 | SKILL.md 集合 | CLAUDE.md + 20 SKILL.md |
| llm-wiki-compiler | 61 | 文档 Wiki 编译 | Claude Code 插件 | 3 个斜杠命令 |
| llm-knowledge-bases | 15 | 知识库全流程 | Claude Code 插件 | 7 个 skill + CLAUDE.md |
| CodeWiki | 新 | 代码库 Wiki | Rust CLI | 命令行工具 |
| browser-use | 87K | 浏览器自动化 | Python SDK + Skill | SKILL.md + AGENTS.md |
| **LLM Wiki 三层架构** | - | 设计范式 | 概念框架 | Raw + Wiki + Schema |

### 共同趋势

1. **CLAUDE.md / AGENTS.md 成为标准** — 所有项目都使用此文件定义 agent 行为
2. **SKILL.md 成为通用能力注入格式** — 无论知识管理还是浏览器自动化
3. **从"检索"到"编译"** — Wiki 方法的核心是预编译，而非运行时检索
4. **LLM 从工具使用者变为知识维护者** — Schema 赋予 LLM 主动维护职责

---

## 9. 与现有研究的综合分析

### 9.1 与《大规模知识库检索方案调研》的关联

| 已有研究 | 新发现补充 |
|----------|-----------|
| **§3 Wiki 法** — 描述了 Karpathy 的理念和手动操作流程 | **三层架构形式化** — Raw/Wiki/Schema 三层划分，特别是 Schema 的定义。**三个开源工具**将 Wiki 法从"手动操作"升级为"自动化 pipeline"。 |
| **§4 知识蒸馏** — 描述了 LLM 预处理知识的策略 | llm-knowledge-bases 的 compile 过程本质就是蒸馏，但被包装为更自然的 "Wiki 编译" 概念 |
| **§15 生命周期管理** — 描述了增量更新策略 | llm-knowledge-bases 的 evolve + lint 实现了自动化生命周期管理 |
| **§18 工具汇总** — 列出了 Repomix, Gitingest, DeepWiki | **缺失 3 个关键工具**：llm-wiki-compiler, llm-knowledge-bases, CodeWiki |

### 9.2 与《Agent 架构深度研究报告》的关联

| 已有研究 | 新发现补充 |
|----------|-----------|
| **§1.3 Agent 四大核心能力** — 推理、工具、记忆、规划 | agent-skills 将第五种能力 **"技能(Skills)"** 形式化 — 不同于工具(Tools)，技能是工作流而非单一操作 |
| **§6 生产级工程实践** — 讨论了最佳实践 | agent-skills 将 Google 的 SWE 最佳实践（Hyrum 定律、Beyonce 规则、Shift Left 等）编码为 agent 可执行的 SKILL.md |
| **§3 Claude Code 源码分析** — 分析了 Claude Code 的钩子和权限系统 | agent-skills 的 hooks/ 目录补充了会话生命周期钩子的实际用法 |

### 9.3 与《Claude-Code 源码上下文策略实验报告》的关联

| 已有研究 | 新发现补充 |
|----------|-----------|
| **§7 推荐方案：分层上下文架构** — 20K map + 20-50K focus + 0-50K on-demand | agent-skills 的 context-engineering skill 定义了类似的 5 层上下文结构，验证了我们的方向 |
| **Repository Map** 实验 — Tree-sitter + PageRank 方案 | CodeWiki 将 Repo Map 升级为 **持久化代码 Wiki**，不再是临时生成的摘要 |

### 9.4 与《钩子详解与 Agent 层级对比》的关联

| 已有研究 | 新发现补充 |
|----------|-----------|
| **Claude Code 27 种钩子事件** | agent-skills 的 hooks/ 目录提供了会话级钩子的实际模板 |
| **PreToolUse / PostToolUse** | agent-skills 可能在其 simplify-ignore hook 中展示了高级钩子用法（Git 保护） |

### 9.5 gap 分析：现有研究中缺失的内容

| 缺失主题 | 来源 | 重要性 |
|----------|------|--------|
| LLM Wiki 三层架构的形式化定义 | 视频截图 | 🔴 高 — 是 Wiki 法的升级版 |
| Schema (CLAUDE.md) 作为 wiki 控制指令的设计模式 | 视频截图 | 🔴 高 — 核心创新 |
| Skill 模式（SKILL.md）作为能力注入机制 | agent-skills, browser-use | 🔴 高 — 新范式 |
| 反理性化表（Anti-rationalization） | agent-skills | 🟡 中 — 提升 agent 质量的手段 |
| Multi-agent 并行研究 pipeline | llm-knowledge-bases | 🟡 中 — Deep research 模式 |
| 浏览器自动化作为 agent 能力扩展 | browser-use | 🟢 低 — 与知识管理无直接关系 |

---

## 10. 新发现的关键范式

### 范式一：从 "检索" 到 "编译" 的转变

```
RAG 范式：     Query → Search → Retrieve → Generate
              （运行时检索，每次从零开始）

Wiki 编译范式： Source → Compile → Wiki → Query
              （预编译，LLM 维护持久化知识）
```

**关键区别**：
- RAG 把知识当"数据库"，LLM 当"搜索引擎"
- Wiki 编译把知识当"源代码"，LLM 当"编译器 + 维护者"
- RAG 的质量取决于 embedding 和检索算法
- Wiki 编译的质量取决于 Schema 设计和 LLM 的理解能力

### 范式二：CLAUDE.md 作为 "Schema" 的设计模式

传统上 CLAUDE.md 被视为"项目规则文件"。三层架构赋予它新的角色：**Wiki 运营指南**。

一个好的 Schema/CLAUDE.md 应包含：

```markdown
# 角色
你是 [领域] 的 Wiki 管理员，不是聊天机器人。

# Wiki 结构
- 目录组织约定
- 命名规范
- 链接格式
- 标签体系

# 工作流
- Ingest：如何将新原始资料编译进 wiki
- Query：如何回答问题（引用 wiki 页面）
- Lint：如何检查一致性
- Evolve：如何建议改进

# 约定
- 信息引用格式
- 置信度标注规则
- 冲突解决策略
```

### 范式三：SKILL.md 作为通用能力注入格式

从 agent-skills 和 browser-use 可以看出，SKILL.md 正在成为 **Agent 能力注入的事实标准格式**：

```
Agent 基础能力（LLM 推理 + 工具调用）
        +
   SKILL.md #1 (context-engineering)     → 上下文管理能力
   SKILL.md #2 (test-driven-development) → TDD 能力
   SKILL.md #3 (browser-use)             → 浏览器操作能力
   SKILL.md #4 (knowledge-base-organizer) → 知识库分析能力  ← 我们的
        =
   定制化 Agent
```

SKILL.md 的设计规范（从 agent-skills 总结）：

| 要素 | 必须 | 说明 |
|------|------|------|
| Frontmatter | ✅ | name + description (触发条件) |
| Overview | ✅ | 做什么 |
| When to Use | ✅ | 什么时候激活 |
| Process | ✅ | 分步工作流，带编号 |
| Rationalizations | 推荐 | Agent 常见借口 + 反驳 |
| Red Flags | 推荐 | 出错信号 |
| Verification | ✅ | 证据要求 |

### 范式四：知识库 = 代码库 的统一视角

CodeWiki 和 llm-knowledge-bases 揭示了一个趋势：**知识管理和代码管理正在融合**。

| 传统区分 | 新趋势 |
|----------|--------|
| 知识库用 RAG | 知识库用 Wiki 编译 |
| 代码库用 syntax parsing | 代码库也用 Wiki 编译 |
| 知识库在 Notion/Confluence | 知识库在 Git 仓库 |
| 代码和知识分别管理 | **统一用 Markdown+Git+LLM 管理** |

---

## 11. 对现有 Skill 和工具的改进建议

基于以上调研，对我们现有的 `skills/knowledge-base-organizer/` 提出以下改进建议：

### 11.1 工具汇总更新

需要更新 `大规模知识库检索方案调研.md` §18 工具汇总，添加：

| 工具 | 用途 | 类型 |
|------|------|------|
| llm-wiki-compiler | 知识文件 → Wiki 编译（Claude Code 插件） | 插件 |
| llm-knowledge-bases | 完整知识管线（Obsidian+多agent） | 插件套件 |
| CodeWiki | 代码库 → Wiki 编译（Rust CLI） | CLI |
| agent-skills | 20 个生产级工程技能 | Skill 集合 |
| browser-use | AI 浏览器自动化 | SDK + Skill |

### 11.2 SKILL.md 格式升级

我们的 `knowledge-base-organizer/SKILL.md` 缺少以下 agent-skills 证明有效的元素：

| 元素 | 当前状态 | 建议 |
|------|---------|------|
| Frontmatter | ❌ 缺少 | 添加 YAML frontmatter (name + description) |
| Anti-rationalization 表 | ❌ 缺少 | 添加 Agent 常见偷懒借口的反驳表 |
| Red Flags | ❌ 缺少 | 添加"出错信号"清单 |
| Verification | 部分有 | 强化为明确的证据要求 |

### 11.3 Wiki 编译策略集成

当 `select_strategy()` 推荐 Wiki 法（策略 B/C）时，应该推荐具体的工具：

```
策略 B/C 推荐时 →
  如果知识库是文档/知识文件 → 推荐 llm-wiki-compiler 或 llm-knowledge-bases
  如果知识库是代码仓库     → 推荐 CodeWiki
  如果已有 Obsidian 环境   → 推荐 llm-knowledge-bases
```

### 11.4 三层架构概念集成

在 SKILL.md 的 Phase 3（Execute）中，对于 Wiki 相关策略，应该引入三层架构概念：

1. 明确区分 Raw Sources（只读）和 Wiki（LLM 维护）
2. 生成 Schema（CLAUDE.md 模板）来控制 LLM 的 Wiki 维护行为
3. 内置 lint（健康检查）步骤

---

## 12. 结论

### 核心发现

1. **Wiki 法已从理念走向工具化** — Karpathy 的 Wiki 法不再是概念性建议，已有至少 3 个可用的开源实现（llm-wiki-compiler、llm-knowledge-bases、CodeWiki）
2. **三层架构是 Wiki 法的形式化框架** — Raw Sources（只读） + Wiki（LLM 拥有） + Schema（CLAUDE.md 控制），Schema 是核心创新
3. **SKILL.md 成为 Agent 能力注入的标准格式** — 从 agent-skills（12K stars）和 browser-use（87K stars）的实践来看，SKILL.md 是跨工具、跨领域通用的
4. **agent-skills 提供了结构化质量保障** — Anti-rationalization 表和 Verification 要求是防止 agent 偷懒的有效手段
5. **Agent 范式正在从"工具调用者"向"知识维护者"演进** — LLM 不只是使用工具，还能主动维护和演进知识库

### 与现有研究的对位

| 我们已有的 | 此次新增的 |
|-----------|-----------|
| 10 种知识检索方案 | Wiki 法的 3 个工具化实现 |
| 知识库画像 + 策略选择 | LLM Wiki 三层架构 |
| 代码库上下文实验 | CodeWiki（代码 → Wiki 持久化） |
| Agent 架构研究 | agent-skills（20 个结构化工作流） |
| 钩子系统分析 | agent-skills 的 hooks/ 实际模板 |

### 后续行动建议

1. ✅ 更新 `大规模知识库检索方案调研.md` 的工具汇总（§18）
2. ✅ 升级 `knowledge-base-organizer/SKILL.md` 的格式（添加 frontmatter、反理性化表）
3. ⬜ 考虑创建一个 "wiki-schema-generator" 工具，根据知识库特征自动生成 CLAUDE.md 模板
4. ⬜ 将 CodeWiki 的理念集成到 analyze_kb.py 的 CODE 策略推荐中

---

> **底线总结**：截图中的内容揭示了 Agent + 知识管理生态的最新趋势 — **SKILL.md 是能力注入标准，CLAUDE.md 是行为控制标准，三层 Wiki 架构是知识管理的最佳实践**。这些不是替代我们现有研究，而是在工具化层面的重要补充。
