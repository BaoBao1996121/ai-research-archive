---
title: 手搓 MCP 与 Skill 实现机制 —— 不依赖框架理解 Agent 三件武器
aliases: [R74, 手搓MCP与Skill实现机制, 手搓MCP, 手搓Skill, MCP协议拆解]
report_id: R74
category: 理论与架构
prev_path: ""
status: completed
tags: [mcp, skill, function-calling, protocol, json-rpc, hands-on, learning]
date: 2026-04-26
tokens: 12000
related:
  - "[R39](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R39_%E9%A3%9E%E4%B9%A6CLI%E4%B8%8EMCP%E9%80%9A%E4%BF%A1%E6%9C%BA%E5%88%B6.md)"
  - "[R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)"
  - "[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "[R64](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md)"
  - "[R03](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
key_insights:
  - "MCP 是协议不是 SDK——核心只有三个方法（initialize / tools/list / tools/call），100 行 Python 能跑通 Server+Client"
  - "Skill 是文件系统约定不是框架——本质是 frontmatter 注入 system prompt + Agent 按需 bash 读 body"
  - "三级加载（L1 元数据常驻 / L2 SKILL.md 触发加载 / L3 资源按需读）是 Token 优化的本质——常驻成本与能力数量解耦"
  - "MCP 解决能力扩展、Skill 解决知识扩展——前者答'能做什么'，后者答'怎么做'，两者正交不冲突"
  - "理解协议比掌握 SDK 更重要——框架封装的只是样板代码，协议设计才是真正的杠杆点"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 手搓 MCP 与 Skill 实现机制 —— 不依赖框架理解 Agent 三件武器

> **一句话概括**：MCP 本质是「JSON-RPC 2.0 + stdio/HTTP + 三个固定方法（initialize / tools/list / tools/call）」的协议约定；Skill 本质是「文件系统目录 + YAML frontmatter + 渐进式上下文注入」的工程约定。两者都不需要框架——MCP 100 行 Python 能跑通 Server+Client，Skill 50 行能跑通 Manager。框架只是把这套约定的样板代码封装了。
> **研究日期**：2026-04-26
> **关联报告**：[R39](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R39_%E9%A3%9E%E4%B9%A6CLI%E4%B8%8EMCP%E9%80%9A%E4%BF%A1%E6%9C%BA%E5%88%B6.md)（MCP 应用层视角）、[R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)（Skill 设计哲学）、[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)（Skill 自迭代）、[R64](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md)（MCP Gateway 网关层）、[R03](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)（Agent 架构）
> **增量价值**：本工作区已有 R39 讲飞书 MCP 应用层、R14/R28 讲 Skill 设计哲学、R64 讲 MCP 网关层，**但「裸 Agent 怎么从零理解和接入 MCP/Skill 协议层」这一空白未被填补**。本报告补上协议层与加载机制层的地基，配套 100% 可运行的最小实现。

---

## TL;DR 速查卡

- **MCP ≠ 框架**：MCP 是协议（spec），不是 SDK。你有 `print(json.dumps({...}))` 就能写 Server，没有 `pip install mcp` 也能跑。
- **MCP 协议三件套**：`initialize`（握手协商能力）→ `tools/list`（列出工具）→ `tools/call`（调用工具）。仅此三个核心方法即可让 LLM 用上 MCP。
- **传输层只有两个**：`stdio`（子进程 + 标准输入输出 + 换行符分隔）/ `Streamable HTTP`（POST + 可选 SSE）。本地优先 stdio，远程才用 HTTP。
- **Skill ≠ 框架**：Skill 是文件系统约定。本质是 `SKILL.md` 的 YAML frontmatter 注入到 system prompt + Agent 通过 bash 按需读 body + 引用文件。
- **三级加载是 Token 优化**：L1 元数据（~100 tokens × N，常驻）/ L2 SKILL.md body（触发后加载，<5K tokens）/ L3 资源文件（按需 bash 读，0 常驻 tokens）。
- **裸 Agent 同时用上两者**：MCP 提供「能做什么」的工具列表，Skill 提供「怎么做」的领域知识——一个解决能力扩展，一个解决知识扩展。
- **核心代码量参考**：手搓 MCP Server ≈ 80 行；手搓 MCP Client ≈ 60 行；手搓 SkillManager ≈ 50 行。三者合一的 Mini-Agent ≈ 200 行。

---

## 目录

