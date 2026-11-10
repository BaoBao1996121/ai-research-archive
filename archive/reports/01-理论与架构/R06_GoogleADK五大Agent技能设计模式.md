---
title: Google ADK 五大 Agent 技能设计模式研究报告
aliases: [R06, ADK设计模式, Google ADK, Google ADK五大Agent技能设计模式研究报告]
tags: [architecture, design-pattern, google-adk, skill]
date: 2026-04-11
category: 理论与架构
report_id: R06
tokens: 4331
status: completed
related:
  - "[Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "Agent-Skills与LLM-Wiki生态调研报告（原稿交叉引用，本归档未解析）"
prev_path: reports/Google ADK五大Agent技能设计模式研究报告.md
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Google ADK 五大 Agent 技能设计模式研究报告

> **原文：** *5 Agent Skill Design Patterns Every ADK Developer Should Know*  
> **来源：** Google Cloud Blog / ADK 官方文档  
> **研究日期：** 2026-04-11

---

## 一、背景概述

### 1.1 什么是 Google ADK

**Agent Development Kit (ADK)** 是 Google 推出的开源、代码优先的 AI Agent 开发框架。它提供了构建、评估和部署复杂 AI Agent 所需的灵活性与控制力。ADK 虽然针对 Gemini 和 Google 生态系统进行了优化，但设计上是**模型无关、部署无关**的，并支持与其他框架的兼容。

**核心理念：** 让 Agent 开发像软件开发一样，便于开发者创建、部署和编排从简单任务到复杂工作流的 Agentic 架构。

### 1.2 ADK 核心能力

| 能力 | 说明 |
|------|------|
| **丰富的工具生态** | 预构建工具、自定义函数、OpenAPI 规范、MCP 工具集成 |
| **代码优先开发** | 直接定义 Agent 逻辑、工具和编排 |
| **模块化多 Agent 系统** | 通过组合多个专业化 Agent 构建可扩展应用 |
| **追踪与监控** | 内置 Agent 可观测性 |
| **多语言支持** | Python、TypeScript、Go、Java |
| **灵活部署** | Cloud Run、GKE、Vertex AI Agent Engine |

### 1.3 为什么需要设计模式

随着 Agentic 应用日趋复杂，单个庞大的 Agent 变得难以开发、维护和推理。ADK 支持通过**组合多个独立 Agent 实例**构建多 Agent 系统（Multi-Agent System, MAS），形成层级结构，实现：

- **模块化**：每个 Agent 职责单一、可独立开发测试
- **可复用性**：通用能力（如搜索、摘要）可跨系统共享
- **可维护性**：修改或替换单个 Agent 不影响整体
- **可控性**：确定性与非确定性执行的灵活组合

---

## 二、ADK 的 Agent 分类体系

在深入五大模式之前，需要理解 ADK 的 Agent 类型划分：

### 2.1 LLM Agent（智能推理型）

```python
LlmAgent(
    model="gemini-flash-latest",
    name="capital_agent",
    description="回答关于国家首都的问题",
    instruction="你是一个提供国家首都信息的 Agent...",
    tools=[get_capital_city]
)
```

- **核心角色：** 利用 LLM 进行推理、理解自然语言、做决策
- **行为特征：** **非确定性** — 根据指令和上下文动态决定如何行动
- **关键配置：** `name`, `model`, `instruction`, `tools`, `output_schema`, `output_key`

### 2.2 Workflow Agent（工作流编排型）

- **核心角色：** 纯粹用于编排子 Agent 的执行流程
- **行为特征：** **确定性** — 按预定义逻辑管理执行顺序，不使用 LLM
- 三种类型：`SequentialAgent`, `ParallelAgent`, `LoopAgent`

### 2.3 Custom Agent（自定义型）

- 继承 `BaseAgent`，实现专用非 LLM 逻辑
- 常用于条件检查、状态控制等辅助功能

---

## 三、五大 Agent 技能设计模式

### 模式一：Single Skill Agent（单一技能 Agent）

> **核心思想：** 一个 Agent 专注于一项功能，配合一个或少量工具

#### 设计理念

这是最基础也最重要的模式。每个 Agent 被设计为执行**单一、明确**的任务，遵循软件工程中的**单一职责原则**（SRP）。

#### ADK 实现

