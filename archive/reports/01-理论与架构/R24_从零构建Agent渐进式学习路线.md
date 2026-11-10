---
title: 从零构建 Agent：基于 Claude Code 源码的渐进式学习路线
aliases: [R24, Agent构建路线, Claude Code学习路线, Agent渐进式教程, 从零构建Agent-基于Claude-Code源码的渐进式学习路线]
tags: [architecture, agent, claude-code, tutorial, learning-path, source-analysis]
date: 2026-04-12
category: 理论与架构
report_id: R24
tokens: 0
status: completed
related:
  - "[Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "Claude-Code源码上下文策略实验报告（原稿交叉引用，本归档未解析）"
  - "[钩子详解与Agent层级对比](R12_%E9%92%A9%E5%AD%90%E8%AF%A6%E8%A7%A3%E4%B8%8EAgent%E5%B1%82%E7%BA%A7%E5%AF%B9%E6%AF%94.md)"
  - "[Google ADK五大Agent技能设计模式研究报告](R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md)"
  - "[Agent部署上线方案全景调研报告](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)"
prev_path: reports/从零构建Agent-基于Claude-Code源码的渐进式学习路线.md
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# 从零构建 Agent：基于 Claude Code 源码的渐进式学习路线

> **一句话概括**：以 Claude Code（113K⭐）的真实源码为解剖标本，将一个生产级 Agent 拆解为 8 个渐进式迭代——从 30 行的最小循环到 50 万行的完整系统——每个迭代都有可运行的 Python 实例代码和源码映射。
>
> **研究日期**：2026-04-12
>
> **增量价值**：在 [Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) 的理论基础和 Claude-Code源码上下文策略实验报告（原稿交叉引用，本归档未解析） 的实验数据上，新增了**构造性学习路径**——不是"拆开一个成品告诉你里面有什么"，而是"从一块铁开始，一步步锻造成一把刀"。
>
> **关联报告**：[Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)（理论基础）、[钩子详解与Agent层级对比](R12_%E9%92%A9%E5%AD%90%E8%AF%A6%E8%A7%A3%E4%B8%8EAgent%E5%B1%82%E7%BA%A7%E5%AF%B9%E6%AF%94.md)（L0-L6 递进）、[Google ADK五大Agent技能设计模式研究报告](R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md)（设计模式）

---

## 目录