- [一、定位透镜：纵横坐标](#一定位透镜纵横坐标)
- [二、三件武器的本质映射：Function Call / MCP / Skill](#二三件武器的本质映射function-call--mcp--skill)
- [三、研究分析轨道：MCP 协议层拆解](#三研究分析轨道mcp-协议层拆解)
- [四、研究分析轨道：Skill 加载机制拆解](#四研究分析轨道skill-加载机制拆解)
- [五、上手实战轨道：手搓最小 MCP Server + Client](#五上手实战轨道手搓最小-mcp-server--client)
- [六、上手实战轨道：手搓最小 Skill Manager](#六上手实战轨道手搓最小-skill-manager)
- [七、上手实战轨道：组装一个无框架 Mini-Agent](#七上手实战轨道组装一个无框架-mini-agent)
- [八、避坑指南](#八避坑指南)
- [九、成本与决策速查](#九成本与决策速查)
- [十、结论与最佳实践](#十结论与最佳实践)
- [📌 来源清单](#-来源清单)

---

## 一、定位透镜：纵横坐标

### 纵轴 · 演化脉络

```
2023 春   │ Function Calling（OpenAI）首次让 LLM 能调用结构化函数
          │ → 痛点：每个 LLM 应用都要重写 N 个函数定义；M 个应用 × N 个工具 = M×N 工程量
          ▼
2024-11   │ Anthropic 发布 MCP 0.1（草案），LSP 启发的"协议化"思路
          │ → 把 M×N 降到 M+N：Server 只写一次，所有 Client（Claude/Cursor/IDE）通用
          ▼
2025-03   │ MCP 2025-03-26：正式规范、Streamable HTTP 取代旧 SSE
          │ → 痛点：MCP 给了"工具"，但没给"领域知识/工作流"
          ▼
2025-10   │ Anthropic 发布 Skills（Agent Skills）+ 引爆 ClawHub 等生态
          │ → 文件系统 + 渐进式加载，把"领域专家手册"塞进 Agent
          ▼
2025-12   │ Skills 成为开源标准（agentskills.io），与 MCP 形成"知识 + 能力"双层
          ▼
2026 现在 │ MCP 已成事实标准（OpenAI 官方支持、Cursor/Cline 内置），Skills 走向跨平台
```

**生命周期定位**：
- **MCP**：成熟期早期（生态健全、协议稳定、企业生产采用迅速）
- **Skills**：上升期中段（标准刚开放、社区在快速试错最佳实践）

### 横轴 · 竞争格局

| 维度 | Function Calling | MCP | Skill |
|------|------------------|-----|-------|
| **解决什么** | 让 LLM 能"叫"函数 | 让"工具"跨应用复用 | 让 LLM 拥有"领域专家手册" |
| **耦合度** | 应用与工具紧耦合（同进程） | 应用与工具解耦（跨进程） | 应用与知识解耦（文件系统） |
| **传输层** | 同进程函数调用 | JSON-RPC 2.0 / stdio / HTTP | 无（直接文件读写） |
| **谁主导** | OpenAI 范式，被 Anthropic/Google 跟进 | Anthropic 主导，OpenAI 加入 | Anthropic 主导（agentskills.io 已开放） |
| **典型场景** | 单应用闭环（chatbot 内调天气 API） | 跨应用工具市场（Claude Desktop 接 GitHub MCP） | 领域专家化（Claude 做 PPT、做财务报表） |
| **配置位置** | 代码里 hardcode | 客户端配置文件（如 `claude_desktop_config.json`） | 文件系统目录（如 `~/.claude/skills/`） |

### 交叉判断（独立结论）

1. **三者不是替代关系，而是分层关系**：Function Calling 是底层执行机制（LLM 永远只输出 JSON 让你去调函数），MCP 是其分布式版本（让函数能跨进程跨机器），Skill 是其知识层（告诉 LLM 怎么组合调用工具）。
2. **手搓门槛远低于想象**：MCP 看似复杂（spec 上百页），但核心只有 3 个 method + JSON-RPC + stdio，**Hello World 100 行内**。Skill 更简单——本质就是把 markdown 注入 system prompt。
3. **不学手搓的代价**：直接用 SDK 能跑，但**不知道协议边界在哪**，遇到 SDK bug、跨语言互通、调试 wire-level 问题时全是黑盒。手搓一遍后再用 SDK，等于从"调库的人"变成"懂库的人"。

---

## 二、三件武器的本质映射：Function Call / MCP / Skill

```
┌──────────────────────────────────────────────────────────────────┐
│  LLM 的本质能力 = 输出 JSON                                          │
│  → 它做不到"执行任何东西"，它只能"说出该执行什么"                       │
│  → 真正的执行权永远在你的程序手里                                      │
└──────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼────────────────────────────┐
        ▼                       ▼                            ▼
┌──────────────┐       ┌──────────────────┐      ┌──────────────────┐
│ Function Call│       │       MCP        │      │      Skill       │
│ ──────────── │       │ ──────────────── │      │ ──────────────── │
│ 同进程调用    │       │ 跨进程协议调用     │      │ 文件系统知识注入   │
│              │       │                  │      │                  │
│ LLM 输出      │       │ LLM 输出          │      │ system prompt   │
│ {name,args}  │       │ {name,args}      │      │ 里有 skill 元数据  │
│      ↓       │       │      ↓           │      │      ↓           │
│ Python 直接   │       │ JSON-RPC over    │      │ LLM 决定触发     │
│ getattr 调用  │       │ stdio/HTTP       │      │      ↓           │
│              │       │      ↓           │      │ Bash 读 SKILL.md │
│              │       │ 别的进程接到调用    │      │ 注入对话上下文     │
│              │       │ 执行后 JSON 返回    │      │      ↓           │
│              │       │                  │      │ LLM 按手册执行     │
└──────────────┘       └──────────────────┘      └──────────────────┘
   "工具的本地版"        "工具的网络版"                "知识的本地版"
```

**关键认知**：上面三个东西本质上**都是 Function Call 的变体**——LLM 只会输出"我想调用 X(args)"，剩下的执行机制是工程问题：
- **Function Call**：你把 X 写在同一个 Python 进程里，`python_func_tableX（原稿引用文件未随本次归档发布）` 直接调
- **MCP**：你把 X 放在另一个进程/机器，通过 JSON-RPC 转发调用
- **Skill**：X 不是函数，而是一段 markdown 知识——但 LLM"调用"它的方式仍然是输出"我想读 skill Y"，由你的程序去 `cat skills/Y/SKILL.md` 把内容拼回上下文

理解了这一点，"手搓"就不再神秘——你只是在替代 SDK 帮 LLM 完成"输出 JSON 后的那一步派发"。

---

## 三、研究分析轨道：MCP 协议层拆解

### 3.1 协议骨架（一张图说清楚）

```
┌─────────────────── MCP 三层架构 ───────────────────┐
│                                                  │
│  应用层    initialize / tools/list / tools/call    │  ← 你写业务的地方
│           prompts/* / resources/* / sampling/*     │
│  ─────────────────────────────────────────────    │
│  消息层    JSON-RPC 2.0                           │  ← 标准化的 request/response 包装
│           {jsonrpc, id, method, params}          │
│  ─────────────────────────────────────────────    │
│  传输层    stdio (本地子进程，换行分隔)              │  ← 字节怎么流动
│           Streamable HTTP (远程，POST + 可选 SSE)  │
│                                                  │
└──────────────────────────────────────────────────┘
```

**铁律**：每一层只关心自己的事。传输层只管把字节送到，消息层只管 JSON-RPC 包装，应用层只管业务方法。手搓时按这个分层组织代码，逻辑非常清晰。

### 3.2 JSON-RPC 2.0 三种消息（这就是全部协议格式）

**Request**（需要响应，必须有 `id`）：
```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "Shanghai"}}}
```

**Response**（成功时含 `result`，失败时含 `error`，二选一）：
```json
{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "晴 22°C"}]}}
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "Unknown tool"}}
```

**Notification**（不需要响应，**不能有 `id`**）：
```json
{"jsonrpc": "2.0", "method": "notifications/initialized"}
```

> 整个 MCP 协议的"语法"就这三种消息，剩下的全是 `method` 和 `params` 内容上的约定。

### 3.3 stdio 传输层（最常用、最易手搓）

> 来源：[MCP Spec 2025-06-18 / Transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)

规则极简，五条铁律：

1. Client 把 Server **作为子进程启动**（`subprocess.Popen`）
2. Client 把消息**写入 server 的 stdin**，server 把响应**写入 stdout**
3. **每条消息一行**，用 `\n` 分隔——消息内部禁止出现换行
4. Server 的 **stderr 用于日志**，client 可以忽略或抓取
5. **stdout 不准混入任何非 MCP 消息**（这是新手最常踩的坑——`print("debug")` 会污染协议流）

### 3.4 Lifecycle：一次完整握手

```
Client                                          Server
  │                                                │
  │── initialize {protocolVersion, capabilities} ─▶│
  │                                                │
  │◀── result {protocolVersion, capabilities,      │
  │           serverInfo, instructions?} ─────────│
  │                                                │
  │── notifications/initialized ──────────────────▶│
  │                                                │  ← 此后才能发业务请求
  │── tools/list ─────────────────────────────────▶│
  │◀── result {tools: [...]} ─────────────────────│
  │                                                │
  │── tools/call {name, arguments} ───────────────▶│
  │◀── result {content: [...], isError} ──────────│
  │                                                │
  │── (close stdin) ──────────────────────────────▶│
  │                                          (server 退出)
```

> **关键节点**：`initialized` 通知**必须发**，没发的话 server 不会处理后续请求——这是协议铁律，也是手搓时最容易漏的步骤。

### 3.5 工具定义的 Schema

Server 在 `tools/list` 响应里返回工具数组：

```json
{
  "name": "get_weather",
  "title": "Weather Lookup",
  "description": "Get current weather for a city",
  "inputSchema": {
    "type": "object",
    "properties": {
      "city": {"type": "string", "description": "City name"}
    },
    "required": ["city"]
  }
}
```

`description` + `inputSchema` 这两个字段就是 LLM 看到的全部信息——LLM 据此决定要不要调、传什么参数。所以**写好 description 比写好代码更重要**——这一点和 OpenAI Function Calling 一脉相承。

---

## 四、研究分析轨道：Skill 加载机制拆解

### 4.1 Skill 不是协议，是文件系统约定

> 来源：[Anthropic Skills 官方文档](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) + [Anthropic Skills Blog](https://claude.com/blog/skills)

Skill 的运行环境假设：**Agent 拥有文件系统访问能力 + bash 执行能力**。整个机制建立在这两个基础原语之上，不需要任何额外协议。

```
~/.claude/skills/                ← 用户级
   ├── pdf-processing/
   │   ├── SKILL.md              ← 必须，含 frontmatter
   │   ├── FORMS.md              ← L3 资源
   │   ├── REFERENCE.md
   │   └── scripts/
   │       └── fill_form.py
   └── financial-analysis/
       ├── SKILL.md
       └── templates/

.claude/skills/                  ← 项目级（项目根目录）
```

### 4.2 三级渐进式加载（Token 优化的核心）

| 级别 | 内容 | 何时加载 | Token 占用 | 加载方式 |
|------|------|---------|-----------|---------|
| **L1 元数据** | `name` + `description`（YAML frontmatter） | Agent 启动时**全部加载** | ~100 tokens × N 个 Skill | 注入 system prompt |
| **L2 主体** | `SKILL.md` body（去掉 frontmatter 的部分） | description 匹配用户请求**触发后**加载 | < 5K tokens / Skill | Bash 读文件 + 拼到对话 |
| **L3 资源** | bundle 的 `.md` / 脚本 / 数据文件 | SKILL.md 里**显式引用**才读 | 不进上下文（脚本仅输出进） | Bash 读 / 执行 |

**L3 的精妙**：脚本被 bash 执行后，**只有 stdout 进上下文，代码本身从不进**——这是 Skill 比"把代码写在 prompt 里"省 10× tokens 的原因。

### 4.3 触发判定的本质：description 匹配

LLM 在每个对话回合都"看见"所有 L1 元数据（已经在 system prompt 里了）。当用户说"帮我处理这个 PDF 表格"时，LLM 自己判断：
- description 里写了 "Use when working with PDF files" → 触发
- LLM 自发输出指令：`bash: cat ~/.claude/skills/pdf-processing/SKILL.md`
- Agent 框架（或你手搓的 loop）执行这条 bash，把内容塞回上下文
- LLM 看到完整 SKILL.md 后，按里面的步骤执行任务

> **关键洞察**：Skill 没有"加载 API"，只有"约定 + 信任 LLM 自主决策"。Anthropic 的设计哲学是「让 LLM 像新员工读 onboarding 手册」——你不需要"调用 Skill"这个 API，你只需要让 SKILL.md 在文件系统上存在。

### 4.4 SKILL.md 的最小合规结构

```yaml
---
name: pdf-processing                  # 必填，≤ 64 字符，小写字母+数字+连字符
description: Extract text and tables from PDF files. Use when working with PDFs, forms, or document extraction.   # 必填，≤ 1024 字符
---

# PDF Processing

## Quick start

Use pdfplumber to extract text:

```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

For form filling, see FORMS.md（原稿引用文件未随本次归档发布）.
For API reference, see REFERENCE.md（原稿引用文件未随本次归档发布）.
```

`description` 决定**何时触发**——这是 Skill 工程化的重点。Anthropic 官方 skill-creator（见 [R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)）甚至有专门的 `improve_description.py` 脚本来自动优化触发率。

---

## 五、上手实战轨道：手搓最小 MCP Server + Client

### 5.1 环境准备

```bash
# 仅需 Python 3.9+，无任何第三方依赖
python --version  # 验证 ≥ 3.9
```

### 5.2 Hello World：80 行 Python MCP Server（stdio 传输）

> 文件：`mcp_server_min.py`

```python
"""
最小 MCP Server，stdio 传输，零依赖
仅实现 initialize / tools/list / tools/call 三个核心方法
"""
import json
import sys

# 工具实现：纯 Python 函数
def get_weather(city: str) -> str:
    fake_db = {"shanghai": "晴 22°C", "beijing": "多云 18°C"}
    return fake_db.get(city.lower(), f"Unknown city: {city}")

def add(a: float, b: float) -> float:
    return a + b

# 工具元数据：暴露给 LLM 的 schema
TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "inputSchema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "add",
        "description": "Add two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
    },
]
TOOL_FUNCS = {"get_weather": get_weather, "add": add}

def handle(msg: dict) -> dict | None:
    """根据 method 派发，返回 None 表示是通知（不需响应）"""
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "min-server", "version": "0.1.0"},
            },
        }
    if method == "notifications/initialized":
        return None  # 通知不响应
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = msg["params"]["name"]
        args = msg["params"].get("arguments", {})
        try:
            result = TOOL_FUNCSname（原稿引用文件未随本次归档发布）
            return {
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"content": [{"type": "text", "text": str(result)}], "isError": False},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"content": [{"type": "text", "text": str(e)}], "isError": True},
            }
    # 未知 method → JSON-RPC 错误
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}

def main():
    # 主循环：从 stdin 逐行读 JSON-RPC，写响应到 stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            print("[debug] bad json", file=sys.stderr)  # 日志走 stderr
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()  # 关键：必须 flush，不然 client 收不到

if __name__ == "__main__":
    main()
```

**预期输出**（手动测试，复制下面 3 行依次粘贴回车）：

```bash
python mcp_server_min.py
# 粘贴：
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"manual","version":"0.1"}}}
# 看到：
# {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "min-server", "version": "0.1.0"}}}

# 再粘贴：
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
# 看到 tools 数组返回

{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_weather","arguments":{"city":"Shanghai"}}}
# 看到 "晴 22°C"
```

### 5.3 Hello World：60 行 Python MCP Client（stdio 传输）

> 文件：`mcp_client_min.py`

```python
"""
最小 MCP Client：拉起 server 子进程，跑完整握手 + 调一次工具
零依赖
"""
import json
import subprocess
import sys

class MinMCPClient:
    def __init__(self, server_cmd: list[str]):
        self.proc = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,  # 行缓冲
        )
        self._next_id = 0

    def _send(self, msg: dict):
        line = json.dumps(msg) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    def _recv(self) -> dict:
        line = self.proc.stdout.readline()
        return json.loads(line)

    def _request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}})
        return self._recv()

    def _notify(self, method: str, params: dict | None = None):
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    # ===== 高层 API =====
    def initialize(self):
        resp = self._request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "min-client", "version": "0.1"},
        })
        self._notify("notifications/initialized")
        return resp["result"]

    def list_tools(self) -> list[dict]:
        return self._request("tools/list")["result"]["tools"]

    def call_tool(self, name: str, arguments: dict) -> str:
        resp = self._request("tools/call", {"name": name, "arguments": arguments})
        return resp["result"]["content"][0]["text"]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)