```python
from google.adk.agents import LlmAgent

def get_capital_city(country: str) -> str:
    """获取指定国家的首都城市"""
    capitals = {"france": "Paris", "japan": "Tokyo", "canada": "Ottawa"}
    return capitals.get(country.lower(), f"未知国家: {country}")

capital_agent = LlmAgent(
    model="gemini-flash-latest",
    name="capital_agent",
    description="回答关于国家首都的问题",
    instruction="""你是一个提供国家首都信息的 Agent。
    当用户询问某国首都时：
    1. 从用户查询中识别国家名称
    2. 使用 get_capital_city 工具查找首都
    3. 清晰地回复用户""",
    tools=[get_capital_city]
)
```

#### 设计要点

| 要素 | 说明 |
|------|------|
| **职责边界** | 每个 Agent 只做一件事 |
| **清晰指令** | instruction 中明确任务目标、工具使用时机、输出格式 |
| **结构化输出** | 使用 `output_schema` 强制 JSON 输出，`output_key` 将结果存入 Session State |
| **描述准确** | `description` 用于其他 Agent 判断是否应路由到此 Agent |

#### 适用场景

- 独立的查询/检索任务
- 单步数据转换或处理
- 作为更大系统中的"微服务"型组件

---

### 模式二：Multi-Tool Agent（多工具 Agent）

> **核心思想：** 一个 Agent 配备多个工具，由 LLM 动态决定使用哪个工具

#### 设计理念

当一个领域内的任务需要多种能力时，可以将多个工具（Function Tools、MCP Tools、OpenAPI Tools）绑定到同一个 LLM Agent。Agent 利用 LLM 的推理能力自主判断**何时使用哪个工具**。

#### ADK 实现

```python
def get_weather(city: str) -> dict:
    """获取指定城市的天气"""
    if city.lower() == "new york":
        return {"status": "success", "report": "纽约天气晴朗，25°C"}
    return {"status": "error", "error_message": f"无法获取 {city} 的天气"}

def get_current_time(city: str) -> dict:
    """获取指定城市的当前时间"""
    if city.lower() == "new york":
        return {"status": "success", "report": "纽约当前时间: 2026-04-11 14:30 EST"}
    return {"status": "error", "error_message": f"无法获取 {city} 的时区"}

weather_time_agent = LlmAgent(
    model="gemini-flash-latest",
    name="weather_time_agent",
    instruction="你可以回答关于城市天气和时间的问题。根据用户需求选择合适的工具。",
    tools=[get_weather, get_current_time]
)
```

#### 与 Single Skill Agent 的关键区别

| 维度 | Single Skill | Multi-Tool |
|------|-------------|------------|
| 工具数量 | 1-2个，职责单一 | 多个，覆盖一个领域 |
| 决策复杂度 | 简单，几乎总是调用同一工具 | 复杂，LLM 需要判断使用哪个工具 |
| 指令重要性 | 基础 | **关键** — 必须说明每个工具的用途和使用时机 |
| 可预测性 | 高 | 中等（依赖 LLM 判断） |

#### Planner（规划器）增强

ADK 为 Multi-Tool Agent 提供了两种 Planner 机制：

1. **BuiltInPlanner** — 利用模型内置的"思考"能力（如 Gemini Thinking）
2. **PlanReActPlanner** — 指导模型遵循 Plan → Action → Reasoning 结构

```python
from google.adk.planners import BuiltInPlanner
from google.genai.types import ThinkingConfig

agent = LlmAgent(
    model="gemini-2.5-pro",
    planner=BuiltInPlanner(
        thinking_config=ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1024,
        )
    ),
    tools=[get_weather, get_current_time]
)
```

#### 适用场景

- 同一领域的多种操作（如天气+时间、读+写数据库）
- 需要 LLM 动态推理选择工具的场景
- 工具之间有逻辑关联但不需要固定顺序

---

### 模式三：Sequential Pipeline（顺序流水线）

> **核心思想：** 多个 Agent 按严格顺序依次执行，前一步的输出作为后一步的输入

#### 设计理念

许多实际任务天然具有**阶段性流水线结构**，例如：获取数据 → 处理数据 → 生成报告。`SequentialAgent` 提供确定性的顺序编排，确保每个步骤按固定顺序执行。

#### ADK 实现

