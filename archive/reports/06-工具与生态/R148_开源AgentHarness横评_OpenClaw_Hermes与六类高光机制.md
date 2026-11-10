---
title: 开源 Agent Harness 横评：OpenClaw、Hermes 与六类高光机制
aliases: [R148, 开源Harness横评, OpenClaw Hermes 对比, Agent Harness 面试对比]
tags: [agent, harness, openclaw, hermes, openhands, mini-swe-agent, letta, langgraph, goose, interview]
date: 2026-07-14
category: 工具与生态
report_id: R148
status: completed
related:
  - "[R34](R34_HermesAgent%E5%BC%80%E6%BA%90%E8%87%AA%E5%AD%A6%E4%B9%A0%E6%99%BA%E8%83%BD%E4%BD%93.md)"
  - "[R35](R35_HermesAgent%E8%AE%B0%E5%BF%86%E4%B8%8ESkill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%BA%90%E7%A0%81%E6%8B%86%E8%A7%A3.md)"
  - "[R36](R36_OpenClaw%E6%9E%B6%E6%9E%84%E8%B0%83%E7%A0%94%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%99%E4%B9%88%E7%81%AB.md)"
  - "[R41](R41_OpenClaw%E6%9E%B6%E6%9E%84%E5%AD%A6%E4%B9%A0%E8%B0%83%E7%A0%94.md)"
  - "[R71](R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md)"
  - "[R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)"
  - "[R142](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R142_LoopEngineering%E5%BE%AA%E7%8E%AF%E5%B7%A5%E7%A8%8B%E8%B0%83%E7%A0%94.md)"
  - "R146（原稿交叉引用，本归档未解析）"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# 开源 Agent Harness 横评：OpenClaw、Hermes 与六类高光机制

> **一句话结论**：不存在一个项目在所有 Harness 模块都最强；OpenClaw 把常驻控制平面做成产品，Hermes 把记忆与 Skill 学习循环接进主路径，OpenHands 把事件和隔离运行时做成可扩展 SDK，mini-SWE-agent 用极薄 Loop 和真实评测证明“复杂不等于强”，Letta 深挖长期记忆，LangGraph 深挖持久编排，Goose/OpenCode 则代表能力生态和交互产品化。

> **已有基础与本次增量**：R34/R35 已拆 Hermes，R36/R41 已拆 OpenClaw，R71/R72 已横评 Coding Agent 与 Memory。本报告不重复功能清单，新增统一六模块坐标、对 Crazy Harness 的真实差距、面试说法与可验证的吸收顺序。

## 1. 先把项目放对位置

**结论：面试时先讲定位，再讲功能；否则会把产品、SDK、研究 Harness 和编排框架混在一起。**

| 项目 | 更准确的定位 | 最突出的 Harness 高光 |
|---|---|---|
| OpenClaw | 本地优先、常驻的个人 Agent 产品与控制平面 | Gateway、渠道接入、Agent/Session 隔离、工具策略、沙箱、自动化 |
| Hermes Agent | 可跨会话学习的个人 Agent 产品 | 有界 Memory、Skill 自生成/改进、后台复盘、Prompt Cache、多执行后端 |
| OpenHands | 软件 Agent SDK、Agent Server 与控制面 | 类型化事件、Action/Observation、隔离 Workspace、远程运行、自动化 |
| mini-SWE-agent | 极简 Coding Agent 与研究/评测基线 | 约百行 Loop、仅 Bash、线性轨迹、独立命令执行、SWE-bench 验证 |
| Letta Code | Memory-first 长寿命 Agent | Memory Blocks、Git 化 MemFS、睡眠期整理、自改 Context、跨 Agent Recall |
| LangGraph | 持久化 Agent 编排 Runtime | Checkpoint、Store、Interrupt、Time Travel、Subgraph 持久化 |
| Goose | MCP-first 通用本地 Agent | MCP 扩展生态、Code Mode 延迟发现工具、Recipe/Subrecipe |
| OpenCode | 开源 Coding Agent 产品 | Provider 无关、LSP、TUI、Client/Server、Plan/Build 权限分层 |

### 纵向：成熟路径