1. [为什么要"从零构建"](#1-为什么要从零构建)
2. [Claude Code 五层架构总览](#2-claude-code-五层架构总览)
3. [八次迭代：从 30 行到生产级](#3-八次迭代从-30-行到生产级)
   - [Iter 0: 增强型 LLM — 单次调用](#iter-0-增强型-llm--单次调用30-行)
   - [Iter 1: 最小 Agent — ReAct 循环](#iter-1-最小-agent--react-循环80-行)
   - [Iter 2: 工具系统 — 注册、调度、执行](#iter-2-工具系统--注册调度执行200-行)
   - [Iter 3: 上下文工程 — 让 Agent 有记忆和感知](#iter-3-上下文工程--让-agent-有记忆和感知350-行)
   - [Iter 4: 流式执行与并发 — 速度是体验](#iter-4-流式执行与并发--速度是体验500-行)
   - [Iter 5: 安全与权限 — 信任边界](#iter-5-安全与权限--信任边界650-行)
   - [Iter 6: 对话压缩 — 无限对话的秘密](#iter-6-对话压缩--无限对话的秘密800-行)
   - [Iter 7: 多 Agent 协作 — 团队作战](#iter-7-多-agent-协作--团队作战1000-行)
4. [全景：八次迭代与 Claude Code 的映射](#4-全景八次迭代与-claude-code-的映射)
5. [核心设计模式提炼](#5-核心设计模式提炼)
6. [学习建议与实施计划](#6-学习建议与实施计划)
7. [开放问题与后续计划](#7-开放问题与后续计划)

---

## 1. 为什么要"从零构建"

**结论先行**：理解 Agent 最好的方式不是读论文，不是看框架文档，而是**自己从第一行代码开始搭**——因为只有在搭建过程中，你才会遇到那些设计决策背后的真实问题。

说白了，看一个完整的 Agent 系统（比如 Claude Code 的 50 万行 TypeScript），你看到的是**结果**——"哦，它有个压缩系统、有个权限系统"。但你不知道**为什么**要有这些东西。是什么问题逼着开发者加了这些复杂机制？

构造性学习路径解决的就是这个问题：

| 方法 | 你学到的 | 缺什么 |
|------|---------|--------|
| 读论文/博客 | 概念、术语 | 不知道怎么写第一行代码 |
| 读成品源码 | 实现细节 | 被 50 万行淹没，抓不住主线 |
| 用框架搭 demo | 跑通了一个 hello world | 不知道框架替你做了什么 |
| **从零构建** | **每个机制存在的原因 + 实现方法** | 需要好的路线图（本报告） |

### 标本选择：为什么是 Claude Code

| 维度 | Claude Code | 其他选择 |
|------|------------|---------|
| 复杂度 | 生产级（50万行，45+工具） | AutoGPT 过度复杂但不够工程化 |
| 透明度 | 完整开源，源码可读 | ChatGPT/Cursor 闭源 |
| 设计质量 | Anthropic 团队，架构清晰 | 许多开源项目架构混乱 |
| 社区验证 | 113K⭐，日活百万级 | 大多数项目未经大规模验证 |
| 文档化 | 官方指南 + 本团队19篇分析报告 | 多数项目缺乏深度分析 |

> 📌 来源：[github.com/anthropics/claude-code](https://github.com/anthropics/claude-code) — 2026-04-12 — 113K Stars，51 Contributors
> 📌 本工作区标本：`claude-code-main/src/`（1884 文件，47.7 万行，759 万 tokens）

---

## 2. Claude Code 五层架构总览

在开始逐步构建之前，先鸟瞰一下最终目标长什么样。这张图你现在看不懂没关系——完成 8 次迭代后，每一层你都会亲手实现过。

```mermaid
graph TB
    subgraph L5["🖥️ UI 层 (screens/components/)"]
        REPL["REPL.tsx — 主交互循环"]
        Input["PromptInput → handlePromptSubmit"]
        Render["消息渲染 + 任务面板"]
    end
    
    subgraph L4["📦 状态层 (state/ + context/)"]
        AppState["AppState (React Context)"]
        Bootstrap["bootstrap/state.ts (全局单例)"]
        MsgArray["Message[] 消息数组"]
    end
    
    subgraph L3["🔄 Agent 循环层 (query.ts + QueryEngine.ts)"]
        Compact["消息压缩 (snip→micro→auto→reactive)"]
        Stream["模型流式调用"]
        Schedule["工具调度 (并发/串行分区)"]
        Decide["决策逻辑 (继续/终止)"]
    end
    
    subgraph L2["🔧 工具/服务层 (services/)"]
        ToolExec["工具执行 (tools/*)"]
        API["API 调用 (services/api/)"]
        MCP["MCP 集成 (services/mcp/)"]
        CompactSvc["压缩服务 (services/compact/)"]
    end
    
    subgraph L1["⚡ 接口层"]
        Claude["Claude API (流式)"]
        Subprocess["子进程 (BashTool)"]
        FS["文件系统"]
    end
    
    L5 --> L4
    L4 --> L3
    L3 --> L2
    L2 --> L1
```

**关键数据**（来源：Claude-Code源码上下文策略实验报告（原稿交叉引用，本归档未解析））：

| 模块 | 文件数 | 代码行数 | 占比 |
|------|--------|---------|------|
| utils/ | 564 | 164,853 | 34.6% |
| components/ | 389 | 80,127 | 16.8% |
| services/ | 130 | 49,025 | 10.3% |
| tools/ | 184 | 47,154 | 9.9% |
| commands/ | 189 | 24,959 | 5.2% |
| 其他 | 428 | 110,806 | 23.2% |

说白了：**工具箱（utils）占了三分之一**，这不奇怪——一个生产级系统大部分代码都在处理边界情况。你在学习路线中不需要写这些，但需要知道它们存在的原因。

---

## 3. 八次迭代：从 30 行到生产级

### 设计哲学

每次迭代遵循同一个模式：

1. **遇到问题** → 上一个版本无法处理的真实场景
2. **理解 Claude Code 怎么做的** → 源码映射
3. **动手实现最小版本** → 可运行的 Python 代码
4. **对比差距** → Claude Code 还做了什么，你暂时可以跳过什么

```mermaid
graph LR
    A["Iter 0<br/>增强型 LLM<br/>30行"] --> B["Iter 1<br/>ReAct 循环<br/>80行"]
    B --> C["Iter 2<br/>工具系统<br/>200行"]
    C --> D["Iter 3<br/>上下文工程<br/>350行"]
    D --> E["Iter 4<br/>流式+并发<br/>500行"]
    E --> F["Iter 5<br/>安全权限<br/>650行"]
    F --> G["Iter 6<br/>对话压缩<br/>800行"]
    G --> H["Iter 7<br/>多Agent<br/>1000行"]
    
    style A fill:#e8f5e9
    style B fill:#e8f5e9
    style C fill:#fff3e0
    style D fill:#fff3e0
    style E fill:#fff9c4
    style F fill:#fff9c4
    style G fill:#fce4ec
    style H fill:#fce4ec
```

---

### Iter 0: 增强型 LLM — 单次调用（30 行）

#### 要解决的问题

你有一个 LLM API，想让它帮你做点事。最简单的方式：发一条消息，拿一个回复。

#### Claude Code 源码映射

这是 Claude Code 最原始的组件——API 调用层。在源码中对应 `services/api/claude.ts` 的模型调用部分。

#### Python 实例

```python
"""
Iter 0: 增强型 LLM — 单次调用
这还不是 Agent，只是一个 LLM 调用。但这是一切的起点。
"""
import openai

client = openai.OpenAI()  # 兼容任何 OpenAI 格式的 API

def ask_llm(user_message: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """最简单的 LLM 调用：一问一答"""
    response = client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content

# 使用
answer = ask_llm("帮我写一个 Python 的快速排序")
print(answer)
```

#### 这个版本的局限

- ❌ 无法执行代码（只能"说"，不能"做"）
- ❌ 无法读取文件（不知道你的项目长什么样）
- ❌ 单轮对话（前一句说了什么它不记得）
- ❌ 没有规划能力（复杂任务一步搞不定就废了）

> **从 Iter 0 到 Iter 1 的跃迁**，就是从"LLM"到"Agent"的本质区别：**让 LLM 能调用工具、能多轮循环、能根据结果调整行动**。

---

### Iter 1: 最小 Agent — ReAct 循环（80 行）

#### 要解决的问题

用户说"帮我看看当前目录有哪些 Python 文件，然后统计总行数"。这需要：
1. 执行 `ls *.py`
2. 看到结果
3. 决定对每个文件执行 `wc -l`
4. 汇总结果

单次调用做不到。你需要一个**循环**：思考 → 行动 → 观察 → 再思考…

#### Claude Code 源码映射

这是 Claude Code 的灵魂：`query.ts` 中的 `queryLoop` 函数。一个 `async generator`，无限循环，直到模型决定停止或达到终止条件。

```
源码路径：claude-code-main/src/query.ts
核心结构：
  while (true) {
    1. 调用模型（流式）→ 收集 assistant message
    2. 检查 stop_reason
       - 'tool_use' → 执行工具，把结果加入 messages，继续循环
       - 'end_turn' → 模型认为任务完成，检查停止钩子
       - 'max_tokens' → 输出被截断，尝试恢复
    3. 如果继续 → 回到步骤 1
    4. 如果终止 → return Terminal
  }
```

#### Python 实例

```python
"""
Iter 1: 最小 Agent — ReAct 循环
这是一个真正的 Agent 了：它能思考、行动、观察，循环直到完成。
核心：while True → call_model → execute_tools → loop_or_stop
"""
import json
import subprocess
import openai

client = openai.OpenAI()

# ━━━ 定义工具（告诉模型它能做什么）━━━
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"],
            },
        },
    }
]

def execute_tool(name: str, args: dict) -> str:
    """执行工具，返回结果字符串"""
    if name == "bash":
        try:
            result = subprocess.run(
                args["command"], shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout + result.stderr
            return output[:5000] if output else "(no output)"  # 截断防爆
        except subprocess.TimeoutExpired:
            return "Error: command timed out (30s)"
        except Exception as e:
            return f"Error: {e}"
    return f"Error: unknown tool '{name}'"

def agent_loop(user_message: str, max_turns: int = 10) -> str:
    """
    核心 Agent 循环 — 对应 Claude Code 的 queryLoop()
    
    关键洞察：模型看到工具执行错误后会自动调整策略。
    错误不是异常，错误是信息。这是 Agent 与普通程序的本质区别。
    """
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant. Use the bash tool to execute commands."},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        # ━━━ Step 1: 调用模型 ━━━
        response = client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg)  # 把模型回复加入历史

        # ━━━ Step 2: 检查是否需要调用工具 ━━━
        if not msg.tool_calls:
            # 模型没有调用工具 → 它认为任务完成了
            return msg.content

        # ━━━ Step 3: 执行所有工具调用 ━━━
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = execute_tool(tool_call.function.name, args)

            # 把工具结果加入历史（模型下一轮能看到）
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        # ━━━ Step 4: 继续循环（模型会看到工具结果，决定下一步）━━━

    return "Reached max turns without completing the task."

# ━━━ 使用 ━━━
result = agent_loop("列出当前目录的 Python 文件，并统计每个文件的行数")
print(result)
```

#### 这段代码对应 Claude Code 的什么

| 我们的实现 | Claude Code 对应 | 差距 |
|-----------|-----------------|------|
| `agent_loop()` | `queryLoop()` in `query.ts` | 我们是同步的，它是 async generator |
| `messages` 列表 | `State.messages` | 我们直接用列表，它有类型系统和压缩 |
| `max_turns` 硬限制 | 多种终止条件（成本、turn数、用户中断） | 我们只有一个退出条件 |
| `execute_tool()` | `runTools()` + `StreamingToolExecutor` | 我们是串行的，它支持并发 |
| 工具执行错误 → 返回字符串 | 同样：错误作为 `tool_result` 返回给模型 | 一致！这是关键设计 |

#### 关键学习点

1. **Agent 的本质就是一个循环**：`while True → think → act → observe`
2. **终止条件很重要**：没有 `max_turns`，Agent 可能无限循环
3. **错误是信息，不是异常**：把工具执行的错误信息返回给模型，让它学习和调整。Claude Code 的源码注释写道："Model learns from errors and adapts"

---

### Iter 2: 工具系统 — 注册、调度、执行（200 行）

#### 要解决的问题

Iter 1 只有一个 `bash` 工具，硬编码在 `execute_tool` 里。真实场景下你需要：
- 多种工具（文件读写、搜索、API 调用…）
- 动态注册（MCP 协议、插件系统…）
- 统一接口（每个工具长什么样？怎么调用？怎么返回结果？）

#### Claude Code 源码映射

Claude Code 的工具系统是其最精心设计的部分之一。核心定义在 `Tool.ts`，注册在 `tools.ts`，执行在 `services/tools/toolOrchestration.ts`。

```
Tool.ts 定义了 Tool 类型（~570 行），核心字段：
  - name: string                    ← 工具名
  - description(): Promise<string>  ← 动态描述（可根据上下文变化！）
  - inputSchema: ZodSchema          ← 输入验证
  - call(): Promise<ToolResult>     ← 执行逻辑
  - isConcurrencySafe(): boolean    ← 能否并行执行
  - isReadOnly(): boolean           ← 是否只读（影响权限）
  - isDestructive(): boolean        ← 是否破坏性（删除/覆写）
  - checkPermissions(): Promise<PermissionResult>  ← 权限检查
  - validateInput(): Promise<ValidationResult>     ← 输入校验
  
tools.ts 负责：
  - 条件加载（feature flag 控制哪些工具可用）
  - 按用户类型过滤（ANT-only 工具）
  - 按权限过滤（deny 规则）
```

**设计亮点**：Claude Code 的 `ToolUseContext` 是**依赖注入**模式——工具不直接 import 服务，所有依赖通过 context 传入。这让工具可测试、可隔离。

#### Python 实例

```python
"""
Iter 2: 工具系统 — 注册、调度、执行
关键进化：工具从硬编码变成可插拔的插件。
"""
import json
import subprocess
import os
from dataclasses import dataclass, field
from typing import Callable, Any
import openai

client = openai.OpenAI()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: 工具接口定义
# 对应 Claude Code 的 Tool.ts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ToolDefinition:
    """
    工具的统一接口。
    
    对应 Claude Code Tool 类型的精简版。
    Claude Code 的完整 Tool 类型有 ~30 个字段/方法，
    我们只保留核心的 5 个。
    """
    name: str
    description: str
    parameters: dict  # JSON Schema
    execute: Callable[[dict], str]  # 输入 → 输出
    is_read_only: bool = True  # 只读工具不需要权限确认

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: 内置工具实现
# 对应 claude-code-main/src/tools/ 目录
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _bash_execute(args: dict) -> str:
    """对应 tools/BashTool/"""
    try:
        result = subprocess.run(
            args["command"], shell=True, capture_output=True, text=True, timeout=30
        )
        output = (result.stdout + result.stderr).strip()
        return output[:10000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out (30s)"
    except Exception as e:
        return f"Error: {e}"

def _file_read_execute(args: dict) -> str:
    """对应 tools/FileReadTool/"""
    try:
        path = args["file_path"]
        if not os.path.exists(path):
            return f"Error: file not found: {path}"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Claude Code 的 FileReadTool 支持行号范围和分页
        # 我们先做简化版：截断超大文件
        if len(content) > 20000:
            content = content[:20000] + f"\n\n... (truncated, total {len(content)} chars)"
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def _file_write_execute(args: dict) -> str:
    """对应 tools/FileWriteTool/"""
    try:
        path = args["file_path"]
        content = args["content"]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def _grep_execute(args: dict) -> str:
    """对应 tools/GrepTool/ (底层用 ripgrep)"""
    try:
        pattern = args["pattern"]
        path = args.get("path", ".")
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, path],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches found for '{pattern}'"
        lines = output.split("\n")
        if len(lines) > 50:
            output = "\n".join(lines[:50]) + f"\n... ({len(lines)} total matches)"
        return output
    except Exception as e:
        return f"Error: {e}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 3: 工具注册表
# 对应 Claude Code 的 tools.ts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ToolRegistry:
    """
    工具注册表 — 管理所有可用工具。
    
    Claude Code 在 tools.ts 中做了更多：
    - Feature flag 条件加载
    - 用户类型过滤
    - 权限规则过滤
    - MCP 工具合并
    """
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)
    
    def all_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())
    
    def to_openai_format(self) -> list[dict]:
        """转换为 OpenAI function calling 格式"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

# 创建注册表并注册工具
registry = ToolRegistry()

registry.register(ToolDefinition(
    name="bash",
    description="Execute a shell command. Use for running scripts, installing packages, git operations, etc.",
    parameters={
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The shell command to run"}},
        "required": ["command"],
    },
    execute=_bash_execute,
    is_read_only=False,  # bash 可以修改系统
))

registry.register(ToolDefinition(
    name="file_read",
    description="Read the contents of a file. Use to understand code, configs, docs.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to read"},
        },
        "required": ["file_path"],
    },
    execute=_file_read_execute,
    is_read_only=True,
))

registry.register(ToolDefinition(
    name="file_write",
    description="Write content to a file. Creates parent directories if needed.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to write to"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["file_path", "content"],
    },
    execute=_file_write_execute,
    is_read_only=False,
))

registry.register(ToolDefinition(
    name="grep",
    description="Search for a text pattern in files. Returns matching lines with file paths and line numbers.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Text pattern to search for"},
            "path": {"type": "string", "description": "Directory to search in", "default": "."},
        },
        "required": ["pattern"],
    },
    execute=_grep_execute,
    is_read_only=True,
))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 4: Agent 循环（使用注册表）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def agent_loop(user_message: str, max_turns: int = 15) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant. Use tools to help the user."},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            tools=registry.to_openai_format(),
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        for tool_call in msg.tool_calls:
            tool = registry.get(tool_call.function.name)
            if tool is None:
                result = f"Error: unknown tool '{tool_call.function.name}'"
            else:
                args = json.loads(tool_call.function.arguments)
                result = tool.execute(args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "Reached max turns."

# ━━━ 使用 ━━━
result = agent_loop("读取 README.md 的内容，然后在当前目录中搜索所有包含 'import' 的 Python 文件")
print(result)
```

#### 关键学习点

1. **工具是 Agent 的手和脚**：Agent 的能力 = LLM 智能 × 工具集
2. **统一接口是基础**：`ToolDefinition` 让所有工具长得一样，Agent 循环不需要关心具体工具实现
3. **注册表模式**：新增工具只需 `registry.register()`，不改循环代码。Claude Code 基于此实现了 MCP 动态工具、插件工具、Skill 工具的无缝接入
4. **`is_read_only` 标记**：看似简单的一个布尔值，是后续权限系统的基础

---

### Iter 3: 上下文工程 — 让 Agent 有记忆和感知（350 行）

#### 要解决的问题

Iter 2 的 Agent 是"无知的"——它不知道自己在哪个项目里，不知道 git 状态，不知道用户之前的偏好。你让它改代码，它连项目结构都不了解。

上下文工程（Context Engineering）就是解决这个问题：**在 Agent 开始思考之前，把相关信息注入到它的 system prompt 里**。

#### Claude Code 源码映射

Claude Code 的上下文系统在 `context.ts` 和 `context/` 目录：

```
context.ts 两个核心函数（都用 memoize 缓存）：
  
  getSystemContext() → {
    gitStatus,         ← git branch, status, recent log
    cacheBreaker       ← 调试用
  }
  
  getUserContext() → {
    projectStructure,  ← 目录树
    memory,           ← CLAUDE.md + user memory
    systemCapabilities,← OS, shell
    workingDirectory,  ← cwd
    modeSpecificInfo   ← coordinator/remote 模式特定信息
  }

使用方式（query.ts 中）：
  systemPrompt = basePrompt 
    + "<system_context>" + systemContext + "</system_context>"
    + userContext
```

**关键设计**：上下文通过 `memoize` 在整个会话中缓存，不是每轮都重新获取。这是一个重要的性能决策——git status 在一次对话中很少变化。

此外，Claude Code 有一套**层次化记忆系统**：
- **CLAUDE.md**（项目记忆）：项目级别的规则和上下文
- **~/.claude/CLAUDE.md**（用户记忆）：跨项目的用户偏好
- **会话内记忆**：对话中的 messages 本身
- **附件系统**（`utils/attachments.ts`）：动态注入相关 memory 片段

#### Python 实例

```python
"""
Iter 3: 上下文工程 — 让 Agent 有记忆和感知
关键进化：Agent 现在知道自己在哪个项目里、项目状态如何、用户有什么偏好。
"""
import os
import subprocess
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: 上下文收集器
# 对应 Claude Code 的 context.ts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ContextBuilder:
    """
    动态构建 system prompt 的上下文。
    
    Claude Code 的做法：memoize(async () => ...) 缓存整个会话。
    我们用简单的属性缓存模拟这个行为。
    """
    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)
        self._cache: dict[str, str] = {}
    
    def _run_cmd(self, cmd: str, timeout: int = 5) -> str:
        """安全执行命令"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=self.working_dir
            )
            return result.stdout.strip()
        except Exception:
            return ""
    
    def get_git_context(self) -> str:
        """
        对应 Claude Code 的 getGitStatus()
        获取 git 分支、状态、最近提交
        """
        if "git" in self._cache:
            return self._cache["git"]
        
        is_git = self._run_cmd("git rev-parse --is-inside-work-tree") == "true"
        if not is_git:
            self._cache["git"] = "(not a git repository)"
            return self._cache["git"]
        
        branch = self._run_cmd("git branch --show-current")
        status = self._run_cmd("git status -s")
        recent_log = self._run_cmd("git log --oneline -5")
        
        # Claude Code 会截断超过 2K 字符的 status
        if len(status) > 2000:
            status = status[:2000] + "\n... (truncated)"
        
        context = f"""Git Branch: {branch}
Git Status:
{status if status else '(clean)'}

Recent Commits:
{recent_log}"""
        
        self._cache["git"] = context
        return context
    
    def get_project_structure(self, max_depth: int = 2, max_files: int = 50) -> str:
        """
        对应 Claude Code 的 projectStructure 上下文
        生成项目目录树（Claude Code 用 Repo Map 做更精细的压缩）
        """
        if "structure" in self._cache:
            return self._cache["structure"]
        
        lines = []
        count = 0
        for root, dirs, files in os.walk(self.working_dir):
            # 跳过隐藏目录和常见忽略目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in 
                       {"node_modules", "__pycache__", "venv", ".git", "dist", "build"}]
            
            depth = root.replace(self.working_dir, "").count(os.sep)
            if depth > max_depth:
                continue
            
            indent = "  " * depth
            folder_name = os.path.basename(root)
            lines.append(f"{indent}{folder_name}/")
            
            for f in sorted(files)[:10]:  # 每个目录最多显示 10 个文件
                lines.append(f"{indent}  {f}")
                count += 1
                if count >= max_files:
                    lines.append(f"\n... ({count}+ files, showing first {max_files})")
                    self._cache["structure"] = "\n".join(lines)
                    return self._cache["structure"]
        
        self._cache["structure"] = "\n".join(lines)
        return self._cache["structure"]
    
    def get_memory(self) -> str:
        """
        对应 Claude Code 的 CLAUDE.md 记忆系统
        读取项目级和用户级的记忆文件
        """
        if "memory" in self._cache:
            return self._cache["memory"]
        
        memory_parts = []
        
        # 项目级记忆（对应 CLAUDE.md）
        project_memory = os.path.join(self.working_dir, "CLAUDE.md")
        if os.path.exists(project_memory):
            with open(project_memory, "r", encoding="utf-8") as f:
                content = f.read()
            memory_parts.append(f"## Project Memory (CLAUDE.md)\n{content}")
        
        # 用户级记忆（对应 ~/.claude/CLAUDE.md）
        user_memory = os.path.expanduser("~/.agent_memory.md")
        if os.path.exists(user_memory):
            with open(user_memory, "r", encoding="utf-8") as f:
                content = f.read()
            memory_parts.append(f"## User Memory\n{content}")
        
        self._cache["memory"] = "\n\n".join(memory_parts) if memory_parts else ""
        return self._cache["memory"]
    
    def build_system_prompt(self, base_prompt: str) -> str:
        """
        组装完整的 system prompt
        
        对应 Claude Code query.ts 中的:
          systemPrompt = basePrompt + systemContext + userContext
        """
        parts = [base_prompt]
        
        # 注入上下文
        git_ctx = self.get_git_context()
        if git_ctx:
            parts.append(f"\n<git_context>\n{git_ctx}\n</git_context>")
        
        structure = self.get_project_structure()
        if structure:
            parts.append(f"\n<project_structure>\n{structure}\n</project_structure>")
        
        memory = self.get_memory()
        if memory:
            parts.append(f"\n<memory>\n{memory}\n</memory>")
        
        parts.append(f"\nCurrent working directory: {self.working_dir}")
        
        return "\n".join(parts)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: 集成到 Agent 循环
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def agent_loop_v3(user_message: str, working_dir: str = ".", max_turns: int = 15) -> str:
    """Iter 3 Agent — 带上下文感知"""
    ctx = ContextBuilder(working_dir)
    
    system_prompt = ctx.build_system_prompt(
        "You are a helpful coding assistant working in the user's project. "
        "Use the available tools to help. Consider the git status and project "
        "structure when making decisions."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    
    # ... 后续 Agent 循环与 Iter 2 相同 ...
    # （省略重复代码，关键变化是 system_prompt 现在包含了丰富的上下文）
```

#### Claude Code 做了什么我们还没做的

| 特性 | Claude Code | 我们的简化版 |
|------|------------|------------|
| 缓存策略 | `lodash.memoize` + 会话级 | 简单字典缓存 |
| 记忆层次 | 5 层（项目/用户/企业/会话/附件） | 2 层（项目/用户） |
| 动态记忆 | `startRelevantMemoryPrefetch()` 按需加载相关记忆 | 全量加载 |
| Repo Map | PageRank 排序的压缩项目地图 | 简单目录树 |
| 上下文模板 | XML 标签包裹 + 可配置注入点 | 硬编码拼接 |

#### 关键学习点

1. **上下文 = Agent 的"眼睛"**：没有上下文的 Agent 是盲人摸象
2. **缓存很重要**：git status 不需要每轮调用都重新获取。Claude Code 的 `memoize` 策略是"一次获取，整个会话复用"
3. **结构化上下文**：用 XML 标签（`<git_context>`）包裹不同类型的上下文，比裸文本更让模型理解
4. **CLAUDE.md 是天才设计**：项目级的记忆文件，解决了"Agent 怎么知道这个项目的特殊规则"的问题

---

### Iter 4: 流式执行与并发 — 速度是体验（500 行）

#### 要解决的问题

Iter 3 的 Agent 是这么工作的：
1. 等模型**完整**生成回复（2-3 秒）
2. 然后**串行**执行每个工具（每个 1-2 秒）
3. 总时间：3 + 2×N 秒

用户看到的是：傻等→突然出一大段→又傻等。体验很差。

Claude Code 用了两个关键优化：
- **流式输出**：模型的回复一边生成一边显示
- **并发工具执行**：多个只读工具同时运行

#### Claude Code 源码映射

```
流式处理：services/api/claude.ts
  → 使用 Anthropic SDK 的流式 API
  → 事件类型：content_block_start, content_block_delta, content_block_stop
  → tool_use block 一完成就立即执行（不等模型整体输出结束）

并发执行：services/tools/toolOrchestration.ts
  → runTools() 函数核心逻辑：
    1. 把工具调用分区：
       - concurrent-safe batch（文件读取、搜索等）
       - exclusive batch（文件写入、bash执行）
    2. concurrent batch → Promise.all() 并行
    3. exclusive batch → 逐个串行
    
判断标准：Tool.ts 的 isConcurrencySafe(input) 方法
  → FileReadTool: always true（读取不冲突）
  → GrepTool: always true
  → FileWriteTool: always false（写入可能冲突）
  → BashTool: always false（命令可能有副作用）
```

**性能提升数据**：流式执行 + 并发工具，相比同步串行，整体延迟约减少 40%。

#### Python 实例

```python
"""
Iter 4: 流式执行与并发
关键进化：Agent 的响应从"等半天突然蹦出一大段"变成"逐字涌出 + 工具并行跑"。
"""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: 工具并发安全标记
# 对应 Tool.ts 的 isConcurrencySafe()
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 在 ToolDefinition 中增加并发安全标记
# is_concurrency_safe: bool = False

CONCURRENCY_SAFE_TOOLS = {"file_read", "grep"}  # 只读工具可以并发

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: 并发工具执行器
# 对应 services/tools/toolOrchestration.ts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def execute_tools_batched(tool_calls: list, registry) -> list[dict]:
    """
    分区执行工具：
    - 并发安全的工具 → 并行执行
    - 非安全的工具 → 串行执行
    
    对应 Claude Code 的 runTools() → partition → concurrent/serial batches
    """
    results = []
    
    # Step 1: 分区
    concurrent_batch = []
    serial_batch = []
    
    for tc in tool_calls:
        if tc.function.name in CONCURRENCY_SAFE_TOOLS:
            concurrent_batch.append(tc)
        else:
            serial_batch.append(tc)
    
    # Step 2: 并行执行 concurrent-safe 的工具
    if concurrent_batch:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for tc in concurrent_batch:
                tool = registry.get(tc.function.name)
                args = json.loads(tc.function.arguments)
                future = loop.run_in_executor(executor, tool.execute, args)
                futures.append((tc, future))
            
            for tc, future in futures:
                result = await future
                results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
    
    # Step 3: 串行执行 exclusive 的工具
    for tc in serial_batch:
        tool = registry.get(tc.function.name)
        if tool:
            args = json.loads(tc.function.arguments)
            result = tool.execute(args)
        else:
            result = f"Error: unknown tool '{tc.function.name}'"
        results.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })
    
    return results

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 3: 流式 Agent 循环
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def agent_loop_v4(user_message: str, max_turns: int = 15):
    """
    Iter 4 Agent — 流式输出 + 并发工具执行
    
    Claude Code 的 queryLoop 是 async generator，
    yield StreamEvent | Message | TombstoneMessage
    
    我们用 print 模拟流式输出。
    """
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": user_message},
    ]
    
    for turn in range(max_turns):
        # ━━━ 流式调用模型 ━━━
        stream = client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            tools=registry.to_openai_format(),
            stream=True,  # 关键：流式！
        )
        
        # 收集流式响应
        collected_content = ""
        tool_calls_buffer = {}
        
        for chunk in stream:
            delta = chunk.choices[0].delta
            
            # 流式输出文本（用户实时看到）
            if delta.content:
                print(delta.content, end="", flush=True)
                collected_content += delta.content
            
            # 收集工具调用（增量拼接）
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": ""
                        }
                    if tc_delta.id:
                        tool_calls_buffer[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_buffer[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc_delta.function.arguments
        
        print()  # 换行
        
        # 构建完整消息
        msg = {"role": "assistant", "content": collected_content or None}
        if tool_calls_buffer:
            msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]}
                }
                for tc in tool_calls_buffer.values()
            ]
        messages.append(msg)
        
        # 没有工具调用 → 完成
        if not tool_calls_buffer:
            return collected_content
        
        # ━━━ 并发执行工具 ━━━
        print(f"  [executing {len(tool_calls_buffer)} tool(s)...]")
        
        # 这里简化处理：构造类似的 tool_call 对象
        class FakeTC:
            def __init__(self, data):
                self.id = data["id"]
                self.function = type("F", (), {
                    "name": data["name"],
                    "arguments": data["arguments"]
                })()
        
        fake_tcs = [FakeTC(tc) for tc in tool_calls_buffer.values()]
        tool_results = await execute_tools_batched(fake_tcs, registry)
        messages.extend(tool_results)
    
    return "Max turns reached."

# ━━━ 使用 ━━━
# asyncio.run(agent_loop_v4("读取 src/ 下的所有 .py 文件并做代码审查"))
```

#### 关键学习点

1. **流式是 UX 的关键**：用户宁愿看到逐字出现的内容，也不愿意等 5 秒看到完整输出
2. **并发分区的设计思维**：不是所有操作都能并行——Claude Code 的 `isConcurrencySafe()` 是一个简单但关键的设计决策
3. **Claude Code 的极致优化**：它甚至在模型**还在流式输出的时候**就开始执行工具（`StreamingToolExecutor`），一个 tool_use block 完成就立即派发。这是 40% 延迟优化的来源

---

### Iter 5: 安全与权限 — 信任边界（650 行）

#### 要解决的问题

到 Iter 4，Agent 可以执行任何命令、读写任何文件。这在自己电脑上玩玩没问题，但一旦涉及：
- 用户不想被修改的文件
- 破坏性命令（`rm -rf`）
- 敏感操作（发送网络请求、修改 git 历史）

你就需要一个**权限系统**。

#### Claude Code 源码映射

Claude Code 有一套精心设计的五级权限模型：

```
Tool.ts 中的 ToolPermissionContext:
  mode: PermissionMode
    - 'default'  → 每次操作弹确认框
    - 'auto'     → 自动批准安全操作，拒绝危险操作
    - 'ask'      → 全部都问
    - 'plan'     → 先展示计划，用户批准后批量执行
    - 'bypass'   → 不检查（危险，需 opt-in）
  
  alwaysAllowRules  → 白名单（如 "bash: git *" 允许所有 git 命令）
  alwaysDenyRules   → 黑名单（如 "bash: rm -rf *"）
  alwaysAskRules    → 必须询问的操作

权限检查流程（hooks/useCanUseTool.tsx）：
  1. 检查 mode
  2. 检查白名单 → 直接放行
  3. 检查黑名单 → 直接拒绝
  4. 检查工具是否 isReadOnly → 只读工具降低风险
  5. 检查工具是否 isDestructive → 破坏性工具提高警告
  6. 根据 mode 决定：自动批准/弹框/拒绝
```

**精妙之处**：工具的 `description()` 方法是**异步函数**，可以根据当前权限上下文返回不同描述。比如当权限更严格时，描述会更明确地说明副作用。

#### Python 实例

```python
"""
Iter 5: 安全与权限 — 信任边界
关键进化：Agent 不再是"无拘无束"的，它学会了"请求许可"。
"""
from enum import Enum
from dataclasses import dataclass, field

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: 权限模型
# 对应 Claude Code 的 ToolPermissionContext
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PermissionMode(Enum):
    DEFAULT = "default"    # 危险操作需确认
    AUTO = "auto"          # 自动批准安全操作
    ASK_ALL = "ask_all"    # 全部都问
    BYPASS = "bypass"      # 不检查（调试用）

@dataclass
class PermissionContext:
    """
    权限上下文 — 控制 Agent 能做什么。
    
    对应 Claude Code 的 ToolPermissionContext（精简版）。
    完整版有 ~15 个字段，我们保留核心 4 个。
    """
    mode: PermissionMode = PermissionMode.DEFAULT
    always_allow: set[str] = field(default_factory=lambda: {
        "file_read", "grep"  # 只读工具默认放行
    })
    always_deny: set[str] = field(default_factory=set)
    dangerous_patterns: list[str] = field(default_factory=lambda: [
        "rm -rf", "rm -r /", "DROP TABLE", "DELETE FROM",
        "git push --force", "git reset --hard",
        "> /dev/", "mkfs", "dd if="
    ])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: 权限检查器
# 对应 hooks/useCanUseTool.tsx
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PermissionChecker:
    def __init__(self, context: PermissionContext):
        self.ctx = context
    
    def check(self, tool_name: str, tool_input: dict, tool_def: 'ToolDefinition') -> tuple[bool, str]:
        """
        检查是否允许执行工具。
        返回 (allowed, reason)
        
        对应 Claude Code 的 canUseTool() 流程：
        mode → whitelist → blacklist → isReadOnly → isDestructive → decide
        """
        # Bypass 模式：全放行
        if self.ctx.mode == PermissionMode.BYPASS:
            return True, "bypass mode"
        
        # 黑名单检查
        if tool_name in self.ctx.always_deny:
            return False, f"tool '{tool_name}' is in deny list"
        
        # 白名单检查
        if tool_name in self.ctx.always_allow:
            return True, "tool is in allow list"
        
        # 对 bash 命令做特殊检查
        if tool_name == "bash":
            command = tool_input.get("command", "")
            for pattern in self.ctx.dangerous_patterns:
                if pattern in command:
                    if self.ctx.mode == PermissionMode.AUTO:
                        return False, f"dangerous pattern detected: '{pattern}'"
                    elif self.ctx.mode == PermissionMode.DEFAULT:
                        # 交互式确认
                        return self._ask_user(tool_name, tool_input, f"⚠️ Dangerous: '{pattern}'")
                    elif self.ctx.mode == PermissionMode.ASK_ALL:
                        return self._ask_user(tool_name, tool_input, "requires confirmation")
        
        # 只读工具 → 放行
        if tool_def.is_read_only:
            return True, "read-only tool"
        
        # 非只读工具在 ASK_ALL 模式下需确认
        if self.ctx.mode == PermissionMode.ASK_ALL:
            return self._ask_user(tool_name, tool_input, "non-read-only operation")
        
        # DEFAULT 模式：非只读操作需确认
        if self.ctx.mode == PermissionMode.DEFAULT:
            return self._ask_user(tool_name, tool_input, "write operation")
        
        # AUTO 模式：非危险操作自动放行
        return True, "auto-approved"
    
    def _ask_user(self, tool_name: str, tool_input: dict, reason: str) -> tuple[bool, str]:
        """交互式确认"""
        print(f"\n🔐 Permission Request: {tool_name}")
        print(f"   Input: {json.dumps(tool_input, ensure_ascii=False)[:200]}")
        print(f"   Reason: {reason}")
        response = input("   Allow? (y/n/a=always allow): ").strip().lower()
        
        if response == "a":
            self.ctx.always_allow.add(tool_name)
            return True, "user approved (always)"
        elif response == "y":
            return True, "user approved (once)"
        else:
            return False, "user denied"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 3: 集成到 Agent 循环
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def agent_loop_v5(user_message: str, 
                   permission_mode: PermissionMode = PermissionMode.DEFAULT,
                   max_turns: int = 15) -> str:
    perm_ctx = PermissionContext(mode=permission_mode)
    perm_checker = PermissionChecker(perm_ctx)
    
    # ... Agent 循环中的工具执行部分变为：
    
    # for tool_call in msg.tool_calls:
    #     tool = registry.get(tool_call.function.name)
    #     args = json.loads(tool_call.function.arguments)
    #     
    #     # ━━━ 权限检查 ━━━
    #     allowed, reason = perm_checker.check(tool_call.function.name, args, tool)
    #     
    #     if not allowed:
    #         # 把拒绝原因告诉模型（模型会调整策略）
    #         result = f"Permission denied: {reason}. Try a different approach."
    #     else:
    #         result = tool.execute(args)
    pass
```

#### 关键学习点

1. **权限拒绝不是错误，是信息**：把"Permission denied"作为 tool_result 返回给模型，模型会学会用替代方案。这与 Iter 1 的"错误是信息"一脉相承
2. **分层权限设计**：Claude Code 的 5 种 mode 不是拍脑袋设计的——DEFAULT 给普通用户、AUTO 给后台 Agent、ASK_ALL 给敏感环境，每种都有明确场景
3. **"Always allow" 的智慧**：让用户 approve 一次后不再烦他，但只对该工具生效。Claude Code 还支持 pattern 级别的 always-allow，如 `bash: git *`

---

### Iter 6: 对话压缩 — 无限对话的秘密（800 行）

#### 要解决的问题

Agent 工作得越多，messages 列表就越长。一个稍复杂的任务可能产生 50+ 轮对话，轻松超过 200K token 的上下文窗口。

怎么办？不能简单截断（会丢失关键信息），也不能什么都不做（context overflow 会让 API 报错）。

#### Claude Code 源码映射

这是 Claude Code 最复杂的子系统之一。五级压缩瀑布（Compaction Cascade）：

```
services/compact/ 目录：

Level 1: Snip（剪切）
  → 删除最老的消息
  → 最简单，信息损失最大
  → threshold: 可配置

Level 2: Microcompact（微压缩）
  → 把连续的 tool_use + tool_result 块合并为摘要
  → "读了 5 个文件" 而不是完整的 5 轮对话
  → 信息损失小

Level 3: Autocompact（自动压缩）
  → 当 context > 100K tokens 时触发
  → 调用 LLM 对整段历史生成摘要
  → 摘要 + 最近 N 条消息 替代完整历史
  → 压缩比可达 50:1

Level 4: Reactive Compact（被动压缩）
  → 当模型返回 max_output_tokens 错误时触发
  → 激进压缩：只保留最近 20 条消息
  → 最后手段

Level 5: Context Collapse（上下文折叠）
  → 高级多消息摘要
  → feature flag 控制，实验性功能

触发逻辑（query.ts 中）：
  tokenCount = estimateTokenCount(messages)
  if tokenCount < 100K → 不压缩
  if 100K-200K → microcompact
  if > 200K → autocompact
  if max_output_tokens error → reactive compact
```

**关键洞察**：压缩不只是技术问题，更是**信息选择**问题——哪些信息值得保留？Claude Code 的做法是"最近的完整保留 + 历史的精华摘要"。

#### Python 实例

```python
"""
Iter 6: 对话压缩 — 无限对话的秘密
关键进化：Agent 从"只能聊 20 轮"变成"理论上无限对话"。
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: Token 估算
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def estimate_tokens(messages: list[dict]) -> int:
    """粗略估算 token 数（1 token ≈ 4 字符英文 / 2 字符中文）"""
    total_chars = sum(
        len(str(m.get("content", ""))) for m in messages
    )
    return total_chars // 3  # 保守估计

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: 压缩策略
# 对应 services/compact/ 目录
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CompactionEngine:
    """
    对话压缩引擎 — Claude Code 五级瀑布压缩的简化版（三级）。
    """
    
    def __init__(self, llm_client):
        self.client = llm_client
    
    def compact_if_needed(self, messages: list[dict], 
                          threshold: int = 80000) -> list[dict]:
        """
        主入口：检查是否需要压缩，选择合适的策略。
        
        Claude Code 的瀑布逻辑：
          < 100K → 不动
          100K-200K → microcompact
          > 200K → autocompact
          error → reactive
        
        我们简化为：
          < threshold → 不动
          threshold-2x → microcompact
          > 2x → autocompact
        """
        token_count = estimate_tokens(messages)
        
        if token_count < threshold:
            return messages
        
        if token_count < threshold * 2:
            print(f"  [microcompact: {token_count} tokens → ", end="")
            result = self._microcompact(messages)
            print(f"{estimate_tokens(result)} tokens]")
            return result
        
        print(f"  [autocompact: {token_count} tokens → ", end="")
        result = self._autocompact(messages)
        print(f"{estimate_tokens(result)} tokens]")
        return result
    
    def _microcompact(self, messages: list[dict]) -> list[dict]:
        """
        Level 2: 微压缩 — 合并连续工具调用
        
        把类似这样的序列：
          assistant: [tool_use: file_read("a.py")]
          tool: "content of a.py..."
          assistant: [tool_use: file_read("b.py")]
          tool: "content of b.py..."
        
        压缩为：
          system: "Previously read files: a.py, b.py"
        """
        compacted = []
        tool_sequence = []
        
        for msg in messages:
            if msg["role"] == "tool":
                # 收集工具结果
                tool_sequence.append(msg)
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                # 收集工具调用
                tool_sequence.append(msg)
            else:
                # 非工具消息：先提交积累的工具序列
                if tool_sequence:
                    summary = self._summarize_tool_sequence(tool_sequence)
                    compacted.append({
                        "role": "system",
                        "content": f"[Compacted tool sequence: {summary}]"
                    })
                    tool_sequence = []
                compacted.append(msg)
        
        # 最后可能还有未处理的工具序列（保留不压缩，因为是最新的）
        compacted.extend(tool_sequence)
        return compacted
    
    def _summarize_tool_sequence(self, sequence: list[dict]) -> str:
        """提取工具序列的摘要"""
        tools_used = []
        for msg in sequence:
            if msg["role"] == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    name = tc.get("function", {}).get("name", "?")
                    tools_used.append(name)
        return f"Used {len(tools_used)} tools: {', '.join(tools_used)}"
    
    def _autocompact(self, messages: list[dict]) -> list[dict]:
        """
        Level 3: 自动压缩 — LLM 生成摘要
        
        Claude Code 的做法：
          1. 取前 N 条消息作为"压缩候选"
          2. 保留最后 M 条消息不压缩
          3. 用 LLM 对候选消息生成摘要
          4. 返回 [compact_boundary + 摘要] + 最后 M 条
        """
        # 保留最后 20 条消息
        keep_count = min(20, len(messages) // 2)
        to_compact = messages[:-keep_count]
        to_keep = messages[-keep_count:]
        
        # 用 LLM 生成摘要
        compact_text = "\n".join(
            f"[{m['role']}]: {str(m.get('content', ''))[:200]}"
            for m in to_compact
        )
        
        summary_response = self.client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": "Summarize this conversation history in 2-3 paragraphs. Focus on: what task is being worked on, what has been accomplished, key files/code involved, any errors encountered."},
                {"role": "user", "content": compact_text[:50000]},  # 截断保护
            ],
            max_tokens=1000,
        )
        summary = summary_response.choices[0].message.content
        
        # 构造压缩后的消息列表
        return [
            {"role": "system", "content": f"[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY — recent messages follow]"},
            *to_keep
        ]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 3: 集成到 Agent 循环
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 在 agent_loop 的每轮开始处：
# messages = compaction_engine.compact_if_needed(messages)
```

#### 关键学习点

1. **压缩是无限对话的前提**：没有压缩机制的 Agent，对话长度受限于上下文窗口。Claude Code 的用户可以连续工作数小时不 interrupt
2. **瀑布策略的优雅**：先用低成本低损失的方式（snip），不够再升级到高成本高效果的方式（autocompact）。不是一上来就做最重的压缩
3. **摘要 ≠ 截断**：简单丢弃旧消息会丢失上下文。LLM 生成的摘要保留了关键信息（任务目标、已完成的工作、遇到的错误）
4. **Claude Code 的成本追踪**（`autoCompactTracking`）：压缩本身消耗 token，需要追踪压缩的 token 开销

---

### Iter 7: 多 Agent 协作 — 团队作战（1000 行）

#### 要解决的问题

有些任务一个 Agent 搞不定（或搞太慢），需要拆分给多人协作：
- "review 这段代码并写测试"→ 一个 reviewer + 一个 tester
- "在这 10 个文件中搜索 bug"→ 10 个并发搜索 agent
- "帮我重构这个模块"→ 一个规划者 + 多个执行者

#### Claude Code 源码映射

Claude Code 有两套多 Agent 机制：

```
1. AgentTool（子 Agent）
   路径：tools/AgentTool/
   
   主 Agent 调用 AgentTool 创建子 Agent：
     → 生成新的 QueryEngine
     → 子 Agent 有自己的 messages 和 tools
     → 深度追踪防无限递归：QueryChainTracking { chainId, depth }
     → 结果返回给父 Agent
   
   关键限制：
     - 子 Agent 不能再调用 AgentTool（防止深度爆炸）
     - 子 Agent 工具集是父的子集
     - 子 Agent 共享 AppState.tasks（进度可见）

2. Coordinator Mode（协调者模式）
   路径：coordinator/coordinatorMode.ts
   
   一个"协调者"Agent 管理多个"工人"Agent：
     → 协调者接收用户任务
     → 拆分为子任务，分配给不同工人
     → 工人并行执行
     → 协调者收集结果、综合输出
   
   工人的工具限制（COORDINATOR_MODE_ALLOWED_TOOLS）：
     - ✅ Bash, FileRead, FileEdit, FileWrite, WebFetch, Grep, Glob
     - ❌ AgentTool（防止递归）
     - ❌ SendMessage（不能直接跟用户说话）

3. Swarm Mode（群体模式）
   → Agents 通过 UDS mailbox 通信
   → 相互独立的进程
   → 更像微服务架构
```

#### Python 实例

```python
"""
Iter 7: 多 Agent 协作 — 团队作战
关键进化：Agent 从"单打独斗"变成"团队协作"。
"""
import uuid
from dataclasses import dataclass
from typing import Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: Agent 定义
# 对应 tools/AgentTool/loadAgentsDir.ts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class AgentDefinition:
    """
    Agent 定义 — Claude Code 支持 .md 文件定义 agent。
    """
    name: str
    system_prompt: str
    allowed_tools: list[str]
    max_turns: int = 10

# 预定义一些专业 Agent
AGENTS = [
    AgentDefinition(
        name="code_reviewer",
        system_prompt="You are a senior code reviewer. Focus on: bugs, security issues, performance problems, code style. Be specific and actionable.",
        allowed_tools=["file_read", "grep"],
    ),
    AgentDefinition(
        name="test_writer",
        system_prompt="You are a test engineer. Write comprehensive unit tests for the given code. Use pytest.",
        allowed_tools=["file_read", "file_write", "bash"],
    ),
    AgentDefinition(
        name="researcher",
        system_prompt="You are a research assistant. Search and read files to answer questions about the codebase.",
        allowed_tools=["file_read", "grep", "bash"],
    ),
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: 深度追踪（防无限递归）
# 对应 Tool.ts 的 QueryChainTracking
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ChainTracking:
    """
    追踪 Agent 调用链的深度。
    
    Claude Code 的设计：
      chainId: 整条调用链的唯一 ID
      depth: 当前深度（主 Agent=0, 子 Agent=1, 孙 Agent=2…）
    """
    chain_id: str
    depth: int
    max_depth: int = 3  # Claude Code 默认限制
    
    def can_spawn(self) -> bool:
        return self.depth < self.max_depth
    
    def child(self) -> 'ChainTracking':
        return ChainTracking(
            chain_id=self.chain_id,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 3: 子 Agent 执行
# 对应 AgentTool 的核心逻辑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_sub_agent(agent_def: AgentDefinition,
                   task: str,
                   chain: ChainTracking,
                   registry: 'ToolRegistry') -> str:
    """
    运行子 Agent。
    
    对应 Claude Code 的 AgentTool → createSubagentContext → queryLoop
    
    关键设计决策:
    1. 子 Agent 有自己的 messages（隔离）
    2. 子 Agent 的工具集是受限的（最小权限）
    3. 递归深度有限制（防止套娃爆炸）
    """
    if not chain.can_spawn():
        return "Error: maximum agent depth reached. Cannot spawn more sub-agents."
    
    # 构造子 Agent 的工具集（受限）
    sub_tools = [t for t in registry.all_tools() 
                 if t.name in agent_def.allowed_tools]
    
    # 子 Agent 不能调用 AgentTool（核心限制）
    sub_tools = [t for t in sub_tools if t.name != "agent"]
    
    sub_registry = ToolRegistry()
    for t in sub_tools:
        sub_registry.register(t)
    
    # 运行子 Agent 循环
    messages = [
        {"role": "system", "content": agent_def.system_prompt},
        {"role": "user", "content": task},
    ]
    
    for turn in range(agent_def.max_turns):
        response = client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            tools=sub_registry.to_openai_format(),
        )
        msg = response.choices[0].message
        messages.append(msg)
        
        if not msg.tool_calls:
            return msg.content
        
        for tc in msg.tool_calls:
            tool = sub_registry.get(tc.function.name)
            args = json.loads(tc.function.arguments)
            result = tool.execute(args) if tool else f"Error: unknown tool"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    
    return "Sub-agent reached max turns."

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 4: Agent 工具（让主 Agent 可以调用子 Agent）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_agent_tool(agents: list[AgentDefinition], 
                       chain: ChainTracking,
                       registry: 'ToolRegistry') -> ToolDefinition:
    """
    把"启动子 Agent"包装成一个工具。
    主 Agent 在需要时，像调用其他工具一样调用它。
    """
    agent_names = [a.name for a in agents]
    
    def agent_execute(args: dict) -> str:
        agent_name = args["agent_name"]
        task = args["task"]
        
        agent_def = next((a for a in agents if a.name == agent_name), None)
        if not agent_def:
            return f"Error: unknown agent '{agent_name}'. Available: {agent_names}"
        
        print(f"  🤖 Spawning sub-agent '{agent_name}' (depth={chain.depth+1})")
        result = run_sub_agent(agent_def, task, chain.child(), registry)
        print(f"  ✅ Sub-agent '{agent_name}' completed")
        return result
    
    return ToolDefinition(
        name="agent",
        description=f"Spawn a specialized sub-agent. Available agents: {', '.join(agent_names)}. "
                    f"Use code_reviewer for reviews, test_writer for tests, researcher for codebase questions.",
        parameters={
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "enum": agent_names,
                    "description": "Which agent to run"
                },
                "task": {
                    "type": "string",
                    "description": "The task for the sub-agent"
                },
            },
            "required": ["agent_name", "task"],
        },
        execute=agent_execute,
        is_read_only=True,  # 子 Agent 本身不修改东西（它内部的工具可能会）
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 使用
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# chain = ChainTracking(chain_id=str(uuid.uuid4()), depth=0)
# agent_tool = create_agent_tool(AGENTS, chain, registry)
# registry.register(agent_tool)
# 
# result = agent_loop("Review the code in main.py and then write unit tests for it")
# → 主 Agent 会自动决定先调用 code_reviewer，再调用 test_writer
```

#### 关键学习点

1. **Agent 就是工具**：子 Agent 被包装成一个工具，主 Agent 按需调用。这是"一切皆工具"的设计哲学
2. **深度限制是必须的**：没有 `max_depth`，Agent 可以无限套娃。Claude Code 用 `QueryChainTracking.depth` 精确控制
3. **最小权限原则**：子 Agent 的工具集是父的子集，code_reviewer 不需要 `bash` 和 `file_write`
4. **隔离 vs 共享**：子 Agent 有自己的 messages（隔离），但共享 AppState（共享任务进度）。Claude Code 的 `setAppStateForTasks` 就是为了让子 Agent 能注册全局可见的任务

---

## 4. 全景：八次迭代与 Claude Code 的映射

```mermaid
graph TB
    subgraph "你构建的（~1000行 Python）"
        I0["Iter 0: LLM 调用<br/>ask_llm()"]
        I1["Iter 1: ReAct 循环<br/>agent_loop()"]
        I2["Iter 2: 工具注册表<br/>ToolRegistry"]
        I3["Iter 3: 上下文工程<br/>ContextBuilder"]
        I4["Iter 4: 流式+并发<br/>execute_tools_batched()"]
        I5["Iter 5: 权限系统<br/>PermissionChecker"]
        I6["Iter 6: 对话压缩<br/>CompactionEngine"]
        I7["Iter 7: 多Agent<br/>run_sub_agent()"]
    end
    
    subgraph "Claude Code 对应（~500K行 TypeScript）"
        C0["services/api/claude.ts"]
        C1["query.ts → queryLoop()"]
        C2["Tool.ts + tools.ts + tools/"]
        C3["context.ts + CLAUDE.md"]
        C4["StreamingToolExecutor<br/>toolOrchestration.ts"]
        C5["ToolPermissionContext<br/>useCanUseTool.tsx"]
        C6["services/compact/*<br/>五级瀑布"]
        C7["AgentTool + coordinator/<br/>QueryChainTracking"]
    end
    
    I0 -.-> C0
    I1 -.-> C1
    I2 -.-> C2
    I3 -.-> C3
    I4 -.-> C4
    I5 -.-> C5
    I6 -.-> C6
    I7 -.-> C7
```

### 复杂度对比

| 迭代 | 我们的代码量 | Claude Code 对应代码量 | 差距倍数 | 差距主要来自 |
|------|-----------|---------------------|---------|------------|
| Iter 0 | ~30 行 | ~500 行 | 17x | 流控、重试、认证、缓存 |
| Iter 1 | ~80 行 | ~800 行 | 10x | 状态管理、事件系统 |
| Iter 2 | ~200 行 | ~10,000 行 | 50x | 45+ 工具实现、MCP、Schema 验证 |
| Iter 3 | ~350 行 | ~5,000 行 | 14x | 多层记忆、动态附件、Repo Map |
| Iter 4 | ~500 行 | ~3,000 行 | 6x | 流式 tool 派发、进度事件 |
| Iter 5 | ~650 行 | ~8,000 行 | 12x | 5 种 mode、规则引擎、钩子集成 |
| Iter 6 | ~800 行 | ~6,000 行 | 8x | 5 级瀑布、token 精确计数 |
| Iter 7 | ~1,000 行 | ~15,000 行 | 15x | Swarm 模式、远程 Agent、任务管理 |
| **总计** | **~1,000 行** | **~500,000 行** | **500x** | UI、边界处理、遥测、企业功能 |

**500 倍的差距来自哪里？**

- 🎨 **UI 层**（~100K 行）：React 组件、终端渲染、主题、键绑定
- 🔧 **工具实现**（~50K 行）：45+ 个工具的完整实现
- 🛡️ **边界处理**（~100K 行）：各种错误恢复、edge case
- 📊 **可观测性**（~30K 行）：日志、遥测、OpenTelemetry
- 🏢 **企业功能**（~50K 行）：远程模式、团队协作、MDM 配置
- 🔌 **插件/MCP**（~30K 行）：MCP 协议集成、插件系统
- 🧪 **测试**（~80K 行）：完整的测试套件
- 📚 **工具链**（~60K 行）：utils/ 基础设施

---

## 5. 核心设计模式提炼

从八次迭代中，提炼出可复用的 Agent 设计模式：

| # | 模式 | 首次出现 | 核心思想 | Claude Code 实现 |
|---|------|---------|---------|-----------------|
| D1 | **错误即信息** | Iter 1 | 工具错误不抛异常，作为 tool_result 返回给模型 | 所有工具的 catch 都返回字符串 |
| D2 | **统一工具接口** | Iter 2 | 所有工具实现同一个 interface，循环代码不关心具体工具 | `Tool` 类型 ~30 个字段 |
| D3 | **依赖注入** | Iter 2 | 工具不 import 服务，依赖通过 context 传入 | `ToolUseContext` 传递一切 |
| D4 | **上下文分层缓存** | Iter 3 | 不同类型的上下文有不同刷新频率 | `memoize` + 会话级缓存 |
| D5 | **并发安全分区** | Iter 4 | 只读工具并行，写入工具串行 | `isConcurrencySafe()` |
| D6 | **流式管道** | Iter 4 | 模型流→工具流→UI 流，不等完整输出 | `StreamingToolExecutor` |
| D7 | **分级拒绝** | Iter 5 | 权限拒绝分多种策略（auto-deny/ask/pattern-match） | 5 种 `PermissionMode` |
| D8 | **瀑布压缩** | Iter 6 | 从低成本到高成本依次尝试 | 5 级 compaction cascade |
| D9 | **Agent 即工具** | Iter 7 | 子 Agent 被包装成工具，主 Agent 按需调用 | `AgentTool` |
| D10 | **深度追踪** | Iter 7 | 全局计数器防止 Agent 无限套娃 | `QueryChainTracking` |

---

## 6. 学习建议与实施计划

### 建议学习节奏

| 阶段 | 迭代 | 建议时间 | 目标 |
|------|------|---------|------|
| **基础** | Iter 0-1 | 1-2 天 | 理解 Agent 循环的本质 |
| **核心** | Iter 2-3 | 3-5 天 | 掌握工具系统和上下文工程 |
| **进阶** | Iter 4-5 | 3-5 天 | 实现流式执行和权限控制 |
| **高级** | Iter 6-7 | 5-7 天 | 掌握对话压缩和多 Agent |

### 每个迭代的验证标准

| 迭代 | 验证场景 | 成功标准 |
|------|---------|---------|
| Iter 0 | 问"1+1=?" | 收到正确回答 |
| Iter 1 | "列出当前目录文件并统计行数" | Agent 执行 2+ 轮工具调用完成任务 |
| Iter 2 | "搜索所有包含 'TODO' 的文件然后读取它们" | Agent 组合使用 grep + file_read |
| Iter 3 | "基于 git diff 做 code review" | Agent 的 review 准确引用了变更文件 |
| Iter 4 | "读取这 5 个文件" | 5 个文件并行读取，总时间接近单个 |
| Iter 5 | "删除 /tmp/ 下所有文件" | 触发权限拦截或确认对话框 |
| Iter 6 | 连续 30 轮对话不报错 | 压缩自动触发，对话继续正常 |
| Iter 7 | "review 代码并写测试" | 自动派发 2 个子 Agent 并汇总结果 |

### 与已有知识的融合路径

本报告的8个迭代，可以与已有研究形成完整学习闭环：

```mermaid
graph LR
    subgraph "理论武装"
        A1["#3 Agent架构报告<br/>四大能力、五种 Workflow"]
        A2["#6 ADK 五模式<br/>设计模式库"]
    end
    
    subgraph "本报告：动手构建"
        B1["Iter 0-1: 循环基础"]
        B2["Iter 2-3: 工具+上下文"]
        B3["Iter 4-7: 并发/安全/压缩/多Agent"]
    end
    
    subgraph "实验验证"
        C1["#5 源码上下文实验<br/>Repo Map / PageRank"]
        C2["#7 代码检索实验<br/>Multi-Signal 融合"]
    end
    
    subgraph "部署上线"
        D1["#4 部署方案调研<br/>L0-L8 九级"]
    end
    
    A1 --> B1
    A2 --> B2
    B2 --> C1
    B3 --> C2
    B3 --> D1
```

---

## 7. 开放问题与后续计划

### 本报告未覆盖但 Claude Code 有的重要系统

| 系统 | 重要性 | 建议后续 |
|------|--------|---------|
| **钩子/生命周期** | ⭐⭐⭐⭐ | 可作为 Iter 8：在工具执行前后注入自定义逻辑 |
| **MCP 协议集成** | ⭐⭐⭐⭐ | 可作为 Iter 9：让 Agent 接入外部工具生态 |
| **可观测性** | ⭐⭐⭐ | 日志 + OpenTelemetry 跟踪 |
| **成本追踪** | ⭐⭐⭐ | token 计数、USD 预算限制 |
| **Skill 系统** | ⭐⭐⭐ | Markdown 定义的可复用能力模块 |
| **远程执行** | ⭐⭐ | 服务端部署 + WebSocket 通信 |

### 可以立即动手的事

1. **把 8 个 Python 文件合并为一个可运行的项目**——每个版本作为一个独立模块
2. **接入真实 LLM API 跑通**——推荐用 Qwen（已有 API Key），与 OpenAI 格式兼容
3. **在本工作区的 `experiments/` 中创建实验**——如 `08_minimal_agent.py`, `09_tool_system.py`

### 延伸阅读

- [钩子详解与Agent层级对比](R12_%E9%92%A9%E5%AD%90%E8%AF%A6%E8%A7%A3%E4%B8%8EAgent%E5%B1%82%E7%BA%A7%E5%AF%B9%E6%AF%94.md)：L0→L6 的 Agent 复杂度递进（与本报告 Iter 0-7 互补）
- [Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) §三：Claude Code 源码逆向的 async generator 状态机分析
- [Google ADK五大Agent技能设计模式研究报告](R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md)：Sequential/Parallel/Loop/Delegate 模式编排

---

> 📌 **来源清单**
> - [github.com/anthropics/claude-code](https://github.com/anthropics/claude-code) — 2026-04-12 — 113K⭐ / 51 Contributors
> - 本工作区标本：`claude-code-main/src/`（1884 文件，47.7 万行）
> - 源码直接分析：query.ts, Tool.ts, tools.ts, context.ts, services/compact/, services/tools/, coordinator/, tools/AgentTool/
> - 模型训练知识 — 作背景参考
>
> ⚖️ 来源一致性：高（源码分析为主，交叉验证官方文档和已有报告）
> 📅 时效性声明：以上信息获取于 2026-04-12
