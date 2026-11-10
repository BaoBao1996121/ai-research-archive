---
title: OpenClaw 架构学习调研报告 — 为什么"龙虾"这么火，和 LangChain/Hermes 有何不同
aliases: [R41, OpenClaw 调研, 龙虾架构分析, OpenClaw vs Hermes, OpenClaw vs LangChain, OpenClaw架构学习调研报告]
tags: [agent, openclaw, hermes, personal-assistant, architecture, comparison, learning]
date: 2026-04-22
category: 工具与生态
report_id: R41
tokens: ~9000
status: completed
related:
  - "[Hermes-Agent开源自学习AI智能体深度研究报告](R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md)"
  - "[Hermes-Agent记忆与Skill自迭代源码拆解报告](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md)"
  - "[Agent架构深度研究报告](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "[部署上线全景调研](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)"
  - "[Anthropic官方Skill-Creator设计哲学研究报告](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)"
prev_path: reports/OpenClaw架构学习调研报告.md
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# OpenClaw 架构学习调研报告

> **一句话概括**：OpenClaw（🦞龙虾）不是又一个 Agent "框架"，而是一个"开箱即用的个人 AI 产品"。它把"Agent 在哪里跑"这个问题从"你的 IDE 里"变成了"你的 iMessage / Telegram / macOS 菜单栏 / Android 锁屏里"——这个定位错位，是它 362K⭐ 的真正原因。
>
> **研究日期**：2026-04-22
>
> **增量价值**：工作区已有 [Hermes-Agent开源自学习AI智能体深度研究报告](R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md)（#23）和 [Hermes-Agent记忆与Skill自迭代源码拆解报告](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md)（#35），本报告**首次**把 OpenClaw 作为主角研究，并给出 OpenClaw ↔ Hermes ↔ LangChain/CrewAI 三方对比。揭示一个关键但工作区尚未记录的事实：**Hermes 本质上是 OpenClaw 的"Python 同胞弟弟"**（设计哲学同源、核心 artifacts（SOUL.md/MEMORY.md）共享，甚至 Hermes 自带 `hermes claw migrate` 命令直接导入 OpenClaw 数据）。
>
> **研究背景**：用户本机已安装 OpenClaw v2026.4.9 并在使用，工作区的 `openclaw-bridge` Skill 将 Copilot 作为大脑、龙虾作为手脚。本报告回答"我每天用的这个东西到底是啥架构"。

---

## TL;DR 速查卡

- **定位独特**：不是 LangChain 那种"给开发者的库"，也不是 ChatGPT 那种"聊天网页"，而是**"你自己的永远在线的 AI 管家"**——跑在 $5 VPS / 你的 Mac 菜单栏 / Docker 里，通过 WhatsApp/iMessage/Telegram/微信/QQ 和你对话。
- **核心范式 = Gateway + Workspace + 多通道**：一个 Gateway 守护进程做 control plane，`~/.openclaw/workspace/` 目录就是 Agent 的"大脑快照"（8 个文件注入 system prompt），25+ 消息平台统一接入。
- **火爆的真相**：靠"多通道 + 原生 App + 个人产品化"三点打穿了 LangChain/CrewAI 够不着的 prosumer 市场。作者 Peter Steinberger 是 iOS 社区大佬，自带号召力。
- **关键数字**：362K⭐、74K fork、1,727 贡献者、102 个发布版本、TypeScript 90% + Swift 4.8%（原生 macOS app）、25+ 消息通道。
- **和 Hermes 的关系**：**亲兄弟**。同样的 SOUL.md/MEMORY.md/USER.md/skills/cron 设计，Hermes 是 Nous Research 用 Python 重写的"自学习强化版"，并支持一键从 OpenClaw 迁移。
- **上手建议**：产品导向用户 → OpenClaw；想改造/训练模型 → Hermes；想构建自己的 Agent 应用 → LangChain/自研。

---

## 目录

