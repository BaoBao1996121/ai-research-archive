---
title: "Ch10: 多 Agent 协作"
tags: [教程, 多Agent, 协作, 架构, spiral-3]
date: 2026-04-12
status: completed
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../ARCHIVE_POLICY.md)阅读。

# Chapter 10: 多 Agent 协作

> 📍 前置：完成 Chapter 9（理解单 Agent 的可靠性挑战）
> 🎯 完成本章后你能：区分三种多 Agent 架构模式；解释"什么时候需要多 Agent"的决策标准；理解 Subagent 的核心价值
> ⏱️ 预计时间：20 分钟阅读 + 25 分钟动手

---

## 为什么需要多个 Agent？（WHY）

Chapter 9 你看到了单个 Agent 的天花板——上下文有限、注意力衰减、大任务容易失控。

一个直觉解法是：**分工。**

就像一个人写不完一个大项目，但一个团队可以——前提是分工明确、沟通高效。多 Agent 的核心价值不是"更多的计算"，而是**隔离上下文 + 专业化分工**。

但多 Agent 不是万能的。它带来了新的问题：Agent 之间怎么沟通？一个 Agent 的错误怎么不扩散到其他 Agent？整体质量谁负责？

> 📌 Anthropic 的建议（来自官方博客）：**"最成功的实现都是用简单的、可组合的模式构建的。"不要为了"多 Agent"而多 Agent。** 如果一个 Agent + 好的工具就能搞定，那比三个 Agent 协作更好、更可靠、更便宜。

---

## 核心概念（WHAT）

### 三种多 Agent 架构模式

回想 Ch3 你学的五种模式里，有两种天然是多 Agent 的：

```
模式 1: Orchestrator-Workers（编排者-工人）
    一个 Boss Agent 分配任务，多个 Worker 执行

     ┌─── Worker A (写代码)
     │
Boss ├─── Worker B (写测试)
     │
     └─── Worker C (写文档)

模式 2: Evaluator-Optimizer（评估者-优化者）
    一个做事，另一个审查，循环迭代

    Generator ──→ Output ──→ Evaluator
        ↑                        │
        └── 改进建议 ─────────────┘

模式 3: Peer Network（对等网络）
    多个 Agent 平等协作，通过协议通信

    Agent A ←─→ Agent B
      ↑  ↘         ↗  ↑
      │   Agent C      │
      └────────────────┘
```

### 什么时候用多 Agent？决策树

```
你的任务...
├── 单个 Agent + 工具能搞定？
│   └── ✅ 是 → 不要用多 Agent（更简单、更可靠、更便宜）
│
├── 需要不同的"专业视角"？
│   └── ✅ 是 → Evaluator-Optimizer（一个做，一个审）
│   └── 例：代码生成 + 安全审计、文章写作 + 事实核查
│
├── 需要并行处理多个独立子任务？
│   └── ✅ 是 → Orchestrator-Workers（Boss 分配，Worker 并行）
│   └── 例：同时测试多个模块、同时搜索多个信息源
│
└── 需要跨系统/跨团队的长期协作？
    └── ✅ 是 → Peer Network + 协议（A2A/MCP）
    └── 例：跨仓库的代码修改、多平台的自动化运维
```

### Subagent：最实用的多 Agent 形式

在实践中，你最先遇到的多 Agent 形式是 **Subagent**——主 Agent 在需要时"派生"一个子 Agent，把上下文隔离的任务交给它。

```
主 Agent（全局视野）
  │
  ├── 遇到需要深入分析的文件
  │   └── 派生 Subagent A: "分析 utils/auth.ts，告诉我认证流程"
  │       └── Subagent A 有自己独立的上下文窗口
  │       └── 分析完成，返回结果给主 Agent
  │
  ├── 遇到需要执行测试的任务
  │   └── 派生 Subagent B: "跑一下登录模块的测试"
  │       └── Subagent B 不受主 Agent 上下文里其他信息干扰
  │
  └── 综合两个子结果，继续主任务
```

Subagent 的核心价值：

| 好处 | 说明 |
|------|------|
| **上下文隔离** | 子任务不污染主 Agent 的上下文，也不受主上下文干扰 |
| **聚焦** | 子 Agent 只做一件事，指令遵守率更高（Ch7 讲过：指令越少，遵守越好） |
| **成本控制** | 子 Agent 用完就销毁，不占主 Agent 的 Token 预算 |
| **并行** | 多个 Subagent 可以同时执行（如果任务独立） |