```python
from google.adk.agents import SequentialAgent, LlmAgent

# 步骤1: 验证输入
validator = LlmAgent(
    name="ValidateInput",
    instruction="验证用户输入的合法性",
    output_key="validation_status"
)

# 步骤2: 处理数据
processor = LlmAgent(
    name="ProcessData",
    instruction="如果 {validation_status} 为 'valid'，则处理数据",
    output_key="result"
)

# 步骤3: 生成报告
reporter = LlmAgent(
    name="ReportResult",
    instruction="基于 {result} 生成最终报告"
)

# 组装流水线
data_pipeline = SequentialAgent(
    name="DataPipeline",
    sub_agents=[validator, processor, reporter]
)
```

#### 核心机制

```
┌─────────────┐    state['validation_status']    ┌─────────────┐    state['result']    ┌─────────────┐
│  Validator   │ ──────────────────────────────► │  Processor   │ ───────────────────► │  Reporter    │
│  (Step 1)    │                                  │  (Step 2)    │                      │  (Step 3)    │
└─────────────┘                                   └─────────────┘                      └─────────────┘
```

**数据传递方式：** 共享 Session State
- 通过 `output_key` 将 Agent 输出自动保存到 Session State
- 后续 Agent 通过 `{state_key}` 模板语法在 instruction 中读取
- 所有子 Agent 共享同一个 `InvocationContext`，包括 `temp:` 临时命名空间

#### 典型应用：代码开发流水线

```python
pipeline = SequentialAgent(
    name="CodeDevPipeline",
    sub_agents=[
        CodeWriterAgent,     # 生成代码
        CodeReviewerAgent,   # 审查代码
        CodeRefactorerAgent  # 重构代码
    ]
)
```

#### 适用场景

- 数据处理流水线（ETL）
- 内容创作流程（生成 → 审核 → 优化）
- 任何具有明确阶段性依赖的任务

---

### 模式四：Parallel Fan-Out/Gather（并行扇出/汇聚）

> **核心思想：** 多个独立任务并行执行以减少延迟，然后汇聚合并结果

#### 设计理念

当多个子任务之间**没有依赖关系**时，并行执行可以显著缩短总处理时间。`ParallelAgent` 提供了并发执行编排能力。

#### ADK 实现

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent

# 并行获取阶段（Fan-Out）
fetch_api1 = LlmAgent(
    name="API1Fetcher",
    instruction="从 API 1 获取数据",
    output_key="api1_data"
)
fetch_api2 = LlmAgent(
    name="API2Fetcher", 
    instruction="从 API 2 获取数据",
    output_key="api2_data"
)

gather_concurrently = ParallelAgent(
    name="ConcurrentFetch",
    sub_agents=[fetch_api1, fetch_api2]
)

# 汇聚合并阶段（Gather）
synthesizer = LlmAgent(
    name="Synthesizer",
    instruction="合并 {api1_data} 和 {api2_data} 的结果"
)

# 整体工作流：先并行获取，再合成
overall_workflow = SequentialAgent(
    name="FetchAndSynthesize",
    sub_agents=[gather_concurrently, synthesizer]
)
```

#### 核心架构

```
                    ┌────────────────┐
                    │   API1Fetcher  │──► state['api1_data']
                   ╱│   (并行执行)    │
┌──────────────┐ ╱  └────────────────┘                         ┌──────────────┐
│ ParallelAgent│╱                                               │  Synthesizer │
│ (Fan-Out)    │╲                                               │  (Gather)    │
└──────────────┘ ╲  ┌────────────────┐                         └──────────────┘
                   ╲│   API2Fetcher  │──► state['api2_data']
                    │   (并行执行)    │
                    └────────────────┘
```

#### 关键注意事项

| 关注点 | 说明 |
|--------|------|
| **独立执行** | 并行子 Agent 之间**不自动共享**对话历史或状态 |
| **状态竞争** | 虽然共享相同的 `session.state`，但需要使用**不同的 key** 避免竞争条件 |
| **结果顺序** | 结果的返回顺序**不确定** |
| **分支隔离** | 每个子 Agent 有自己的 `InvocationContext.branch`（如 `ParentBranch.ChildName`） |

#### 适用场景

- 多源数据检索（多个 API 并行调用）
- 并行研究/调研任务
- 重计算任务的并行化
- 前置阶段使用 ParallelAgent，后续用 SequentialAgent 合并结果

---

### 模式五：Iterative Refinement Loop（迭代精炼循环）

> **核心思想：** 通过重复执行"生成 → 评估 → 改进"循环，逐步提升输出质量

#### 设计理念

某些任务（如代码优化、文本润色、图像生成）需要多轮迭代才能达到满意结果。`LoopAgent` 管理这种重复执行模式，支持设定最大迭代次数或自定义终止条件。

#### ADK 实现

```python
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.events import Event, EventActions

