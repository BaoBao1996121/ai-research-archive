> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Agent SDK 选型指南（2026 Q2 · 格式验证版）

> 一句话概括：七大主流 Agent SDK 形成三层格局——底层图引擎（LangGraph）、中层全栈框架（OpenAI/PydanticAI/ADK/MAF）、高层编排壳（CrewAI）。选型的核心问题不是"谁功能最多"，而是"你的团队在控制力-生产力光谱上站哪个位置"。
> 研究日期：2026-05-21
> 关联报告：R131（同题材，测试 agent.md 迭代效果）

## Key Takeaways

- **PydanticAI 是 2026 Q2 综合性价比最高的选择**——类型安全 + model-agnostic + DI 可测 + Logfire 可观测，适合大多数 Python 工程团队
- **OpenAI Agents SDK 最快上手但 v0.x 有 API 不稳定风险**——适合 PoC 和 OpenAI 重度用户，生产系统等 v1.0
- **LangGraph 仍是复杂有状态编排的唯一成熟选项**——Durable Execution + Checkpoint 无人能及，代价是学习曲线
- **Google ADK 2.0 昨天刚发，潜力大但现在不要用于生产**——等 2.1 再入坑
- **CrewAI Stars 最多但天花板最低**——Demo 快但生产调试困难，适合 PoC 不适合长期维护

---

## 目录

