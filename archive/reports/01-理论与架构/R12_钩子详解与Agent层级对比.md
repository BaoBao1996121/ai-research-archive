---
title: 钩子详解与 Agent 层级对比
aliases: [R12, 钩子详解, Hooks, 钩子详解与Agent层级对比]
tags: [architecture, hooks, lifecycle, claude-code]
date: 2026-04-10
category: 理论与架构
report_id: R12
tokens: 2773
status: completed
related:
  - "[Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
prev_path: reports/钩子详解与Agent层级对比.md
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 钩子（Hooks）详解 + 最简Agent vs 主流Agent对比

---

## 第一部分：什么是钩子（Hooks）？

### 一句话定义

**钩子就是"卡在关键节点上的监听器"** — 让你在 Agent 执行的关键时刻"插一脚"，做检查、修改、拦截或记录。

### 生活比喻

想象你开了一家快递公司，包裹从收件到送达有很多环节：

```
收件 → 分拣 → 装车 → 运输 → 派送 → 签收
```

现在你想在某些环节加"检查点"：
- 收件时：检查是不是违禁品（安全检查钩子）
- 装车前：记录包裹重量（日志钩子）
- 派送前：通知收件人（通知钩子）
- 签收后：发送满意度调查（后处理钩子）

**这些检查点就是"钩子"** — 你不用改物流主流程的代码，只需要在关键位置"挂"上你的自定义逻辑。

### 在 Agent 中的钩子

Agent 的执行也有很多关键时刻：

```
用户输入 → LLM 思考 → 选择工具 → [执行工具前] → 执行工具 → [执行工具后] → 返回结果 → 下一轮...
                                    ↑ PreToolUse       ↑ PostToolUse
                                    这里可以插钩子        这里也可以
```

### Claude Code 的 27 个钩子事件

从源码分析得到，Claude Code 支持 **27 种**钩子事件：

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code 钩子事件全表                 │
├────────────────────┬────────────────────────────────────┤
│    会话生命周期     │  SessionStart → SessionEnd          │
│                    │  Setup (初始化)                      │
├────────────────────┼────────────────────────────────────┤
│    用户交互         │  UserPromptSubmit                   │
│                    │  (用户提交 prompt 时触发)             │
├────────────────────┼────────────────────────────────────┤
│    工具执行         │  PreToolUse    → 执行前（可拦截）     │
│    （最常用）       │  PostToolUse   → 执行后（可修改结果）  │
│                    │  PostToolUseFailure → 失败后         │
├────────────────────┼────────────────────────────────────┤
│    权限相关         │  PermissionRequest → 请求权限时      │
│                    │  PermissionDenied  → 权限被拒后      │
├────────────────────┼────────────────────────────────────┤
│    Agent 控制      │  Stop / StopFailure → Agent 结束时   │
│                    │  SubagentStart / SubagentStop       │
├────────────────────┼────────────────────────────────────┤
│    上下文管理       │  PreCompact → 压缩前                 │
│                    │  PostCompact → 压缩后               │
├────────────────────┼────────────────────────────────────┤
│    Team 协作       │  TeammateIdle, TaskCreated,          │
│                    │  TaskCompleted                       │
├────────────────────┼────────────────────────────────────┤
│    MCP             │  Elicitation, ElicitationResult      │
├────────────────────┼────────────────────────────────────┤
│    配置/环境        │  ConfigChange, CwdChanged,          │
│                    │  FileChanged, InstructionsLoaded,    │
│                    │  WorktreeCreate, WorktreeRemove      │
├────────────────────┼────────────────────────────────────┤
│    通知            │  Notification                        │
└────────────────────┴────────────────────────────────────┘
```

### 钩子的 5 种类型

| 类型 | 说明 | 用途示例 |
|------|------|---------|
| **Command** (命令) | 执行 Shell 命令 | `bash validate.sh` 检查代码规范 |
| **Prompt** (提示) | 用另一个 LLM 调用来判断 | "检查这个 prompt 是否合规" |
| **Agent** (Agent) | 启动一个子 Agent 做多步判断 | 复杂的安全审查 |
| **HTTP** (远程) | 调用远程 API | 通知企业审计系统 |
| **Callback** (回调) | 代码内注册的函数 | SDK 内部集成 |

### 钩子能做什么？

通过退出码（exit code）控制行为：

```
exit 0 → ✅ 放行（一切正常，继续执行）
exit 2 → ❌ 拦截（阻止工具执行，告诉 Agent 被拒绝了）
其他   → ⚠️ 警告（记录错误，但不阻止执行）
```

### 实际例子：禁止 Agent 用 rm -rf

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo $TOOL_INPUT | grep -q 'rm -rf' && exit 2 || exit 0",
            "shell": "bash"
          }
        ]
      }
    ]
  }
}
```