1. SWE-agent/mini-SWE-agent 从研究问题出发：怎样用最少 Scaffold 公平测模型。
2. OpenHands/LangGraph 从 Runtime 出发：怎样持久、隔离、扩展和恢复执行。
3. OpenClaw/Hermes/Letta 从长寿命产品出发：Agent 怎样常驻、记住、跨入口工作。
4. Goose/OpenCode 从开发者产品出发：怎样把工具生态和交互体验做得可日用。

### 横向：设计哲学

| 哲学 | 代表 | 核心取舍 |
|---|---|---|
| Fat Runtime | OpenClaw、OpenHands | 更多运行时能力换来产品完整度，也扩大配置与安全面 |
| Learning Agent | Hermes、Letta | 让 Memory/Skill 随使用演进，但必须治理错误学习和额外 Token 成本 |
| Thin Harness | mini-SWE-agent | 把能力尽量交给模型和 Bash，获得可读性与可复现性，牺牲长期状态和治理 |
| Explicit Graph | LangGraph | 以状态图换取可恢复和 HITL，复杂任务容易退化为固定工作流 |
| Capability Ecosystem | Goose、OpenCode | 优先扩展性与日用体验，核心创新不一定在 A2A 或 Memory |

## 2. 每个项目真正过人之处

### 2.1 OpenClaw：把 Agent 变成常驻控制平面

**结论：OpenClaw 的优势不是新 Loop，而是把 Loop 放进了真正可长期运行、可接入、可治理的产品壳。**

- Gateway 是常驻控制平面，统一承载渠道连接、RPC/HTTP、控制台、Hooks 与路由。
- 每个 Agent 有独立 workspace、状态目录、认证资料和 SQLite Session；Bindings 把渠道、账号和用户确定性路由到 Agent。
- Agent-to-Agent 默认关闭，需要显式开启和 allowlist；Subagent 默认独立上下文，确有需要才 fork 父上下文。
- Tool Policy、Sandbox、Elevated、Exec Approval 是不同控制层；工具在模型调用前就会被过滤。
- Context 同时有 Tool Result Pruning 与 Full Compaction；完整历史仍在磁盘，接近窗口时摘要，旧工具结果可只做内存裁剪。
- Tool Search、Tokenjuice、Skill/Plugin/Hook、Cron、后台任务和多渠道已经形成完整生态。

**超过 Crazy Harness 的地方**：24x7 进程、真实渠道、原生客户端、配置热加载、分层安全、Agent 隔离、工具生态和运维面都远成熟于我们的单机教学 MVP。

**不能混淆的地方**：OpenClaw 的“多 Agent”很大一部分是隔离路由和父子委派，不等同于我们定义的“Coordinator + 持久 Mailbox + 事件驱动 Team”。它的 workspace 也不是天然硬沙箱，官方文档明确要求另开 sandbox 才能形成边界。

### 2.2 Hermes：把学习循环接进每次使用

**结论：Hermes 最值得学的是 Memory 与 Skill 的分工，以及学习写入可以被暂存、审查和拒绝。**

- `MEMORY.md` 与 `USER.md` 是有字符上限的小型常驻事实；Skill 是按需加载的长流程知识，遵循 Progressive Disclosure。
- Memory 在 Session 开始时以冻结快照注入，Session 内写盘但不改旧前缀，以保护 Prompt Cache。
- 后台复盘会从成功、踩坑和纠正中提出 Memory/Skill 改动；`write_approval` 可把改动暂存到 pending，人工看 diff 后批准。
- Context 有 Agent 内主压缩和 Gateway Session Hygiene 两层保护；Prompt Cache、Provider fallback、辅助模型路由都进入真实主路径。
- Subagent 有独立 Conversation、Terminal 和 Toolset，只把最终摘要返回父上下文；也支持并发、模型降级和深度限制。
- 轨迹导出、批处理和 RL 数据生成，使“使用数据 -> 训练/改进模型”成为可操作接口。

**超过 Crazy Harness 的地方**：我们的 Candidate/Approval 是机制样例；Hermes 已把记忆、Skill、后台复盘、缓存、多 Provider、多执行后端、Gateway 和轨迹数据连成日用产品。