# 生成/精炼 Agent
code_refiner = LlmAgent(
    name="CodeRefiner",
    instruction="读取 state['current_code']，根据 state['requirements'] 生成/改进代码",
    output_key="current_code"  # 每次迭代覆盖上一版代码
)

# 质量检查 Agent
quality_checker = LlmAgent(
    name="QualityChecker",
    instruction="评估 state['current_code'] 是否满足 state['requirements']，输出 'pass' 或 'fail'",
    output_key="quality_status"
)

# 终止条件检查 Agent（自定义）
class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(self, ctx):
        status = ctx.session.state.get("quality_status", "fail")
        should_stop = (status == "pass")
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_stop)  # True 时终止循环
        )

# 组装迭代循环
refinement_loop = LoopAgent(
    name="CodeRefinementLoop",
    max_iterations=5,
    sub_agents=[code_refiner, quality_checker, CheckStatusAndEscalate(name="StopChecker")]
)
```

#### 核心流程

```
                                    ┌─────────────────┐
                              ┌────►│  CodeRefiner     │──── state['current_code']
                              │     │  (生成/改进)     │
                              │     └────────┬────────┘
                              │              ▼
  max_iterations=5            │     ┌─────────────────┐
  ◄───────────────────────────┤     │  QualityChecker  │──── state['quality_status']
  或 escalate=True            │     │  (质量评估)      │
                              │     └────────┬────────┘
                              │              ▼
                              │     ┌─────────────────┐
                              │     │  StopChecker     │
                              └─────│  (终止判断)      │──── escalate=True/False
                                    └─────────────────┘
```

#### 终止机制

LoopAgent 本身**不判断**何时停止循环，需要开发者实现终止逻辑：

| 方式 | 说明 |
|------|------|
| **max_iterations** | 设置最大迭代次数，硬性上限 |
| **escalate=True** | 子 Agent 在 Event 中设置 `escalate=True`，触发循环终止 |
| **组合使用** | 推荐同时设置 max_iterations + escalate 条件双重保障 |

#### 典型应用：文档迭代改进

```python
loop = LoopAgent(
    name="DocImprovement",
    max_iterations=5,
    sub_agents=[WriterAgent, CriticAgent]
)
# WriterAgent 生成/修改文档
# CriticAgent 评价并决定是否发出 STOP 信号
```

#### 适用场景

- 代码生成与自动优化
- 文本写作的多轮润色
- 图像生成的质量控制（生成 → 计数验证 → 重试）
- 任何需要"做到满意为止"的迭代任务

---

## 四、高级组合模式

五大基础模式可以自由组合，形成更复杂的架构：

### 4.1 Coordinator/Dispatcher（协调器/分发器）

**结构：** 一个中央 LLM Agent 管理多个专业化子 Agent

```python
coordinator = LlmAgent(
    name="HelpDeskCoordinator",
    model="gemini-flash-latest",
    instruction="路由用户请求：支付问题用 Billing agent，技术问题用 Support agent",
    sub_agents=[billing_agent, support_agent]
)
```

**交互机制：**
- **LLM 驱动委派** — LLM 生成 `transfer_to_agent(agent_name='Billing')` 函数调用
- **AgentTool 显式调用** — 将子 Agent 包装为工具显式调用

### 4.2 Hierarchical Task Decomposition（层级任务分解）

**结构：** 多层 Agent 树，高层分解问题，底层执行

```python
from google.adk.tools import agent_tool

# 底层工具型 Agent
web_searcher = LlmAgent(name="WebSearch", description="执行网页搜索")
summarizer = LlmAgent(name="Summarizer", description="摘要文本")

# 中层组合 Agent
research_assistant = LlmAgent(
    name="ResearchAssistant",
    tools=[agent_tool.AgentTool(agent=web_searcher), 
           agent_tool.AgentTool(agent=summarizer)]
)

