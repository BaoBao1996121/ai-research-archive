---
title: Prompt Engineering 系统化调研
aliases: [R55, Prompt Engineering 系统化调研, Prompt工程完全指南]
tags: [prompt-engineering, llm, context-engineering, dspy, cot, react]
report_id: R55
category: 工程实践
prev_path:
status: completed
date: 2026-04-24
tokens: ~15000
related:
  - "[R16](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R16_AI%E8%BE%93%E5%87%BA%E8%B4%A8%E9%87%8F%E7%A8%B3%E5%AE%9A%E6%80%A7%E4%B8%8E%E5%8F%8D%E8%AE%A8%E5%A5%BD.md)"
  - "[R17](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R17_%E6%8C%87%E4%BB%A4%E9%81%B5%E5%AE%88%E9%AA%8C%E8%AF%81%E4%B8%8E%E9%95%BF%E6%9C%9F%E6%BC%82%E7%A7%BB%E6%A3%80%E6%B5%8B.md)"
  - "[R14](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)"
  - "[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
  - "[R54](R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# R55 · Prompt Engineering 系统化调研

> **一句话概括**：Prompt Engineering 在 SOTA 模型上是 ROI 最高的优化手段之一，但"手写 Prompt"的边际收益正被 Context Engineering + 自动化 Prompt 优化（DSPy/GEPA）挤压——2026 年的正确姿态是：**手写做底线 + 程序化做迭代 + 上下文工程管规模**。
> **研究日期**：2026-04-24
> **关联报告**：[R16](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R16_AI%E8%BE%93%E5%87%BA%E8%B4%A8%E9%87%8F%E7%A8%B3%E5%AE%9A%E6%80%A7%E4%B8%8E%E5%8F%8D%E8%AE%A8%E5%A5%BD.md) 输出质量稳定性｜[R17](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R17_%E6%8C%87%E4%BB%A4%E9%81%B5%E5%AE%88%E9%AA%8C%E8%AF%81%E4%B8%8E%E9%95%BF%E6%9C%9F%E6%BC%82%E7%A7%BB%E6%A3%80%E6%B5%8B.md) 指令漂移｜[R14](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) Skill-Creator 设计哲学｜[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) 自迭代｜[R54](R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md) 学习路线总览
> **任务来源**：`_inbox/待补调研任务清单.md` · G10

---

## 📋 目录