**风险边界**：官方默认允许 Agent 直接写 Skill，只有开启 `write_approval` 才强制审查；后台学习是否正提升仍需 Eval。普通 `delegate_task` 还是同步委派，父轮被打断时子任务会取消，不是持久 Mailbox。

### 2.3 OpenHands：事件化 Runtime 的工程完成度

**结论：OpenHands 最像我们 EventLog 理念的工业化版本。**

- Event 是不可变的 Pydantic 类型，组成 append-only log，同时驱动状态、LLM 消息转换和旁路服务。
- `ActionEvent`、`ObservationEvent`、`AgentErrorEvent`、`ConversationErrorEvent` 明确区分模型动作、环境事实、可恢复错误和运行级错误。
- `Event.source` 与 LLM `role` 分离，能区分真实用户输入和 Harness 注入的伪 user 消息。
- Condenser、并行工具、Tracing、Metrics、Security Confirmation 已进入 SDK 组件。
- Agent Server 可在 Docker、VM、Kubernetes 或远程 API Workspace 运行，通过 WebSocket 推送事件；同一 SDK 在本地和远程只换 Workspace。

**超过 Crazy Harness 的地方**：类型系统、远程隔离、运行生命周期、扩缩容、观察面、SDK 可组合性和真实 Coding Agent 场景都更完整。

**边界**：它的主场仍是软件开发 Agent；跨任务长期人格 Memory、常驻多渠道和我们强调的受控 A2A Team 不是它最突出的卖点。

### 2.4 mini-SWE-agent：对“Harness 越多越强”的反证

**结论：mini-SWE-agent 是这次横评里最应该认真对待的反方。**

- 核心 Agent 类约百行，只有 Bash，不依赖模型原生 Tool Calling。
- History 线性追加，轨迹就是实际发给模型的消息，便于调试、微调和公平对比。
- 每次命令用独立 `subprocess.run`，比持久 Shell 更容易替换成 Docker 执行并批量扩展。
- 官方报告在 SWE-bench Verified 上达到 74% 以上；关键价值不是单个数字，而是结果来自固定任务集与可复现 Harness。

**超过 Crazy Harness 的地方**：它有大规模公开任务和量化结果，能证明“这些默认值有效”；我们的机制更多，但尚未证明每个机制带来净提升。

**边界**：它主动放弃了持久状态、Memory、A2A、复杂权限和长程 Context 治理，因此是优秀基线，不是常驻 Team Runtime。

### 2.5 Letta：Memory 成为 Agent 的核心状态

**结论：Letta 把我们目前的 Memory 治理样例扩展成了完整的长寿命 Agent 产品。**

- Memory Blocks 是 Agent 可更新的常驻 Context；外部存储负责更大量的可召回内容。
- MemFS 把 Context/Memory 映射到 Git 管理的文件，支持版本、审计、直接编辑和跨环境同步。
- Sleeptime/Dreaming 用后台 Agent 整理 Memory 和 Skill；内置 Recall、History Analyzer 等 Subagent。
- 同一个 Agent 可从 CLI、桌面、浏览器和消息渠道继续工作。

**超过 Crazy Harness 的地方**：Memory 的可视化、版本化、跨入口连续性和后台维护已产品化。

**风险边界**：自动改写 Context 容易把误判长期化，后台模型调用有持续成本；必须用候选、证据、冲突、TTL、回归集和人工抽检约束。旧 `letta-ai/letta` 仓库已标注为 legacy，活跃开发迁往 Letta Agent/Letta Code，面试时不要把旧架构当最新实现。

### 2.6 LangGraph：持久暂停、恢复和人工介入

**结论：LangGraph 的长处不是“会画图”，而是 Checkpoint 语义已经覆盖恢复、HITL 和 Time Travel。**

- Checkpointer 保存线程内图状态，Store 保存跨线程长期数据。
- `interrupt()` 可持久暂停并等待外部审批；恢复时从持久状态继续。
- Time Travel 可 replay 或 fork 历史 checkpoint；Subgraph 可选 per-invocation、per-thread 或 stateless。
- PostgreSQL/SQLite 等持久适配器减少自建恢复层工作量。

