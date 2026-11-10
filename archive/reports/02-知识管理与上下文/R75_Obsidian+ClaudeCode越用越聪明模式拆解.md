---
title: "Obsidian + Claude Code '越用越聪明'模式拆解：机制、对比与借鉴"
aliases: [R75, Obsidian越用越聪明, Claude Code Auto Memory, 自增长知识库]
report_id: R75
category: 知识管理与上下文
status: completed
tags: [obsidian, claude-code, auto-memory, knowledge-base, self-improving, copilot, memory]
date: 2026-04-28
tokens: 8000
related:
  - "[R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)"
  - "[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "[R35](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md)"
  - "[R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)"
  - "[R20](R20_ObsidianWiki%E7%9F%A5%E8%AF%86%E5%BA%93%E6%96%B9%E6%A1%88.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Obsidian + Claude Code "越用越聪明"模式拆解：机制、对比与借鉴

> **一句话概括**：社区热议的"Obsidian + Claude Code 越用越聪明"本质是 Claude Code 的 **Auto Memory**（Agent 自动记笔记）+ **CLAUDE.md**（人写持久指令）+ **Skills**（可复用工作流）三机制联动——问题没命中已有知识时 Agent 会自动记录新笔记，下次同类问题直接复用。当前 Copilot + Obsidian 模式在静态指令和知识沉淀层面有积累，但在**自动记录的触发可靠性和粒度覆盖**上与 Claude Code 存在明显差距，本报告分析差距成因并给出 3 项改进建议。
>
> **研究日期**：2026-04-28
> **研究类型**：快速调研（定位透镜 + 机制拆解 + 对比分析 + 落地建议）
> **增量价值**：在 [R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)（Copilot 五层指令记忆架构）、[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)（Skill 自迭代）、[R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)（Agent 记忆系统横评）基础上，**首次将 Claude Code 的 Auto Memory 机制与我们现有 Copilot 知识库模式做结构化对比**，并给出可立即执行的借鉴方案
> **关联报告**：[R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)（Copilot 全局记忆架构）、[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)（Skill 自迭代机制）、[R35](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md)（Hermes 记忆与 Skill 自迭代源码拆解）、[R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)（Agent 记忆系统横评）、[R20](R20_ObsidianWiki%E7%9F%A5%E8%AF%86%E5%BA%93%E6%96%B9%E6%A1%88.md)（Obsidian Wiki 知识库方案）

---

## 目录