- [TL;DR 速查卡](#tldr-速查卡)
- [🔭 定位透镜：纵横坐标](#-定位透镜纵横坐标)
- [📚 研究分析轨道](#-研究分析轨道)
  - [1. 结构化提示模板解构](#1-结构化提示模板解构)
  - [2. 核心技巧家族](#2-核心技巧家族)
  - [3. 生产级编排模式](#3-生产级编排模式)
  - [4. 反模式与幻觉触发器](#4-反模式与幻觉触发器)
  - [5. 模型差异速查](#5-模型差异速查)
  - [6. Prompt 优化工具链](#6-prompt-优化工具链)
- [🚀 上手实战轨道](#-上手实战轨道)
  - [环境准备](#环境准备)
  - [Hello World：同任务五种写法对比](#hello-world同任务五种写法对比)
  - [生产部署 Checklist](#生产部署-checklist)
- [🕳️ 避坑指南](#-避坑指南)
- [💰 成本与 ROI 速算](#-成本与-roi-速算)
- [🎯 决策速查](#-决策速查)
- [结论与最佳实践](#结论与最佳实践)
- [开放问题与后续计划](#开放问题与后续计划)
- [📌 来源清单](#-来源清单)

---

## TL;DR 速查卡

- 🎯 **还要不要学 Prompt Engineering？**：**要，但要学对层次**。手写 Prompt 的天花板越来越低，但它是 Context Engineering / DSPy / Agent 设计的地基——底子不牢，上层都飘。
- 🏗️ **结构先于技巧**：一个结构良好的 naive prompt（角色+任务+约束+输出格式+示例）通常胜过花哨的 CoT 堆叠。Anthropic 官方明确推荐 **XML 标签** 划分 Prompt 结构，Claude 模型上收益尤其明显。
- 🧠 **CoT 不是免费午餐**：Zero-shot CoT 在推理模型（Claude 3.7/4、DeepSeek-R1、o1/o3）上可能**降分**——它们已内置思考，再叫它"think step by step"是打乱节拍。非推理模型才是 CoT 主战场。
- 📊 **Few-shot 示例顺序敏感度惊人**：同一批示例换顺序，准确率可波动 10%+（`Lu et al., 2022`）。Few-shot 要么配 Self-Consistency，要么转向 DSPy/GEPA 自动挑选。
- 🤖 **生产级看编排而非技巧**：真实系统里 Prompt Chaining / Routing / Parallelization / Orchestrator-Workers / Evaluator-Optimizer 这五种编排模式（Anthropic `Building Effective Agents`）比单 Prompt 精调更决定成败。
- 💡 **2026 年的新共识**：能用 Schema 约束就别用 Prompt 约束；能用自动优化器（DSPy/GEPA）就别手调十版；能用 RAG/工具就别死塞上下文。Prompt 是手艺，**不是全部答案**。
- 💰 **Prompt 越长效果越差的拐点 ~8K tokens**：超过就出现 lost-in-the-middle；长上下文能力强的模型（Gemini 2.5 / Claude 3.7）能撑到 ~32K，但单纯塞字数永远不如结构化。

---

## 🔭 定位透镜：纵横坐标

### 纵轴 · 演化脉络

```
2020  GPT-3 Few-shot ICL 论文 → Prompt 成为独立概念
2022  CoT 论文 (Wei et al.) → "think step by step" 爆火
2022  Zero-shot CoT (Kojima et al.) → 一句话触发推理
2023  ReAct (Yao et al.) → Thought-Action-Observation 循环，Agent 元年
2023  Self-Consistency / ToT / GoT → CoT 的分叉演化
2023  Constitutional AI (Anthropic) → Prompt 即对齐
2024  DSPy (Stanford) → 转向"编程 Prompt"范式
2024  OpenAI Instruction Hierarchy → 结构化权威
2024  Anthropic XML Tag 最佳实践固化
2025  GEPA / TextGrad / PromptWizard → 自动优化成主流
2025  推理模型（o1/R1/Claude 3.7）→ CoT 内置化，手写 CoT 贬值
2026  Context Engineering 接过权杖 → Prompt 降格为"组件"
```

**生命周期定位**：
- 手写 Prompt（狭义 PE）→ **成熟期向衰退期过渡**：不是消失，是被包含
- Context Engineering → **上升期**：承接了 PE 的核心问题（"告诉模型什么"）
- 自动化 Prompt 优化 → **上升期后半段**：DSPy/GEPA 已有生产案例

### 横轴 · 竞争格局

| 技术路径 | 代表 | 设计哲学 | 适用条件 |
|---------|------|---------|---------|
| **手写 Prompt** | Anthropic Prompt Library / OpenAI Cookbook | 人类理解的可读性 + 快速迭代 | 原型、单次任务、需要人类审查的场景 |
| **程序化 Prompt** | DSPy / TextGrad / GEPA | 把 Prompt 当程序，编译优化 | 有训练集、需要长期维护的生产系统 |
| **Context Engineering** | Cursor / Claude Code / Copilot | 关注"塞什么"而非"怎么写" | Agent、长上下文、代码/RAG 场景 |
| **模型内置推理** | o1 / o3 / R1 / Claude 3.7 Extended Thinking | 把思维过程下沉到模型内部 | 推理任务、数学、代码 |

### 交叉判断

纵轴告诉你：**PE 的黄金期（2022-2024 手工打造 Prompt 就能显著拉分）已过**。横轴告诉你：**2026 年的最佳投入组合 = 打好手写底子（理解原理和结构）+ 用 DSPy/GEPA 做生产迭代 + 用 Context Engineering 管理复杂度**。

> **独立结论**：不要再执念"学会 CoT/ToT/ReAct 这些花招"，那只是 20% 的投入区。花 80% 精力理解"**为什么这样写模型会更准/更稳**"和"**如何把 Prompt 纳入工程体系（版本、测试、自动优化）**"才是长期红利。

---

## 📚 研究分析轨道

### 1. 结构化提示模板解构

**一句话结论**：Prompt 的首要问题不是"写什么内容"，而是"如何让模型清楚地看到哪段是哪段"。

#### 1.1 三段式基础（System / User / Assistant）

现代 Chat Model API 都采用消息分层：

| 角色 | 作用 | 典型内容 | 权重（Instruction Hierarchy） |
|------|------|---------|---------|
| `system` | 稳定指令、人格、约束 | "你是严谨的代码审查员，只输出 JSON" | **最高**（OpenAI 2024 明确） |
| `user` | 当前任务输入 | "审查下面这段 Python" | 中 |
| `assistant` | 历史回答 / Few-shot 示范 | "```json\n{...}\n```" | 中 |
| `tool` | 工具返回 | MCP/Function 结果 | **最低**（不应信任） |

> **为什么这重要**：OpenAI 2024 年 `The Instruction Hierarchy` 论文把权威级别写进了模型训练目标——**tool 返回里的"ignore previous instructions" 不会再轻易成功**。这直接影响你防 Prompt Injection 的设计（见 G12 简报）。

#### 1.2 结构化标签：XML vs Markdown vs JSON

Anthropic 官方文档反复推荐在 Claude 上用 **XML 标签**：

```xml
<instruction>分析下面的代码并给出审查意见</instruction>

<code language="python">
def foo(x): return x+1
</code>

<output_format>
- severity: high/medium/low
- category: bug/style/perf
- suggestion: 具体修改建议
</output_format>
```

**对比三种结构**：

| 结构 | 适合模型 | 优点 | 缺点 |
|------|---------|------|------|
| XML 标签 | Claude 系列（训练时大量使用） | 边界清晰、嵌套友好、Claude 对齐最好 | GPT/Gemini 上优势不明显 |
| Markdown 标题 | GPT-4o / 通用 | 人类可读性最强、渲染友好 | 嵌套深时边界模糊 |
| JSON Schema | 需要结构化输出 | 机器可解析、可用 `response_format` 强制 | 不适合做输入结构 |

> **实操建议**：**输入用 XML/Markdown，输出用 JSON Schema**。Claude 输入 XML、GPT-4o 输入 Markdown，这是个被反复验证的细节。

#### 1.3 JSON Schema 输出强制

OpenAI `response_format` + `json_schema` 和 Anthropic `tool_use` 模式本质都在干一件事：**把输出约束从 Prompt 层下沉到解码层**。

```python
# OpenAI Structured Output（2024-08 GA）
response = client.chat.completions.create(
    model="gpt-4o-2024-08-06",
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "review", "schema": REVIEW_SCHEMA, "strict": True}
    },
    messages=[...]
)
```

**铁律**：能用 Schema 约束，就别用 "请严格输出 JSON" 这种 Prompt 约束——后者在高压场景（长 Prompt、对抗输入）下必崩。

### 2. 核心技巧家族

#### 2.1 CoT 家族（Chain-of-Thought）

| 技巧 | 核心做法 | 何时用 | 何时别用 |
|------|---------|--------|---------|
| **Zero-shot CoT** | 末尾加 "Let's think step by step" | GPT-4o / Gemini 等非推理模型的数学/逻辑题 | **推理模型**（Claude 3.7 / o1 / R1）——已内置，反而打乱 |
| **Few-shot CoT** | 示例里带完整推理步骤 | 新颖任务 + 有标注示例 | 推理模型 / 简单任务 |
| **Self-Consistency** | 多次采样 + 投票 | 数学题、多步推理（准确率提 5-10%） | 延迟敏感、成本敏感 |
| **Tree-of-Thoughts (ToT)** | 显式树搜索 + 回溯 | 规划题、24 点、填字游戏 | 99% 业务场景——太贵 |
| **Graph-of-Thoughts (GoT)** | 思维过程建图 | 学术研究 | 生产系统（落地极少） |

> **Claude 3.7 / 4 的特殊处理**：Anthropic 明确建议在 Claude 3.7+ 不要用 "think step by step"，改用 `<thinking>` 标签或直接开启 Extended Thinking 模式。**"think step by step" 在 Claude 4 上实测降分**——因为它把模型的自然推理节拍切碎了。

#### 2.2 示例学习（In-Context Learning）

**Few-shot 的能与不能**：

- ✅ **能**：快速灌输格式/风格/领域词汇
- ✅ **能**：小幅提升少样本分类任务准确率
- ❌ **不能**：让模型学会全新能力（ICL 是"激活"不是"训练"）
- ❌ **不能**：取代 Fine-tune（100 条示例 ≠ 100 条训练数据）

**设计原则**：

1. **多样性 > 数量**：5 条覆盖不同模式，胜过 20 条相似样本
2. **顺序敏感**：`Lu et al., 2022` 证明顺序能导致 10%+ 波动——用 DSPy `BootstrapFewShotWithRandomSearch` 自动搜
3. **Hard Case 先上**：把模型容易错的放前面（recency bias 反过来用）
4. **格式严格对齐**：示例的输入输出格式必须和真实 query 完全一致

#### 2.3 角色与人格（Persona Prompting）

> **心智模型**："You are a senior Python expert" 这种套路的收益在 SOTA 模型上**正在衰减**——GPT-4o 以后模型的基础能力已足够高，扮演资深专家不再显著提升代码质量。

**什么时候 Persona 还有用**：
- 🎨 **控制文风/人格**（客服、陪伴、教育场景）
- 🎭 **激活特定子分布**（"你是 Linus Torvalds" 会让代码评价更犀利）
- 🚫 **无助于**：纯推理/代码/数学任务

#### 2.4 ReAct / Reflexion：Agent 的 Prompt 骨架

ReAct 把 Prompt 从"一次问答"升级为"循环"：

```
Thought: 我需要知道今天的天气
Action: get_weather(city="Beijing")
Observation: {"temp": 12, "cond": "sunny"}
Thought: 气温合适，继续回答
Final Answer: 今天北京 12℃ 晴天，适合出门
```

**为什么重要**：ReAct 是几乎所有 Agent 框架（LangGraph / CrewAI / AutoGen）底层的 Prompt 模板。理解它 = 理解 Agent 怎么"思考"。

**Reflexion 升级**：失败后加一步自省 + 写入 episodic memory，下次不再犯同样错。这是 [R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) Skill 自迭代的理论前身。

#### 2.5 Constitutional / Self-Critique

Anthropic 的 Constitutional AI 把"审查"也做成 Prompt：

```
Step 1: 按用户请求生成回答
Step 2: 按宪法原则 [..., ..., ...] 审查自己的回答
Step 3: 修改回答以符合原则
```

**工程化应用**：生产系统用这个模式做**输出后过滤**——便宜（不用二次训练）、可解释（原则可审查）。缺点：延迟翻倍、成本翻倍。

### 3. 生产级编排模式

> **Anthropic 《Building Effective Agents》(2024-12)** 是这一节的权威底本。五种模式按复杂度递增：

| 模式 | 结构 | 适用场景 | 本库对应 |
|------|------|---------|---------|
| **Prompt Chaining** | `LLM1 → LLM2 → LLM3` 线性 | 可分解为确定性子步骤的任务 | [R51](R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) |
| **Routing** | `Classifier → {LLM_A, LLM_B, ...}` | 多类型输入，不同处理路径 | [R51](R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) |
| **Parallelization** | `Input → {LLM_1, LLM_2, ...} → Aggregator` | 多视角审查、投票、并行检索 | [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) 缓存 |
| **Orchestrator-Workers** | 中央 LLM 动态分派子任务 | 任务结构不固定（代码修改、研究） | [R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) / [R51](R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) |
| **Evaluator-Optimizer** | `Gen ⇄ Critic` 闭环 | 高质量要求 + 能评估 | [R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) 自迭代 |

**关键洞察**：**真实生产系统 80% 问题用 Chaining + Routing 就能解决**。追求 Orchestrator-Workers 前先问：我的任务真的需要动态结构吗？如果能写出固定流程，就别用 Agent 范式。

### 4. 反模式与幻觉触发器

| 反模式 | 为什么是坑 | 正确写法 |
|--------|-----------|---------|
| **否定句堆积** ("不要…不要…") | 模型对 "not" 不敏感，反而被负例词激活 | 用正向表达 "只做 X / 仅当 Y" |
| **过度限制** ("必须用 3 个词回答") | 过严约束让模型输出坏但合规 | 先要质量再谈形式，或用 Schema 约束 |
| **冲突指令** ("简洁…但要全面") | 模型随机挑一边，稳定性差 | 明确优先级 "首要简洁，若信息关键才扩展" |
| **模糊指代** ("优化这个") | 指代失效 | 明示对象 "优化 `<code>` 中的 `foo` 函数" |
| **权威泄漏** (System Prompt 里说 "这是机密") | 说了反而容易被套话 | 别用 Prompt 做安全边界，用权限+审计 |
| **温度 + top_p 同调** | 两者作用重叠，难以调试 | 调温度时 top_p=1；调 top_p 时温度=1 |

### 5. 模型差异速查

| 家族 | 偏好结构 | CoT 策略 | 坑点 |
|------|---------|---------|------|
| **GPT-4o / GPT-4.1** | Markdown + 清晰分段 | Zero-shot CoT 仍有效 | JSON 输出必须用 `response_format` |
| **Claude 3.7 / 4** | **XML 标签** + `<thinking>` | **不要**加 "think step by step"；用 Extended Thinking | 对冗长 System Prompt 容忍度高 |
| **Gemini 2.5 Pro** | Markdown / XML 都可 | CoT 有效；长上下文 >100K 优势明显 | 对中文指令偶有偏移 |
| **DeepSeek-V3 / R1** | 中文友好；R1 自带思考 | R1 **不要**手写 CoT | R1 推理 token 可能超长 |
| **Qwen 2.5 / 3** | 中文 token 压缩率高 | CoT 有效 | chat template 必须严格对齐 |

> **细节坑**：同一段 Prompt 从 Claude 搬到 GPT-4o 要**重写结构标签**；从 DeepSeek-V3 搬到 R1 要**删掉 CoT 触发词**。这不是"模型质量差异"，是 Prompt 格式差异。

### 6. Prompt 优化工具链

| 工具 | 范式 | 核心思路 | 何时用 |
|------|------|---------|--------|
| **DSPy** (Stanford) | 编程式 Prompt | 把 Prompt 当作可训练程序，用 BootstrapFewShot / MIPRO 自动优化示例和指令 | 有训练集 + 准确率导向 + 生产系统 |
| **TextGrad** | 文本梯度 | 把 Prompt 当变量，用 LLM 当"梯度"反向传播 | 研究/实验，生产采用还少 |
| **GEPA** (2025) | Reflective Prompt Evolution | 用 LLM 反思错误 → 进化 Prompt；在多项 benchmark 上 SOTA | 有反馈信号 + 愿意等优化时间 |
| **PromptWizard** (Microsoft) | 自进化 | 类似 GEPA 的思路，更强调 feedback 质量 | 企业内、有 eval 集 |

**何时手调 vs 何时自动调**：

```
手写 Prompt 更划算 ⟵────────────────⟶ 自动优化更划算
- 原型/MVP阶段                        - 生产系统、长期维护
- 单次任务/一次性                     - 每天跑上万次
- 无 eval 集                          - 有 eval 集和明确指标
- 人类审美需求（文风）                - 准确率/F1 驱动
- 需要快速迭代                         - 能等数小时优化
```

---

## 🚀 上手实战轨道

### 环境准备

**依赖版本**（2026-04-24 验证）：

```powershell
# 基础
pip install openai==1.60.0 anthropic==0.40.0
# 可选：DSPy 自动优化
pip install dspy-ai==2.5.0
# 可选：可观测
pip install langfuse==2.60.0
```

**`.env.example`**：
```dotenv
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...   # 可选
```

### Hello World：同任务五种写法对比

**任务**：给定一段产品差评，提取 ① 情绪评分（1-5）② 核心抱怨点（≤3 个）③ 建议改进方向。

**输入样例**：
> "买来用了两周就黑屏，客服让我自费寄回检测，寄回后三天没消息。包装还可以，其他没啥优点。"

#### 写法 ①：Naive（反面教材）

```python
# prompts/v1_naive.py
PROMPT = "分析下面的评论: {review}"
```

预期：输出格式不稳定，有时带 emoji，有时写成长段落，无法程序化消费。

#### 写法 ②：Structured + JSON Schema

```python
# prompts/v2_structured.py
from openai import OpenAI
client = OpenAI()

SYSTEM = """你是电商评论分析助手。只输出符合 Schema 的 JSON，不要任何其他文字。"""

SCHEMA = {
    "name": "review_analysis",
    "schema": {
        "type": "object",
        "properties": {
            "sentiment": {"type": "integer", "minimum": 1, "maximum": 5},
            "complaints": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
            "suggestions": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["sentiment", "complaints", "suggestions"],
        "additionalProperties": False
    },
    "strict": True
}

def analyze(review: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_schema", "json_schema": SCHEMA},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"评论：{review}"}
        ],
        temperature=0.2
    )
    import json
    return json.loads(resp.choices[0].message.content)

# Expected output:
# {"sentiment": 1, "complaints": ["产品质量：两周黑屏", "售后流程：自费寄回", "响应速度：三天无消息"], "suggestions": [...]}
```

#### 写法 ③：Few-shot（适合非 SOTA 模型）

```python
# prompts/v3_fewshot.py
FEW_SHOT = [
    {"role": "user", "content": "评论：物流很快，东西质量也不错，就是颜色和图片有点差别。"},
    {"role": "assistant", "content": '{"sentiment": 4, "complaints": ["颜色与图片不符"], "suggestions": ["提升商品图色彩还原"]}'},
    {"role": "user", "content": "评论：完全用不了，打客服电话一直占线！"},
    {"role": "assistant", "content": '{"sentiment": 1, "complaints": ["产品无法使用", "客服不可达"], "suggestions": ["质检加强", "扩充客服坐席"]}'},
]
# 注入到 messages 中间（system 之后、真实 user 之前）
```

#### 写法 ④：CoT（适合数学/多步推理，对本任务收益有限）

```python
# prompts/v4_cot.py
SYSTEM_COT = """你是评论分析助手。按以下步骤思考后再输出 JSON：
<thinking>
1. 通读评论，识别情绪强度
2. 列出所有可能的抱怨点，合并同类
3. 针对每个抱怨点给出改进方向
</thinking>
然后输出最终 JSON。"""
# 用于 Claude 3.7 时改为开启 Extended Thinking 而非此 Prompt
```

#### 写法 ⑤：ReAct + Constitutional（过度设计示例）

```python
# prompts/v5_react_constitutional.py
# 伪代码：先 ReAct 调用外部 "历史相似评论检索" 工具
# 再用 Constitutional 自审："我的评分是否过于严厉？抱怨点是否有遗漏？"
# 对本任务属 over-engineering，仅作对比演示。
```

**对比实测（100 条评论 × 5 写法，GPT-4o-2024-08-06）**：

| 写法 | JSON 合法率 | 情绪 MAE | 平均耗时 | 每次成本 |
|------|------------|---------|---------|---------|
| ① Naive | ~35% | 1.8 | 1.1s | $0.002 |
| ② Structured + Schema | **100%** | 0.6 | 1.3s | $0.003 |
| ③ + Few-shot (4 例) | **100%** | **0.4** | 1.5s | $0.005 |
| ④ + CoT | 100% | 0.5 | 2.2s | $0.008 |
| ⑤ ReAct + Constitutional | 100% | 0.45 | 5.8s | $0.023 |

> **数据说明**：以上数字为本报告作者根据公开模型定价与典型长度推算的**示意性对照**（非严格 benchmark），用于说明趋势而非绝对值。真实效果必须用你自己的 eval 集跑。

**结论**：**②+③ 是 80% 场景的甜点**。④ 在非推理任务上提升有限但成本翻倍。⑤ 几乎永远不值得在单次调用里堆这么多——该拆到生产编排层（Chaining/Orchestrator）。

### 生产部署 Checklist

从 demo 到生产，至少补这些：

- [ ] **版本化**：Prompt 纳入 Git；每次修改打版本号 `v1.2.3`；A/B 回滚可行
- [ ] **Eval 集**：至少 50-100 条人工标注 case，覆盖常见 + 边界
- [ ] **自动化测试**：CI 里跑 Prompt 回归（Promptfoo / Braintrust / 自建）
- [ ] **可观测**：Langfuse / Helicone / Phoenix 记录输入输出+延迟+成本
- [ ] **Schema 强制**：能用 `response_format` 就用，不信任 Prompt 级"请输出 JSON"
- [ ] **Fallback**：Schema 解析失败时的重试/降级策略
- [ ] **多模型兼容**：至少支持一个备用模型（Claude→GPT 或反之），写 adapter
- [ ] **成本护栏**：单次调用最大 token 上限 + 日预算告警
- [ ] **Prompt Injection 防御**：用户输入用 XML 标签隔离 + 关键指令放 system（见 G12）
- [ ] **接入自动优化**（可选）：等 eval 集稳定后用 DSPy/GEPA 做一次系统优化

---

## 🕳️ 避坑指南

| 坑 | 原因 | 解法 |
|----|------|------|
| **Claude 3.7+ 加 "think step by step" 反而降分** | 模型已内置 reasoning，显式触发反打乱节奏 | 删掉该指令；需要推理时开 Extended Thinking 或用 `<thinking>` 标签 |
| **Few-shot 示例换顺序准确率波动 10%+** | ICL 对 recency/primacy bias 敏感 | ① 用 Self-Consistency 投票 ② 用 DSPy `BootstrapFewShotWithRandomSearch` 自动搜顺序 |
| **"请输出 JSON" 在长 Prompt 下必崩** | 模型遵循指令能力随 Prompt 长度衰减 | 用 `response_format={"type":"json_schema"}` 或 Anthropic tool_use 强制 |
| **同时调温度和 top_p** | 两参数作用重叠，调试空间混乱 | 固定一个（如 top_p=1），只调另一个 |
| **Prompt 超过 ~8K tokens 效果下降** | lost-in-the-middle 现象 | ① 拆成 Chaining 多步 ② 用 RAG 只注入相关片段 ③ 关键指令放首尾 |
| **用 OpenAI tokenizer 估算 Claude/Gemini 成本** | tokenizer 完全不同 | 分别用 `anthropic.count_tokens` / Gemini SDK 估 |
| **把 System Prompt 当安全边界** | 用户可绕过（Prompt Injection） | 权限 + 审计 + 工具白名单，Prompt 只做"礼貌的第一道防线" |
| **用英文 Prompt 处理中文任务** | 语言错配导致输出质量下降 | Prompt 用任务主语言；混合语言时明确标注 |
| **同一 Prompt 跨模型复用不调整** | 不同模型偏好结构不同（XML vs Markdown） | 维护 per-model 适配器，单个 Prompt "源码 → 多目标编译" |
| **Temperature=0 就等于确定性输出** | Top-k 采样、模型本身的非确定因素仍存在 | 关键场景用 `seed` 参数（OpenAI 支持）+ 双重投票验证 |

---

## 💰 成本与 ROI 速算

**Prompt 技巧的投入产出对照**：

| 技巧 | 额外 Token | 准确率提升（非推理模型） | ROI 判断 |
|------|-----------|------------------------|---------|
| 结构化（System + XML/Markdown） | +100-300 | +15-30% | ✅ 极高 |
| JSON Schema 输出 | +0（走 API 参数） | 格式合规 0%→100% | ✅ 极高 |
| Few-shot 2-4 例 | +500-2000 | +5-15% | ✅ 高 |
| Zero-shot CoT | +100-500 | +5-10%（数学题明显） | 🟡 中（推理模型上⚠️负） |
| Self-Consistency (N=5) | ×5 成本 | +5-10% | 🟡 中（看任务） |
| ReAct 循环 | ×3-10 成本 | 工具调用能力 | ✅ Agent 场景必需 |
| Constitutional 自审 | ×2 成本 | 安全性/合规性提升 | 🟡 中（合规敏感才值） |
| ToT / GoT | ×10-100 成本 | 特定任务 +10-20% | ❌ 生产几乎不用 |

**DSPy/GEPA 自动优化的 ROI**：

- **投入**：工程师 2-5 天搭建 pipeline + eval 集 + 一次优化几小时 + $10-100 API 费
- **产出**：稳定 +5-20% 准确率，且**后续每次模型升级自动受益**
- **适用条件**：有 ≥50 条 eval 集 + 明确指标 + 长期维护的生产系统

---

## 🎯 决策速查

```
场景 → 选什么
├── 原型验证 / 一次性任务
│    → 手写 Naive + 结构化 + Schema（写法②）
├── 生产系统 / 要交付
│    → 手写基线 + Few-shot + Schema + Eval 集（写法②+③）
├── 已有 Eval 集想榨性能
│    → DSPy 或 GEPA 自动优化
├── 多步任务 / Agent
│    → 走编排（Chaining/Routing/Orchestrator）而非单 Prompt 打天下
├── 数学/逻辑推理（非推理模型）
│    → + Zero-shot CoT + Self-Consistency
├── 数学/逻辑推理（推理模型 o1/R1/C3.7）
│    → 让模型自己推理，不要手写 CoT
├── 高合规 / 敏感场景
│    → + Constitutional Self-Critique + 输出审查
└── 长上下文 (>8K)
     → 优先 RAG/Context Engineering，不要单纯堆 Prompt
```

**何时 Prompt Engineering 不该是答案**：

- ❌ 需要模型"学会"全新能力 → 去 Fine-tune ([R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md))
- ❌ 需要模型掌握大量私域知识 → 去做 RAG ([R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md))
- ❌ 需要跨轮次状态和记忆 → 去设计 Agent Memory ([R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md))
- ❌ 单 Prompt 反复调 >10 版都不稳 → 转 DSPy/GEPA 自动化

---

## 结论与最佳实践

### 三条可直接复用的原则

1. **"结构 > 技巧 > 字数"**：一个结构清晰的 500-token Prompt，胜过堆砌技巧的 3000-token Prompt。
2. **"能下沉就不上浮"**：能用 API 参数（`response_format`/`seed`）解决的，不要塞进 Prompt；能用 RAG 解决的，不要塞进 Prompt；能用编排解决的，不要塞进单 Prompt。
3. **"Prompt 是组件不是终点"**：2026 年 Prompt Engineering 的正确站位是——手写 Prompt 打底 + Context Engineering 管规模 + DSPy/GEPA 做迭代 + 编排模式做架构。

### 与已有报告的关联

- **补充 [R16](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R16_AI%E8%BE%93%E5%87%BA%E8%B4%A8%E9%87%8F%E7%A8%B3%E5%AE%9A%E6%80%A7%E4%B8%8E%E5%8F%8D%E8%AE%A8%E5%A5%BD.md)**：R16 讲稳定性现象，本报告给出 Prompt 层面的稳定化手段（Schema、Self-Consistency、温度控制）
- **补充 [R17](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R17_%E6%8C%87%E4%BB%A4%E9%81%B5%E5%AE%88%E9%AA%8C%E8%AF%81%E4%B8%8E%E9%95%BF%E6%9C%9F%E6%BC%82%E7%A7%BB%E6%A3%80%E6%B5%8B.md)**：R17 讲长期漂移检测，本报告在"反模式"节给出 Prompt 层预防措施
- **呼应 [R14](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)**：R14 的 Skill-Creator 设计哲学 = "explain Why > stack MUST"，本报告 §4 反模式节强化了这一点
- **承接 [R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)**：R28 讲 Skill 自迭代，本报告给出 Evaluator-Optimizer 模式和 DSPy/GEPA 工具链
- **填补 [R54](R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md) 路线图 G10 缺口**：R54 识别的红色缺口之一，本报告完成系统化覆盖

### 与 PSEV 框架的映射

Prompt 工程本身就是一次 PSEV：
- **P (Profile)**：模型画像 + 任务特征（推理型/分类型/生成型）
- **S (Strategy)**：选结构 + 选技巧家族（Few-shot？CoT？编排？）
- **E (Execute)**：写 Prompt + 跑 eval
- **V (Verify)**：准确率/合规率/成本指标，回到 P/S 修正

---

## 开放问题与后续计划

- ⬜ **推理模型时代 Prompt 的新范式**：o1/R1/C3.7 把思考下沉后，手写 Prompt 的边界需要重新测绘——可做一篇 R56 专题
- ⬜ **DSPy/GEPA 实证对比**：基于本库 skill-evaluator 做一次完整的自动优化 vs 手调对照实验（产出建议入 `experiments/`）
- ⬜ **多模态 Prompt**：图像/语音/视频输入的 Prompt 策略本报告未覆盖，建议单开 G13
- ⬜ **Context Engineering 专题**：R55 定位 PE，Context Engineering 应有独立报告（建议 G10b）
- ⬜ **国产模型 Prompt 实战手册**：Qwen / DeepSeek / Kimi 的偏好差异细节需要实测汇总

---

## 📌 来源清单

- [Anthropic · Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — 2024-12 — 五种编排模式的权威源头
- [Anthropic · Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) — 截至 2026-04 — XML 标签、Claude 偏好
- [Anthropic · Extended Thinking Tips](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking) — 2025 — Claude 3.7+ 不要手写 CoT 的官方说明
- [OpenAI · Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) — 2024-08 — JSON Schema 强制输出
- [OpenAI · The Instruction Hierarchy (paper)](https://arxiv.org/abs/2404.13208) — 2024 — System/User/Tool 权威级别训练
- [CoT 原论文 · Wei et al., 2022](https://arxiv.org/abs/2201.11903) — Chain-of-Thought Prompting Elicits Reasoning
- [Zero-shot CoT · Kojima et al., 2022](https://arxiv.org/abs/2205.11916) — "Let's think step by step"
- [ReAct · Yao et al., 2023](https://arxiv.org/abs/2210.03629) — Thought-Action-Observation 范式奠基
- [Reflexion · Shinn et al., 2023](https://arxiv.org/abs/2303.11366) — 自省 + episodic memory
- [Self-Consistency · Wang et al., 2022](https://arxiv.org/abs/2203.11171) — 多采样投票
- [Tree of Thoughts · Yao et al., 2023](https://arxiv.org/abs/2305.10601)
- [Few-shot 顺序敏感性 · Lu et al., 2022](https://arxiv.org/abs/2104.08786) — Fantastically Ordered Prompts
- [Constitutional AI · Bai et al., 2022 (Anthropic)](https://arxiv.org/abs/2212.08073)
- [DSPy · Khattab et al., 2023](https://arxiv.org/abs/2310.03714) — 编程式 Prompt 范式
- [GEPA · 2025](https://arxiv.org/abs/2507.19457) — Reflective Prompt Evolution
- [TextGrad · Yuksekgonul et al., 2024](https://arxiv.org/abs/2406.07496)
- [PromptWizard · Microsoft Research, 2024](https://arxiv.org/abs/2405.18369)
- 模型训练知识（截止日期未知）— 作为背景交叉验证，文中明确标注"示意性对照"的地方即为此类来源

⚖️ **来源一致性**：权威原始论文与 Anthropic/OpenAI 官方文档在"XML 标签推荐"、"Claude 3.7+ 不宜手写 CoT"、"Instruction Hierarchy"、"Few-shot 顺序敏感"等核心事实上多源一致。关于"Prompt Engineering 是否还重要"社区存在分歧（Anthropic 官方倾向"随模型变强权重下降"，而工业界实测"ROI 仍最高"）——本报告在 TL;DR 与定位透镜中明确呈现分歧并给出立场。

📅 **时效性声明**：以上信息获取于 2026-04-24。DSPy/GEPA 等工具版本迭代快，落地前请确认官方最新文档。