**超过 Crazy Harness 的地方**：我们的 JSONL + Reducer 用来理解原理；LangGraph 已把持久暂停、状态检查、分支重放和存储后端做成通用 Runtime。

**风险边界**：显式图很容易把智能编排写成固定 DAG；节点恢复还要求调用方理解幂等性，Checkpoint 并不会自动消除外部副作用重复执行。

### 2.7 Goose 与 OpenCode：能力生态和日用体验

**结论：这两者提醒我们，Harness 不只是一套正确机制，还必须让能力易发现、易组合、易使用。**

- Goose 以 MCP 扩展为主，Code Mode 只向模型暴露少量元工具，按需发现具体工具，并在一段代码中批量调用、串联中间结果；Recipe 可封装目标、Prompt、扩展与 Subrecipe。
- OpenCode 强在 Provider 无关、LSP、TUI、Client/Server 和 Plan/Build 权限分层，说明 Agent 核心与交互客户端可以解耦。

**超过 Crazy Harness 的地方**：工具生态、渐进式披露、桌面/终端体验、配置与分发成熟度。

**风险边界**：Goose 官方文档提示默认 Developer 扩展可按当前用户权限执行命令和改文件；MCP 多不等于安全。OpenCode 的高光主要在 Coding UX，不等于它解决了持久 Team 或 Memory 治理。

## 3. 投影到六大 Harness 模块

**结论：每个模块都应找一个“标杆项目”，不要拿一个项目当全部答案。**

| 我们的六问 | 当前最值得看的标杆 | 应学什么 |
|---|---|---|
| LLM 如何和物理世界交互？ | OpenHands、OpenClaw、Goose | Typed Tool、Sandbox、Policy、Approval、MCP 延迟发现、远程 Workspace |
| LLM 如何持续行动并完成长任务？ | mini-SWE-agent、OpenHands、LangGraph | 最小 Loop、Action/Observation、Checkpoint、Interrupt、幂等恢复 |
| LLM 每轮看什么？ | Hermes、OpenClaw、OpenHands | Frozen Prefix、Prompt Cache、Pruning、Compaction、Condenser、Tool Search |
| LLM 跨任务记什么？ | Hermes、Letta | Fact/Procedure 分离、有界 Memory、Skill、后台复盘、Git 版本和写入审批 |
| 多 LLM 如何协作？ | OpenClaw、Hermes、LangGraph | 隔离 Session、Brief/Final Summary、并发上限、深度限制、Subgraph 持久策略 |
| 如何证明改动更好？ | mini-SWE-agent、OpenHands | 固定任务集、Trajectory、可复现配置、Sandbox Eval、成本与成功率共同度量 |

## 4. Crazy Harness 的真实位置

**结论：我们的优势是“机制广、边界清、适合内化”；成熟项目的优势是“某一纵深真的跑过规模和用户”。**

### 我们值得保留的独特价值

1. Model Response -> Validated Command -> Authorized Operation -> Observation 的信任边界讲得非常显式。
2. Contract、Plan、Progress、Nudge、CompletionGate 把长程任务控制拆成可解释职责。
3. Context 每轮编译，Offload、Microcompact、Full Compact 分层，而不是无脑追加 History。
4. A2A 用 Brief + Refs + Schema，普通 Agent 只允许受控一跳；Coordinator 掌握全局编排。
5. Memory 与 Harness 改动先成为 Candidate，再经过证据、Scope、冲突、Eval 和版本门。
6. 所有机制都能落到自己可单步调试的代码，不被框架 API 隐藏。

### 目前明显落后的地方

| 维度 | Crazy Harness 当前状态 | 成熟项目领先点 |
|---|---|---|
| 真实 Runtime | GuardedLocalRuntime，不等于硬沙箱；Docker 未验证 | OpenHands/OpenClaw 的容器、远程 Workspace 和多层 Policy |
| 常驻产品 | 本地 Mailbox/Scheduler MVP | OpenClaw/Hermes 的 Gateway、渠道、Cron、控制台和运维 |
| Context | 主路径有 Microcompact/Offload；Full Compact 未自动接入 | Hermes/OpenClaw/OpenHands 的双层压缩、缓存、Condenser 与插件引擎 |
| Memory | 组件场景可运行 | Hermes/Letta 的日用写入、Recall、版本、后台维护和 UI |
| A2A | Team 场景跑通，Schema 校验和并发未完全端到端 | 成熟项目的并发、隔离、模型降级、深度与生命周期控制 |
| Eval | 确定性样例，未做真实 DeepSeek 重复采样 | mini-SWE-agent/OpenHands 的公开任务、批量轨迹和可复现基准 |
| 生态 | 少量 Tool/Skill/MCP 示例 | OpenClaw/Goose/OpenCode 的市场、扩展、客户端和 Provider 适配 |