当 Agent 想执行 `rm -rf` 时：
1. 钩子检测到危险命令
2. 返回 exit code 2（拦截）
3. Agent 收到"工具被拒绝"的反馈
4. Agent 必须换一种方式来完成任务

---

## 第二部分：最简 Agent + 主流 Agent 层层对比

### 最简 Agent（The Bare Minimum）

一个最简的 Agent 只需要 **不到 30 行代码**：

```python
# === 世界上最简单的 Agent ===
# 只有3个部分：LLM + 工具 + 循环

import openai

# 1. 定义工具
tools = [{
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "做数学计算",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            }
        }
    }
}]

# 2. 工具执行
def run_tool(name, args):
    if name == "calculate":
        return str(eval(args["expression"]))  # 生产中绝不能用 eval！

# 3. Agent 循环（核心！）
messages = [{"role": "user", "content": "计算 (3+5) * 12 / 4"}]

while True:
    # 调用 LLM
    response = openai.chat.completions.create(
        model="gpt-4o", messages=messages, tools=tools
    )
    msg = response.choices[0].message
    messages.append(msg)

    # 如果没有工具调用 → 结束
    if not msg.tool_calls:
        print(msg.content)
        break

    # 执行工具并把结果反馈给 LLM
    for tc in msg.tool_calls:
        result = run_tool(tc.function.name, json.loads(tc.function.arguments))
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
```

**这个最简 Agent 有什么？**

```
✅ LLM 调用
✅ 工具定义 + 执行
✅ 循环（LLM → 工具 → 反馈 → LLM → ...）
```

**这个最简 Agent 缺什么？**

```
❌ 错误处理          ❌ 权限控制          ❌ 上下文管理
❌ 记忆系统          ❌ 多 Agent 协作     ❌ 流式输出
❌ 可观测性          ❌ 安全护栏          ❌ 成本控制
❌ 钩子/扩展点       ❌ 并发工具执行      ❌ MCP 集成
❌ 人类确认          ❌ 会话持久化        ❌ 模型降级
```

### 层层递进对比表

下面的表格以"最简Agent"为基线（Level 0），逐层展示各主流Agent在每个维度上增加了什么：

---

### 📊 核心能力大对比表

```
图例：  ✅ = 内置支持    ⚙️ = 需要配置/插件    🔧 = 需要自己写    ❌ = 不支持
```