# ===== 演示 =====
if __name__ == "__main__":
    client = MinMCPClient(["python", "mcp_server_min.py"])
    info = client.initialize()
    print(f"Connected: {info['serverInfo']['name']} v{info['serverInfo']['version']}")
    # Expected: Connected: min-server v0.1.0

    tools = client.list_tools()
    print(f"Tools: {[t['name'] for t in tools]}")
    # Expected: Tools: ['get_weather', 'add']

    print("Weather:", client.call_tool("get_weather", {"city": "Shanghai"}))
    # Expected: Weather: 晴 22°C

    print("Add:", client.call_tool("add", {"a": 3, "b": 4}))
    # Expected: Add: 7

    client.close()
```

**跑通验证**：
```bash
python mcp_client_min.py
# 完整输出 4 行，全部命中 Expected 即成功
```

恭喜——你已经手搓了一个**符合 MCP 2025-06-18 规范的 Server 和 Client**。剩下的 SDK 功能（resources/prompts/sampling/HTTP 传输/auth）都是在这个骨架上加方法。

---

## 六、上手实战轨道：手搓最小 Skill Manager

### 6.1 设计目标

不依赖 Anthropic SDK，自己实现：
1. 扫描目录，加载所有 SKILL.md 的 frontmatter
2. 把 L1 元数据注入 system prompt
3. 提供"按需读取 SKILL.md body"的能力（模拟 LLM 的 bash 调用）

### 6.2 Hello World：50 行 SkillManager

> 文件：`skill_manager_min.py`

```python
"""
最小 Skill Manager：扫描目录、解析 frontmatter、按需加载 body
仅依赖 PyYAML（pip install pyyaml）
"""
from pathlib import Path
import yaml