所以不能说“我们比它们完整”。更准确的说法是：**我们在一个小项目中建立了完整认知地图和关键控制边界，但每个成熟项目都在自己的主战场把其中一两层做得更深。**

## 5. 最值得吸收的四步，不照搬整个项目

**结论：先用实验挑战自己的设计，再加复杂度。**

1. **mini-SWE-agent 对照实验**：同一组 CI/CD 故障任务跑 Thin Loop 与 Crazy Harness，比较成功率、Token、工具次数、延迟、提前停止和越权次数。
2. **OpenHands Runtime 化**：把 Event 改为强类型不可变对象，明确 `source` 与 LLM 可见性；补真正 Docker/远程 Workspace。
3. **OpenClaw/Hermes 常驻化**：增加单一 Gateway、per-agent SQLite 状态和 deterministic bindings；Memory/Skill 写入走 pending diff 审批。
4. **Letta 式 Memory 审计**：Memory 文件 Git 版本化，再用固定 Recall 问题、冲突案例和人工抽检验证异步蒸馏是否负提升。

每新增一个机制都做 ablation：关闭它跑一次，开启它再跑一次。没有稳定收益的机制不应进入默认 Harness。

## 6. 面试可直接说

### 30 秒版本

> 我不会把 OpenClaw、Hermes、OpenHands 和 LangGraph简单排强弱，因为定位不同。OpenClaw 是常驻个人 Agent 的控制平面，强在 Gateway、渠道、隔离和工具治理；Hermes 强在有界记忆、按需 Skill 和后台学习；OpenHands 强在类型化 Event、Action/Observation 和隔离 Runtime；mini-SWE-agent 则用百行 Loop 和 SWE-bench 提醒我们，Harness 不是越厚越好；Letta 与 LangGraph分别代表 Memory-first 和 durable orchestration。我的手搓项目主要价值是把这些机制放进同一个可调试骨架，明确模型建议与 Harness 事实的边界。它覆盖面广，但在沙箱、生态、真实评测和产品运行深度上还不如这些成熟项目。

### “为什么不用现成框架？”

> 生产项目我会选成熟 Runtime，但这个项目的目标是掌握控制权在哪里。手搓以后，我能解释 Response 为什么不能直接执行、Crash Recovery 为什么区分模型响应和外部副作用、Context 为什么每轮编译、Memory 为什么先候选后晋升、A2A 为什么传 Brief/Refs/Schema。框架可以节省代码，但也会隐藏这些设计决定。

### “OpenClaw/Hermes 最值得借鉴什么？”

> OpenClaw 借 Gateway、per-agent 隔离、Bindings 和分层权限；Hermes 借 Fact Memory 与 Procedural Skill 分离、Frozen Prefix、Prompt Cache、后台 Review 和 write-approval。两者都不应该原样抄：OpenClaw 的常驻高权限扩大攻击面，Hermes 的自动学习必须由 Eval 和人工闸门约束。

### “你的方案有什么不同？”

> 我们更强调受控 Team：Coordinator 根据事件和 AgentCard 动态委派，普通 Agent 只能受控一跳对账，双方不共享完整 Context，只传 Brief、Artifact Ref 和 Schema；再用 Persistent Mailbox 保存跨进程状态。这个设计比普通 Subagent 返回摘要更强调长期协作语义，但目前只是 MVP，还缺真实并发、分布式 Broker 和规模评测。

## 7. 风险与开放问题

**结论：开源项目的 README 能证明“实现了什么”，不能单独证明“长期效果一定更好”。**

