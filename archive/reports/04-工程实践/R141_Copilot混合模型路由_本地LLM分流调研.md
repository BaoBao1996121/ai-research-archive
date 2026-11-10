---
title: "Copilot 混合模型路由：用本地 LLM 分流调查任务节约主模型 Token"
aliases: [R141, Copilot混合模型路由, 本地LLM分流, AI-Infra路由]
tags: [copilot, model-routing, cost-optimization, local-llm, subagent, mcp]
date: 2026-05-31
category: 工程实践
report_id: R141
status: completed
tokens: 8000
related:
  - "[R116](R116_OpenHuman%E5%9B%9B%E5%A4%A7%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E6%B7%B1%E5%BA%A6%E6%8B%86%E8%A7%A3%E4%B8%8E%E5%80%9F%E9%89%B4%E6%96%B9%E6%A1%88.md)"
  - "[R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md)"
  - "[R32](R32_Copilot%E5%85%A8%E5%B1%80%E8%87%AA%E5%AE%9A%E4%B9%89%E8%B7%A8%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%A4%8D%E7%94%A8.md)"
key_insights:
  - "技术上完全可行——VS Code 已原生支持 Custom Endpoint BYOK + subagent 异构模型，AI-Infra 只要暴露 OpenAI 兼容接口就能接入"
  - "经济可行性取决于本地模型质量门槛——质量不够导致的返工比省下的 Token 还贵"
  - "最稳路径：MCP Tool 桥接（零侵入 + 主模型控制质量），次优路径：subagent model 指定（省 Token 更彻底但需验证 cost-tier 兼容性）"
  - "适合委托的任务类型很窄：文本总结、格式转换、事实检索、代码搜索聚合——复杂推理必须留在主模型"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Copilot 混合模型路由：用本地 LLM 分流调查任务节约主模型 Token

> 一句话概括：**技术上完全可行，经济上有条件可行，但真正省 Token 的甜点比直觉想象的窄——不是"调查任务"都适合委托，而是只有"质量门槛低于本地模型能力上限"的子任务才值得分流。**
>
> 研究日期：2026-05-31
> 关联报告：[R116](R116_OpenHuman%E5%9B%9B%E5%A4%A7%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E6%B7%B1%E5%BA%A6%E6%8B%86%E8%A7%A3%E4%B8%8E%E5%80%9F%E9%89%B4%E6%96%B9%E6%A1%88.md) OpenHuman hint-based 模型路由、[R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md) Coding Agent 横评、[R32](R32_Copilot%E5%85%A8%E5%B1%80%E8%87%AA%E5%AE%9A%E4%B9%89%E8%B7%A8%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%A4%8D%E7%94%A8.md) Copilot 全局自定义

---

## 目录

