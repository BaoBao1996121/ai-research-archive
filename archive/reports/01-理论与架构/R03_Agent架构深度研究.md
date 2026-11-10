---
title: AI Agent 架构深度研究报告
aliases: [R03, Agent架构, 架构报告, Agent架构深度研究报告]
tags: [architecture, agent, claude-code, workflow, react]
date: 2026-04-10
category: 理论与架构
report_id: R03
tokens: 9513
status: completed
related:
  - "[钩子详解与Agent层级对比](R12_%E9%92%A9%E5%AD%90%E8%AF%A6%E8%A7%A3%E4%B8%8EAgent%E5%B1%82%E7%BA%A7%E5%AF%B9%E6%AF%94.md)"
  - "[Agent开发Python知识清单](R02_Agent%E5%BC%80%E5%8F%91Python%E7%9F%A5%E8%AF%86%E6%B8%85%E5%8D%95.md)"
  - "[Agent部署上线方案全景调研报告](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)"
  - "[Google ADK五大Agent技能设计模式研究报告](R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md)"
prev_path: reports/Agent架构深度研究报告.md
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# AI Agent 架构深度研究报告

> 从零到精通：理论、架构、实战全解析
>
> 研究日期：2026年4月10日
>
> 基于：Anthropic官方指南 + Claude Code源码逆向分析 + 业界主流框架对比

---

## 目录