# 高层决策 Agent
report_writer = LlmAgent(
    name="ReportWriter",
    instruction="撰写关于X的报告，使用 ResearchAssistant 收集信息",
    tools=[agent_tool.AgentTool(agent=research_assistant)]
)
```

### 4.3 Generator-Critic（生成-评审）

**结构：** SequentialAgent 包含生成器和评审器

```python
review_pipeline = SequentialAgent(
    name="WriteAndReview",
    sub_agents=[
        LlmAgent(name="DraftWriter", output_key="draft_text"),
        LlmAgent(name="FactChecker", instruction="审查 {draft_text} 的准确性")
    ]
)
```

### 4.4 模式组合示例

**迭代精炼 + 顺序流水线 + 并行扇出：**

```
SequentialAgent("TotalPipeline")
├─ ParallelAgent("DataGather")          # 并行收集多源数据
│  ├─ DataSourceAgent_A
│  └─ DataSourceAgent_B
├─ LoopAgent("RefinementLoop")          # 迭代改进
│  ├─ ProcessorAgent                    # 生成/改进
│  ├─ QualityAgent                      # 评估
│  └─ StopCheckAgent                    # 终止判断
└─ ReporterAgent                        # 最终报告
```

---

## 五、Agent 间通信机制

### 5.1 共享 Session State（最基础）

```python
# Agent A 写入
agent_a = LlmAgent(name="AgentA", output_key="capital_city")

# Agent B 读取
agent_b = LlmAgent(name="AgentB", instruction="告诉我关于 {capital_city} 的信息")
```

- 所有同一 Invocation 中的 Agent 共享同一 Session 对象
- `temp:` 命名空间用于临时数据（仅当前回合有效）
- 最适合 SequentialAgent 和 LoopAgent 场景

### 5.2 LLM 驱动委派（Agent Transfer）

```python
# LLM 自动生成: transfer_to_agent(agent_name='Booker')
coordinator = LlmAgent(
    name="Coordinator",
    instruction="预订请求转给 Booker，信息查询转给 Info",
    sub_agents=[booking_agent, info_agent]
)
```

- 动态路由，基于 LLM 对上下文的理解
- 需要子 Agent 有清晰的 `description`

### 5.3 AgentTool（显式调用）

```python
from google.adk.tools import agent_tool

image_tool = agent_tool.AgentTool(agent=image_generator_agent)
artist_agent = LlmAgent(
    name="Artist",
    tools=[image_tool]  # 像工具一样调用另一个 Agent
)
```

- 同步调用，结果直接作为工具返回值
- 状态和 Artifact 变更会传回父 Agent 上下文

---

## 六、Skills 特性（实验性）

ADK 最新引入了 **Skills** 概念 — 自包含的功能单元，Agent 可按需加载：

### 6.1 三层结构

| 层级 | 内容 | 加载时机 |
|------|------|----------|
| **L1 (Metadata)** | Skill 名称、描述 — 用于发现 | 始终加载 |
| **L2 (Instructions)** | 主要指令 — 核心行为定义 | Agent 触发 Skill 时加载 |
| **L3 (Resources)** | 参考资料、资产、脚本 | 按需加载 |

### 6.2 文件结构

```
my_agent/
    agent.py
    skills/
        weather_skill/
            SKILL.md           # 主指令（必需）
            references/
                REFERENCE.md   # 详细 API 参考
                FORMS.md       # 表单填写指南
            assets/
                *.*            # 模板、数据文件
            scripts/
                *.py           # 工具脚本（暂不支持执行）
```

### 6.3 使用方式

```python
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

weather_skill = load_skill_from_dir(Path("skills/weather_skill"))
my_skill_toolset = skill_toolset.SkillToolset(skills=[weather_skill])