- “Self-improving”是否正提升，必须看固定 Eval、长期回归、误记率、人工撤回率和成本，不接受营销措辞替代证据。
- GitHub Stars 是热度信号，不是 Harness 质量指标；本报告不按 Stars 排技术结论。
- OpenClaw/Hermes 的高权限常驻形态，攻击面显著大于一次性 Coding Agent；Prompt Injection、恶意 Skill/MCP、Secrets 和宿主机权限都要单独测。
- A2A 的公开评测仍弱于单 Agent Coding Benchmark；“多个 Agent”可能只是增加 Token 和协调失败。
- Crazy Harness 下一阶段最缺的不是新模块，而是同任务、同模型、同预算的 ablation 数据。

## 8. Sources and freshness

检索日期：2026-07-14。以下均为官方仓库、官方文档或项目论文。

- [OpenClaw 官网](https://openclaw.ai/)：常驻、本地优先、多渠道产品定位。
- [OpenClaw Gateway](https://docs.openclaw.ai/gateway)：常驻控制平面、端口、认证和运行模型。
- [OpenClaw Multi-agent routing](https://docs.openclaw.ai/concepts/multi-agent)：per-agent 隔离、Bindings、A2A 默认关闭。
- [OpenClaw Sub-agents](https://docs.openclaw.ai/subagents)：isolated/fork Context、后台任务与工具限制。
- [OpenClaw Compaction](https://docs.openclaw.ai/compaction)：摘要、磁盘历史、Pruning 区别。
- [OpenClaw Tools](https://docs.openclaw.ai/tools)：Tool/Skill/Plugin、Policy 与 Tool Search。
- [Hermes Agent 官方仓库](https://github.com/NousResearch/hermes-agent)：产品能力、版本、迁移与入口。
- [Hermes Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/)：有界 Memory、Frozen Snapshot、后台 Review。
- [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)：Progressive Disclosure、自建 Skill、Write Approval。
- [Hermes Context Compression](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching/)：双层压缩与可插拔 Context Engine。
- [Hermes Delegation](https://hermes-agent.nousresearch.com/docs/guides/delegation-patterns/)：独立子上下文、只返摘要、同步委派边界。
- [OpenHands Events](https://docs.openhands.dev/sdk/arch/events)：不可变类型事件、Action/Observation、Source/Role。
- [OpenHands Agent Server](https://docs.openhands.dev/sdk/guides/agent-server/overview)：远程 Agent Server 与 WebSocket 事件。
- [OpenHands Runtime](https://docs.openhands.dev/openhands/usage/architecture/runtime)：Docker Sandbox 的安全、隔离和复现目标。
- [mini-SWE-agent 官方仓库](https://github.com/SWE-agent/mini-swe-agent)：百行 Agent、Bash-only、线性历史、SWE-bench 结果。
- [SWE-agent ACI](https://swe-agent.com/latest/background/aci/)：工具界面对 Agent 表现的影响；原 SWE-agent 已进入维护模式。
- [Letta 官方仓库](https://github.com/letta-ai/letta)：Memory-first 定位与活跃仓库迁移说明。
- [Letta Code 官方仓库](https://github.com/letta-ai/letta-code)：MemFS、Sleeptime、Subagent、Hooks 和长期 Agent。
- [LangGraph Persistence](https://docs.langchain.com/oss/javascript/langgraph/persistence)：Checkpointer 与 Store。
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：持久暂停与恢复语义。
- [Goose 官方仓库](https://github.com/aaif-goose/goose)：MCP/ACP、桌面/CLI/API 与 AAIF 治理。
- [Goose Code Mode](https://goose-docs.ai/docs/guides/managing-tools/code-mode/)：按需工具发现、批处理与结果串联。
- [OpenCode 官方仓库](https://github.com/anomalyco/opencode)：Provider 无关、LSP、TUI 和 Client/Server。

一致性：官方 README 与官方文档在各项目定位和机制上基本一致。

未验证：没有在同一台机器、同一模型和同一任务集上实跑全部项目；README 中的 benchmark 数字仅按官方口径引用，尚未独立复现。OpenClaw 与 Hermes 的代码血缘关系未从一手资料获得足够证据，本报告只陈述官方可确认的迁移兼容，不称其为官方分支。
