---
title: Crazy A2A 通用 Agent Team 平台北极星与王牌集成路线
aliases: [R151, Crazy A2A 北极星, 通用 Agent Team 平台]
tags: [agent, harness, a2a, mcp, open-source, architecture, roadmap]
date: 2026-07-16
category: 工具与生态
report_id: R151
status: completed
related:
  - "[R148](R148_%E5%BC%80%E6%BA%90AgentHarness%E6%A8%AA%E8%AF%84_OpenClaw_Hermes%E4%B8%8E%E5%85%AD%E7%B1%BB%E9%AB%98%E5%85%89%E6%9C%BA%E5%88%B6.md)"
  - "[R149](R149_OpenClaw%E4%B8%8EHermes%E5%9B%9B%E5%A4%A7Harness%E4%BA%AE%E7%82%B9%E6%BA%90%E7%A0%81%E6%B7%B1%E6%8B%86_%E5%AF%B9%E6%AF%94ClaudeCode.md)"
  - "[R150](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R150_AgentMemory%E4%B8%8EDream%E5%88%86%E9%A1%B9%E5%86%A0%E5%86%9B%E8%9E%8D%E5%90%88%E8%AE%BE%E8%AE%A1.md)"
  - "[R142](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R142_LoopEngineering%E5%BE%AA%E7%8E%AF%E5%B7%A5%E7%A8%8B%E8%B0%83%E7%A0%94.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Crazy A2A 通用 Agent Team 平台北极星与王牌集成路线

> **一句话结论**：Crazy A2A 应采用“自研确定性 Kernel + 公开 Protocol + 可替换 Champion Adapter”，而不是直接嵌套 OpenClaw、Hermes、OpenHands、Letta 等多套 Agent Loop；第一里程碑先证明真实单 Agent，再用同任务对照决定 Team、Memory 和 Evolution 是否值得成为默认能力。

> **已有基础与本次增量**：R148 已完成八类 Harness 横评，R149 深拆 OpenClaw/Hermes 四个高光机制，R150 固定六家 Memory/Dream 源码。本报告新增统一集成原则、目标架构、Golden Task、7 阶段实施路线、GitHub 发布策略与明确准出。

## 1. 定位透镜

### 纵向：项目从学习内核走向公开产品

1. v0.1 已证明 Event、Candidate、Mailbox、Scheduler、Context、Memory 和 Chaos 机制能运行。
2. 下一阶段不是继续扩展示意机制，而是把 Scripted Provider 和固定 Team 链路替换为真实 LLM、真实 Tool 和动态 Orchestration。
3. 公开 Beta 必须让陌生用户五分钟内完成真实任务，并能从 Story View 下钻到 Trace。

### 横向：和现有项目的差异

| 项目 | 强项 | Crazy 不与其正面重复的地方 |
|---|---|---|
| OpenClaw | 常驻个人 Agent 产品、渠道与 Gateway | 不重做几十种渠道，学习 Gateway-first 与隔离 |
| Hermes | 学习循环、Skill、PTC、多执行后端 | 不引入其 Loop，学习 Candidate 化学习与代码化 Tool Chain |
| OpenHands | 类型化事件与 Workspace | 不成为 Coding-only SDK，吸收 Runtime 契约 |
| mini-SWE-agent | 极薄 Loop 与公开 Benchmark | 永久保留为复杂度反方和同任务基线 |
| Letta/Hindsight/Graphiti | 不同深度的长期记忆 | Crazy 保留唯一 Memory Authority，外部系统只作 Adapter |
| LangGraph | 持久图编排 | 不让显式 DAG 取代动态 Team Policy |

交叉判断：Crazy 的差异化不是“功能最多”，而是 **模型提议与系统事实边界显式、Team 可崩溃恢复、行为变化先评测后晋升、全部过程可解释**。

## 2. 三种吸收方式

| 方式 | 何时使用 | 例子 |
|---|---|---|
| Pattern | 核心不变量值得学，但不能引入对方 Loop | OpenClaw Gateway、Letta Git HEAD 生效 |
| Adapter | 能力成熟且替换成本可控 | Daytona、Browser Use、Hindsight、Langfuse |
| Protocol | 需要跨实现互操作 | MCP、A2A 1.0、OpenTelemetry GenAI |

核心禁令：外部组件不能绕过 ControlKernel 写 Event、Memory 或执行高风险副作用。

## 3. 分项冠军地图