1. [定位透镜：AI 辅助知识库的自增长范式](#定位透镜ai-辅助知识库的自增长范式)
2. [Claude Code "越用越聪明"机制全拆解](#claude-code-越用越聪明机制全拆解)
3. [我们当前模式是怎么做的](#我们当前模式是怎么做的)
4. [结构化对比：差什么？差多少？](#结构化对比差什么差多少)
5. [可落地的借鉴方案](#可落地的借鉴方案)
6. [结论](#结论)
7. [来源清单](#来源清单)

---

## 定位透镜：AI 辅助知识库的自增长范式

### 纵轴 · 演化脉络

AI 辅助知识库的"自动变聪明"经历了三个阶段：

| 阶段 | 时期 | 代表 | 核心机制 |
|------|------|------|----------|
| **静态指令期** | 2023-2024 | `.cursorrules`、`.github/copilot-instructions.md` | 人写规则文件，Agent 每次读取，不会自动修改 |
| **手动迭代期** | 2024-2025 | Anthropic Skill-Creator、CLAUDE.md 手动维护 | 人发现问题 → 人修改规则 → Agent 下次表现更好 |
| **自动记忆期** | 2025-2026 | Claude Code Auto Memory、Copilot /memories/、Hermes routines | **Agent 自己发现值得记住的东西 → 自动写笔记 → 下次自动加载** |

**关键转折**：2025 年底 Claude Code 推出 Auto Memory（v2.1.59+），将"Agent 自主记笔记"从实验变成产品级特性。社区大量帖子说的"越用越聪明"就是这个。

### 横轴 · 竞争格局

| 方案 | 自动记录 | 人工指令 | Skill/工作流 | 知识索引 | 适用工具 |
|------|---------|---------|-------------|---------|---------|
| **Claude Code** (Auto Memory + CLAUDE.md + Skills) | ✅ 原生 | ✅ CLAUDE.md | ✅ .claude/skills/ | ❌ 无全局索引 | Claude Code CLI |
| **Copilot** (/memories/ + instructions + prompts) | ✅ 三层 memory | ✅ .instructions.md | ✅ .prompt 文件 | ❌ 手动维护 | VS Code Copilot |
| **Cursor** (.cursorrules + @docs) | ❌ | ✅ .cursorrules | ❌ | ❌ | Cursor IDE |
| **Hermes** (routines + reflection) | ✅ 自学习 | ✅ AGENTS.md | ✅ routines | ❌ | CLI Agent |
| **本工作区模式** (Copilot + Obsidian + agent.md) | ⚠️ 有协议但触发不稳定 | ✅ agent.md 内容详尽 | ✅ skills/ 目录 | ✅ KNOWLEDGE_INDEX（手动维护） | VS Code Copilot |

### 交叉判断

Claude Code 的 Auto Memory 在**自动记录环节的产品化程度最高**（零配置、自动归类、200 行预算控制），是当前工具中"越用越聪明"体验最流畅的。本工作区在知识索引和结构化报告层面有额外投入，但这属于人工运营积累，并非工具本身的自动记忆能力——两者不在同一维度上直接可比。客观地说，**在"Agent 自主发现并记录经验"这件事上，Claude Code 明确领先**；本工作区的优势在于报告和索引的深度，但这依赖持续的人工投入来维护。

---

## Claude Code "越用越聪明"机制全拆解

### 核心机制：三个齿轮咬合

社区说的"越用越聪明"不是一个机制，而是 **三个机制协同** 的结果：

```
┌──────────────────────────────────────────────────────────────────┐
│                  Claude Code 知识自增长飞轮                       │
│                                                                  │
│   ① CLAUDE.md (人写)          ② Auto Memory (Agent写)           │
│   ┌──────────────┐            ┌──────────────┐                  │
│   │ 项目规则      │            │ 自动笔记      │                  │
│   │ 编码规范      │            │ 调试经验      │                  │
│   │ 架构约束      │ ◄─── 人发现 │ 偏好习惯     │                  │
│   │ 构建命令      │    Agent 不足│ 架构理解     │                  │
│   └──────┬───────┘    时升级   └──────┬───────┘                  │
│          │                            │                          │
│          ▼                            ▼                          │
│   ┌─────────────────────────────────────────┐                   │
│   │         每次新会话自动加载                 │                   │
│   │   CLAUDE.md 全量 + MEMORY.md 前200行      │                   │
│   └──────────────────┬──────────────────────┘                   │
│                      │                                           │
│                      ▼                                           │
│            ┌──────────────────┐                                  │
│            │ ③ Skills (按需)   │                                  │
│            │  可复用的工作流    │                                  │
│            │  Agent 自动匹配   │                                  │
│            └──────────────────┘                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 齿轮一：CLAUDE.md — 人写的持久指令

- **位置**：项目根目录 `./CLAUDE.md` 或 `~/.claude/CLAUDE.md`（个人级）
- **角色**：相当于给 Agent 的"员工手册"，每次会话开头全量注入
- **增长方式**：人手动写。通常在 Agent 犯同一个错第二次时添加
- **最佳实践**：< 200 行，只放 Agent 无法自己发现的规则

> **类比**：CLAUDE.md ≈ 我们的 `agent.md`（AI Research Expert 指令）+ `.instructions.md`

### 齿轮二：Auto Memory — Agent 自动记笔记（核心亮点）

这是"越用越聪明"的**发动机**。机制如下：

1. **触发条件**：Claude 在工作过程中**自行判断**某条信息值得记住（不是每次都记）
2. **存储位置**：`~/.claude/projects/<project>/memory/MEMORY.md`（入口文件）+ 按主题分的子文件（如 `debugging.md`、`api-conventions.md`）
3. **加载规则**：每次新会话自动加载 MEMORY.md 的前 200 行或 25KB
4. **分文件管理**：MEMORY.md 是索引，详细内容在子文件中，Agent 按需读取
5. **可审计**：纯 Markdown 文件，人随时可以编辑或删除

**典型场景**：
- 你纠正了 Claude "不要用 CommonJS，用 ESM" → Claude 自动记到 memory
- 你的项目用了特殊的测试命令 → Claude 发现后记下来
- 一个复杂的调试过程揭示了架构特点 → Claude 记录架构笔记

**关键设计决策**：
- **不是什么都记**：Claude 自己判断什么值得记（基于"未来会话是否有用"）
- **预算控制**：只加载前 200 行，超出的放子文件按需读
- **不跨机器**：memory 只存本地，不同步到云端
- **可关闭**：`autoMemoryEnabled: false` 或环境变量 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`

### 齿轮三：Skills — 可复用工作流

- **本质**：`.claude/skills/<name>/SKILL.md` 文件，定义可复用的操作流程
- **加载方式**：Claude 根据 description 自动匹配，或用户 `/skill-name` 手动调用
- **按需加载**：不像 CLAUDE.md 每次全量注入，Skill 只在相关时才加载，节省上下文

### "越用越聪明"的完整循环

```
用户提问 → Agent 处理
   │
   ├─ 命中 CLAUDE.md 规则 → 直接按规则执行 ✅
   │
   ├─ 命中 Memory 笔记 → 调取笔记辅助回答 ✅
   │
   ├─ 命中 Skill → 加载 Skill 执行 ✅
   │
   └─ 都没命中 → Agent 从头分析
        │
        └─ 分析完成后，Agent 判断：
            ├─ 这是项目通用知识 → 建议写入 CLAUDE.md（人决定）
            ├─ 这是发现的模式/偏好 → 自动写入 Memory ⭐
            └─ 这是可复用流程 → 建议创建 Skill（人决定）
```

**"越用越聪明"的关键 = Memory 自动增补这一环**。没命中时不是简单回答完就完了，而是会在回答的同时把有价值的发现"记住"。

---

## 我们当前模式是怎么做的

本工作区的 Copilot + Obsidian Vault 模式在不同层面各有积累：

### 层次对照

| 层次 | Claude Code 对应 | 本工作区对应 | 评估 |
|------|----------------|-----------|------|
| **持久指令** | CLAUDE.md（官方建议 < 200 行） | `agent.md`（900+ 行）+ 多个 `.instructions.md` | 内容量大，但行数远超官方建议的 200 行上限，可能存在指令遵从率下降的风险（[R17](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R17_%E6%8C%87%E4%BB%A4%E9%81%B5%E5%AE%88%E9%AA%8C%E8%AF%81%E4%B8%8E%E9%95%BF%E6%9C%9F%E6%BC%82%E7%A7%BB%E6%A3%80%E6%B5%8B.md) 已研究此问题） |
| **自动记忆** | Auto Memory — 产品级内置，Agent 自主触发 | Copilot `/memories/` 三层 — 依赖 protocol 文件约束 Agent 行为 | 本工作区依赖 Agent "自觉"执行 protocol，实际触发率不稳定；Claude Code 是产品层面的硬编码行为，可靠性高一档 |
| **可复用工作流** | Skills（.claude/skills/） | `skills/` 目录（6 个 Skill）+ `.prompt` 文件 | 两者设计思路一致，能力基本持平 |
| **知识索引** | 无 | `KNOWLEDGE_INDEX.md`（75 篇报告索引） | 本工作区额外投入，但这是人工运营成果，非工具自动生成 |
| **结构化报告** | 无 | `reports/` 目录 75 篇深度报告 | 同上，属于内容资产，不等同于工具能力 |
| **Forge 审视** | 无 | agent.md 中的"产物锻造"六阶段 | 方法论层面的设计，实际执行覆盖率未系统验证 |

### Memory Protocol（我们已有的自动记录机制）

我们在 `/memories/memory-protocol.md` 中定义了一套自动记录协议：

```
触发条件：修复了非显而易见的 bug、发现了 workaround、遇到了 API/工具 quirk
记录格式：### <标题> → Trigger / Symptom / Root cause / Fix / Scope
组织方式：/memories/kb/<domain>.md 按领域分文件
预算控制：/memories/ 总计前 200 行自动加载
```

设计思路与 Claude Code 的 Auto Memory 有相似之处（分文件、按主题、预算控制、自动加载），但关键区别在于：Claude Code 的 Auto Memory 是**产品内置行为**，记录动作在运行时层面被硬编码；而本工作区的 protocol 是一份**约束性文档**，Agent 是否执行取决于指令遵从率——这是本质差距。

---

## 结构化对比：差什么？差多少？

### 五维对比

| 维度 | Claude Code | 本工作区 | 判断 | 备注 |
|------|-------------|-----------|------|------|
| **① 指令丰富度** | CLAUDE.md < 200 行（官方推荐） | agent.md 900+ 行 | 量大≠更好 | 超长指令可能导致遵从率下降，Claude Code 官方明确建议精简 |
| **② 自动记录触发** | 产品内置，零配置，Agent 天然执行 | protocol 文件约束，Agent 依指令遵从率执行 | Claude Code 明确领先 | 这是"越用越聪明"体验差距的核心成因 |
| **③ 记忆加载机制** | 每次自动加载 MEMORY.md 前 200 行 | 每次自动加载 /memories/ 前 200 行 | 基本持平 | 两者都有预算控制 |
| **④ 知识深度** | 扁平笔记，按会话积累 | 75 篇结构化报告 + KNOWLEDGE_INDEX | 不同维度 | 本工作区深度大，但属人工运营成果而非自动能力；Claude Code 用户若同样投入运营也可达到 |
| **⑤ 跨会话一致性** | Auto Memory 文件稳定持久 | /memories/ 稳定，但 INDEX 更新依赖 Agent 执行强制序列 | Claude Code 略优 | Agent 执行强制序列的稳定性未经系统化验证 |

### 核心差距诊断

差距存在于多个层面，不只是"执行一致性"这么简单：

1. **实现层级不同**：Claude Code 的 Auto Memory 是**产品级内置行为**——写入 memory 的逻辑在 Claude Code 运行时中被硬编码，不依赖 prompt 遵从。本工作区的 Memory Protocol 是**指令级约束**——写在 `/memories/memory-protocol.md` 中，Agent 是否执行取决于指令遵从率。这不是"偶尔忘了"的问题，而是**机制层级根本不同**。

2. **反馈回路缺失**：Claude Code 有专门的 UI 提示（"Writing memory" / "Recalled memory"），用户能直观看到记忆系统在工作，形成正反馈循环。Copilot 的 /memories/ 写入发生在后台，用户无感知，难以判断系统是否在积累经验。

3. **记忆粒度差异**：Claude Code 会记录微观偏好（如"用户偏好 2 空格缩进"），覆盖从偏好到架构认知的完整光谱。本工作区的 protocol 侧重于 bug/workaround 等较大粒度经验，微观偏好层缺少覆盖。

4. **指令臃肿风险**：本工作区 agent.md 900+ 行，远超 Claude Code 官方建议的 200 行上限。指令越长，单条指令被遵从的概率越低——这可能是 Memory Protocol 执行不稳定的根因之一。

---

## 可落地的借鉴方案

### 方案一：强化 Memory Protocol 的执行一致性（推荐，最低成本）

**目标**：让 Copilot Agent 的自动记录从"偶尔做"变成"每次有价值发现都做"

**做法**：在 `/memories/memory-protocol.md` 中增加更明确的触发条件：

```markdown
## 扩展触发条件（对齐 Claude Code Auto Memory）
除原有规则外，以下场景也应自动记录：
- 用户纠正了 Agent 的行为 → 记录正确做法
- 发现了项目/工具的非显而易见特性 → 记录发现
- 用户表达了明确的偏好（如"以后别用 X，用 Y"）→ 记录偏好  
- 一次复杂调试/研究揭示了有价值的模式 → 记录模式摘要
- 多次搜索后才找到的正确路径 → 记录高效路径
```

**预期效果**：Memory 文件从目前的 4 个增长到 8-12 个，覆盖更细粒度的经验。

### 方案二：为 Obsidian Vault 添加"快速笔记"入口

**目标**：仿 Claude Code 的 MEMORY.md 入口文件模式，建一个轻量级的"经验速记"文件

**做法**：在工作区根目录创建 `QUICK_NOTES.md`

```markdown
# 快速经验笔记

> Agent 在研究/工作中发现的零散但有价值的信息，定期整理到正式报告或 /memories/kb/ 中

## 格式
每条笔记一行或一小段，标注日期和来源

## 笔记
- [2026-04-28] 飞书 wiki 节点嵌套电子表格时需要先尝试 docs +fetch，失败后根据报错切换 → 已在 feishu-api.md 中记录
- ...
```

**价值**：降低记录门槛。有些发现不值得写进 `/memories/kb/`（太小），也不值得写报告（太碎），但确实有复用价值——这就是 Claude Code Auto Memory 擅长捕获的那一层。

### 方案三：在 agent.md 的"知识沉淀 Archive"阶段增加自动记忆检查点

**目标**：确保每次研究结束时，不仅更新 KNOWLEDGE_INDEX，也同步更新 /memories/

**做法**：在 agent.md 的强制执行序列中，在 ⑦ 知识沉淀 之后增加：

```
⑦b 记忆同步：检查本次研究是否产生了 /memories/kb/ 应记录的经验
    - 新的工具用法/坑 → 更新对应的 kb 文件
    - 新的模式/偏好 → 更新 memory-protocol 或新建 kb 文件
    - 新的项目索引信息 → 更新 project-index.md
```

---

## 结论

| 维度 | 判断 |
|------|------|
| **"越用越聪明"的核心机制** | Claude Code Auto Memory = 产品级内置的 Agent 自动记笔记 + 下次自动加载。机制清晰，不神秘。 |
| **本工作区有没有类似能力** | 有设计（/memories/ 三层 + Memory Protocol），但实现层级不同——指令约束 vs 产品内置，可靠性有差距。 |
| **差在哪** | 核心差距是**实现层级**：Claude Code 在产品层面硬编码了记忆行为，不依赖 prompt 遵从；本工作区依赖 Agent 自觉执行 protocol。此外，指令文件过长可能进一步降低执行率。 |
| **本工作区的额外投入** | KNOWLEDGE_INDEX + 75 篇结构化报告 + Forge 锻造方法论——但这是人工运营成果，非工具自动能力，维护成本不可忽视。 |
| **是否需要切换工具** | 不必然。但应正视差距：在"自动记忆"这个维度上 Claude Code 确实做得更好。改进方向是提升现有 protocol 的触发覆盖和降低指令冗余。 |

**一句话总结**：Claude Code 通过产品级 Auto Memory 实现了可靠的"越用越聪明"体验。本工作区在静态指令和知识报告上有深度积累，但自动记忆的可靠性存在实现层级差距。改进路径是精简指令（降低遵从负担）+ 扩展 memory protocol 触发条件 + 补充反馈机制，而非简单地宣称"架构已覆盖"。

---

## 开放问题

1. **Copilot 是否会推出类似 Auto Memory 的原生特性？** 目前 Copilot 的 /memories/ 已经有类似机制，但 Agent 自主记录的一致性取决于 system prompt 而非产品级内置
2. **记忆膨胀问题**：Claude Code 限制 200 行/25KB，我们也有类似预算。但随着使用时间增长，是否需要定期"记忆整理"（合并、清理过时条目）？
3. **跨设备同步**：Claude Code 的 Memory 不跨机器。我们的 /memories/ 也是本地的。如果需要团队共享经验，需要另外的机制（比如把 /memories/kb/ 内容定期整合到 Obsidian Vault 的报告中）

---

## 来源清单

- [Claude Code 官方文档 - Memory](https://code.claude.com/docs/en/memory) — 2026-04-28 获取 — Auto Memory 和 CLAUDE.md 完整机制说明
- [Claude Code 官方文档 - Skills](https://code.claude.com/docs/en/skills) — 2026-04-28 获取 — Skill 系统设计和 frontmatter 规范
- [Claude Code 官方文档 - Best Practices](https://code.claude.com/docs/en/best-practices) — 2026-04-28 获取 — CLAUDE.md 编写最佳实践
- [Claude Code 官方文档 - Common Workflows](https://code.claude.com/docs/en/tutorials) — 2026-04-28 获取 — 包括"Work in notes and non-code folders"章节
- [R19](R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md) Copilot 全局记忆架构 — 本工作区已有报告 — 五层指令体系和三层运行时记忆
- [R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) Skill 自迭代机制深度研究 — 本工作区已有报告 — GEPA 范式和三层自迭代架构
- [R35](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md) Hermes 记忆与 Skill 自迭代源码拆解 — 本工作区已有报告 — 开源自学习 Agent 的 routines 机制
- [R72](R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md) Agent 记忆系统横评 — 本工作区已有报告 — 五家记忆框架的技术对比
- 本工作区 `/memories/memory-protocol.md` — 现有的 Copilot 记忆协议

⚖️ **来源一致性**：高一致 — Claude Code 官方文档为单一权威源，社区讨论与官方文档结论一致
📅 **时效性声明**：以上信息获取于 2026-04-28