### Claude Code 的 Subagent 实现

Claude Code 有一个 `AgentTool`——主 Agent 可以调用它来派生 Subagent：

```
Claude Code 的 tools/AgentTool.tsx：
  - 接收一个子任务描述
  - 创建一个新的 Agent 实例（独立上下文）
  - 给子 Agent 传递：任务描述 + 相关文件路径
  - 等待子 Agent 完成，收集结果
  - 将简短的结果摘要返回给主 Agent
```

关键设计：**子 Agent 返回给主 Agent 的是摘要，不是完整对话。** 这确保了主 Agent 不会被子任务的细节淹没。

---

## 动手做（HOW）

### 实现一个简单的 Orchestrator-Workers 系统

基于 Ch4 的 `agent_loop`，扩展为多 Agent：

```python
"""
简单的 Orchestrator-Workers：Boss 分配任务，Worker 并行执行
"""
import openai
import json
from concurrent.futures import ThreadPoolExecutor

client = openai.OpenAI()

def worker_agent(task: str, worker_id: str) -> str:
    """单个 Worker Agent：接收任务，执行，返回结果"""
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": f"你是 Worker {worker_id}。专注完成分配给你的任务，简洁返回结果。"},
            {"role": "user", "content": task},
        ]
    )
    return response.choices[0].message.content

def boss_agent(user_request: str) -> str:
    """Boss Agent：分解任务并分配给 Workers"""
    
    # Step 1: Boss 分解任务
    plan_response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": """你是一个任务分解专家。
将用户请求拆分为可独立执行的子任务。
输出 JSON 数组: [{"id": "W1", "task": "具体任务描述"}, ...]
最多 4 个子任务。如果任务很简单，1 个就够。"""},
            {"role": "user", "content": user_request},
        ],
        response_format={"type": "json_object"},
    )
    
    plan = json.loads(plan_response.choices[0].message.content)
    tasks = plan.get("tasks", plan.get("subtasks", [plan]))
    if isinstance(tasks, dict):
        tasks = [tasks]
    
    print(f"📋 Boss 分解了 {len(tasks)} 个子任务:")
    for t in tasks:
        print(f"  [{t.get('id', '?')}] {t.get('task', t)}")
    
    # Step 2: Workers 并行执行
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for t in tasks:
            tid = t.get('id', str(tasks.index(t)))
            task_desc = t.get('task', str(t))
            futures[executor.submit(worker_agent, task_desc, tid)] = tid
        
        for future in futures:
            tid = futures[future]
            results[tid] = future.result()
            print(f"  ✅ Worker {tid} 完成")
    
    # Step 3: Boss 综合结果
    synthesis_response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一个结果综合专家。将多个 Worker 的结果整合为一份完整回答。"},
            {"role": "user", "content": f"原始请求: {user_request}\n\nWorker 结果:\n" + 
                "\n---\n".join(f"[{k}]: {v}" for k, v in results.items())},
        ]
    )
    
    return synthesis_response.choices[0].message.content

# 使用
result = boss_agent("分析一下 Python、TypeScript、Rust 各自适合什么场景，给出推荐。")
print("\n📊 最终结果:")
print(result)
```

### 思考题

1. **上面的 Boss 分解得不好（比如把一个不可分的任务也拆成 4 个），会怎样？** 最终结果质量会比单 Agent 更差。这说明了什么？（提示：多 Agent 的开销是实在的）
2. **Ch9 的双 Agent Harness（Initializer + Coding Agent）本质上是哪种模式？** 是 Orchestrator-Workers、Evaluator-Optimizer、还是别的？
3. **Anthropic Skill-Creator 的三个 Sub-Agent（Grader/Comparator/Analyzer）本质上是哪种模式？** （提示：Ch8 讲过盲比管线）

---

## 同一任务，三种实现：体感"框架帮你做了什么"

Ch4 你学了手搓 Agent。现在看看**同一个 Orchestrator-Workers 任务**（技术调研助手），分别用手搓、Claude SDK、LangGraph 三种方式实现的差异——这比只看文档更有体感：