- [定位透镜：纵横坐标](#定位透镜纵横坐标)
- [数据快照](#数据快照)
- [甜区深度拆解](#甜区深度拆解)
- [六场景决策树](#六场景决策树)
- [最佳实践](#最佳实践)
- [反模式清单](#反模式清单)
- [结论与推荐路径](#结论与推荐路径)
- [信息来源清单](#信息来源清单)
- [开放问题](#开放问题)

---

## 定位透镜：纵横坐标

### 纵轴 · 演化脉络

**Agent SDK 的演化是一部"控制权下沉"的历史。**

**第一阶段：对话链（2023H1）。** LangChain 把"LLM + 工具"封装为 Agent，但本质是线性 Chain——出错只能从头来，无法暂停、无法人工介入。类比：单线程程序，崩了就重启。

**第二阶段：图引擎觉醒（2023H2—2024H2）。** LangGraph 引入有状态图解决持久化和循环；AutoGen 推广多 Agent 对话；CrewAI 降低门槛。关键转折：OpenAI Function Calling 标准化了工具调用协议。类比：从单线程进化到多线程+断点续跑。

**第三阶段：厂商官方入场（2025—至今）。** OpenAI、Google、Microsoft 相继发布官方 SDK，第三方框架的"API 封装"护城河消失。存活下来的第三方必须有不可替代的差异化（LangGraph 的控制力、PydanticAI 的类型系统、CrewAI 的低门槛）。

**当前阶段判定**：

| SDK | 生命周期 | 一句话判断 |
|-----|---------|-----------|
| LangGraph | 成熟期 | API 稳定，企业客户验证，可安心用于生产 |
| CrewAI | 上升→平台期 | 增长放缓，核心架构未大变，创新在 Flows 上 |
| OpenAI Agents SDK | 快速上升 | 14 个月 100 releases，能力在追赶但 API 未锁定 |
| Google ADK | 动荡期 | v2.0 刚发 breaking changes，赌性高收益高 |
| PydanticAI | 快速上升 | v1.99→v2.0 在即，生态加速中 |
| MS Agent Framework | 早期 | 社区小但微软资源充足，长期看好 |
| AutoGen | 退役 | Maintenance Mode，不再接受新功能 |

### 横轴 · 竞争格局（设计哲学分野）

**七个产品不是在同一维度竞争，而是回答了不同的核心问题：**

| 核心信条 | 代表 | 适合的团队画像 |
|---------|------|--------------|
| "图就是一切，你对每个节点负全责" | LangGraph | 要极致控制的平台团队 |
| "三个概念走天下" | OpenAI Agents SDK | 要最快出活的小团队 |
| "类型即文档，DI 即测试" | PydanticAI | 有代码洁癖的工程团队 |
| "像写剧本一样定义 Agent" | CrewAI | 非深度技术背景的探索者 |
| "谷歌全家桶入口" | Google ADK | GCP 原住民 |
| "企业中间件全栈" | MS Agent Framework | Azure + .NET 企业 |

### 交叉判断

- 纵轴信号：**官方 SDK 正在挤压社区框架**。OpenAI 14 个月 100 releases 的节奏说明——如果你只是封装 API，迟早被官方替代
- 横轴信号：能活下来的第三方必须有**设计哲学级差异**，而非功能级差异
- **两轴交叉的选型入口**：先问"我的控制力需求在哪"（高→LangGraph，中→PydanticAI/OpenAI，低→CrewAI），再问"我的生态绑定是什么"（Google→ADK，Azure→MAF，无→按控制力选）

---

## 数据快照

> 下表展示七大 SDK 的 GitHub 核心指标，数据获取于 2026-05-21。

| SDK | Stars | Version | License | Contributors | 状态 |
|-----|-------|---------|---------|--------------|------|
| CrewAI | 51.8K | 1.14.5 | MIT | 318 | 活跃 |
| LangGraph | ~35K | 1.2.0 | MIT | ~200 | 稳定 |
| OpenAI Agents SDK | 26.5K | 0.17.3 | MIT | 292 | 快速迭代 |
| Google ADK | 19.7K | 2.0.0 | Apache-2.0 | 279 | 刚重构 |
| PydanticAI | 17.2K | 1.99.0 | MIT | 461 | 快速迭代 |
| MS Agent Framework | 10.6K | 1.5.0 | MIT | 144 | 早期 |
| AutoGen ⚠️ | 58.2K | 0.7.5 | MIT | 558 | 维护模式 |

AutoGen 的 58.2K Stars 是历史积累——最后一次 feature release 在 2025-09，官方引导迁移至 MS Agent Framework。

---

## 甜区深度拆解

### 1. LangGraph · 底层图引擎之王

**一句话：你需要的不是框架帮你"编排 Agent"，而是一个让你精确控制每一步状态流转的引擎。**

**甜区**：长时运行 + checkpoint/resume + 自定义状态机 + HITL（人工审批）+ 非标准控制流。

**核心优势**：
- Durable Execution：任意步骤故障自动恢复
- 状态粒度到 TypedDict 字段级别
- Human-in-the-loop 是一等公民（interrupt → 改 state → resume）
- LangSmith 深度集成的端到端 trace

**致命短板**：
- 学习曲线：Hello World 也要理解 5 个概念
- 样板代码多：每个节点手写状态读写
- LangSmith 付费服务绑定（最佳体验需要）

**适合**：3-5 人 Agent 专项团队，需要生产级可靠性。
**不适合**：快速 PoC、1-2 人小团队、简单工具调用。

---

### 2. OpenAI Agents SDK · 极简主义标杆

**一句话：Agent 开发的 Hello World——概念最少、路径最短、与 OpenAI 生态无缝对接。**

**甜区**：以 OpenAI 模型为主力、追求最小概念集、快速从零到产品。

**核心优势**：
- Agent + Tool + Handoff 三概念覆盖 80% 场景
- 内置 Tracing UI
- Guardrails 一等公民
- Sandbox Agent 解决长时运行代码执行
- 100+ LLM 支持（LiteLLM 扩展）

**致命短板**：
- v0.x = API 未锁定（14 个月 100 releases）
- 多 Agent 编排有限（无图级分支/循环/并行）
- 无内建 checkpoint/持久化
- 高级特性仍绑定 OpenAI

**适合**：OpenAI 重度用户、追求最快 time-to-first-value。
**不适合**：需要复杂 DAG、需要 API 稳定性保证、必须多模型。

---

### 3. PydanticAI · 类型安全主义的极致

**一句话：如果 FastAPI 让你爱上了 Python Web 开发，PydanticAI 会让你爱上 Agent 开发。**

**甜区**：重视代码质量和可维护性、有 FastAPI 经验、需要强类型保障。

**核心优势**：
- `Agent[Deps, Output]` 全链路类型安全
- 依赖注入（RunContext[T]）天然可测试
- Model-agnostic 最彻底
- Capabilities 系统（Thinking/WebSearch/MCP 可组合）
- Pydantic Logfire（OTel 标准）
- 内置 Evals + Graph 支持

**致命短板**：
- v1.99.0 = v2.0 前夕，可能有 breaking changes
- 多 Agent 编排不如 LangGraph 成熟
- Logfire 绑定付费（最佳体验）
- 社区教程不如 CrewAI/LangGraph 丰富

**适合**：FastAPI 背景、类型安全是团队文化、需要模型灵活切换。
**不适合**：追求"最快跑通 demo"、不习惯类型标注。

---

### 4. CrewAI · 声明式编排甜蜜圈

**一句话：非技术人员也能看懂的"AI 团队协作"——但天花板低。**

**甜区**：快速搭建"角色扮演"式多 Agent 协作原型。

**核心优势**：
- 最低上手门槛（YAML 声明角色/目标/任务）
- CLI 脚手架 30 秒出项目
- Crews + Flows 双模式
- 100K+ 社区开发者

**致命短板**：
- 黑盒问题：Agent 交互不透明，出错难定位
- 过度依赖 LLM 做编排决策（不确定性高）
- 生产级能力弱（无 checkpoint、无 durable execution）
- 控制粒度粗：想定制就撞墙

**适合**：PoC 快速验证、非工程主导的探索。
**不适合**：生产系统、SLA 要求高、需要精确控制。

---

### 5. Google ADK 2.0 · 谷歌生态深度绑定

**一句话：v2.0 的 Workflow Runtime + Task API 让 ADK 从"Gemini 封装"升级为正面对标 LangGraph 的图编排框架——但昨天才发布。**

**甜区**：GCP 基础设施 + Gemini 主力模型 + 能承受早期不稳定。

**核心优势**：
- Workflow Runtime（图级执行：routing/fan-out/fan-in/loops/retry）
- Task API（结构化 Agent 间委托）
- 与 Vertex AI/Cloud Run 原生集成
- `adk web` 开发 UI

**致命短板**：
- **昨天才 GA**——生产验证为零
- 1.x → 2.0 Breaking Changes（Session 不兼容）
- Gemini 优先，其他模型二等公民
- Python 3.11+ 要求偏高

**适合**：GCP 原住民 + 愿意承担早期风险。
**不适合**：需要立刻稳定生产（等 2.1-2.2）。

---

### 6. MS Agent Framework · 企业全栈继任者

**一句话：Azure 生态的 Agent 基础设施——唯一的 Python + .NET 双语言方案。**

**甜区**：Azure 企业 + .NET 团队 + 已有 Semantic Kernel 投资。

**核心优势**：
- Python/.NET 一致 API
- 四种编排模式（sequential/concurrent/handoff/group）
- Foundry Hosted Agents 两行代码部署
- A2A 协议支持

**致命短板**：
- 社区小（10.6K Stars, 144 contributors）
- Azure 倾斜严重
- 心智负担重（五层概念）
- 文档质量参差

**适合**：Azure 企业、.NET 团队。
**不适合**：非微软生态、小团队、Python 单语言。

---

### 7. AutoGen · 退役

**状态**：⚠️ Maintenance Mode。不再接受新功能，官方引导迁移至 MS Agent Framework。新项目不应选用。

---

## 六场景决策树

### 场景 1：快速 PoC（1-3 天）

**推荐：OpenAI Agents SDK**（概念最少）或 **CrewAI**（角色模型直觉）。

不确定用什么模型 → PydanticAI（model-agnostic 最好）。

### 场景 2：生产级单 Agent 系统

**推荐：PydanticAI。**

理由：DI 可测 + 类型安全 + Logfire trace 三件套。OpenAI SDK 是备选但 v0.x 减分。

### 场景 3：复杂多 Agent DAG + 持久化

**推荐：LangGraph。**

理由：Durable Execution + Checkpoint 是这个场景的刚需，其他框架达不到同等成熟度。

### 场景 4：Azure + .NET 企业

**推荐：MS Agent Framework。** 这是唯一选择。

### 场景 5：Google Cloud + Gemini

**推荐：Google ADK 做实验，PydanticAI 做生产过渡。** 等 ADK 2.1 再迁移生产。

### 场景 6：避免 vendor lock-in

**推荐：PydanticAI > LangGraph > OpenAI SDK。**

PydanticAI 对多 provider 支持最均匀；LangGraph 本身 model-agnostic 但最佳体验绑 LangSmith。

---

## 最佳实践

**BP-1 · 先验证 LLM 能力，再选框架**

```python
# ✅ 正确：先用原始 API 确认 LLM 能解决问题
from openai import OpenAI
client = OpenAI()
response = client.responses.create(
    model="gpt-4.1",
    input="分析这份合同的风险点...",
    tools=[{"type": "function", "function": {...}}]
)
# 确认可行后，再引入框架处理编排/持久化/可观测
```

```python
# ❌ 错误：还没验证能力就花一周搭框架
from langgraph.graph import StateGraph
# ... 200 行图定义 ...
# 结果 LLM 根本做不好核心任务
```

**BP-2 · 可观测性从 Day 1 开始**

```python
# ✅ PydanticAI + Logfire（一行接入）
import logfire
logfire.configure()  # 所有 Agent 调用自动 tracing
agent = Agent('openai:gpt-4.1', output_type=Report)
result = await agent.run('...')  # 自动记录 input/output/latency/cost
```

```python
# ❌ 生产上线后才发现不知道 Agent 为什么返回错误结果
# 这时再补 trace 需要改大量代码——早知如此何必当初
```

**BP-3 · 结构化输出是你的安全网**

```python
# ✅ 用 Pydantic 模型约束 LLM 输出
from pydantic import BaseModel, Field
class RiskReport(BaseModel):
    risk_level: int = Field(ge=0, le=10)
    findings: list[str]
    recommendation: str

agent = Agent('...', output_type=RiskReport)
# 输出不符合 schema → 自动重试 → 保证类型安全
```

```python
# ❌ 假设 LLM 输出格式正确然后 json.loads()
result = json.loads(llm_response)  # 某天必炸
```

**BP-4 · Token 预算 + 早停是生命线**

```python
# ✅ 任何 Agent 必须有的护栏
result = await Runner.run(
    agent, "...",
    max_turns=10,  # 防止死循环
)
# 补充：设置 total_token_budget 和 per-turn timeout
```

```python
# ❌ 无预算控制 = 信用卡无额度限制交给不可预测的 AI
# 一个失控循环 10 分钟烧 $50
```

**BP-5 · 工具函数写成纯函数 + 类型注解**

```python
# ✅ 框架无关的工具定义
from pydantic import BaseModel
class SearchInput(BaseModel):
    query: str
    max_results: int = 5

def web_search(input: SearchInput) -> list[dict]:
    """搜索网页信息。当用户问题需要实时数据时使用。"""
    return requests.get(f"...?q={input.query}").json()
# 这样定义的工具可以：被任何框架加载 / 单独测试 / 通过 MCP 暴露
```

```python
# ❌ 工具逻辑和框架耦合
@crew_tool  # 只能在 CrewAI 里用，换框架全部重写
def search(query): ...
```

**BP-6 · 渐进式采纳：先简单再复杂**

正确的演进路径：
1. 原始 API 验证能力 → 确认可行
2. 单 Agent + 工具（PydanticAI/OpenAI SDK）→ 解决 80%
3. 需要多步骤 → 引入 Handoff 或简单 DAG
4. 真正需要复杂编排 → 上 LangGraph

大多数项目**永远不需要走到第 4 步**。过度设计的代价比将来迁移更高。

**BP-7 · MCP 优先，自定义工具其次**

```python
# ✅ 优先使用 MCP Server 提供的工具（跨框架复用）
from smolagents import ToolCollection
tools = ToolCollection.from_mcp(
    "npx -y @modelcontextprotocol/server-filesystem"
)
# MCP 工具可被任何支持 MCP 的 Agent 复用
```

```python
# ❌ 每个框架单独写一遍相同的工具
# CrewAI 写一遍、LangGraph 写一遍、PydanticAI 又写一遍
```

---

## 反模式清单

下表列出七大高频反模式，含症状、根因和修正方案：

| 反模式 | 症状 | 根因 | 修正 |
|--------|------|------|------|
| **框架先行** | 花一周搭框架，核心能力未验证 | 技术兴奋驱动 | 先 API 验证再引入框架 |
| **God Agent** | 一个 Agent 挂 20+ 工具，频繁选错 | 低估 LLM 工具选择错误率 | 拆为专责 Agent + Router |
| **过度编排** | 3 步任务用 50 行 StateGraph | 被能力吸引而非需求驱动 | 简单用 if/else，复杂才用图 |
| **忽视成本** | Agent 循环 50 轮才得到答案 | 无 max_turns/early_stop | 设硬上限 + 成本告警 |
| **裸跑无 trace** | "为什么返回这个？"——不知道 | Day 1 没上可观测 | Logfire/LangSmith 从第一行接入 |
| **Lock-in 不自知** | 换模型时改动遍及全代码库 | 业务逻辑与模型调用耦合 | 用框架的 model-agnostic 接口 |
| **追星选型** | "Stars 最多所以最好" | Stars ≠ 适合你 | Stars 看健康度，选型看约束匹配 |

---

## 结论与推荐路径

**如果你只看一句话：Python 工程团队选 PydanticAI，它在类型安全、模型灵活性和测试友好性上的综合表现是 2026 Q2 最优解。**

按场景的推荐矩阵：

| 你的情况 | 第一选择 | 第二选择 | 不要选 |
|---------|---------|---------|--------|
| Python 团队，要快 | OpenAI Agents SDK | PydanticAI | LangGraph |
| Python 团队，要稳 | **PydanticAI** | LangGraph | ADK 2.0 |
| 复杂 DAG + 持久化 | **LangGraph** | — | CrewAI |
| Azure + .NET | **MS Agent Framework** | — | 纯 Python 方案 |
| Google Cloud | ADK（实验）| PydanticAI（生产过渡）| — |
| 最快出 demo | CrewAI | OpenAI SDK | LangGraph |
| 避免 vendor lock | **PydanticAI** | LangGraph | OpenAI/ADK/MAF |

### 2026 Q2 五个趋势判断

1. **PydanticAI 综合最优**——但 v2.0 breaking changes 在即，现在入坑需接受迁移成本
2. **OpenAI SDK 在快速收敛**——一旦到 v1.0 锁定 API 可能成为默认选择
3. **LangGraph 地位稳固但护城河变薄**——ADK 2.0 和 pydantic_graph 都在侵蚀
4. **CrewAI 天花板低**——Demo 快但 repeat user 的技术深度存疑
5. **ADK 2.0 是 dark horse**——半年后可能是 Gemini 用户不二之选，但现在别赌生产

---

## 信息来源清单

📌 来源清单
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI) — 2026-05-21 — 51.8K⭐, v1.14.5, MIT
- [OpenAI Agents SDK GitHub](https://github.com/openai/openai-agents-python) — 2026-05-21 — 26.5K⭐, v0.17.3, MIT
- [Google ADK GitHub](https://github.com/google/adk-python) — 2026-05-21 — 19.7K⭐, v2.0.0 (14h ago), Apache-2.0
- [PydanticAI GitHub](https://github.com/pydantic/pydantic-ai) — 2026-05-21 — 17.2K⭐, v1.99.0, MIT, 461 contributors
- [MS Agent Framework GitHub](https://github.com/microsoft/agent-framework) — 2026-05-21 — 10.6K⭐, v1.5.0, MIT
- [AutoGen GitHub](https://github.com/microsoft/autogen) — 2026-05-21 — 58.2K⭐, MAINTENANCE MODE
- [LangGraph PyPI](https://pypi.org/project/langgraph/) — 2026-05-21 — v1.2.0, MIT

⚖️ 来源一致性：多源一致（所有数据来自 GitHub 实时抓取）
📅 时效性声明：以上信息获取于 2026-05-21

---

## 开放问题

1. **PydanticAI v2.0 的 breaking changes 范围**——v1.99.0 暗示在即，具体变更待跟踪
2. **Google ADK 2.0 生产验证**——刚发布不到 24h，社区实战反馈为零
3. **A2A 协议互通性**——PydanticAI/MAF/ADK 都声称支持，跨框架能否真正互通未验证
4. **Anthropic 的 Agent SDK 策略**——目前无官方 SDK（仅 tool use API），出 SDK 会改变格局
5. **MCP Server 生态质量**——所有框架都支持 MCP，但社区 Server 质量参差不齐