- [TL;DR 结论](#tldr-结论)
- [定位透镜](#定位透镜)
- [三条技术路径](#三条技术路径)
- [Token 经济学：什么时候真能省钱](#token-经济学什么时候真能省钱)
- [适合 vs 不适合委托的任务](#适合-vs-不适合委托的任务)
- [推荐实施方案](#推荐实施方案)
- [Dry Run 验证计划](#dry-run-验证计划)
- [风险与局限](#风险与局限)
- [来源清单](#来源清单)

---

## TL;DR 结论

| 维度 | 判断 |
|------|------|
| **技术可行性** | ✅ VS Code 原生支持（Custom Endpoint BYOK + subagent 异构模型 + MCP Tool）|
| **经济可行性** | ⚠️ 有条件——仅当本地模型能力 ≥ 子任务质量门槛时才真正省钱 |
| **最佳切入点** | MCP Tool 桥接方案（30 分钟搭建，零风险验证）|
| **预估节省** | 日常调研类操作 Token 消耗减 30-50%（保守）；但总 Token 中调研占比本身可能不高 |
| **核心风险** | 本地模型返回低质结果 → 主模型重做 = 反而多花 Token |

**我的推荐**：先用 MCP Tool 方式花半小时搭一个最小验证，跑 10 个典型"调查"场景，量化本地模型的命中率。如果命中率 > 80%，再考虑做成 subagent 自动化路由。

---

## 定位透镜

### 纵轴 · 演化脉络

| 时期 | 能力 | 你的场景对应 |
|------|------|-------------|
| 2025 Q3 | VS Code 支持 subagent 异构模型（P05 已验证） | 可以给 worker 配便宜模型 |
| 2025 Q4 | VS Code Custom Endpoint（BYOK）正式上线 | 可以接入任意 OpenAI 兼容 API |
| 2026 Q1 | `chatLanguageModels.json` 支持 Chat Completions / Responses / Messages 三种 API 类型 | AI-Infra 网关只要兼容其中一种就能接 |
| 2026 Q2（当前） | Auto model selection + MCP sampling | VS Code 本身在尝试自动路由 |

**生命周期定位**：你想做的事，VS Code 的基础设施**已经就绪**。不是"能不能做"的问题，是"怎么做效果最好"的问题。

### 横轴 · 实现方式竞争格局

| 路径 | 侵入性 | Token 节省程度 | 质量控制力 | 实施难度 |
|------|--------|--------------|-----------|---------|
| **A. MCP Tool 桥接** | 零（不改主模型行为） | 中（主模型仍要组织 prompt + 解读返回） | 高（主模型决定何时调用） | ⭐ 30 分钟 |
| **B. Subagent 模型指定** | 低（配 .agent.md） | 高（整个子任务链在本地模型跑） | 中（subagent 独立决策） | ⭐⭐ 2 小时 |
| **C. run_in_terminal 脚本** | 零 | 中 | 高 | ⭐ 15 分钟 |

### 交叉判断

P05 实验已经证明了 subagent 异构模型是 VS Code 官方支持的特性。BYOK Custom Endpoint 也已正式推出。**技术路径通畅，无需 hack**。但这里有一个未被验证的关键假设需要 Dry Run：

> **BYOK 模型能否被 subagent 的 `model:` 字段引用？**  
> P05 验证的是 Copilot 目录内的模型（Haiku/Sonnet）。BYOK 模型是否进入同一个模型池、是否受 cost-tier 约束——这是需要实验回答的。

---

## 三条技术路径

### 路径 A：MCP Tool 桥接（推荐首选）

**原理**：写一个 MCP Server，暴露一个 `investigate` 工具。主模型（Opus）在需要调查时调用这个工具，工具内部把 prompt 转发给 AI-Infra 本地模型，返回结果。

```
┌─────────────┐    tool_call     ┌──────────────┐    HTTP     ┌──────────────┐
│ Opus 4.6    │ ──────────────→  │  MCP Server  │ ─────────→  │  AI-Infra    │
│ (主模型)    │ ←────────────── │ (investigate) │ ←───────── │  本地 LLM    │
│             │   tool_result    │              │   response  │              │
└─────────────┘                  └──────────────┘             └──────────────┘
```

**实现骨架**（Python + FastMCP）：

```python
# mcp_ai_infra_bridge.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import httpx, json

app = Server("ai-infra-bridge")

AI_INFRA_URL = "http://your-ai-infra-gateway/v1/chat/completions"
AI_INFRA_MODEL = "qwen3-32b"  # 或你们网关上可用的模型

@app.tool()
async def investigate(query: str, context: str = "") -> list[TextContent]:
    """
    将调查/搜索/总结类任务委托给本地大模型执行。
    适用于：文本总结、代码搜索结果聚合、格式转换、事实检索。
    不适用于：复杂推理、方案设计、代码生成。
    """
    messages = [
        {"role": "system", "content": "你是一个高效的调研助手。直接给出事实性答案，不要废话。"},
        {"role": "user", "content": f"{query}\n\n参考材料：\n{context}" if context else query}
    ]
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(AI_INFRA_URL, json={
            "model": AI_INFRA_MODEL,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.3
        }, headers={"Authorization": "Bearer YOUR_TOKEN"})
    result = resp.json()["choices"][0]["message"]["content"]
    return [TextContent(type="text", text=result)]
```

**VS Code 配置**（`.vscode/mcp.json`）：

```json
{
  "servers": {
    "ai-infra-bridge": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/mcp_ai_infra_bridge.py"]
    }
  }
}
```

**优势**：
- 主模型完全控制何时委托——不会盲目把复杂任务丢给弱模型
- 零侵入：不改任何已有配置，随时可以移除
- 工具描述中写明适用边界，模型自行判断是否调用

**劣势**：
- 主模型仍需消耗 Token 来组织 tool_call prompt 和解读返回（每次约 300-500 tokens）
- 不适合大段落生成——工具返回太长反而撑大主模型上下文

---

### 路径 B：Subagent 模型指定（节省最彻底）

**原理**：利用 P05 验证过的 subagent 异构模型能力。创建一个 `researcher.agent.md`，在 frontmatter 指定 BYOK 模型。

**Step 1**：在 `chatLanguageModels.json` 注册 AI-Infra 为 Custom Endpoint

```json
[
  {
    "name": "AI-Infra Local",
    "vendor": "customendpoint",
    "apiKey": "YOUR_AI_INFRA_TOKEN",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "qwen3-32b",
        "name": "Qwen3-32B (Local)",
        "url": "http://your-ai-infra-gateway/v1/chat/completions",
        "toolCalling": true,
        "maxInputTokens": 32000,
        "maxOutputTokens": 8000
      }
    ]
  }
]
```

**Step 2**：创建 researcher subagent

```yaml
---
name: local-researcher
description: "调查类子任务执行者。负责文本总结、代码搜索聚合、事实检索。"
user-invocable: false
model: ['Qwen3-32B (Local)']
tools: ['read_file', 'grep_search', 'file_search', 'semantic_search', 'fetch_webpage']
---

你是一个高效的调研助手，运行在本地模型上。

## 你的职责
- 根据主 Agent 交给你的调查任务，利用工具搜索和阅读文件
- 返回简洁的事实性摘要（不超过 500 字）
- 如果任务超出你的能力（复杂推理、方案设计），明确说"此任务需要主模型处理"

## 硬约束
- 不要编造信息——找不到就说找不到
- 不要做超出事实总结的推理
- 返回格式：先结论，后证据（文件路径+行号）
```

**Step 3**：主 Agent 通过 `runSubagent` 调用

主模型在 agent.md 的工作流程中，遇到"需要查阅/搜索/总结"类任务时，自动 `runSubagent` 给 `local-researcher`。

**优势**：
- Token 节省最彻底——整个子任务的推理过程（工具调用链 + 多轮思考）全在本地模型消化
- 主模型只付出 `runSubagent` 的 prompt + 返回 summary 的 Token

**劣势 / 待验证风险**：
- ⚠️ **Cost-tier 兼容性未验证**：BYOK 模型是否能被 subagent 的 `model:` 字段正确识别？需要 Dry Run
- ⚠️ **Tool calling 能力**：Qwen3-32B 的 tool calling 是否稳定？如果 JSON 格式出错，subagent 会崩
- 本地模型如果"自信地胡说"，主模型拿到错误信息做决策，后果可能比不省 Token 更差

---

### 路径 C：Terminal 脚本桥接（最简单粗暴）

**原理**：写一个 Python 脚本，主模型通过 `run_in_terminal` 调用它。

```python
# scripts/ask_local.py
import sys, httpx, json

query = sys.argv[1] if len(sys.argv) > 1 else input()
resp = httpx.post("http://ai-infra-gateway/v1/chat/completions", json={
    "model": "qwen3-32b",
    "messages": [{"role": "user", "content": query}],
    "max_tokens": 1000
}, headers={"Authorization": "Bearer TOKEN"})
print(resp.json()["choices"][0]["message"]["content"])
```

主模型执行：`python scripts/ask_local.py "总结这个文件的核心逻辑"`

**优势**：15 分钟就能跑通。**劣势**：粗糙，不支持流式，不适合复杂交互。

---

## Token 经济学：什么时候真能省钱

### 关键公式

```
净节省 = (委托任务的 Opus Token 消耗) - (调用开销 + 失败返工成本)

其中：
- 调用开销 = tool_call prompt (~300 tokens) + result 解读 (~500 tokens) ≈ 800 tokens/次
- 失败返工成本 = 失败率 × 委托任务 Token × 2（本地做一次 + 主模型重做一次）
```

### 场景估算

| 场景 | 不委托（Opus 全做） | 委托（本地做） | 净节省 | 前提 |
|------|-------------------|--------------|--------|------|
| "总结这个 2000 行文件" | ~5000 tokens（读取+推理+输出） | ~800 tokens（调用开销） | **~4200 tokens** (84%) | 本地模型总结质量 OK |
| "搜索代码库中所有用到 Redis 的地方" | ~3000 tokens（多次工具调用+汇总） | ~800 tokens | **~2200 tokens** (73%) | 搜索本来就是工具做的，模型只做汇总 |
| "分析这个方案的优劣" | ~4000 tokens | ~800 + 4000（本地做垃圾→Opus 重做）= 4800 | **-800 tokens** (亏了) | 本地模型推理不行 |
| "帮我写这段代码" | ~3000 tokens | 不应该委托 | N/A | 代码质量要求高 |

### 结论

**只有当本地模型在该任务类型上的成功率 > 60% 时，委托才是正 ROI。** 成功率 < 60%，每次失败的返工成本会吃掉所有节省。

对于当前的 Qwen3-32B 级别模型，保守估计：
- 简单总结/格式转换：成功率 ~90% → **值得委托**
- 代码搜索聚合：成功率 ~85% → **值得委托**
- 复杂分析/推理：成功率 ~40% → **不值得委托**
- 代码生成：成功率 ~50% → **不值得委托**

---

## 适合 vs 不适合委托的任务

### ✅ 适合委托给本地模型

| 任务类型 | 典型场景 | 为什么可以 |
|---------|---------|-----------|
| **文本总结** | "总结这个文件的核心逻辑" | 信息压缩，门槛低 |
| **格式转换** | "把这段 JSON 转成 Markdown 表格" | 机械性操作 |
| **事实检索+聚合** | "列出所有 controller 的路由" | 搜索工具做主力，模型只整理 |
| **翻译** | "把这段英文文档翻成中文" | 翻译质量 32B 级别基本够用 |
| **简单分类** | "这个 issue 属于 bug 还是 feature request" | 二分类，错了也无大碍 |

### ❌ 不适合委托（必须留在 Opus）

| 任务类型 | 为什么不行 |
|---------|-----------|
| **架构决策** | 需要深度推理 + 全局视角 |
| **代码生成** | 格式错误/逻辑错误的代价太高 |
| **方案评审** | 需要挑战假设、发现盲点 |
| **指令遵守类任务** | 本地模型指令跟随能力弱，容易漂移 |
| **多步规划** | 需要长链推理 + 自纠错 |
| **上下文密集型判断** | "基于前面 20 轮对话的上下文做决策" |

### 灰色地带（需要实验验证）

- 代码 Review 中的"找明显 bug"：可能可以用本地模型初筛
- 文档写作的"初稿生成"：取决于对质量的容忍度
- 测试用例生成：如果有好的 Spec 约束，可能可行

---

## 推荐实施方案

### Phase 1：30 分钟验证（MCP Tool，本周就能做）

1. 写一个最简 MCP Server（上面路径 A 的代码）
2. 在 `.vscode/mcp.json` 注册
3. 在 Agent 模式下手动 `#investigate` 触发几次，观察：
   - AI-Infra 响应延迟
   - 返回质量是否达标
   - 主模型是否正确使用了工具

### Phase 2：量化实验（1 天）

准备 20 个典型"调查"场景（10 个适合委托 + 10 个边界），分别：
- A 组：全在 Opus 上做
- B 组：委托给本地模型

对比：Token 消耗、任务完成质量、耗时。**如果 B 组质量达标率 < 70%，停止。**

### Phase 3：自动化路由（确认 Phase 2 正 ROI 后）

两个选择（不互斥）：

**3a. 增强 MCP Tool 的触发智能**：
- 在工具描述中精确列出适用场景
- 主模型自己判断何时调用（当前 Opus 判断力足够）

**3b. Subagent 路由（如果 BYOK + subagent 兼容性验证通过）**：
- 注册 AI-Infra 到 `chatLanguageModels.json`
- 创建 `local-researcher.agent.md`
- 在主 Agent 指令中加入 "调查类任务优先 runSubagent 给 local-researcher"

---

## Dry Run 验证计划

在实施 Phase 1 之前需要确认的前置条件：

| 验证项 | 方法 | 预期结果 | 阻断级别 |
|--------|------|---------|---------|
| AI-Infra 网关暴露 OpenAI 兼容接口 | `curl http://gateway/v1/chat/completions` | 200 + 正常响应 | 🔴 阻断 |
| 网关延迟在可接受范围 | 10 次调用取平均 | < 10s | 🟡 影响体验 |
| 本地模型支持 tool calling | 发送含 tools 参数的请求 | 正确返回 tool_calls | 🟡 仅影响路径 B |
| BYOK 模型出现在 VS Code model picker | 配置 `chatLanguageModels.json` 后检查 | 下拉中可见 | 🟡 仅影响路径 B |
| Subagent 能引用 BYOK 模型名 | 在 `.agent.md` 写 `model: ['Qwen3-32B (Local)']` 并触发 | 日志显示使用了该模型 | 🟡 仅影响路径 B |

---

## 风险与局限

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 本地模型质量不够 → 返工反而更费 | 中 | 高 | Phase 2 量化验证，设准入门槛 |
| AI-Infra 网关不稳定/延迟高 | 低 | 中 | MCP Tool 加 timeout + fallback |
| BYOK + subagent 不兼容 | 中 | 低（有路径 A 兜底） | 先跑路径 A |
| 主模型过度委托（把不该委托的也丢了） | 低 | 中 | 工具描述中严格限定适用边界 |
| 安全风险：敏感代码经过本地模型 | — | 取决于 AI-Infra 的数据策略 | 确认 AI-Infra 数据不出域 |

### 这个方案的天花板在哪

说白了：**你日常使用 Copilot 时，真正属于"简单调查且本地模型能胜任"的任务占比可能没有想象中高。** 

我观察你的使用模式（从交互日志和 P05 实验看），大部分操作是：
- 深度调研（需要复杂推理 → 必须 Opus）
- 代码修改（质量要求高 → 必须 Opus）
- 方案设计（创造性工作 → 必须 Opus）
- 读文件+搜索（**已经是工具在做**，模型只花少量 Token 发起调用）

真正能被分流的甜点窄于直觉——可能只占总 Token 的 15-25%。乘以 70% 的节省率 = 实际总 Token 减少 10-17%。

**不是说不值得做**——如果你的 Copilot 账户有 premium request 限制或硬成本约束，10-17% 的节省乘以高频使用量也不小。但如果期望是"砍掉一半 Token 消耗"，大概率会失望。

---

## 来源清单

- VS Code 官方文档 · Bring Your Own Language Model Key · https://code.visualstudio.com/docs/copilot/customization/language-models — 2026-05-28 更新
- VS Code 官方文档 · AI Extensibility Overview（MCP Tool） · https://code.visualstudio.com/docs/copilot/copilot-extensibility-overview — 2026-05-28 更新
- [R116](R116_OpenHuman%E5%9B%9B%E5%A4%A7%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E6%B7%B1%E5%BA%A6%E6%8B%86%E8%A7%A3%E4%B8%8E%E5%80%9F%E9%89%B4%E6%96%B9%E6%A1%88.md) OpenHuman hint-based 模型路由（PATTERN_LIBRARY P-003）
- P05（原稿交叉引用，本归档未解析） VS Code Copilot 多 Agent 编排原型（异构模型实证）
- VS Code 官方文档 · Subagents · https://code.visualstudio.com/docs/copilot/agents/subagents — 2026-04-26 确认

**来源一致性**：多源一致。VS Code 官方文档（2026-05-28）+ 本工作区 P05 实验数据（2026-04）互相印证。  
**时效性声明**：信息获取于 2026-05-31。

---

## 开放问题

1. **AI-Infra 网关具体兼容哪种 API 格式？** 需要确认是 Chat Completions 还是其他格式
2. **BYOK 模型 + subagent `model:` 字段的兼容性** 需要实际 Dry Run 验证
3. **集团对 AI-Infra 调用有无频率限制/审计要求？** 影响 MCP Server 的设计
4. **本地模型的 tool calling 稳定性** 如果不稳定则只能走路径 A（MCP Tool 不需要本地模型支持 tool calling）