### 编排的四个核心维度

无论哪种实现，多 Agent 编排都在解决四件事：

| 维度 | 做什么 | 手搓怎么做 | SDK/框架怎么做 |
|------|--------|-----------|--------------|
| **任务分解** | 把大任务拆成子任务 | 自己写 Prompt 让 Boss 分解 | 相同（本质是 LLM 能力） |
| **上下文隔离** | Worker 之间互不干扰 | 手动管 `messages` 列表 | 自动隔离（独立 session） |
| **执行协调** | 串行/并行/有依赖 | 手动 `ThreadPoolExecutor` | 框架图引擎自动调度 |
| **结果综合** | 把子结果合并为最终答案 | 自己写综合 Prompt | 图状态自动 merge |

### 三种方式速览

```
方式一：手搓 Python（你在上面写的）
  - 你手动管所有事：分解、执行、综合、并行
  - 优势：完全透明，想怎么改就怎么改
  - 代价：工程量大，状态管理全靠自己

方式二：Claude Agent SDK
  - 定义 AgentDefinition（子 Agent），Claude 自主决定何时调用
  - 优势：Agent 有 ID/版本/Session，云端持久化
  - 代价：绑定 Anthropic 模型

方式三：LangGraph 图编排
  - 定义 StateGraph：节点=Agent，边=路由条件
  - 优势：检查点恢复、HITL 审批、可视化调试
  - 代价：学习曲线（需要理解图编排模型）
```

**核心洞察**：三种方式在"任务分解"维度上没有差别——都是 LLM 做的。真正的差异在**上下文隔离**和**执行协调**——这正是框架帮你解决的问题。

> 📌 [多Agent编排三种实现方式学习指南](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) 提供了完整的代码级并排对比，三种实现都可运行。如果你想深入体感差异，建议去跑一遍。

---

## 编排框架选型：三派九家

当你决定用框架时，2026 年的 Agent 框架格局是**"三派九家"**：

```
┌──────────────────────────────────────────────────────┐
│              Agent 编排框架三大流派                      │
│                                                       │
│  📊 图编排派（精确控制工作流）                            │
│  ┌─────────┐  ┌─────────────────┐                    │
│  │LangGraph │  │Microsoft Agent  │                    │
│  │29.2K⭐   │  │Framework 9.4K⭐ │                    │
│  │事实标准   │  │企业级,.NET+Py   │                    │
│  └─────────┘  └─────────────────┘                    │
│                                                       │
│  🎭 角色编排派（直觉好，上手快）                          │
│  ┌─────────┐                                         │
│  │CrewAI   │  "定义角色→分配任务→自动协作"               │
│  │48.8K⭐   │  15分钟上手，非技术团队友好                 │
│  └─────────┘                                         │
│                                                       │
│  🔧 轻量 SDK 派（最小 API 面积）                        │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐           │
│  │OpenAI SDK│ │Pydantic AI│ │Google ADK │           │
│  │20.8K⭐   │ │16.3K⭐    │ │           │           │
│  │Handoff   │ │类型安全    │ │内置GEPA   │           │
│  └──────────┘ └───────────┘ └───────────┘           │
└──────────────────────────────────────────────────────┘
```

### 选型决策树

```
你需要...
├── 多 Agent + 持久状态 + HITL + 复杂工作流？
│   ├── Python 生态 → LangGraph（事实标准，37K下游依赖）
│   └── .NET 企业环境 → Microsoft Agent Framework
│
├── 快速搭 demo + 角色扮演 + 非技术团队？
│   └── CrewAI（最快上手，15分钟出demo）
│
├── 绑定特定模型供应商 OK？
│   ├── Claude 生态 → Claude Agent SDK（内置 10+ 工具）
│   ├── OpenAI 生态 → OpenAI Agents SDK（Handoff + Guardrails）
│   └── Google 生态 → Google ADK（内置优化器 + A2A）
│
├── 要类型安全 + FastAPI 般 DX？
│   └── Pydantic AI（依赖注入 + 结构化输出）
│
└── 不确定？
    └── 从手搓开始，遇到以下瓶颈再选框架：
        - 需要断点恢复 → LangGraph
        - 需要人工审批 → LangGraph
        - 需要角色分工 → CrewAI
        - 需要内置工具 → Claude Agent SDK
```