class Skill:
    def __init__(self, path: Path):
        self.path = path
        text = (path / "SKILL.md").read_text(encoding="utf-8")
        # 解析 frontmatter（--- 包裹的 YAML 段）
        if not text.startswith("---"):
            raise ValueError(f"{path}: missing frontmatter")
        _, frontmatter, body = text.split("---", 2)
        self.meta = yaml.safe_load(frontmatter)
        self.body = body.strip()
        # 校验
        assert "name" in self.meta and "description" in self.meta, f"{path}: name/description required"

class SkillManager:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.skills: dict[str, Skill] = {}
        self._scan()

    def _scan(self):
        for skill_md in self.root.glob("*/SKILL.md"):
            s = Skill(skill_md.parent)
            self.skills[s.meta["name"]] = s

    def system_prompt_block(self) -> str:
        """L1 元数据：拼成一段 system prompt 注入"""
        lines = ["## Available Skills (read SKILL.md when relevant)\n"]
        for s in self.skills.values():
            lines.append(f"- **{s.meta['name']}**: {s.meta['description']}")
        return "\n".join(lines)

    def load_body(self, name: str) -> str:
        """L2：触发后加载完整 SKILL.md body"""
        if name not in self.skills:
            return f"[error] skill '{name}' not found"
        return self.skills[name].body

    def read_resource(self, skill_name: str, file: str) -> str:
        """L3：按需读取 bundle 文件"""
        s = self.skills[skill_name]
        target = (s.path / file).resolve()
        # 安全：防止 ../../ 越权
        if not str(target).startswith(str(s.path.resolve())):
            return "[error] path escape detected"
        return target.read_text(encoding="utf-8")