1. [研究分析轨道 — 为什么 OpenClaw 和别人不一样](#1-研究分析轨道)
   - 1.1 [定位透镜：纵横坐标快速锚定](#11-定位透镜纵横坐标快速锚定)
   - 1.2 [架构特别之处：Gateway + Workspace + 多通道三件套](#12-架构特别之处)
   - 1.3 [为什么这么火：三个错位打穿的市场](#13-为什么这么火)
   - 1.4 [和 LangChain/AutoGPT/CrewAI 对比](#14-和主流-agent-框架对比)
   - 1.5 [和 Hermes Agent 对比（重点）](#15-和-hermes-agent-对比)
2. [上手实战轨道 — 从零到跑通](#2-上手实战轨道)
3. [避坑指南](#3-避坑指南)
4. [成本与 ROI 速算](#4-成本与-roi-速算)
5. [决策速查](#5-决策速查)
6. [结论与学习路径](#6-结论与学习路径)

---

## 1. 研究分析轨道

### 1.1 定位透镜：纵横坐标快速锚定

> 搞清楚一个新东西，先别急着读源码，先在"纵轴演化"和"横轴竞争"两个维度定位它在江湖中的位置。

**纵轴 · 演化脉络**

| 时间 | 事件 | 意义 |
|------|------|------|
| 2024 年中 | Peter Steinberger（iOS 社区大佬，PSPDFKit 作者）启动 **Molty**，一只"太空龙虾"AI 助理项目 | 种子阶段，域名 `openclaw.ai` + `soul.md` |
| 2024 下半年 | 开源核心为 **OpenClaw**（`openclaw/openclaw` on GitHub，MIT License） | 从个人玩具变为开源基础设施 |
| 2025 上半年 | 多通道支持成熟：WhatsApp/Telegram/iMessage/Discord/Slack... | 产品形态清晰："Any OS, Any Platform" |
| 2025 下半年 | 生态爆发：**ClawHub** skills 中心（5,400+ skills）、字节开源 **OpenViking** 专为 OpenClaw 做 context DB、1Panel 集成、CowAgent 做"轻量替代"、nanoclaw/zeroclaw 做"Rust 替代" | 生态效应成立，形成事实标准 |
| 2026 初 | Nous Research 发布 **Hermes Agent**（Python 版），带原生 `hermes claw migrate`，深度架构同源 | 出现"强化版 Python 同胞" |
| **当前** | OpenClaw 362K⭐、Hermes 110K⭐、总生态 6,710+ 仓库 | 成熟期，社区健康度顶级 |

**横轴 · 竞争格局**（解决"个人永远在线 AI 助理"这个问题的玩家）

| 玩家 | 本质 | 定位差异 |
|------|------|---------|
| **OpenClaw** | 本地 Gateway + 多通道个人助理 | "我自己的 AI，跑在我的硬件上" |
| **Hermes Agent** | OpenClaw 的 Python 亲兄弟 + 自学习强化 | "研究实验室味"，Nous Portal/RL 训练友好 |
| **ChatGPT/Claude App** | 厂商托管云产品 | 封闭、不可 self-host、无真正 cron/长期记忆/多通道 |
| **LangChain/LangGraph** | 给开发者的 Agent 构建库 | 不是"一个产品"，是"一堆积木" |
| **AutoGPT/BabyAGI** | 早期实验性 GOAT 循环 | 社区热度已过 |
| **CrewAI / AutoGen** | 多 Agent 协作编排 | 学术/企业方向，不做 prosumer |
| **Dify / n8n / Coze** | 流程编排 + 可视化 | 偏"低代码工作流"，不是"个人常驻助理" |
| **Open WebUI / LibreChat** | Chat UI 套壳 | 只是前端，没有长期运行/调度能力 |

**交叉判断**：

- 纵轴告诉我们：OpenClaw 处在**成熟期早段**，生态（ClawHub + awesome-openclaw-skills + OpenViking + 1Panel 集成）已经形成飞轮，不是昙花一现。
- 横轴告诉我们：它占据了"**self-hosted personal AI assistant**"这个**被 LangChain 忽视、被 ChatGPT 不可能做**的生态位。竞品都不在同一个坐标点。
- 结论：OpenClaw 的火不是运气，是**精准错位**——它是"Prosumer 自托管 AI 助理"这个市场的第一个工业级实现。

---

### 1.2 架构特别之处

把 OpenClaw 剖开，你会看到一个**三层栈**——和 LangChain"给你一堆组件"的风格完全不同。

```mermaid
flowchart TB
    subgraph ChannelLayer["📱 Channel Layer（25+ 消息平台 + 原生 App）"]
        direction LR
        WA[WhatsApp]
        TG[Telegram]
        iM[iMessage]
        DC[Discord]
        SK[Slack]
        WC[WeChat/QQ]
        MB[macOS 菜单栏 App]
        iOS[iOS/Android Node]
        VC[Voice Wake<br/>唤醒词]
        CV[Live Canvas<br/>可视工作区]
    end

    subgraph Gateway["🎛️ Gateway — 单一 Control Plane（Node.js 守护进程）"]
        ROUTE[Multi-agent Routing<br/>通道→Agent 映射]
        AUTH[DM Pairing<br/>配对码鉴权]
        SANDBOX[Sandbox 策略<br/>main 裸跑/non-main 强制 Docker]
        RPC[HTTP /tools/invoke + WebSocket<br/>端口 18789]
    end

    subgraph AgentLayer["🧠 Agent Layer — 每个 Agent = 一个 Workspace"]
        WS["`~/.openclaw/workspace/`<br/>注入 8 个 .md 文件"]
        TOOLS[20+ 内置工具<br/>read/edit/write/exec/process/cron/...]
        SKILLS[Skills 系统<br/>SKILL.md + ClawHub 仓库]
        SESSIONS[Sessions + Subagents<br/>可 fork 子 Agent]
        MEM[Memory<br/>memory_search/memory_get]
    end

    ChannelLayer --> Gateway --> AgentLayer
    AgentLayer -->|生成内容| Gateway -->|投递回通道| ChannelLayer
```

下面逐层拆解。

#### 第一层：Gateway — "控制面"的发明

**核心洞察**：LangChain/AutoGPT 的 Agent 是"跑一次算一次"的短命进程。OpenClaw 的 Agent 是**长驻守护进程**（launchd/systemd user service），靠 Gateway 协调一切——这是产品化的前提。

Gateway 做四件事：

1. **会话路由**：把 WhatsApp 的老王、Telegram 的你自己、Slack 的工作号路由到不同的 Agent workspace（防人格和数据串门）
2. **通道适配**：统一 25+ 消息平台的收发协议（Baileys for WhatsApp、Telegraf for Telegram、iMessage Bridge via BlueBubbles...）
3. **鉴权与沙箱**：DM pairing 用配对码防陌生人发消息、non-main session 强制跑在 Docker 里
4. **HTTP + WebSocket API**：`POST /tools/invoke` 让 Copilot 这类外部大脑直接调用龙虾工具（这就是本工作区 `openclaw-bridge` Skill 的底层原理）

**和 LangChain 的差异**：LangChain 没有 Gateway 这个概念——它假设你自己搭 FastAPI、自己做路由。OpenClaw 把"产品化的脏活"做完了。

#### 第二层：Workspace — "人格与记忆的物理载体"

**核心洞察**：OpenClaw 把 Agent 的"人格+记忆+工具+状态"全部**物化为一个目录**（`~/.openclaw/workspace/`）。

从我本机实测的 systemPromptReport 看，每次启动 Agent 会**注入 8 个 Markdown 文件**到 system prompt：

| 文件 | 作用 | 类比 |
|------|------|------|
| `AGENTS.md` | 主指令/项目上下文（9142 字符） | C++ 项目的 `CMakeLists.txt` + 团队 README |
| `SOUL.md` | 人格定义（1664 字符） | 一个"世界观设定集" |
| `IDENTITY.md` | 身份标识（721 字符） | `whoami` 的输出 |
| `USER.md` | 用户画像（717 字符） | 通讯录里的备注 |
| `TOOLS.md` | 工具使用偏好（1263 字符） | API 客户端的"首选 endpoint 列表" |
| `MEMORY.md` | 长期事实记忆（1423 字符） | `~/.bash_history` 里的精华 |
| `HEARTBEAT.md` | 周期指令（687 字符，每 30min 触发） | cron 里 "别忘了刷牙" 的闹钟 |
| `BOOTSTRAP.md` | 启动期特殊指令（可选） | 开机自启脚本 |

**关键设计决策**：
- **总预算 150K 字符**，单文件 20K，超过就截断（`bootstrapMaxChars`）
- 这 8 个文件占 system prompt 约 **15K 字符**（实测 `projectContextChars=15558`），加上 tool schema（15763 字符）+ skills（1590 字符）+ 其他，总 system prompt 约 27K 字符
- 文件即状态：你改 `SOUL.md`，Agent 立刻换人格；你改 `MEMORY.md`，Agent 立刻"想起来"。**可版本控制、可 grep、可备份、可迁移**

**说白了**：这就是把 Agent 的"内存快照"做成了 Unix 风格的文件系统。和 LangChain 把一切藏在 Python 对象里的风格完全相反。

#### 第三层：Skills + Tools + Subagents

**Tools（硬编码能力）**：20+ 内置工具，从 systemPromptReport 实测：

```
read/edit/write/exec/process/cron/video_generate/
sessions_list/sessions_history/sessions_send/sessions_yield/sessions_spawn/
subagents/session_status/
web_search/web_fetch/image/
memory_search/memory_get
```

**Skills（可插拔能力）**：每个 skill 是一个目录，含 `SKILL.md`：

```
~/.openclaw/workspace/skills/
├── healthcheck/SKILL.md    (495 chars)
├── skill-creator/SKILL.md  (300 chars) ← 元能力：Agent 自己造 Skill
└── weather/SKILL.md        (420 chars)
```

**ClawHub**（clawhub.ai）是中心化 skill registry——这点和 Hermes 的 `agentskills.io` 开放标准略有差异（后文详述）。

**Subagents 与 Session Spawn**：`sessions_spawn` 工具让主 Agent **fork 一个隔离子 Agent**（带独立 workspace、独立 context window），并发执行任务后汇总。这解决了"一个长对话上下文爆炸"的问题。

参见 [渐进式Agent构建实战指南](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R44_%E6%B8%90%E8%BF%9B%E5%BC%8FAgent%E6%9E%84%E5%BB%BA%E5%AE%9E%E6%88%98.md) 关于子 Agent 模式的讨论。

---

### 1.3 为什么这么火

> 数据先行：**362K⭐、74K fork、1,727 贡献者、TypeScript 90% + Swift 4.8%（iOS/macOS 原生 App）**、102 个 release、5 个月贡献代码每天 merge。

**飞轮不是偶然，是三个错位同时发生**：

#### 错位 1：产品形态 — "不是框架，是产品"

大多数 Agent 项目选择"给开发者的库"（LangChain、CrewAI、AutoGen）。OpenClaw 选择"给用户的产品"——`npm install -g openclaw` 一条命令装完，`openclaw onboard` 向导配完所有东西（gateway、workspace、channels、skills），`launchd/systemd` 自动开机启动。

**对比**：LangChain 的 "Getting Started" 是"import langchain.agents"，OpenClaw 的 "Getting Started" 是"`openclaw onboard --install-daemon`"。受众完全不同，OpenClaw 触达了 **prosumer（专业消费者）** 这个被所有 Agent 框架忽视的市场。

#### 错位 2：交互形态 — "多通道 + 原生 App"

没有第二个开源 Agent 做到这个程度的通道整合：

| 通道 | 支持方式 |
|------|---------|
| WhatsApp | Baileys 协议桥 |
| Telegram | Bot API + User API |
| iMessage | BlueBubbles bridge（Mac 中转）|
| WeChat / QQ | 第三方协议 |
| Slack / Discord / Teams | 官方 API |
| Signal / Matrix / IRC | 原生协议 |
| 原生 App | macOS 菜单栏 App + iOS/Android node（Swift + Kotlin）|
| 语音 | Voice Wake 唤醒词 + Talk Mode 连续对话 |
| 可视化 | Live Canvas（A2UI）|

**说白了**：OpenClaw 不要求你改习惯。你在 iMessage 里和朋友聊天，随手也能 @ 你的 Agent。这就是 ChatGPT 做不到、LangChain 不打算做的事情。

#### 错位 3：社区与作者势能 — "大佬的号召力 + 精准 meme"

- 作者 **Peter Steinberger (@steipete)**：前 PSPDFKit CEO、iOS 圈 30 万粉的博主，自带流量
- **品牌化做到极致**：🦞 龙虾、"EXFOLIATE! EXFOLIATE!"（Dalek 梗）、"The lobster way"、Molty/Clawdbot/Moltbot 子品牌、专属域名 `openclaw.ai` + `soul.md` + `lobster.bot`
- **生态自发聚拢**：字节开源 **OpenViking**（明确 "designed for Agents such as OpenClaw"）、1Panel 控制面板一键部署、VoltAgent 聚合 5,400+ skills、CowAgent 做"更轻量替代"

对比 LangChain：LangChain 是 Harrison Chase 做的严肃库，没有 meme、没有原生 App、没有品牌情感。

---

### 1.4 和主流 Agent 框架对比

| 维度 | **OpenClaw** | LangChain/LangGraph | AutoGPT | CrewAI/AutoGen | OpenAI Swarm |
|------|--------------|---------------------|---------|----------------|--------------|
| **本质** | 产品 | 库 | 实验工具 | 库/框架 | 轻量调度库 |
| **受众** | Prosumer 用户 | 开发者 | 研究者/爱好者 | 开发者/研究者 | 开发者 |
| **安装** | `npm i -g openclaw` | `pip install` | `git clone + python` | `pip install` | `pip install` |
| **交互入口** | 25+ 消息平台 + 原生 App | 你自己搭 UI | CLI + Web UI | 你自己搭 | 你自己搭 |
| **长期运行** | ✅ launchd/systemd 守护进程 | ❌ 自己想办法 | ❌ 单次运行 | ❌ 自己想办法 | ❌ |
| **工作区/记忆** | ✅ 文件系统化（8 份 .md 注入）| ⚠️ 需要集成 memory 组件 | ⚠️ 简单 JSON 持久化 | ⚠️ 需要集成 | ❌ |
| **多 Agent 隔离** | ✅ workspace-per-agent | ⚠️ 自己管 | ❌ | ✅ 核心特性 | ✅ handoff |
| **Skills 生态** | ✅ ClawHub（5400+） | ⚠️ LangChain Hub（偏 prompt） | ❌ | ❌ | ❌ |
| **原生 App/语音** | ✅ macOS 菜单栏 + iOS/Android + Voice Wake | ❌ | ❌ | ❌ | ❌ |
| **沙箱隔离** | ✅ Docker/SSH/OpenShell 内建 | ❌ 自己搞 | ⚠️ Docker 可选 | ❌ | ❌ |
| **代码量** | 巨大（~200K+ LOC, TS+Swift+Kotlin）| 中等 | 中等 | 小 | 极小 |
| **GitHub⭐** | 362K | ~100K | 170K | ~25K | ~20K |

**一句话**：
- 想**自己用**一个跨平台的 AI 管家 → OpenClaw
- 想**给别人做**一个 Agent 产品 → LangChain / 自研
- 想**研究**多 Agent 协作 → CrewAI / AutoGen
- 想**玩**一下 Agent 概念 → OpenAI Swarm / AutoGPT

---

### 1.5 和 Hermes Agent 对比

> **这是本报告最有价值的部分**，工作区已有 [Hermes-Agent开源自学习AI智能体深度研究报告](R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md)，但**从未明确 Hermes 与 OpenClaw 的血缘关系**。

#### 血缘证据（五个"巧合"）

1. **Hermes README 里写着** `hermes claw migrate` 命令，并在 setup 向导中**自动检测** `~/.openclaw` 目录主动提议迁移
2. **v0.5.0 release notes**："OpenClaw migration v2 — 17 new modules, terminal recap for migrating from OpenClaw to Hermes"
3. **v0.9.0 release notes**："Rebrand OpenClaw → Hermes during migration"——明确的改品牌行为
4. **核心 artifacts 完全同名同形**：`SOUL.md`、`MEMORY.md`、`USER.md`、`skills/`、`cron`、`sessions` 都一致
5. **工具命名习惯**：`sessions_list/sessions_spawn/subagents/memory_search` 两边一模一样

**结论**：Hermes 是 **Nous Research 用 Python 重写并强化后的 OpenClaw 同胞项目**——不是 fork（语言都换了），但设计哲学、artifacts 格式、用户体验都是同源的。可以理解为"Python 重写版 + 加上 Nous Research 的自学习强化 + 加上 Atropos RL 训练集成"。

#### 架构 DNA 对比

| 维度 | OpenClaw 🦞 | Hermes Agent ☤ | 关系 |
|------|-----------|---------------|------|
| **发起方** | Peter Steinberger + 社区（1,727 人） | Nous Research（研究实验室）+ 550 人 | 独立 |
| **语言** | TypeScript 90% + Swift + Kotlin | Python 87.8% + TypeScript 8.2% | **不同** |
| **定位口号** | "Your own personal AI assistant. The lobster way." | "The agent that grows with you. Self-improving." | **偏产品 vs 偏自学习** |
| **核心 artifacts** | SOUL.md / MEMORY.md / USER.md / skills | SOUL.md / MEMORY.md / USER.md / skills | **完全一致** |
| **Workspace 位置** | `~/.openclaw/workspace/` | `~/.hermes/` | 结构镜像 |
| **Gateway** | 有（Node 守护进程，port 18789）| 有（hermes gateway） | 一致 |
| **Channel 数** | 25+（含 iMessage/WeChat/QQ/IRC...）| 15+（覆盖主流）| OpenClaw 更全 |
| **原生 App** | ✅ macOS 菜单栏 + iOS + Android node | ❌ 仅 CLI + gateway | **OpenClaw 独有** |
| **Voice/Canvas** | ✅ Voice Wake + Live Canvas (A2UI) | ⚠️ Voice Mode（CLI/Telegram/Discord VC）| OpenClaw 多媒体更重 |
| **Skills 标准** | ClawHub（中心化）| agentskills.io（开放标准）+ Skills Hub | **Hermes 更开放** |
| **记忆系统** | memory_search/memory_get（较简） | 三层金字塔（MEMORY.md + FTS5 会话检索 + Honcho/mem0/supermemory 等 8 插件）| **Hermes 更深** |
| **自学习闭环** | ⚠️ Skill-creator 元能力 | ✅ Closed learning loop（Nudge + 背景审查 + 自动 Skill 创建/优化）| **Hermes 核心卖点** |
| **RL 训练集成** | ❌ | ✅ Atropos RL environments + trajectory 导出 | **Hermes 独有** |
| **Serverless 部署** | Docker/Podman/Nix | Daytona / Modal（空闲休眠）| Hermes 更现代 |
| **沙箱后端** | Docker + SSH + OpenShell | local + Docker + SSH + Daytona + Singularity + Modal | **Hermes 更多** |
| **⭐ 数** | **362K** | 110K | OpenClaw 3x |

#### 设计哲学同异

**相同之处（DNA）**：
- 文件系统即状态（Markdown 文件驱动 Agent 行为）
- Gateway + Workspace 分层
- Skills 作为"过程性记忆"（procedural memory）
- Cron 内置调度
- 跨消息平台统一体验
- 可版本控制、可迁移的"Agent 人格"

**差异之处（基因）**：

| 方面 | OpenClaw | Hermes | 取舍原因 |
|------|----------|--------|---------|
| **技术栈** | TypeScript（前端生态 + Node）| Python（AI/ML 生态） | OpenClaw 想覆盖 iOS/Android/Web；Hermes 想接 RL/trajectory 训练 |
| **产品 vs 研究** | 产品导向（ElevenLabs/Menu Bar App） | 研究实验室（batch_runner/trajectory_compressor）| 作者背景差异 |
| **生态策略** | ClawHub 中心仓库（类 App Store） | agentskills.io 开放标准 | OpenClaw 追求一致体验；Hermes 追求生态开放 |
| **自学习能力** | 靠 prompt + skill-creator 元 Skill | 多层闭环（Nudge + 背景子 Agent + 压缩触发 + 8 插件）| Hermes 是 Nous Research "模型训练实验室" 产物 |
| **语音/UI** | 原生 App 一流（Steinberger 本行）| CLI + messaging 为主 | 作者技能栈差异 |
| **部署哲学** | 自托管（本地/VPS/Docker） | 自托管 + 现代 serverless（Daytona/Modal 空闲休眠）| Hermes 更云原生 |

#### 核心洞察：它们是"兄弟"，不是"竞争对手"

二者解决的是**同一个问题的不同侧面**：

```
                  "我需要一个永远在线的个人 AI 助理"
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    OpenClaw（产品侧最强）          Hermes（研究/自进化最强）
    • 25+ 通道，原生 App            • 自学习闭环
    • Voice/Canvas/移动端            • RL 训练 / Trajectory
    • 非技术用户友好                 • 模型中立，接 Nous/OR/GLM
    • ClawHub 生态                   • agentskills 开放标准
    • TypeScript / Node              • Python / AI 生态
```

**Hermes 自带从 OpenClaw 迁移的工具**，说明 Nous Research 把 OpenClaw 用户视为**自然延伸的受众**——这是合作关系，不是零和竞争。实际上，社区项目 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) 让两者**在同一个微信账号上并行运行**。

**我的选择建议**：
- 如果你是 **普通用户 / 想快速有个跨平台 AI 管家** → 选 OpenClaw
- 如果你是 **AI 工程师 / 想探索自学习 / 想做 RL 训练** → 选 Hermes
- **或者两个都装**——本工作区的 `openclaw-bridge` Skill 展示了"GitHub Copilot = 大脑，OpenClaw = 手脚"的组合路径，本质上把两个 Agent 当成管道上的不同单元

---

## 2. 上手实战轨道

### 2.1 环境准备

- **Node.js 24**（推荐，22.16+ 也行）
- **macOS / Linux / WSL2**（Windows 原生不支持）
- **消息平台账号**（看你想接哪个）

### 2.2 Hello World — 5 分钟跑通

```bash
# 装
npm install -g openclaw@latest

# 配置（交互向导）
openclaw onboard --install-daemon

# 启动 Gateway（已在 onboard 时自动装成后台服务）
openclaw gateway --port 18789 --verbose &

# 第一次对话
openclaw agent --agent main --message "Hello, who are you?"
```

预期输出：返回 JSON，payloads 里是 Agent 的自我介绍。

### 2.3 真实场景 — 从 Copilot 操控 OpenClaw

本工作区已有 `openclaw-bridge` Skill（见 `C:/Users/USER\.agents\skills\openclaw-bridge\SKILL.md`），实战模式如下：

```powershell
# Windows PowerShell 示例：让 OpenClaw 搜索 GitHub 趋势
$env:HTTP_PROXY="http://127.0.0.1:10809"
$env:HTTPS_PROXY="http://127.0.0.1:10809"

openclaw agent --agent main `
  --message "搜索本周 GitHub 上新创建的 AI Agent 相关仓库，生成 Markdown 报告" `
  --timeout 900 --thinking medium --json

# 读取产出
cat C:/Users/USER\.openclaw\workspace\reports\github-trending\latest.md
```

**关键参数**：
- `--agent main` **必加**，不加会报 "Pass --to, --session-id, or --agent" 错
- `--timeout` 默认 120s 不够，简单任务 300s，深度研究 900-1800s
- `--thinking` 五档：off / minimal / low / medium / high / xhigh（影响推理深度和成本）
- `--json` 返回结构化 JSON 便于 Copilot 解析

### 2.4 HTTP Tools Invoke（快速通道）

Gateway 在 `localhost:18789` 暴露 HTTP：

```powershell
# 直接调用龙虾的单个工具（秒级，无需走完整 Agent 循环）
$body = '{"tool":"sessions_list","action":"json","args":{}}'
Invoke-RestMethod -Uri "http://127.0.0.1:18789/tools/invoke" `
  -Method Post -ContentType "application/json" -Body $body
```

**安全限制**：HTTP 通道默认禁止 `exec/spawn/shell`（防远程命令执行）。只有 CLI 通道能跑危险工具。

### 2.5 定时任务（cron）

```bash
# 添加每天 8 点的 GitHub 趋势报告
openclaw cron add \
  --name "github-trending-daily" \
  --cron "0 8 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "扫描 GitHub Trending，生成 Markdown 报告" \
  --no-deliver

# 查看所有任务
openclaw cron list

# 手动触发
openclaw cron run <job-id>
```

这就是 LangChain 死活不做的功能——**长期自动化**。

---

## 3. 避坑指南

| 坑 | 原因 | 解法 |
|----|------|------|
| CLI 卡住不返回 | 没加 `--agent main`，Gateway 不知道投给谁 | 所有 `openclaw agent` 命令必加 `--agent main` |
| 超时 Error | 默认 120s 太短，复杂任务需要加载 27K 字符 system prompt + 多轮工具调用 | `--timeout 900` 起步，深度研究 1800 |
| HTTP /tools/invoke 调 `exec` 403 | 默认拒绝列表，防 SSRF | 用 CLI，或者修改 `gateway.security.denyHttpTools` |
| Windows 原生装不上 | 依赖 native addon（opus/whatsapp baileys），无 Windows wheel | 用 WSL2（强烈推荐）或 Docker |
| Agent "记不住"事 | Workspace `.md` 文件有**字符硬上限**（MEMORY 1423/HEARTBEAT 687），超了就截断 | 定期让 Agent `compact` 记忆，或用子 Agent 分派长任务 |
| DM 陌生人收不到回复 | 默认 `dmPolicy="pairing"`，陌生人要配对码 | `openclaw pairing approve <channel> <code>`，或改成 `open` |
| 前缀缓存失效、费用飙升 | system prompt 里有动态内容（时间戳）导致缓存 miss | 检查 `AGENTS.md` 等注入文件是否有时间戳，去掉 |
| macOS App 权限重启丢失 | 未签名构建 | 用官方签名的 appcast 发布版 |
| `~/.openclaw` 和 `~/.hermes` 同时装时混乱 | 二者 artifacts 同名（SOUL.md/MEMORY.md）| 用 `hermes claw migrate` 一次性迁移后，停用其中一个 |

---

## 4. 成本与 ROI 速算

### Token 消耗（实测数据）

从本机 v2026.4.9 测量：
- **Bootstrap system prompt**：约 27K 字符（约 **7K tokens** for Qwen tokenizer）
- **单次简单调用**：system prompt（7K）+ 工具 schema（4K）+ 对话（1-3K）≈ **12-15K input tokens**
- **深度任务**：多轮工具调用可达 **600K+ input tokens**（实测一次研究任务 `input: 669819`，得益于前缀缓存 `cacheRead` 占大头）

### 成本估算示例

假设用 Qwen3.5-plus（约 $0.7/M input, $1.4/M output）：

| 场景 | 单次成本 | 日均 10 次 | 月成本 |
|------|---------|-----------|-------|
| 简单问答 | ~$0.01 | $0.1 | ~$3 |
| 定时 GitHub 趋势报告 | ~$0.1 | $1 | ~$30 |
| 深度研究任务（600K tokens）| ~$0.4 | $4 | ~$120 |

**ROI 判断**：
- ✅ **值得用**：日常管家 / 定时自动化 / 多通道提醒 / 长期记忆 / 跨设备连续性
- ❌ **不值得**：一次性问答（直接 ChatGPT）、代码编辑（Claude Code/Cursor 更专业）、高频调用（成本失控）

---

## 5. 决策速查

**什么时候选 OpenClaw**：
- 想要跨平台（iMessage/微信/Slack/桌面）统一体验
- 作为**非技术用户**或 **prosumer**，想"开箱即用"
- 需要**长期运行**（cron / 每日报告 / 持续监控）
- 需要**原生 App**（macOS 菜单栏 / iOS 锁屏 / 语音唤醒）
- 重视**可版本控制、可迁移**的 Agent 人格

**什么时候选 Hermes**：
- 追求**自学习闭环**（自动创建/优化 Skill）
- 想做**模型训练**（RL trajectory / Atropos）
- 用 **Nous Portal 或 OpenRouter** 生态
- 喜欢 Python 生态工具链
- 需要**serverless 部署**（Daytona/Modal 空闲休眠省钱）

**什么时候都不选**：
- 想**构建 Agent 产品卖**给 B 端 → LangChain/自研
- 想做**多 Agent 并行协作研究** → CrewAI/AutoGen
- 想**一次性实验** → OpenAI Swarm / 直接调 API

**关键约束条件**：
- Windows 原生用户 → OpenClaw 需 WSL2，Hermes 同
- 国内不能稳定访问 OpenAI/Anthropic → 两个都支持 OpenRouter/Qwen/GLM/Kimi，选你付得起 API 的那个
- 对前缀缓存敏感（想控成本）→ 两个都做了缓存优化，实测效果相当

---

## 6. 结论与学习路径

### 核心结论

1. **OpenClaw 的特别之处不在"架构创新"，在"产品化定位"**——它把 LangChain/AutoGPT 不屑做的"长驻守护进程 + 多通道 + 原生 App + 用户向 onboard"做到了工业级。这是它 362K⭐ 的根本原因。

2. **架构三层栈（Gateway + Workspace + Skills）值得学习**——特别是"Agent 状态 = 文件系统目录"的设计，使 Agent 人格**可 grep、可版本控制、可迁移**，是对 LangChain"一切藏在 Python 对象里"的优秀矫正。

3. **OpenClaw 和 Hermes 是亲兄弟**，不是竞争关系——二者可以共存（HermesClaw 社区项目证明），甚至可以**从 OpenClaw 一键迁移到 Hermes**（`hermes claw migrate`）。选择取决于你的目的：**产品用 OpenClaw，研究用 Hermes**。

4. **这个赛道的本质是"Prosumer 自托管 AI 助理"**——ChatGPT 不会做（威胁商业模式）、LangChain 不会做（不是它的市场），只有开源项目能做。这解释了为什么两个项目都能 10 万⭐ 级别，因为**市场够大，且被厂商主动放弃**。

### 学习路径建议（给想深度理解的开发者）

**阶段 1 · 用起来**（半天）
- 装 OpenClaw：`npm i -g openclaw && openclaw onboard`
- 配一个微信/Telegram 通道，和它对话一天
- 感受"多通道 + 长期运行 + cron" 的产品形态

**阶段 2 · 解剖 workspace**（1 天）
- `cat ~/.openclaw/workspace/*.md` 把 8 个注入文件全读一遍
- 修改 `SOUL.md` 换人格，观察行为变化
- 用 `openclaw agent ... --json` 看 systemPromptReport 字段，理解 Token 构成

**阶段 3 · 读 Gateway 源码**（2-3 天）
- `git clone github.com/openclaw/openclaw`
- 读 `src/gateway/` 看 HTTP/WS 路由、沙箱、DM pairing
- 读 `src/channels/` 看 25 个通道的适配器模式
- 读 `src/agent/` 看 workspace 注入、tool dispatch、session 管理

**阶段 4 · 对比阅读 Hermes**（2-3 天）
- 对着 [Hermes-Agent记忆与Skill自迭代源码拆解报告](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md) 看 Hermes Python 版的实现
- 对比同名 artifacts（SOUL.md/MEMORY.md）在 TS vs Python 里的处理差异
- 重点看 Hermes 的"自学习闭环"（Nudge + 背景审查）——这是 OpenClaw 缺失的

**阶段 5 · 动手扩展**（持续）
- 用 `skill-creator` 元 Skill 让 Agent 自己造新 Skill
- 用 HTTP `/tools/invoke` 让 Copilot 操控 OpenClaw（参考本工作区 `openclaw-bridge` Skill）
- 给 OpenClaw 贡献一个 PR（文档友好、PR 门槛低、社区 merge 速度快）

### 与工作区其他研究的关联

- 架构层面：扩展了 [Agent架构深度研究报告](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) 的"产品化 Agent"维度
- 对比层面：补齐了 [Hermes-Agent开源自学习AI智能体深度研究报告](R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md) 缺失的"Hermes 的前身"背景
- 部署层面：丰富了 [部署上线全景调研](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) 中 prosumer 场景的选项
- 记忆层面：与 [Hermes-Agent记忆与Skill自迭代源码拆解报告](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md) 形成"文件系统即状态"范式的双重佐证

### 开放问题（待深入）

- ⬜ OpenClaw Live Canvas (A2UI) 的协议设计——Agent 如何驱动 UI？
- ⬜ OpenClaw 沙箱 Docker/SSH/OpenShell 三种后端的实测开销对比
- ⬜ ClawHub 中心化 vs agentskills.io 开放标准的生态演化（谁会赢？）
- ⬜ OpenClaw 如何处理前缀缓存与 HEARTBEAT.md（30min 触发）的冲突？
- ⬜ 深入读 `src/gateway/` 源码，补一份源码级拆解报告（参考 [Hermes-Agent记忆与Skill自迭代源码拆解报告](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md) 的方法）

---

## 📌 来源清单

- **OpenClaw GitHub 仓库**：[openclaw/openclaw](https://github.com/openclaw/openclaw) — 2026-04-22 — 362K⭐ / 74K fork / 1,727 贡献者 / TypeScript 90%
- **OpenClaw 官方文档**：[docs.openclaw.ai](https://docs.openclaw.ai/) — 2026-04-22 — 架构、Gateway、Channels、Skills 概念
- **Hermes Agent GitHub**：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — 2026-04-22 — 110K⭐ / Python 87.8%
- **Hermes Agent 文档**：[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/) — 2026-04-22
- **GitHub Topic openclaw**：[topics/openclaw](https://github.com/topics/openclaw) — 2026-04-22 — 6,710 仓库，证实生态繁荣度
- **本机实测**：OpenClaw v2026.4.9 on Windows，通过 Tee-Object 捕获的 systemPromptReport JSON — 2026-04-22
- **工作区已有报告**：[Hermes-Agent开源自学习AI智能体深度研究报告](R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md)、[Hermes-Agent记忆与Skill自迭代源码拆解报告](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md)
- **openclaw-bridge Skill**：`C:/Users/USER\.agents\skills\openclaw-bridge\SKILL.md` — 本工作区已沉淀的操控技能

⚖️ **来源一致性**：官方 README + 文档 + 本机实测 + GitHub Topic 页四源交叉验证，**高置信**
📅 **时效性声明**：以上信息采集于 2026-04-22，OpenClaw 版本 v2026.4.21（最新 release 11 小时前），Hermes 版本 v0.10.0（2026.4.16）