| 能力维度 | 最简Agent | OpenAI Agents SDK | LangGraph | CrewAI | AutoGen | Claude Code |
|---------|----------|-------------------|-----------|--------|---------|-------------|
| **── 基础层 ──** | | | | | | |
| LLM 调用 | ✅ 手写 | ✅ 封装 | ✅ 封装 | ✅ 封装 | ✅ 封装 | ✅ 流式+缓存 |
| 工具定义 | ✅ JSON手写 | ✅ 装饰器 `@function_tool` | ✅ 灵活绑定 | ✅ `@tool` | ✅ schema | ✅ Zod schema + 描述 |
| Agent 循环 | ✅ while True | ✅ `Runner.run()` | ✅ 状态图驱动 | ✅ Task循环 | ✅ 对话循环 | ✅ async generator |
| **── 工具执行层 ──** | | | | | | |
| 工具并发执行 | ❌ 串行 | ❌ 串行 | 🔧 自己编排 | ❌ 串行 | 🔧 异步 | ✅ 自动分区(只读并行/写入串行) |
| 流式工具执行 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 边解析边执行 |
| 工具结果裁剪 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 微压缩+磁盘存储 |
| 动态工具发现 | ❌ 全部载入 | ❌ 全部载入 | ❌ 全部载入 | ❌ 全部载入 | ❌ 全部载入 | ✅ ToolSearch 按需加载 |
| **── 安全与权限层 ──** | | | | | | |
| 权限控制 | ❌ | ⚙️ Guardrail | 🔧 自己实现 | 🔧 自己实现 | 🔧 自己实现 | ✅ 5级分层 + ML分类器 |
| 安全护栏 | ❌ | ✅ Guardrail装饰器 | 🔧 | 🔧 | 🔧 | ✅ 多层(权限+钩子+拒绝追踪) |
| 人类确认(HITL) | ❌ | ❌ | ✅ interrupt | 🔧 | ⚙️ 人类代理 | ✅ 深度集成(每工具可配) |
| 沙箱隔离 | ❌ | ❌ | ❌ | ❌ | ⚙️ Docker | ✅ Worktree + Remote |
| **── 上下文管理层 ──** | | | | | | |
| 对话历史 | ✅ 原始列表 | ✅ 自动管理 | ✅ 状态存储 | ✅ 基础 | ✅ 基础 | ✅ 多层(原始+摘要+快照) |
| 上下文压缩 | ❌ 满了就炸 | ❌ | 🔧 | ❌ | ❌ | ✅ 自动异步压缩(子Agent摘要) |
| Prompt缓存 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 静态/动态分离缓存边界 |
| Token预算控制 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Token Budget + Task Budget |
| **── 记忆层 ──** | | | | | | |
| 短期记忆(会话内) | ✅ messages列表 | ✅ 自动 | ✅ State | ✅ 基础 | ✅ 基础 | ✅ Session Memory |
| 长期记忆(跨会话) | ❌ | ❌ | 🔧 外部存储 | ⚙️ 向量DB | ⚙️ 可选模块 | ✅ Project Memory + Memory Dir |
| 经验学习 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ extractMemories自动提取 |
| **── 多Agent层 ──** | | | | | | |
| 子Agent派生 | ❌ | ✅ Handoff | ✅ 子图 | ✅ 角色Agent | ✅ 对话Agent | ✅ AgentTool(fork+后台) |
| Agent间通信 | ❌ | ✅ Handoff单向 | ✅ 共享State | ✅ 任务链 | ✅ 消息传递 | ✅ SendMessage双向 |
| 团队协作 | ❌ | ❌ | 🔧 | ✅ Crew | ✅ GroupChat | ✅ Team(Lead+成员) |
| 编排者模式 | ❌ | ❌ | ✅ 图编排 | ✅ Hierarchical | ✅ SelectorGroup | ✅ Coordinator Mode |
| Agent隔离 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Worktree/Remote/进程 |
| **── 错误处理层 ──** | | | | | | |
| 工具错误重试 | ❌ 直接崩 | ⚙️ 基础 | 🔧 | ⚙️ | ⚙️ | ✅ 自动反馈LLM重试 |
| 模型降级 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ opus→sonnet→haiku |
| 流式中断恢复 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 丢弃+fallback模型 |
| 拒绝死循环检测 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ denialTracking熔断 |
| **── 扩展性层 ──** | | | | | | |
| 钩子/生命周期 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 27个钩子事件 |
| 插件系统 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Plugin + Skill |
| MCP协议集成 | ❌ | ❌ | 🔧 社区 | ❌ | ❌ | ✅ 完整(STDIO/HTTP/SSE/WS) |
| 自定义工具协议 | ❌ | 🔧 | 🔧 | 🔧 | 🔧 | ✅ MCP标准化 |
| **── 可观测性层 ──** | | | | | | |
| Token/成本追踪 | ❌ | ❌ | ⚙️ LangSmith | ❌ | ❌ | ✅ cost-tracker内置 |
| 执行追踪 | ❌ | ✅ 内置Tracing | ✅ LangSmith | ❌ | ⚙️ 基础日志 | ✅ Perfetto + 会话录制 |
| 会话回放 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ asciicast录制 |
| **── 用户体验层 ──** | | | | | | |
| 流式输出 | ❌ 等全部完成 | ✅ 流式 | 🔧 | ❌ | ⚙️ | ✅ SSE流式+进度条 |
| 后台任务 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 后台Agent+通知 |
| Plan模式 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 规划→确认→执行 |

---

### 📊 架构复杂度对比（代码量级估算）

| 维度 | 最简Agent | OpenAI SDK | LangGraph | CrewAI | AutoGen | Claude Code |
|------|----------|------------|-----------|--------|---------|-------------|
| 核心代码量 | ~30行 | ~2K行 | ~15K行 | ~10K行 | ~20K行 | ~100K+行 |
| 工具数量 | 1个 | 3内置+自定义 | 自定义 | 自定义 | 自定义 | 40+内置 |
| 配置项 | 0 | ~10 | ~30 | ~20 | ~30 | ~200+ |
| 学习曲线 | 10分钟 | 1小时 | 1-2天 | 半天 | 1-2天 | N/A(产品) |