# ===== 演示 =====
if __name__ == "__main__":
    # 准备示例：mkdir -p ./skills/weather && cat > ./skills/weather/SKILL.md
    mgr = SkillManager("./skills")
    print(mgr.system_prompt_block())
    print("---")
    print(mgr.load_body("weather")[:200])
```

**配套示例 Skill**（`./skills/weather/SKILL.md`）：
```markdown
---
name: weather
description: Look up weather for cities. Use when user asks about temperature, rain, weather conditions in any city.
---

# Weather Skill

## Workflow

1. Identify the city from user's message
2. Call `get_weather` tool (provided via MCP)
3. Format the response in user's preferred unit (default Celsius)
4. If user asks about multiple cities, batch the calls

## Edge cases

- City not in database → suggest user check spelling
- Multiple matches → ask user to disambiguate
```

**跑通验证**：
```bash
mkdir -p skills/weather
# 把上面 markdown 写入 skills/weather/SKILL.md
python skill_manager_min.py
# Expected: 输出 "Available Skills" 列表 + weather body 前 200 字符
```

### 6.3 Skill 比 MCP 更"佛系"的原因

注意到了吗？SkillManager 没有任何"协议"——它就是 `glob + yaml.safe_load + str`。**Skill 把所有协调权交给了 LLM 本身**：
- LLM 看到 system prompt 里的元数据
- LLM 自己决定"我需要读 weather SKILL.md"
- LLM 自己输出 `bash: cat skills/weather/SKILL.md`（或在 Anthropic 的 code execution 容器里执行）
- 你的 Agent loop 拦截这条 bash，调 `mgr.load_body("weather")`

这就是为什么 Skill 的"加载机制"看起来过于简单——**复杂性被 LLM 本身的推理能力吸收了**。

---

## 七、上手实战轨道：组装一个无框架 Mini-Agent

把 MCP + Skill + LLM 调用拼成一个完整 Agent，验证三件武器协同工作。

### 7.1 总架构

```
User Query
   │
   ▼