- [第一部分：Agent 基础概念](#第一部分agent-基础概念)
- [第二部分：Agent 核心架构模式](#第二部分agent-核心架构模式)
- [第三部分：生产级 Agent 系统剖析 — Claude Code 源码分析](#第三部分生产级-agent-系统剖析--claude-code-源码分析)
- [第四部分：主流 Agent 框架对比](#第四部分主流-agent-框架对比)
- [第五部分：多智能体架构](#第五部分多智能体架构)
- [第六部分：生产级 Agent 关键工程实践](#第六部分生产级-agent-关键工程实践)
- [第七部分：Agent 架构选型指南](#第七部分agent-架构选型指南)
- [第八部分：未来趋势与展望](#第八部分未来趋势与展望)

---

## 第一部分：Agent 基础概念

### 1.1 什么是 Agent？

**Agent（智能体）** 是一个能够感知环境、做出决策、并采取行动来实现目标的自主系统。在 AI 领域，Agent 特指 **以大语言模型（LLM）为核心推理引擎**，通过工具调用与环境交互，自主完成复杂任务的系统。

```
┌─────────────────────────────────────────┐
│              AI Agent                    │
│                                         │
│   感知(Perceive) → 思考(Think) → 行动(Act) │
│        ↑                         │      │
│        └─────── 反馈(Feedback) ──┘      │
│                                         │
└─────────────────────────────────────────┘
```

### 1.2 Agent vs 普通 LLM 调用

| 特性 | 普通 LLM 调用 | Agent 系统 |
|------|-------------|-----------|
| 交互方式 | 单轮问答 | 多轮自主循环 |
| 决策方式 | 被动响应 | 主动规划与执行 |
| 工具使用 | 无或手动编排 | 自主选择和调用工具 |
| 状态管理 | 无状态 | 有状态，维护上下文 |
| 错误处理 | 无 | 自主检测、重试、恢复 |
| 任务复杂度 | 单步任务 | 多步骤、多依赖任务 |

### 1.3 Agent 的四大核心能力

```
┌──────────────────────────────────────────────────┐
│                  AI Agent 核心能力                  │
├──────────────┬───────────┬──────────┬─────────────┤
│   🧠 推理     │  🔧 工具   │  📝 记忆   │  📋 规划     │
│   Reasoning  │  Tools    │  Memory  │  Planning   │
│              │           │          │             │
│ - 逻辑推断   │ - 代码执行 │ - 短期记忆│ - 任务分解   │
│ - 上下文理解 │ - API调用  │ - 长期记忆│ - 步骤排序   │
│ - 意图识别   │ - 文件操作 │ - 工作记忆│ - 优先级判断 │
│ - 风险评估   │ - 搜索检索 │ - 经验积累│ - 动态调整   │
└──────────────┴───────────┴──────────┴─────────────┘
```

### 1.4 Agentic 系统的光谱

Anthropic 提出了一个重要观点：**agentic 系统是一个光谱**，而非二元分类。

```
简单 ◄─────────────────────────────────────────────► 复杂

单次LLM调用  →  带工具的LLM  →  预定义工作流  →  自主Agent
  │               │              │               │
  │               │              │               │
 prompt +      function       orchestrated     autonomous
 response      calling        workflow          agent
```

**关键洞察**（来自Anthropic官方博客）：
> "最成功的实现并不是使用复杂框架或专门的库。相反，它们都是用简单的、可组合的模式构建的。"

---

## 第二部分：Agent 核心架构模式

### 2.1 基础构建块：增强型 LLM（Augmented LLM）

所有 Agent 系统的基本单元是 **增强型 LLM**：一个装备了检索（Retrieval）、工具（Tools）和记忆（Memory）能力的大语言模型。

```
                    ┌─────────────┐
                    │  Retrieval  │
                    │  (RAG/搜索)  │
                    └──────┬──────┘
                           │
┌─────────────┐    ┌──────┴──────┐    ┌─────────────┐
│    Tools    │────│     LLM     │────│   Memory    │
│  (工具集合)  │    │  (核心引擎)  │    │  (上下文记忆) │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 2.2 五大 Workflow 模式（工作流模式）

Anthropic 在其官方指南中定义了5种核心 Workflow 模式，这些是构建 Agent 系统的基础积木：

#### 模式一：Prompt Chaining（提示链）

**定义**：将复杂任务分解为顺序执行的步骤链，每一步的输出是下一步的输入。

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Step 1  │───►│  Gate ✓  │───►│  Step 2  │───►│  Step 3  │
│ LLM Call │    │ (检查点)  │    │ LLM Call │    │ LLM Call │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

**适用场景**：
- 先生成大纲、检查大纲、再根据大纲写文章
- 先生成营销文案、再翻译成目标语言
- 先写代码、再审查代码、再生成测试

**优点**：每一步都更简单可控，可以在步骤之间加入校验
**缺点**：延迟较高，步骤之间耦合性强

#### 模式二：Routing（路由分发）

**定义**：根据输入类型分类，将请求导向不同的专门处理流程。

```
                    ┌──────────────┐
                    │   Router     │
                    │  (分类器)     │
                    └──────┬───────┘
                   ┌───────┼───────┐
                   ▼       ▼       ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │ Handler A│ │ Handler B│ │ Handler C│
            │ (退款处理)│ │ (技术支持)│ │ (一般咨询)│
            └──────────┘ └──────────┘ └──────────┘
```

**适用场景**：
- 客服系统：区分退款请求、技术支持、一般咨询
- 将简单问题路由到小模型（低成本），复杂问题路由到大模型（高质量）

**优点**：关注点分离，每个分支可以独立优化
**缺点**：分类器准确性是瓶颈

#### 模式三：Parallelization（并行化）

**定义**：将任务拆分为可同时执行的子任务，然后聚合结果。两种子模式：

```
模式A：Sectioning（分段并行）         模式B：Voting（投票并行）

     ┌─► Task A ─┐                     ┌─► Attempt 1 ─┐
     │            │                     │               │
Task─┼─► Task B ─┼─► Aggregate    Task─┼─► Attempt 2 ─┼─► Vote
     │            │                     │               │
     └─► Task C ─┘                     └─► Attempt 3 ─┘
```

**适用场景**：
- **分段并行**：一个模型处理用户查询、另一个模型检查内容安全
- **投票并行**：多个提示独立审查代码漏洞，综合判断

**关键实战经验**（来自Claude Code源码）：
> Claude Code 的 `toolOrchestration.ts` 实现了**自动并发分区**：将工具调用分为"并发安全"（只读工具如文件读取、搜索）和"需串行"（写入操作如编辑文件），只读工具自动并行执行，写入工具串行执行。最大并发数默认为 10。

#### 模式四：Orchestrator-Workers（编排者-工作者）

**定义**：一个中央 LLM（编排者）动态分解任务、分配给工作 LLM（工作者），最后综合结果。

```
                    ┌───────────────┐
                    │  Orchestrator │
                    │   (编排者)     │
                    └───────┬───────┘
                    ┌───────┼───────┐
                    ▼       ▼       ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Worker 1 │ │ Worker 2 │ │ Worker N │
             │ (动态分配) │ │ (动态分配) │ │ (动态分配) │
             └──────┬───┘ └──────┬───┘ └──────┬───┘
                    └────────┬───────┘────────┘
                             ▼
                    ┌───────────────┐
                    │  Synthesizer  │
                    │  (结果合成)    │
                    └───────────────┘
```

**vs Parallelization 的关键区别**：子任务不是预定义的，而是由编排者根据输入动态决定。

**适用场景**：
- 代码修改任务：需要改多少文件、每个文件怎么改，都因任务而异
- 多源搜索：需要搜哪些信息源取决于查询本身

**真实案例 — Claude Code 的 AgentTool**：
> Claude Code 的 `AgentTool` 正是这种模式。主 Agent 可以动态地通过 `AgentTool` 派生子 Agent 来处理子任务。每个子 Agent 有独立的上下文、工具集、甚至可以使用不同的模型（sonnet/opus/haiku）。

#### 模式五：Evaluator-Optimizer（评估者-优化者）

**定义**：一个 LLM 生成输出，另一个 LLM 评估并给出反馈，形成迭代优化循环。

```
           ┌──────────────────────────────────┐
           │                                  │
           ▼                                  │
    ┌──────────────┐    ┌──────────────┐      │
    │  Generator   │───►│  Evaluator   │──────┘
    │  (生成者)     │    │  (评估者)     │   反馈循环
    └──────────────┘    └──────────────┘
           │
           ▼ 评估通过
    ┌──────────────┐
    │   Output     │
    └──────────────┘
```

**适用场景**：
- 文学翻译的反复打磨
- 复杂搜索任务的多轮检索与验证

### 2.3 Agent 模式（自主代理）

**终极形态**：LLM 在一个循环中自主决策，使用工具，根据环境反馈调整行为，直到任务完成或触发停止条件。

```
┌──────────────────────────────────────────────┐
│                  Agent Loop                   │
│                                              │
│  User Input                                  │
│      │                                       │
│      ▼                                       │
│  ┌─────────┐     ┌─────────────┐             │
│  │  Think  │────►│ Act (Tool)  │             │
│  │  (推理)  │     │ (工具调用)   │             │
│  └─────────┘     └──────┬──────┘             │
│      ▲                  │                    │
│      │           ┌──────▼──────┐             │
│      │           │  Observe    │             │
│      │           │ (环境反馈)   │             │
│      │           └──────┬──────┘             │
│      │                  │                    │
│      │           ┌──────▼──────┐             │
│      └───────────│  Continue?  │             │
│         Yes      │ (是否继续?)  │             │
│                  └──────┬──────┘             │
│                         │ No                 │
│                  ┌──────▼──────┐             │
│                  │   Output    │             │
│                  └─────────────┘             │
└──────────────────────────────────────────────┘
```

**这就是 ReAct（Reasoning + Acting）模式**——目前最广泛使用的 Agent 架构。

---

## 第三部分：生产级 Agent 系统剖析 — Claude Code 源码分析

> 以下分析基于对工作区 `claude-code-main/src/` 源码的逆向工程。这是目前业界最先进的生产级 Coding Agent 之一。

### 3.1 整体架构总览

```
┌───────────────────────────────────────────────────────────────┐
│                     Claude Code 架构                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    入口层 (Entrypoints)                   │  │
│  │  main.tsx → CLI / REPL / SDK / Remote                   │  │
│  └────────────────────────┬────────────────────────────────┘  │
│                           │                                   │
│  ┌────────────────────────▼────────────────────────────────┐  │
│  │              查询引擎层 (QueryEngine)                     │  │
│  │  QueryEngine.ts → 会话管理、多轮对话、状态维护              │  │
│  └────────────────────────┬────────────────────────────────┘  │
│                           │                                   │
│  ┌────────────────────────▼────────────────────────────────┐  │
│  │              查询循环层 (Query Loop)                      │  │
│  │  query.ts → LLM调用 → Tool执行 → 循环控制                 │  │
│  │                                                         │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │  │
│  │  │ 上下文构建 │  │ API 调用     │  │ 工具编排与执行     │  │  │
│  │  │ context  │  │ claude.ts    │  │ toolOrchestration │  │  │
│  │  └──────────┘  └──────────────┘  └───────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    能力层 (Capabilities)                  │  │
│  │                                                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐  │  │
│  │  │  Tools  │ │ Memory  │ │  MCP    │ │ Permissions  │  │  │
│  │  │ 40+工具  │ │ 三层记忆 │ │ 协议集成 │ │ 多级权限     │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐  │  │
│  │  │  Hooks  │ │ Skills  │ │ Compact │ │  Tasks       │  │  │
│  │  │ 生命周期 │ │ 技能系统 │ │ 上下文压缩│ │ 后台任务     │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                  多Agent层 (Multi-Agent)                  │  │
│  │  AgentTool → 子Agent派生                                  │  │
│  │  TeamCreate/SendMessage → 群组协作                        │  │
│  │  Coordinator Mode → 编排者模式                            │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 核心循环 — Query Loop（查询循环）

**文件**：`src/query.ts`

这是 Claude Code 的心脏——一个 **async generator 状态机**：

```typescript
// 简化的核心循环伪代码（基于源码分析）
async function* query(params: QueryParams) {
  while (true) {
    // 1. Token 预算检查 → 触发自动压缩
    checkTokenBudget();
    
    // 2. 微压缩工具结果（缓存感知裁剪）
    microcompactToolResults();
    
    // 3. 构建完整系统提示（静态 + 动态）
    const systemPrompt = buildSystemPrompt(static + dynamic);
    
    // 4. 调用 Claude API（SSE流式）
    const stream = await callAPI(messages, systemPrompt, tools);
    
    // 5. 流式解析响应
    for await (const event of stream) {
      if (event.type === 'tool_use') {
        // 6. 工具权限检查
        const permission = await checkPermission(event);
        
        // 7. 执行工具（并发安全的并行，其余串行）
        const result = await executeTool(event);
        
        // 8. 后处理钩子
        await runPostToolHooks(result);
      }
    }
    
    // 9. 决定：继续循环 or 终止
    if (shouldTerminate()) break;
  }
}
```

**关键设计决策**：

1. **Async Generator 模式**：整个循环用 `async generator` 实现，每一步的中间产物都可以被上层消费（流式UI、SDK事件），这是非常优雅的生产级设计。

2. **流式工具执行**（`StreamingToolExecutor`）：不等 LLM 完整响应，解析到 `tool_use` 块就立即开始执行。这大幅降低了延迟。

3. **自动并发分区**：框架自动检测只读工具，安全并行执行：
```typescript
// toolOrchestration.ts 中的核心逻辑
function partitionToolCalls(toolCalls, context) {
  // 自动将工具调用分为：
  // 1. 并发安全批次（只读工具 → 并行）
  // 2. 需串行批次（写入工具 → 串行逐个执行）
}
```

4. **错误恢复循环**：最多3次重试，支持：
   - max_output_tokens 错误 → reactive compact / 截断
   - 流式错误 → 丢弃部分消息，fallback 到备用模型

### 3.3 工具系统（Tool System）

**文件**：`src/Tool.ts`, `src/tools.ts`, `src/tools/`

Claude Code 拥有 **40+ 内置工具**，每个工具都遵循统一的接口：

```typescript
// Tool 接口核心结构（简化）
type Tool = {
  name: string;                    // 工具名称
  description: string;             // 工具描述（影响LLM选择）
  inputSchema: ZodSchema;          // 输入参数的 Zod 验证
  isEnabled(): boolean;            // 是否启用（功能门控）
  isReadOnly(): boolean;           // 是否只读（影响并发策略）
  needsPermission(): boolean;      // 是否需要权限
  call(input, context): Result;    // 执行函数
}
```

**工具分类**：

| 类别 | 工具 | 说明 |
|------|------|------|
| 文件操作 | FileRead, FileEdit, FileWrite, Glob, Grep | 代码读写搜索 |
| 执行环境 | Bash, PowerShell, REPLTool | 命令执行 |
| Agent | AgentTool, TeamCreate, SendMessage | 多Agent编排 |
| 任务管理 | TaskCreate/Get/Update/List/Stop/Output | 后台任务 |
| 网络 | WebFetch, WebSearch | 网络访问 |
| MCP | MCPTool, ListMcpResources, ReadMcpResource | 外部协议集成 |
| 辅助 | TodoWrite, Config, Brief, LSP, SkillTool | 辅助功能 |
| 模式切换 | EnterPlanMode, ExitPlanMode, EnterWorktree | 工作模式 |

**工具设计的黄金准则**（来自Anthropic官方 + 源码实践）：

1. **绝对路径优于相对路径** — Claude Code 强制所有文件操作使用绝对路径
2. **Schema 即文档** — Zod schema 的 `.describe()` 直接成为 LLM 看到的参数说明
3. **Poka-yoke（防错设计）** — 从接口层面防止错误，而非依赖 LLM 遵守规则
4. **明确工具边界** — 每个工具做一件事，避免"万能工具"

### 3.4 权限系统（Permission System）

**文件**：`src/utils/permissions/`

Claude Code 实现了业界最精细的 Agent 权限控制：

```
┌────────────────────────────────────────────────┐
│              权限层级（从严到松）                  │
│                                                │
│  default        → 所有敏感操作都需要用户确认      │
│  plan           → 只有计划批准后才能执行          │
│  acceptEdits    → 自动接受文件编辑，其余仍需确认  │
│  bypassPermissions → 跳过大部分确认              │
│  dontAsk (YOLO) → 完全自主，不询问               │
│                                                │
│  + ML "auto"    → 机器学习分类器自动评估风险      │
└────────────────────────────────────────────────┘
```

**规则匹配机制**：
```typescript
// 权限规则支持通配符匹配
{
  tool: "Bash",
  content: "npm install *",  // 匹配 npm install 任何包
  permission: "allow"
}
```

**生产级洞察**：这个多层权限系统展示了一个关键原则——**Agent 的自主性不是全有或全无，而是一个可调节的旋钮**。生产环境必须提供这种精细控制。

### 3.5 记忆系统（Memory System）

Claude Code 实现了 **三层记忆架构**：

```
┌─────────────────────────────────────────────────┐
│                  记忆三层架构                      │
│                                                 │
│  Layer 1: Session Memory（会话记忆）              │
│  ├─ 范围：单次会话                                │
│  ├─ 存储：SESSIONMEMORY.md                       │
│  ├─ 触发：子 Agent 自动提取关键信息               │
│  └─ 上限：200行 / 25KB                           │
│                                                 │
│  Layer 2: Project Memory（项目记忆）              │
│  ├─ 范围：项目级别                                │
│  ├─ 存储：~/.claude/projects/<slug>/memory/      │
│  ├─ 触发：用户主动指令 + 自动提取                  │
│  └─ 持久化：跨会话保存                            │
│                                                 │
│  Layer 3: Context Compaction（上下文压缩）         │
│  ├─ 范围：当前对话上下文                           │
│  ├─ 触发：Token 预算耗尽时自动触发                  │
│  ├─ 策略：fork 子 Agent 异步压缩旧消息             │
│  └─ 特点：非阻塞，用户无感知                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Compaction（上下文压缩）的精妙设计**：

当对话历史过长时，Claude Code 不是简单截断，而是：
1. Fork 一个子 Agent 专门做摘要
2. 识别逻辑断点（而非按长度切分）
3. 保留近期消息的完整性
4. 压缩过程异步执行（不阻塞用户交互）

这解决了所有 Agent 系统都面临的 **"上下文窗口有限"** 问题。

### 3.6 系统提示构建（System Prompt Architecture）

**核心创新：缓存边界分离**

```
┌──────────────────────────────────────────────┐
│        系统提示 = 静态部分 + 动态部分            │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  静态部分（缓存边界之上）                 │  │
│  │  ├─ 核心指令                            │  │
│  │  ├─ 内置工具定义                         │  │
│  │  ├─ 模型能力描述                         │  │
│  │  └─ 💡 跨用户/跨会话可缓存               │  │
│  ├────────── 缓存边界 ──────────────────── │  │
│  │  动态部分（缓存边界之下）                 │  │
│  │  ├─ 用户上下文（git状态、项目信息）        │  │
│  │  ├─ MCP 工具描述                        │  │
│  │  ├─ 语言/主题设置                        │  │
│  │  └─ 🔄 每次会话变化                      │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  设计目标：最大化缓存命中率，降低延迟和成本       │
└──────────────────────────────────────────────┘
```

### 3.7 MCP（Model Context Protocol）集成

**文件**：`src/services/mcp/`

MCP 是 Anthropic 主导的 **工具标准化协议**，Claude Code 是其最完整的实现之一：

```
┌─────────────────────────────────────────────────┐
│              MCP 集成架构                         │
│                                                 │
│  传输层支持：                                     │
│  ├─ STDIO  → 本地二进制（最常用）                  │
│  ├─ HTTP   → 基于轮询                            │
│  ├─ SSE    → 服务器推送                           │
│  ├─ WS     → 全双工 WebSocket                    │
│  └─ SDK    → IDE 内嵌集成                        │
│                                                 │
│  工具发现与注册：                                  │
│  ├─ listTools() 获取服务器提供的所有工具            │
│  ├─ 包装为 MCPTool 类，统一 schema 验证            │
│  ├─ 工具名标准化（防冲突）                         │
│  └─ 大输出自动保存到磁盘 + 截断                    │
│                                                 │
│  认证流程：                                       │
│  ├─ OAuth 2.0 支持                               │
│  ├─ 401 → 浏览器认证 → 轮询完成 → 缓存 token       │
│  └─ 跨应用访问（XAA）支持                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**MCP 的价值**：它让 Agent 可以像"插件"一样接入任何外部服务，而不需要为每个服务编写专门的工具代码。这是 Agent 生态系统的基础设施。

### 3.8 Hooks 系统（生命周期钩子）

**文件**：`src/utils/hooks/`

Claude Code 提供了 **15+ 个生命周期钩子**，让用户可以在不修改核心代码的情况下自定义 Agent 行为：

```
会话生命周期：
  session-start ──────────────────────── session-end
       │                                     │
       │    工具执行生命周期（每次工具调用）：    │
       │    pre-tool-use → tool-use → post-tool-use
       │         │                              │
       │    permission-request                  │
       │    permission-denied                   │
       │                                        │
       │    上下文管理：                          │
       │    pre-compact → post-compact           │
       │                                        │
       │    协作：                               │
       │    teammate-idle / task-* events        │
       │                                        │
```

**Hooks 是 Shell 命令**，接收 JSON 事件，返回控制 JSON。这个设计极其灵活，可以用任何语言编写扩展，实现：
- CI/CD 集成（自动触发测试）
- 审计日志（记录所有工具调用）
- 自定义安全策略（拦截危险操作）

### 3.9 多 Agent 协作系统

**文件**：`src/tools/AgentTool/`, `src/tools/TeamCreateTool/`, `src/tools/SendMessageTool/`

Claude Code 支持两种多 Agent 模式：

#### 模式一：子 Agent 派生（AgentTool）

```
┌──────────────────────────────────────────┐
│  Main Agent                              │
│  ├─► SubAgent(prompt="分析这段代码")       │
│  │   └─ 独立上下文、独立工具集             │
│  │   └─ 可选择不同模型                     │
│  │   └─ 支持后台执行                      │
│  │                                       │
│  ├─► SubAgent(prompt="搜索相关文档")       │
│  │   └─ 并行执行                          │
│  │                                       │
│  └─► 合成子Agent结果                      │
└──────────────────────────────────────────┘
```

**Fork SubAgent（分叉子Agent）**：
> 源码中发现了一个精妙的 "fork" 机制：子 Agent 继承父 Agent 的上下文和 prompt 缓存，但获得独立的执行空间。这比全新创建子Agent更高效，因为可以**复用缓存**。

#### 模式二：Team 协作（Agent Swarm）

```
┌──────────────────────────────────────────┐
│              Team Collaboration           │
│                                          │
│  ┌──────────┐   SendMessage   ┌───────┐ │
│  │  Lead    │◄───────────────►│Agent A│ │
│  │  Agent   │   SendMessage   │       │ │
│  │  (协调者) │◄───────────────►├───────┤ │
│  │          │   SendMessage   │Agent B│ │
│  │          │◄───────────────►│       │ │
│  └──────────┘                 └───────┘ │
│                                          │
│  通信：消息邮箱（pendingUserMessages 队列）  │
│  隔离：AsyncLocalStorage / tmux 进程      │
│  权限：teamAllowedPaths 路径限制           │
└──────────────────────────────────────────┘
```

#### 模式三：Coordinator Mode（编排者模式）

```
┌──────────────────────────────────────────┐
│        Coordinator Mode                  │
│                                          │
│  Coordinator（用所有工具思考和规划）          │
│       │                                  │
│       ├─► Worker 1 (限制工具集)             │
│       ├─► Worker 2 (限制工具集)             │
│       └─► Worker N (限制工具集)             │
│                                          │
│  Workers 只能使用 ASYNC_AGENT_ALLOWED_TOOLS│
│  工作隔离：worktree / remote              │
└──────────────────────────────────────────┘
```

---

## 第四部分：主流 Agent 框架对比

### 4.1 框架全景图

```
┌──────────────────────────────────────────────────────────────────┐
│                    2024-2026 Agent 框架全景                       │
│                                                                  │
│  基础层（直接调用API）                                             │
│  ├─ Anthropic Claude API + Tool Use                              │
│  ├─ OpenAI Responses API + Built-in Tools                        │
│  └─ 适合：高度定制化需求，性能敏感场景                               │
│                                                                  │
│  框架层（Agent SDK/框架）                                          │
│  ├─ LangGraph (LangChain)  → 图状态机，最灵活                     │
│  ├─ CrewAI                 → 角色扮演多Agent，最直觉                │
│  ├─ AutoGen (Microsoft)    → 多Agent对话，企业级                   │
│  ├─ OpenAI Agents SDK      → OpenAI生态，简单直接                  │
│  ├─ Claude Agent SDK       → Anthropic生态                       │
│  ├─ Strands (AWS)          → AWS生态集成                          │
│  └─ Semantic Kernel (MS)   → .NET/Java 企业集成                   │
│                                                                  │
│  产品层（即用型Agent）                                              │
│  ├─ Claude Code            → 编程Agent                           │
│  ├─ Cursor / Windsurf      → IDE集成Agent                        │
│  ├─ Devin                  → 全自主编程Agent                      │
│  ├─ OpenAI Codex           → 云端编程Agent                        │
│  └─ ChatGPT Operator       → 通用任务Agent                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 详细框架对比

#### LangGraph（LangChain）

**核心理念**：用有向图（DAG）定义 Agent 的状态流转。

```python
# LangGraph 核心概念
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)
graph.add_node("think", think_fn)       # 思考节点
graph.add_node("act", act_fn)           # 行动节点
graph.add_node("observe", observe_fn)   # 观察节点
graph.add_edge("think", "act")          # 边：连接节点
graph.add_conditional_edges("observe",  # 条件边：动态路由
    should_continue,
    {"continue": "think", "end": END}
)
```

**优点**：
- 极其灵活，可以表达任意复杂的 Agent 拓扑
- 内置状态持久化（checkpointing）
- 支持人类介入（human-in-the-loop）
- 强大的调试和可视化工具

**缺点**：
- 学习曲线陡峭
- 额外的抽象层增加了调试难度
- 对于简单Agent来说过度复杂

**适用场景**：复杂的、有多分支的 Agent 工作流

---

#### CrewAI

**核心理念**：用"角色扮演"的方式定义多 Agent 协作。

```python
# CrewAI 核心概念
from crewai import Agent, Task, Crew

researcher = Agent(
    role="资深研究员",
    goal="发现最新AI趋势",
    backstory="你有20年AI研究经验...",
    tools=[search_tool, web_tool]
)

writer = Agent(
    role="技术写手",
    goal="将复杂技术概念转化为易懂文章",
    tools=[file_tool]
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential  # 或 hierarchical
)
```

**优点**：
- 最直觉的多Agent框架——像组建一个团队
- 内置角色定义、任务分配、流程控制
- 上手简单

**缺点**：
- 灵活性不如LangGraph
- 角色描述质量直接影响效果
- 对复杂交互模式支持有限

**适用场景**：需要多个"专家角色"协作的任务

---

#### AutoGen（Microsoft）

**核心理念**：多Agent对话驱动，Agent之间通过消息传递协调。

```python
# AutoGen 核心概念
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat, Swarm

# 两种协调模式：
# 1. SelectorGroupChat → 中央选择器决定谁发言
# 2. Swarm → 工具驱动的本地化选择

team = SelectorGroupChat(
    participants=[agent1, agent2, agent3],
    model_client=model_client
)
```

**核心架构**：
- **AgentChat**（高层API）→ 快速构建
- **autogen-core**（底层API）→ 事件驱动，完全控制

**优点**：
- 微软背书，企业级考虑
- 灵活的多Agent对话编排
- 支持 GraphFlow（有向图工作流）
- 内置 Magentic-One（通用多Agent系统）

**缺点**：
- API 经历了大版本重构(0.2→0.4)
- 文档和社区相对碎片化

---

#### OpenAI Agents SDK

**核心理念**：极简设计，Agent + Handoff + Guardrail。

```python
from agents import Agent, Runner, WebSearchTool, function_tool, guardrail

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route the user to the correct agent.",
    handoffs=[shopping_agent, support_agent],  # 任务移交
)

output = Runner.run_sync(
    starting_agent=triage_agent,
    input="What shoes work best with my outfit?"
)
```

**优点**：
- 极简API设计
- 内置安全护栏（Guardrail）
- 追踪与可观测性
- 深度集成OpenAI生态（搜索、文件搜索、计算机使用等内置工具）

**缺点**：
- 深度绑定OpenAI生态
- 灵活性不如LangGraph

---

### 4.3 框架对比矩阵

| 维度 | LangGraph | CrewAI | AutoGen | OpenAI SDK | Claude Code(参考) |
|------|-----------|--------|---------|------------|---------|
| **架构模型** | 状态图 | 角色团队 | 对话驱动 | Agent+Handoff | 增强循环 |
| **灵活性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **上手难度** | 较难 | 简单 | 中等 | 简单 | N/A(产品) |
| **多Agent** | 支持 | 核心特性 | 核心特性 | 基础支持 | 完整支持 |
| **状态管理** | 内置持久化 | 基础 | 中等 | 基础 | 多层 |
| **可观测性** | LangSmith | 基础 | 基础 | 内置追踪 | 完整遥测 |
| **模型锁定** | 无 | 无 | 无 | OpenAI | Anthropic |
| **生产就绪** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **权限控制** | 需自建 | 需自建 | 需自建 | Guardrail | 多层精细 |

---

## 第五部分：多智能体架构

### 5.1 多Agent协作的核心挑战

```
┌──────────────────────────────────────────────────┐
│            多Agent系统的五大挑战                    │
│                                                  │
│  1. 通信协议  → Agent之间如何交换信息？              │
│  2. 任务分配  → 谁来决定哪个Agent做什么？            │
│  3. 冲突解决  → Agent的行动互相矛盾怎么办？          │
│  4. 状态同步  → 如何确保所有Agent信息一致？           │
│  5. 成本控制  → N个Agent的Token消耗如何管理？        │
└──────────────────────────────────────────────────┘
```

### 5.2 多Agent架构模式

#### 模式一：Hub-Spoke（中心辐射）

```
                 ┌──────────┐
          ┌─────►│ Worker 1 │
          │      └──────────┘
┌─────────┴──┐   ┌──────────┐
│ Coordinator│──►│ Worker 2 │
│  (中心节点)  │   └──────────┘
└─────────┬──┘   ┌──────────┐
          └─────►│ Worker 3 │
                 └──────────┘
```
- **代表**：Claude Code Coordinator Mode, OpenAI Agent SDK Handoff
- **优点**：控制清晰，易于调试
- **缺点**：中心节点可能成为瓶颈

#### 模式二：Peer-to-Peer（对等网络）

```
┌──────────┐     ┌──────────┐
│ Agent A  │◄───►│ Agent B  │
└──────┬───┘     └───┬──────┘
       │             │
       └──────┬──────┘
              │
       ┌──────▼───────┐
       │   Agent C    │
       └──────────────┘
```
- **代表**：AutoGen Swarm, CrewAI hierarchical process
- **优点**：灵活，适合松散型协作
- **缺点**：难以调试，可能出现无限循环

#### 模式三：Pipeline（流水线）

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Agent A  │──►│ Agent B  │──►│ Agent C  │──►│ Agent D  │
│ (研究)    │   │ (分析)    │   │ (写作)    │   │ (审核)    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```
- **代表**：CrewAI sequential process
- **优点**：可预测，易于理解
- **缺点**：不灵活，延迟累积

#### 模式四：Blackboard（黑板模型）

```
┌──────────────────────────────────────┐
│         Shared Blackboard (共享黑板)   │
│  ┌──────────────────────────────────┐│
│  │  Task Status | Findings | Plans  ││
│  └──────────────────────────────────┘│
└──────┬──────────┬──────────┬────────┘
       │          │          │
┌──────▼───┐ ┌───▼──────┐ ┌▼─────────┐
│ Agent A  │ │ Agent B  │ │ Agent C  │
│ (读/写)   │ │ (读/写)   │ │ (读/写)   │
└──────────┘ └──────────┘ └──────────┘
```
- **代表**：Claude Code Team（通过共享文件系统 + 消息队列）
- **优点**：松耦合，灵活
- **缺点**：需要处理并发冲突

---

## 第六部分：生产级 Agent 关键工程实践

### 6.1 🔑 上下文管理（最关键的挑战）

LLM 上下文窗口有限（即使是 200K token 也会耗尽），生产级方案：

```
策略 1: Compaction（压缩）
├─ 自动检测 token 预算耗尽
├─ 异步 fork 子 Agent 做摘要
├─ 保留逻辑完整性（非按长度切）
└─ Claude Code 的做法 ✓

策略 2: RAG 增强
├─ 不把所有信息放上下文
├─ 按需检索相关片段
└─ 向量搜索 + 关键词搜索

策略 3: 工具结果预算
├─ 大的工具输出自动截断
├─ 存储到磁盘，只放摘要到上下文
└─ Claude Code 的 toolResultStorage ✓

策略 4: 动态工具集
├─ 不是所有工具都放到 prompt 里
├─ 按需搜索和加载工具
└─ Claude Code 的 ToolSearchTool ✓
```

### 6.2 🛡️ 安全与权限

```
┌──────────────────────────────────────────────────┐
│            生产级安全清单                           │
│                                                  │
│  □ 沙箱化执行环境                                  │
│    └─ Docker / gVisor / Worktree 隔离             │
│                                                  │
│  □ 分级权限控制                                    │
│    └─ 区分读操作 vs 写操作 vs 危险操作              │
│                                                  │
│  □ 人类确认关键步骤                                │
│    └─ Human-in-the-loop for destructive actions  │
│                                                  │
│  □ 速率限制与预算控制                               │
│    └─ 最大轮次、最大 Token、最大美元数               │
│                                                  │
│  □ 输入/输出验证                                   │
│    └─ Prompt injection 防御                       │
│    └─ 输出内容安全检查                              │
│                                                  │
│  □ 审计日志                                       │
│    └─ 记录所有工具调用和 LLM 决策                    │
│                                                  │
│  □ 拒绝追踪与熔断                                  │
│    └─ Claude Code 的 denialTracking ✓             │
│    └─ 连续拒绝自动停止，防止死循环                   │
└──────────────────────────────────────────────────┘
```

### 6.3 🔄 错误处理与恢复

```python
# 生产级错误处理策略（基于 Claude Code 源码分析）

class AgentErrorRecovery:
    """
    3层错误恢复机制
    """
    
    # Layer 1: 工具级重试
    def tool_level_retry(self):
        """
        - 工具超时 → 自动重试
        - 工具返回错误 → 将错误信息返回给 LLM，让它调整策略
        - 关键：不是简单重试相同参数，而是让 LLM 看到错误后决定下一步
        """
        pass
    
    # Layer 2: 循环级恢复
    def loop_level_recovery(self):
        """
        - max_output_tokens → reactive compact（压缩上下文后重试）
        - prompt_too_long → 自动压缩历史消息
        - 最多3次重试
        """
        pass
    
    # Layer 3: 模型级降级
    def model_level_fallback(self):
        """
        - 主模型不可用 → fallback 到备用模型
        - 流式中断 → 丢弃部分结果，用备用模型重试
        - Claude Code 支持 opus → sonnet → haiku 降级
        """
        pass
```

### 6.4 📊 可观测性

```
┌──────────────────────────────────────────────────┐
│           Agent 可观测性三大支柱                    │
│                                                  │
│  1. Tracing（追踪）                               │
│     ├─ 每个 LLM 调用的输入/输出                     │
│     ├─ 每个工具调用的参数/结果                      │
│     ├─ Agent 间消息传递                            │
│     └─ Claude Code: Perfetto tracing 集成         │
│                                                  │
│  2. Metrics（指标）                               │
│     ├─ Token 消耗和成本追踪                        │
│     ├─ 延迟分布                                   │
│     ├─ 工具调用频率和成功率                         │
│     └─ Claude Code: cost-tracker.ts              │
│                                                  │
│  3. Logging（日志）                               │
│     ├─ 结构化日志（JSON格式）                      │
│     ├─ 会话录制与回放                              │
│     ├─ 异常和错误记录                              │
│     └─ Claude Code: sessionStorage, asciicast    │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 6.5 ⚡ 性能优化

**Claude Code 中发现的性能优化技巧**：

```
1. 启动性能
   ├─ 并行预取：启动时同时预取 MDM 配置、Keychain 凭证
   ├─ 延迟加载：大量模块使用 lazy require / dynamic import
   └─ Feature Gate：编译时死代码消除

2. 运行时性能
   ├─ 只读工具自动并行（最大并发 10）
   ├─ 流式工具执行（不等完整响应就开始执行）
   ├─ Prompt 缓存优化（静态/动态分离）
   └─ 子 Agent Fork（复用父 Agent 缓存）

3. 上下文效率
   ├─ 微压缩（microcompact）：自动裁剪过大的工具输出
   ├─ 工具结果存磁盘：只在上下文放引用
   ├─ 动态工具集：ToolSearch 按需加载
   └─ 缓存破坏检测：避免不必要的重建
```

### 6.6 🧪 测试策略

```
┌──────────────────────────────────────────────────┐
│            Agent 测试金字塔                        │
│                                                  │
│              ┌─────────┐                         │
│             │ E2E Test │ ← 完整 Agent 交互测试     │
│            │ (端到端)   │                          │
│           ├───────────┤                           │
│          │ Integration │ ← 工具 + LLM 集成测试     │
│         │   (集成)      │                          │
│        ├───────────────┤                           │
│       │   Unit Tests    │ ← 单工具/组件单元测试     │
│      │  (单元)           │                          │
│     ├───────────────────┤                           │
│    │    Evals (评估)     │ ← 专门的大规模基准评估    │
│   └─────────────────────┘                           │
│                                                  │
│  关键洞察：Agent 测试需要"评估"（Evals），            │
│  而非只是传统测试。在沙箱中运行Agent解决真实任务，     │
│  用自动化方式评判结果质量。                          │
└──────────────────────────────────────────────────┘
```

---

## 第七部分：Agent 架构选型指南

### 7.1 决策树

```
你的任务需要什么？
│
├─ 单步 LLM 调用就能完成？
│  └─ YES → 不需要 Agent，直接用 LLM API + 好的 Prompt
│
├─ 需要工具调用？
│  ├─ 步骤固定可预测？
│  │  └─ YES → 使用 Workflow 模式（Prompt Chain / Routing）
│  └─ 步骤不确定需动态调整？
│     └─ YES → 使用 Agent 模式（ReAct 循环）
│
├─ 需要多个 Agent 协作？
│  ├─ 角色明确任务顺序固定？
│  │  └─ CrewAI Sequential / Pipeline
│  ├─ 需要中央协调？
│  │  └─ Orchestrator-Workers / LangGraph
│  └─ 需要灵活对话协调？
│     └─ AutoGen / Agent Swarm
│
└─ 生产级需求？
   ├─ 需要精细权限控制？ → 参考 Claude Code 权限系统
   ├─ 需要成本控制？ → Token Budget + Task Budget
   ├─ 需要可观测性？ → Tracing + Metrics + Logging
   └─ 需要自定义扩展？ → Hooks / Plugin 系统
```

### 7.2 按场景推荐

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 快速原型 | OpenAI Agents SDK | 最简API，开箱即用 |
| 复杂工作流 | LangGraph | 图状态机最灵活 |
| 多角色协作 | CrewAI | 最直觉的团队建模 |
| 企业级应用 | AutoGen + Azure | 微软生态集成 |
| 编程Agent | 参考 Claude Code 架构 | 最成熟的生产实现 |
| 从零自建 | 直接调用 LLM API | Anthropic推荐的最佳实践 |

### 7.3 Anthropic 的核心建议（黄金法则）

> **1. 从最简单的方案开始**
> 不要一上来就搭建复杂的多Agent系统。先试试单次LLM调用+好的prompt。
>
> **2. 只在有证据时增加复杂度**
> 每增加一层抽象，都需要通过评估（evals）证明它确实带来了改善。
>
> **3. 框架可以快速上手，但要理解底层**
> 使用框架是可以的，但必须理解底层发生了什么。"不正确的底层假设是客户错误的常见原因"。
>
> **4. 精心设计 ACI（Agent-Computer Interface）**
> 投入在设计人机界面上多少精力，就应该投入多少精力在设计 Agent-工具界面上。

---

## 第八部分：未来趋势与展望

### 8.1 2025-2026 关键趋势

```
┌──────────────────────────────────────────────────┐
│              Agent 技术发展趋势                    │
│                                                  │
│  1. 🔌 MCP 标准化                                │
│     Model Context Protocol 成为工具集成标准        │
│     Agent 生态从碎片化走向统一                      │
│                                                  │
│  2. 🖥️ Computer Use（计算机使用）                  │
│     Agent 直接操控 GUI                            │
│     替代传统 API 集成                              │
│     OpenAI CUA + Anthropic Computer Use          │
│                                                  │
│  3. 🤝 多Agent协作成熟                            │
│     从实验走向生产                                 │
│     标准化通信协议                                 │
│     Claude Code Team / AutoGen Swarm             │
│                                                  │
│  4. 🧠 长期记忆与学习                              │
│     Agent 跨会话记住偏好和经验                      │
│     个性化 Agent                                  │
│     Claude Code Memory System                    │
│                                                  │
│  5. 🔐 安全与治理                                 │
│     企业级权限控制                                 │
│     审计与合规                                    │
│     Guardrails 标准化                             │
│                                                  │
│  6. 📉 成本大幅下降                               │
│     Prompt Caching 技术成熟                       │
│     Task Budget API（Anthropic）                  │
│     小模型做简单任务，大模型做复杂任务               │
│                                                  │
│  7. ⚡ 后台/异步 Agent                             │
│     7×24 后台运行的 Agent                         │
│     Cron 触发 + Webhook 触发                      │
│     Claude Code: KAIROS / DreamTask / ProActive  │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 8.2 给学习者的建议路径

```
阶段1：理解基础（1-2周）
├─ 学习 LLM API 基础（Tool Use / Function Calling）
├─ 手写一个简单的 ReAct 循环（不用任何框架）
├─ 理解 Prompt Engineering 基础
└─ 阅读 Anthropic "Building Effective Agents" 博客

阶段2：掌握框架（2-3周）
├─ 选择一个框架深入学习（推荐 LangGraph）
├─ 实现一个多工具 Agent
├─ 尝试多 Agent 协作
└─ 理解状态管理和上下文控制

阶段3：深入源码（2-4周）
├─ 阅读 Claude Code 源码（本报告的参考）
├─ 理解生产级设计决策
├─ 关注：错误恢复、权限系统、上下文压缩
└─ 尝试实现类似的工程模式

阶段4：生产实战（持续）
├─ 构建一个生产级 Agent
├─ 实现完整的可观测性
├─ 添加安全控制和权限管理
├─ 持续评估和优化
└─ 关注 MCP 生态和新框架发展
```

---

## 附录

### 附录A：关键术语表

| 术语 | 英文 | 含义 |
|------|------|------|
| Agent | Agent | 能自主决策和行动的AI系统 |
| ReAct | Reasoning + Acting | 推理与行动交替的Agent模式 |
| Tool Use | Tool Use / Function Calling | LLM调用外部工具的能力 |
| MCP | Model Context Protocol | 工具标准化协议 |
| RAG | Retrieval-Augmented Generation | 检索增强生成 |
| HITL | Human-in-the-Loop | 人类参与的执行循环 |
| ACI | Agent-Computer Interface | Agent与计算机的交互接口 |
| Compaction | Context Compaction | 上下文压缩/摘要 |
| Guardrail | Guardrail | 安全护栏/防护机制 |
| Handoff | Agent Handoff | Agent间的任务移交 |
| Swarm | Agent Swarm | 多Agent群组协作 |
| Token Budget | Token Budget | 令牌使用预算控制 |

### 附录B：推荐阅读

1. **Anthropic: Building Effective Agents** — https://www.anthropic.com/engineering/building-effective-agents
2. **OpenAI: New Tools for Building Agents** — https://openai.com/index/new-tools-for-building-agents/
3. **LangGraph Documentation** — https://langchain-ai.github.io/langgraph/
4. **AutoGen Documentation** — https://microsoft.github.io/autogen/
5. **CrewAI Documentation** — https://docs.crewai.com/
6. **MCP Specification** — https://modelcontextprotocol.io/

### 附录C：Claude Code 源码关键文件索引

| 文件路径 | 职责 |
|---------|------|
| `src/main.tsx` | 应用入口，CLI/REPL启动 |
| `src/QueryEngine.ts` | 会话管理，多轮对话引擎 |
| `src/query.ts` | 核心Agent循环（LLM→工具→反馈） |
| `src/Tool.ts` | 工具接口定义 |
| `src/tools.ts` | 工具注册表 |
| `src/tools/AgentTool/` | 子Agent派生工具 |
| `src/coordinator/coordinatorMode.ts` | 编排者模式 |
| `src/services/tools/toolOrchestration.ts` | 工具并发编排 |
| `src/services/tools/StreamingToolExecutor.ts` | 流式工具执行器 |
| `src/services/mcp/` | MCP协议集成 |
| `src/services/compact/` | 上下文压缩服务 |
| `src/memdir/` | 记忆目录管理 |
| `src/utils/permissions/` | 权限系统 |
| `src/utils/hooks/` | 生命周期钩子 |
| `src/context.ts` | 系统/用户上下文构建 |
| `src/tasks/` | 后台任务管理 |
| `src/skills/` | 技能系统 |

---

> **结语**：Agent 技术正处于从"实验"到"生产"的关键转型期。最重要的不是选择最复杂的架构，而是**理解核心原理，从简单开始，按需增加复杂度**。Claude Code 的源码是目前可以公开分析的最完整的生产级 Agent 实现之一，值得深入研究。
>
> 祝学习顺利！🚀