> 📌 P5 范式的边界再次明确：**单 Agent 场景下"简单可组合 > 复杂框架"成立；多 Agent + 持久状态场景下，框架的价值 > 自建成本。** 详见 [现代智能体编排框架深度调研报告](../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md)。

---

## Agent 间通信：MCP vs A2A

当你的多个 Agent 需要跨框架、跨团队协作时，需要标准化的通信协议。2026 年有两个互补的标准：

```
MCP（Anthropic 主导）              A2A（Google → Linux Foundation）
┌─────────────────┐               ┌─────────────────┐
│ Agent ↔ 工具     │               │ Agent ↔ Agent    │
│                 │               │                 │
│ "给 Agent 装手"  │               │ "让 Agent 找同事"│
│                 │               │                 │
│ 类比：USB 接口   │               │ 类比：HTTP 协议  │
│ 插上就能用工具   │               │ 不同系统能对话   │
└─────────────────┘               └─────────────────┘
```

**MCP** 解决"Agent 怎么用工具"——统一工具接口，Agent 不需要知道工具的实现细节。
**A2A** 解决"Agent 怎么找另一个 Agent 合作"——通过 Agent Card 发现能力，通过 Task 协调工作。

> 什么时候需要 A2A？**跨框架/跨团队/跨组织的 Agent 协作**才需要。如果你的 Agent 都在同一个框架内，框架自带的编排就够了。详见 [A2A协议入门学习指南](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R50_A2A%E5%8D%8F%E8%AE%AE%E5%85%A5%E9%97%A8%E5%AD%A6%E4%B9%A0%E6%8C%87%E5%8D%97.md)。

---

## 深入阅读（IF）

| 主题 | 报告 | 关注章节 |
|------|------|---------|
| 同一任务三种实现的完整代码对比 | [多Agent编排三种实现方式学习指南](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) | §3-5 三种实现 |
| 9 大框架"三派九家"全景 + 选型决策树 | [现代智能体编排框架深度调研报告](../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) | §3 框架对比 + §5 选型 |
| LangGraph 图编排从入门到实战 | [LangChain与LangGraph从入门到实战完全指南](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R26_LangChain%E4%B8%8ELangGraph%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md) | §4-6 LangGraph 核心 |
| A2A 协议五大核心概念 + Hello World | [A2A协议入门学习指南](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R50_A2A%E5%8D%8F%E8%AE%AE%E5%85%A5%E9%97%A8%E5%AD%A6%E4%B9%A0%E6%8C%87%E5%8D%97.md) | §3 核心概念 + §4 实战 |
| 多智能体架构理论 | [Agent架构深度研究报告](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) | §五 多智能体架构 |
| 五种组合模式 | [Google ADK五大Agent技能设计模式研究报告](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md) | §Delegate 模式 |
| 双 Agent Harness 模式 | [长效Agent-Harness工程化研究报告](../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) | §二 双 Agent 架构 |
| 多 Agent Demo 原型 | `prototypes/multi-agent-demo/` | 直接运行 |
| Hermes Agent 的多平台 Gateway | [Hermes-Agent开源自学习AI智能体深度研究报告](../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md) | §5 六大子系统 |
| Claude Agent SDK 子 Agent 系统 | [Claude-Agent-SDK从入门到实战完全指南](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R27_ClaudeAgentSDK%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md) | §6 子 Agent |

---

## 本章小结

| 你学到了 | 对应能力 |
|---------|---------|
| 三种多 Agent 模式：指挥/审查/对等 | 按场景选择合适的架构 |
| "不要为了多 Agent 而多 Agent" | 知道什么时候**不该**用 |
| Subagent = 上下文隔离 + 聚焦 | 最实用的多 Agent 形式 |
| 手搓/SDK/框架三种实现的体感差异 | 知道框架帮你解决了什么 |
| "三派九家"框架格局 + 选型决策树 | 能为项目选择合适的编排方案 |
| MCP vs A2A：工具协议 vs Agent 协议 | 理解跨框架协作的标准 |
| Boss 分解质量决定整体质量 | 理解多 Agent 的核心风险 |

> ⏭️ 下一章：本地跑通了，怎么让别人也能用？→ [Chapter 11: 部署上线](Ch11-%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF.md)