| 模块 | 默认路线 | 标杆来源 |
|---|---|---|
| 常驻入口 | 原生 Gateway、确定性身份路由 | OpenClaw |
| Agent Loop | 原生 Contract/Plan/Progress/Nudge/Gate | Claude Code/Hermes 思路 + mini-SWE baseline |
| 事件与恢复 | 强类型 Event、Mailbox、Ledger | OpenHands + Crazy v0.1 |
| Tool/Skill | CapabilityCompiler + MCP + Agent Skills | MCP、Anthropic Skills |
| 沙箱 | Docker Local，Daytona/E2B 可选 | OpenHands、Daytona、E2B |
| 浏览器 | Playwright 确定性 Tool，Browser Use 隔离 Worker | Browser Use |
| A2A | 内部丰富领域事件，外部 A2A 1.0 Adapter | A2A Project |
| Memory | Native Candidate Authority，Hindsight A/B | Hindsight、Letta、Graphiti |
| Dream | Durable Job + frozen evidence + read-only reflect | Hindsight、Honcho、Hermes |
| Eval | Native EvalCase + Inspect AI Bridge | Inspect AI、mini-SWE-agent |
| Evolution | Offline GEPA/DSPy -> Candidate/PR -> Gate | Hermes Self-Evolution |
| Observability | EventLog 真相 + OTel 公共语义 + Langfuse 可选 | OpenTelemetry、Langfuse |

## 4. 通用性的真实边界

“通用”限定为明确工具和权限下的知识工作：代码仓库、网页研究、文档数据、模拟运维和外部系统协作。它不等于无工具的任意任务，更不等于无人监管的生产操作。

通用性由 TaskPack 提供：Task Schema、Capability、Team Template、Completion Contract、Policy Profile、Eval Cases。World Adapter 只翻译外部世界，不能决定完成。

## 5. 实施优先级

1. Phase 0：公开工程地基与 License Matrix。
2. Phase 1：DeepSeek 真实单 Agent 修复 toy repo Bug。
3. Phase 2：MCP、Skill、Browser 与通用 Capability。
4. Phase 3：动态 Team、并发、Crash Recovery、A2A 1.0 Remote Agent。
5. Phase 4：Context、Native Memory、Dream、Hindsight A/B。
6. Phase 5：Inspect Eval、Shadow/Canary/Rollback、GEPA 候选。
7. Phase 6：Story View、一键部署、三个 Demo、GitHub Beta。

完整计划位于：`E:\LLM\AI\Crazy\docs\GENERAL_AGENT_TEAM_MASTER_PLAN.md`。

## 6. 第一里程碑

> DeepSeek 能否在 disposable repo 中，依靠 Crazy 的真实 Loop 和 read/search/patch/test 工具，修复一个未知 Bug，并由测试与 Evidence 而不是模型自述证明完成？

在该问题通过前，不引入 Graphiti、分布式 Broker、云沙箱或更多 Agent。这个约束防止项目再次变成“机制地图很完整，但用户不知道它能做什么”。

## 7. 开源判断

- 高星不能承诺，Star 不作为工程 KPI。
- 当前目录不能原样公开；`research_sources/`、飞书原文、Obsidian、本地 runs、个人路径和凭据必须隔离。
- 对外真正可传播的故事应是：真实任务、可读 Story、可展开 Trace、Kill-Restart 不丢任务、Single/Team 对照、行为变更可回滚。
- 建议 Apache-2.0，最终发布前确认；所有上游代码级借鉴进入 License Matrix 与 THIRD_PARTY_NOTICES。

## 8. 风险与限制

- 多 Agent 可能增加 Token、延迟和协调错误，因此 Single Agent 是永久基线。
- Memory/Dream 可能负提升，因此必须记录 harmful recall 和人工撤回。
- 常驻高权限 Agent 扩大 Prompt Injection、恶意 MCP/Skill 和 Secrets 风险，默认必须 fail-closed。
- agentgateway、Langfuse、Hindsight、云沙箱都只能是可选 Profile，不得破坏本地 Quickstart。
- 上游 README 的 Benchmark 和性能声明只作为候选证据，不等于 Crazy 的实测结果。

## 9. Sources and freshness

检索日期：2026-07-16。

- [OpenClaw](https://github.com/openclaw/openclaw)
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [OpenHands Software Agent SDK](https://github.com/OpenHands/software-agent-sdk)
- [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent)
- [Anthropic Agent Skills](https://github.com/anthropics/skills)
- [MCP](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [A2A 1.0](https://github.com/a2aproject/A2A/blob/main/docs/specification.md)
- [agentgateway](https://github.com/agentgateway/agentgateway)
- [Browser Use](https://github.com/browser-use/browser-use)
- [Daytona](https://github.com/daytonaio/daytona)
- [Hindsight](https://github.com/vectorize-io/hindsight)
- [Letta Code](https://github.com/letta-ai/letta-code)
- [Graphiti](https://github.com/getzep/graphiti)
- [OpenTelemetry GenAI](https://github.com/open-telemetry/semantic-conventions)
- [Langfuse](https://github.com/langfuse/langfuse)
- [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai)
- [Hermes Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution)

一致性：多源一致支持协议化边界、隔离执行、持久状态和评测优先。  
待验证：DeepSeek 真实 Tool Calling、Windows Docker、A2A 1.0 Python SDK、Memory Adapter 的净收益。

## 10. 设计审查

设计审查：5/5 通过。外部依赖入口已核对；性能和周期均标预估；异常路径进入阶段准出；统计阈值留待实测；范围限定在通用工具任务平台。