root_agent = Agent(
    model="gemini-flash-latest",
    name="skill_user_agent",
    tools=[my_skill_toolset]
)
```

**设计价值：** Skills 通过增量加载最小化对上下文窗口的影响，实现按需能力扩展。

---

## 七、与其他 Agent 框架的对比

| 维度 | Google ADK | LangGraph | CrewAI | AutoGen |
|------|-----------|-----------|--------|---------|
| **编排方式** | 确定性 Workflow Agent + LLM 委派 | 图状态机 | 角色扮演 + 流程 | 对话驱动 |
| **SequentialAgent** | ✅ 内置 | 需手动构建链 | ✅ Process.sequential | 需自定义 |
| **ParallelAgent** | ✅ 内置 | 支持并行节点 | ✅ Process.parallel（有限） | 部分支持 |
| **LoopAgent** | ✅ 内置 (max_iterations + escalate) | 循环边 | ❌ 需变通 | 自然支持 |
| **Agent 间通信** | Session State + Transfer + AgentTool | 共享状态 + 边 | 共享内存 | 消息传递 |
| **确定性 vs 动态** | 明确分离两种模式 | 图结构定义 | 主要确定性 | 主要动态 |
| **模型支持** | 多模型（Gemini 优化） | 多模型 | 多模型 | 多模型 |
| **部署集成** | Google Cloud 深度集成 | 通用 | 通用 | 通用 |

**ADK 的差异化优势：**
1. **Workflow Agent 与 LLM Agent 的明确分离** — 确定性编排和智能推理解耦
2. **Skills 按需加载** — 上下文窗口优化
3. **Google Cloud 原生集成** — Agent Engine、Cloud Run、GKE 一键部署
4. **多语言 SDK** — Python、TypeScript、Go、Java 统一 API

---

## 八、最佳实践总结

### 8.1 设计原则

1. **单一职责** — 每个 Agent 只负责一项明确任务
2. **明确指令** — `instruction` 中精确描述任务、工具用法、输出格式
3. **结构化数据流** — 使用 `output_key` + `{state_var}` 模板实现 Agent 间数据传递
4. **分层编排** — 用 Workflow Agent 管理流程，用 LLM Agent 处理智能决策
5. **防御性设计** — LoopAgent 务必设置 `max_iterations` 防止无限循环

### 8.2 选择模式的决策树

```
任务是否可以由单个 Agent 完成？
├─ 是 → 任务需要多个工具？
│       ├─ 否 → 模式一: Single Skill Agent
│       └─ 是 → 模式二: Multi-Tool Agent
└─ 否 → 子任务之间有顺序依赖？
        ├─ 是 → 需要迭代改进？
        │       ├─ 否 → 模式三: Sequential Pipeline
        │       └─ 是 → 模式五: Iterative Refinement Loop
        └─ 否 → 模式四: Parallel Fan-Out/Gather
```

### 8.3 常见反模式

| 反模式 | 问题 | 建议 |
|--------|------|------|
| **巨型 Agent** | 一个 Agent 塞入过多工具和逻辑 | 拆分为多个 Single Skill Agent |
| **无上限循环** | LoopAgent 不设 max_iterations | 始终设置上限 + escalate 条件 |
| **模糊指令** | instruction 不明确导致 LLM 行为不可预期 | 明确任务、约束、工具用法和输出格式 |
| **并行竞争** | ParallelAgent 子 Agent 写入相同 state key | 使用不同 key，必要时加锁 |
| **过度委派** | 每层 Agent 都只转发不处理 | 减少不必要的中间层 |

---

## 九、结论

Google ADK 的五大 Agent 技能设计模式为构建复杂 AI Agent 系统提供了清晰、可组合的架构蓝图：

1. **Single Skill Agent** — 基础单元，一个 Agent 做一件事
2. **Multi-Tool Agent** — 单 Agent 内的工具选择与推理
3. **Sequential Pipeline** — 确定性顺序编排
4. **Parallel Fan-Out/Gather** — 并行加速与结果汇聚
5. **Iterative Refinement Loop** — 质量驱动的迭代优化

这五种模式的真正力量在于**组合使用**。通过嵌套 Sequential、Parallel 和 Loop Agent，配合智能的 LLM Agent 进行动态决策，开发者可以构建出既可预测又灵活的大规模 Agent 系统。

**ADK 的核心哲学：让 Agent 开发像软件工程一样 — 模块化、可测试、可维护、可组合。**

---

## 参考链接

- [Google Cloud Blog: 5 Agent Skill Design Patterns Every ADK Developer Should Know](https://cloud.google.com/blog/products/ai-machine-learning/5-agent-skill-design-patterns-every-adk-developer-should-know)
- [ADK 官方文档](https://adk.dev/)
- [ADK GitHub 仓库](https://github.com/google/adk-docs)
- [Workflow Agents 文档](https://adk.dev/agents/workflow-agents/)
- [Multi-Agent Systems 文档](https://adk.dev/agents/multi-agents/)
- [LLM Agent 文档](https://adk.dev/agents/llm-agents/)
- [Skills 文档](https://adk.dev/skills/)
- [ADK Python SDK](https://pypi.org/project/google-adk/)