┌──────────────────────────────────────────┐
│  Mini-Agent Loop                          │
│                                          │
│  1. 构建 system prompt：                   │
│     - SkillManager.system_prompt_block() │   ← Skill L1
│     - tools = MinMCPClient.list_tools()  │   ← MCP tools
│  2. 调 LLM（OpenAI/Anthropic 兼容 API）    │
│  3. 检查响应：                             │
│     - 若 tool_call → MCP client 调用       │
│     - 若 read_skill → SkillManager 加载    │
│     - 否则 → 返回最终答案                   │
│  4. 把结果拼回对话，回到 2                   │
│                                          │
└──────────────────────────────────────────┘
```

### 7.2 核心代码（约 80 行，省略错误处理）

> 文件：`mini_agent.py`（伪代码骨架，OpenAI SDK 仅作示例，可换 Anthropic）

```python
from openai import OpenAI  # pip install openai
from mcp_client_min import MinMCPClient
from skill_manager_min import SkillManager

llm = OpenAI()  # 读 OPENAI_API_KEY
mcp = MinMCPClient(["python", "mcp_server_min.py"])
mcp.initialize()
mcp_tools = mcp.list_tools()
skills = SkillManager("./skills")

# 把 MCP tools 转成 OpenAI Function Calling 格式（一对一映射）
oai_tools = [{
    "type": "function",
    "function": {
        "name": t["name"],
        "description": t["description"],
        "parameters": t["inputSchema"],
    }
} for t in mcp_tools]
# 加一个特殊工具：read_skill
oai_tools.append({
    "type": "function",
    "function": {
        "name": "read_skill",
        "description": "Load full SKILL.md body for the named skill",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
})

system_prompt = f"""You are a helpful assistant.

{skills.system_prompt_block()}

When a skill matches the user's request, call read_skill(name=...) FIRST to load
its instructions, then follow them step by step.
"""

messages = [{"role": "system", "content": system_prompt}]

def chat(user_input: str) -> str:
    messages.append({"role": "user", "content": user_input})
    while True:
        resp = llm.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=oai_tools,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            if name == "read_skill":
                result = skills.load_body(args["name"])
            else:
                result = mcp.call_tool(name, args)
            messages.append({
                "role": "tool", "tool_call_id": tc.id, "content": result,
            })
        # 回到 while 顶部，让 LLM 看到 tool 结果再决策

# Demo
print(chat("上海今天天气怎么样？"))
# 预期 LLM 行为：
# 1. 看到 weather skill 描述，先 read_skill(name="weather") 学习工作流
# 2. 再 tool_call get_weather(city="Shanghai")
# 3. 拿到 "晴 22°C"，按 skill 工作流格式化输出
```

**这段代码证明了一件事**：MCP + Skill + LLM 三个东西用最朴素的 Python 就能组装到一起，框架的价值是「省样板代码 + 提供高级特性」，而不是「这事儿不用框架做不了」。

---

## 八、避坑指南

| 坑 | 原因 | 解法 |
|----|------|------|
| MCP server `print("debug")` 后 client 全乱 | stdout 必须只有 MCP 消息，任何额外输出都污染 JSON-RPC 流 | 所有日志走 stderr：`print(..., file=sys.stderr)` |
| client 收不到 server 响应，永远 hang 住 | 没 `sys.stdout.flush()`，Python 默认行缓冲在 pipe 下变块缓冲 | server 每次写完 stdout 必须 flush；或启动 Python 时加 `-u` 参数 |
| MCP 调用 `tools/call` 报 -32002 协议错误 | 漏发 `notifications/initialized` 通知 | 严格按 lifecycle：initialize → 等响应 → 发 initialized 通知 → 才能发业务请求 |
| Skill 写得很好但 LLM 永远不触发 | description 只描述"是什么"，没说"何时用" | description 必须包含触发关键词："Use when user asks about X, mentions Y, needs Z" |
| Skill 文件夹里有 `.DS_Store` / `__pycache__` 把 SkillManager 搞崩 | glob 没过滤 | scan 时只匹配 `*/SKILL.md`，跳过没有 SKILL.md 的目录 |
| 多个 Skill 的 description 措辞接近，LLM 触发错的 | 描述歧义、关键词重叠 | 用 [R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) skill-creator 的方法做 description 优化（A/B 测触发率） |
| MCP 跨进程调用慢（每次 50-200ms） | stdio 子进程通信 + JSON 序列化开销 | 同进程能跑就用 Function Calling，必须解耦才上 MCP；批量调用用一次 batch 请求 |
| HTTP MCP 部署后被远程站点 DNS rebind 攻击 | server 绑了 `0.0.0.0`，没校验 Origin | 本地 server 必须绑 `127.0.0.1`；HTTP 必须校验 Origin header（spec 强制） |
| Skill 被恶意污染（外部源的 SKILL.md 含恶意指令） | Skill 本质是 prompt injection 的合法通道 | 只用可信源的 Skill；审计每个 SKILL.md 和脚本（参考 Anthropic 安全提示） |
| MCP `tools/list` 返回的 schema LLM 看不懂 | description 太短或没有 examples | description 写满（"Use this when X, returns Y in Z format. Example: ..."） |

---

## 九、成本与决策速查

### 何时手搓 vs 用 SDK

| 场景 | 推荐 |
|------|------|
| 学习理解协议本质 | ✅ 手搓一遍，不超过半天 |
| 跨语言互通调试（Python client 接 Rust server） | ✅ 至少手搓一边，能看 wire-level 包 |
| 快速做原型/MVP | ❌ 用官方 SDK（Python `mcp`、TS `@modelcontextprotocol/sdk`） |
| 生产部署 | ❌ 用 SDK + 它内置的错误处理/超时/重连/auth |
| 评估 SDK 是否有 bug | ✅ 手搓最小 client 复现 |
| 嵌入式/受限环境（不想拉依赖） | ✅ 手搓核心 80 行就够 |

### 三件武器选型决策树

```
你想给 LLM 加一个能力 X：

X 是单进程内的 Python 函数？
├─ 是 → Function Calling（最简单，0 协议开销）
└─ 否 ↓

X 需要被多个 Agent 应用复用？或 X 在另一个进程/语言？
├─ 是 → MCP（一处实现，全平台调用）
└─ 否 → Function Calling 直接搞

你想给 LLM 加的不是"能力"而是"做事的手册/流程"？
└─ 是 → Skill（不需要执行新代码，注入知识就够）

X 既要"知识"又要"能力"？
└─ MCP + Skill 组合：MCP 提供工具，Skill 教 LLM 怎么用工具
```

### Token / 性能成本

| 模式 | 启动 Token | 每次调用 Token | 延迟 |
|------|-----------|---------------|------|
| Function Calling | 工具 schema（~50-200 tokens × N） | tool_call + result（~20-100） | < 1ms（同进程） |
| MCP（stdio） | 同上 + 子进程内存 ~30MB | 同上 + JSON-RPC 序列化 | 5-50ms（本地） |
| MCP（HTTP） | 同上 + HTTP 连接 | 同上 + 网络 RTT | 20-200ms |
| Skill L1（启动） | ~100 tokens × N（永驻） | 0 | 0 |
| Skill L2（触发） | 0 | SKILL.md body 的 token 数（一次性）| 一次文件读 ~ms |
| Skill L3（资源） | 0 | 仅脚本 stdout 进上下文 | 取决于脚本 |

**经验法则**：
- 装 100 个 Skill ≈ 加 10K tokens system prompt（可承受）
- 装 100 个 MCP 工具 ≈ 加 5-20K tokens schema（接近上下文窗口的 5-10%，开始要选择性挂载）
- 不要给一个 LLM 同时挂 50+ 工具——LLM 的工具选择准确率会显著下降（这是 [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 调研的发现）

---

## 十、结论与最佳实践

### 核心结论

1. **MCP/Skill 都不是黑盒**：MCP = JSON-RPC + 三个 method + stdio/HTTP；Skill = 文件系统 + frontmatter + 信任 LLM 自主触发。手搓门槛极低。
2. **三件武器是分层关系不是替代关系**：Function Calling 是底座，MCP 是其分布式版本，Skill 是其知识层。生产 Agent 通常三者并用。
3. **协议简单 ≠ 工程简单**：手搓核心 100 行就能跑，但生产化（auth、重连、并发、容错、observability）需要 1000+ 行——这才是 SDK 真正的价值所在。
4. **理解协议层，再用 SDK，效率倍增**：调试时不再是黑盒、跨语言互通时知道边界、自定义传输层时有底气。

### 落地最佳实践

- **学习路径**：手搓一次 MCP server+client（半天）→ 跑通 mini-agent（1 小时）→ 切到官方 SDK 写生产服务
- **Skill 设计原则**：一个 Skill 一件事；description 包含明确的触发条件；脚本永远比让 LLM 生成代码更可靠（详见 [R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)）
- **MCP 工具设计原则**：description 要写"何时调 + 输入啥 + 返回啥格式"；inputSchema 字段都加 description；返回值结构化（用 `outputSchema` 让 LLM 解析更稳）
- **生产防护**：stdio server 的日志走 stderr；HTTP server 校验 Origin + 绑 localhost；Skill 仅信任审计过的源

### 与本工作区已有报告的关系

- 本报告补全了 [R39](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R39_%E9%A3%9E%E4%B9%A6CLI%E4%B8%8EMCP%E9%80%9A%E4%BF%A1%E6%9C%BA%E5%88%B6.md)（飞书 MCP 应用层）的协议层基础：现在你既知道 MCP 怎么用，也知道它怎么实现的
- 本报告补全了 [R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)（Skill 设计哲学）的运行时基础：现在你既知道为什么这么设计 SKILL.md，也知道 Agent 怎么把它注入上下文
- 本报告与 [R64](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md)（MCP Gateway）形成"协议层 ↔ 网关层"双视角，配合阅读可以理解完整 MCP 生态
- 本报告引用 [R03](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) 的 Agent 架构基础范式

### 开放问题（未来可深入）

1. **MCP `sampling` 反向能力**：让 server 反过来调 client 的 LLM——本报告未实现，是 MCP 比 Function Calling 强大的关键差异点之一
2. **Skill 与 MCP 的统一打包**：能否把 Skill 当成一种特殊的 MCP "resource" 类型暴露？社区已在讨论
3. **跨语言互通验证**：手搓 Python client 接官方 TypeScript server（或反之）—— wire-level 兼容性如何？
4. **Skill 触发率自动优化的 EDD 实践**：将 [R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) 的 description 优化思路落到本工作区的 [skill-evaluator](../../skills/skill-evaluator/SKILL.md) 工具上

---

## 📌 来源清单

- [Model Context Protocol Specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18) — 2025-06-18 — MCP 协议官方规范（Overview）
- [MCP Spec / Base Protocol](https://modelcontextprotocol.io/specification/2025-06-18/basic) — 2025-06-18 — JSON-RPC 2.0 消息定义
- [MCP Spec / Lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle) — 2025-06-18 — initialize / capabilities / shutdown
- [MCP Spec / Transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) — 2025-06-18 — stdio + Streamable HTTP 传输层细节
- [MCP Spec / Server Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) — 2025-06-18 — tools/list / tools/call / Tool schema
- [Anthropic Skills 官方文档](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — 2025-10 — 三级渐进式加载机制
- [Anthropic Skills Blog](https://claude.com/blog/skills) — 2025-10-16（更新 2025-12-18）— Skills 设计理念与跨平台开放标准
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification) — 2010 — MCP 消息层基础
- 本工作区报告 [R39](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R39_%E9%A3%9E%E4%B9%A6CLI%E4%B8%8EMCP%E9%80%9A%E4%BF%A1%E6%9C%BA%E5%88%B6.md) / [R14](R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) / [R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) / [R64](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) / [R03](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) / [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)

⚖️ **来源一致性**：MCP spec 与官方 SDK 实现一致（已交叉验证）；Skills 文档与开源仓库 [anthropics/skills](https://github.com/anthropics/skills) 一致；模型训练知识与实时官方文档无冲突。
📅 **时效性声明**：以上信息获取于 2026-04-26。MCP 当前最新版本为 2025-11-25（spec 已升级），但 2025-06-18 版本仍是大多数 SDK 实现的稳定基线，本报告示例对最新版本保持向后兼容。


---

## 🔑 核心洞见

> 本报告最精华的高维洞见。读懂这几条 = 拔高一个维度理解整篇报告。

- MCP 是协议不是 SDK——核心只有三个方法（initialize / tools/list / tools/call），100 行 Python 能跑通 Server+Client
- Skill 是文件系统约定不是框架——本质是 frontmatter 注入 system prompt + Agent 按需 bash 读 body
- 三级加载（L1 元数据常驻 / L2 SKILL.md 触发加载 / L3 资源按需读）是 Token 优化的本质——常驻成本与能力数量解耦
- MCP 解决能力扩展、Skill 解决知识扩展——前者答'能做什么'，后者答'怎么做'，两者正交不冲突
- 理解协议比掌握 SDK 更重要——框架封装的只是样板代码，协议设计才是真正的杠杆点

*（本节内容与 frontmatter key_insights 字段同步，由 INSIGHTS（原稿交叉引用，本归档未解析） 自动聚合）*