---

### 📊 从最简到最强：每层增加了什么？

用一张图看清楚从最简Agent到生产级Agent，每一层叠加了什么：

```
┌──────────────────────────────────────────────────────────────────┐
│ Level 6: 生产级 Agent (Claude Code)                              │
│ 新增：27个钩子、插件/技能系统、MCP标准协议、Plan模式、              │
│       后台任务、配置管理、Prompt缓存分离、会话回放、Worktree隔离    │
├──────────────────────────────────────────────────────────────────┤
│ Level 5: 企业级 Agent (AutoGen/LangGraph 深度使用)                │
│ 新增：状态持久化/Checkpoint、复杂多Agent拓扑、GraphFlow编排、       │
│       Magentic-One 通用多Agent、事件驱动底层                      │
├──────────────────────────────────────────────────────────────────┤
│ Level 4: 多Agent框架 (CrewAI / AutoGen / OpenAI SDK)             │
│ 新增：多Agent协作、角色定义、任务移交(Handoff)、团队管理、           │
│       Guardrail安全护栏、执行追踪                                 │
├──────────────────────────────────────────────────────────────────┤
│ Level 3: 成熟单Agent框架 (LangGraph 基础)                        │
│ 新增：状态图驱动、条件路由、Human-in-the-loop中断、                │
│       子图嵌套、长期记忆外接                                      │
├──────────────────────────────────────────────────────────────────┤
│ Level 2: 简单Agent框架                                           │
│ 新增：工具自动解析(装饰器)、错误基础处理、流式输出、                │
│       简单对话历史管理                                            │
├──────────────────────────────────────────────────────────────────┤
│ Level 1: 最简Agent (30行代码)                                     │
│ 有且仅有：LLM调用 + 1个工具 + while循环                           │
│                                                                  │
│ 缺少一切：崩了就崩、没有安全、没有记忆、没有多Agent、没有扩展点     │
└──────────────────────────────────────────────────────────────────┘
```

---

### 📊 主流框架的"特色菜"——各自最独特的贡献

每个框架都对Agent生态做出了独特贡献，这些是它们各自的"杀手特性"：

| 框架 | 独门绝技 | 一句话解释 |
|------|---------|-----------|
| **OpenAI Agents SDK** | Handoff（任务移交） | Agent 之间像接力赛一样传递控制权，极简优雅 |
| **LangGraph** | StateGraph（状态图） | 用有向图定义Agent行为，想画多复杂画多复杂 |
| **CrewAI** | Role Play（角色扮演） | "你是资深研究员，你有20年经验..."最直觉的多Agent建模 |
| **AutoGen** | GroupChat（群聊协调） | 多个Agent像开会一样讨论，Selector决定谁发言 |
| **Claude Code** | Stream + 自动并发分区 | 边解析LLM响应边执行工具，只读工具自动并行 |
| **Claude Code** | 27个生命周期钩子 | 不改核心代码就能定制Agent行为的一切 |
| **Claude Code** | Prompt缓存边界分离 | 把系统提示分成可缓存和不可缓存两段，省钱省时间 |
| **Claude Code** | Fork SubAgent | 子Agent继承父Agent缓存，比新建Agent快很多 |

---

## 总结

### 钩子的本质

> **钩子 = 不改主流程代码也能定制 Agent 行为的"插入点"**

就像 Git 的 pre-commit hook、React 的 useEffect、Vue 的 onMounted 一样。你不需要修改 Agent 的核心循环代码，只需要在指定事件点"挂"上自定义逻辑。

### 从最简到最强的关键跃迁

| 跃迁 | 核心变化 |
|------|---------|
| L0→L1 | 从"单次调用"到"循环" — **Agent 的灵魂** |
| L1→L2 | 从"手写JSON"到"装饰器" — **降低开发门槛** |
| L2→L3 | 从"while循环"到"状态图" — **可控的复杂流程** |
| L3→L4 | 从"单Agent"到"多Agent" — **分工协作** |
| L4→L5 | 从"一次性"到"可恢复" — **持久化和容错** |
| L5→L6 | 从"能用"到"生产级" — **安全、性能、可观测** |
