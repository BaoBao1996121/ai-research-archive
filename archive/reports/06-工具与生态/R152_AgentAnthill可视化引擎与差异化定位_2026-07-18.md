---
title: Agent Anthill 可视化引擎与差异化定位（2026-07-18）
aliases: [R152, Agent Anthill 可视化选型, Agent 可视化观测站]
tags: [AI-Agent, 可观测性, 可视化, PixiJS, Phaser, 产品定位]
date: 2026-07-18
status: current
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Agent Anthill 可视化引擎与差异化定位（2026-07-18）

> **一句话结论：** PixiJS 8.19.0 WebGL 是首个生产竖切候选，但先不换引擎；先以 X/Y/Z 三份等构材料比较当前 Canvas 与两名视觉候选能否更快形成正确心智模型，再用 Phaser 4.2.1 同场景基准决定是否迁移。

## 1. 已有基础与本次增量

**结论：仓库已有完整的真值与渲染边界设计，本次新增的是 2026-07-18 的依赖核验、竞争空位和可执行的 Phase 0 实验合同。**

已有基础：

- Agent Anthill 0.7.0 已实现 measurement truth contract、Evidence/Coverage/Compare、确定性 Chromium 视觉回归和受保护分支门禁；
- `docs/VISUAL_SYSTEM.md` 已推荐 PixiJS 8，要求 Phaser 4.2.1 同场景对照，并将 Blender、Pixelorama、Rive、Spine 限定在清楚的边界内；
- `tests/fixtures/visual_rich_v1.json` 提供 44 个确定性事件，可作为理解度和视觉方向的固定控制材料。

本次新增：

- 核验 PixiJS 8.19.0 与 Phaser 4.2.1 在官方 npm registry 的版本与完整性元数据；
- 发现维护者工作站的 npm 镜像能解析 PixiJS、但对 Phaser 4.2.1 返回 404；
- 核验 PixiJS 官方文档对 Canvas fallback 的表述不一致，因而不能把实验性 Canvas 当作可靠降级；
- 横向比较 Langfuse、Arize Phoenix、AgentOps，确认“把 Trace 画成图”已经不是差异化；
- 将下一里程碑冻结为 `v0.8 — Visual evidence lab`，并公开预注册 8 个机制问题与错误推断编码。

## 2. 定位透镜

### 2.1 纵轴：从 Trace 存储到可验证解释

**结论：行业已经成熟到“有 Trace、有图、有评估”，下一层稀缺能力是解释一个视觉判断凭什么成立。**

1. 早期观测：记录 prompt、completion、token、延迟和错误。
2. 平台化：Trace/Session、Prompt、Eval、Dataset、Experiment、Dashboard 进入同一产品。
3. 结构可视化：Span tree、waterfall、agent graph 让用户看到层级和时序。
4. 可验证解释：严格区分时序、span parent、显式 causation、推断和未知；每个视觉对象都可回到事件与来源。

Langfuse 与 Phoenix 已处于第 2–3 层的成熟阶段。Agent Anthill 不应重新建设它们已有的平台广度，而应把第 4 层做深。

### 2.2 横轴：相邻产品的设计哲学

**结论：Anthill 的目标位置是“平台广度中低、因果与认识论解释最高”，并通过适配器与现有平台共存。**

| 产品 | 当前强项 | 公开可视化主线 | 对 Anthill 的含义 |
|---|---|---|---|
| Langfuse | Trace、Prompt、Eval、Dataset、Experiment、Dashboard | Agent Graph、Trace/Observation/Session；通用图可基于 timing/nesting 形成结构 | 不能以“Agent Graph”作为卖点；必须证明因果边和推断边的证据 |
| Arize Phoenix | OpenTelemetry、Trace、Annotation/Eval、Dataset/Experiment | Project→Trace→Span 与实验分析 | 不卷通用 Eval 平台；把机制解释和捕获盲区做成一等产品概念 |
| AgentOps | Session、Timeline、Tree、Waterfall、成本和错误 | step-by-step execution graph、时间线和详情 | “执行回放”也不够；需要 truth status、Unknown、机制级 Compare |
| Agent Anthill | 目标能力 | 时空回放 + Evidence + Coverage + Compare + hash/来源路线 | 每个像素都能回答“它凭什么出现”，且不知道时明确说不知道 |

事实：2026-07-18 GitHub 快照中，Langfuse 31,365 Stars、Phoenix 10,612 Stars、AgentOps 5,716 Stars。Stars 只表示社区信号，不证明产品质量或适配当前需求。

推断：公开信息架构里尚没有产品把 observed/inferred/unknown、adapter blind spot、显式因果与时间邻接的分离同时作为核心视觉合同。这是基于公开官方页面的证据性判断，不是对隐藏功能的绝对否定。

## 3. 引擎与资产工具决策

**结论：PixiJS 8.19.0 是最匹配的薄渲染层；Phaser 4.2.1 必须作为同场景对照，但不能因 demo 更快完成而获胜。**

| 方案 | 推荐角色 | 优势 | 天花板 / 风险 | 当前决定 |
|---|---|---|---|---|
| PixiJS 8.19.0 | 生产候选 | Web 原生、场景图薄、WebGL 稳定、可手动控制 ticker/culling/accessibility overlay | 需要项目自己承担状态、相机、LOD、确定性动画、降级和 DOM mirror | 默认候选；明确选择 WebGL，不采用 WebGPU |
| Phaser 4.2.1 | 同场景基准 | 场景、相机、输入、tween、动画和资产系统完整 | Phaser 4 渲染器生命周期短；框架对象生命周期可能侵入领域状态；bundle/内存更大 | 仅在等价语义和无障碍下显著赢性能或总维护成本才采用 |
| 现有 Canvas + DOM | 语义 oracle 与降级 | 已有 49 个浏览器合同；依赖少；真值语法稳定 | 场景管理、对象池、LOD 和资产动画扩展成本高 | 在 VisualModel 之前保留；不能先拆掉 |
| Godot Web | 边界方案 | 完整编辑器和游戏能力 | Web 包体、DOM/无障碍整合、现有 Web UI 组合和部署成本不匹配 | 不进入首轮基准 |
| Blender | 离线资产制作 | 正交镜头、统一比例、低模、rig、批量渲染 | 清理成本可能超过直接绘制；不能进入浏览器 runtime | 只做一个角色/机器小试 |
| Pixelorama | 离线像素清理与 atlas | MIT、像素网格、调色、spritesheet、CLI 导出 | 导出确定性仍需实测 | 推荐作为最后人工权威 |
| Rive / Spine | 条件触发的特殊资产 | 高质量状态机或骨骼动画 | 额外 runtime/许可/订阅与状态所有权风险 | 当前不采用；达到文档触发条件再复议 |

### 3.1 依赖核验

**结论：官方 registry 可用，但本机镜像滞后，基准必须显式隔离 registry 并提交 lockfile。**

官方 npm registry 实测：

- `pixi.js@8.19.0`：`sha512-pq1O6emA/GFjjeF+8d3Pb5t7knD8FsnfWGqQcRjYjsqFZ7QdzG1XgjLDUu0DFJRbafjV5+g8iNLFBx0b9649lg==`
- `phaser@4.2.1`：`sha512-WUNwCPJpdjvZiuT6SgCfYVW8Qw/3j0jJ4ws7P2QkhFLFu74sbGuyHJcbFueGkY/AYO4Pi47bNQXn1OCJeLX//w==`

本机配置的 npm 镜像对 `phaser@4.2.1` 返回 404。正确处理不是修改维护者的全局 registry，而是在隔离的 benchmark 安装中显式指定官方 registry，提交 lockfile，并记录 resolved URL 与 integrity。

PixiJS 官方材料还存在一个需要保守处理的分歧：8.16.0 发布文称 Canvas renderer 已以 experimental 形式回归并可自动 fallback，但当前 8.x renderer guide 仍将 Canvas 标成 coming soon。故生产降级继续使用 Anthill 自有 Canvas/semantic DOM，不能依赖 PixiJS experimental Canvas。

## 4. 推荐视觉方向

**结论：首选“正交剖面式技术蚁巢”，而不是强透视等距游戏场景。**

推荐方向具备：

- 正面剖面或弱透视：房间、标签、因果边不会互相遮挡；
- 小人是稳定身份编码：Agent 角色只负责身份和状态识别，不用表演推断出来的动作；
- 机器是机制编码：Model、Tool、Memory、Context、Compaction、Checkpoint 等房间保持稳定位置；
- 实线表示来源声明，点线表示推断，斜线纹理表示 unknown/not observed；
- 已恢复事故保留历史痕迹，不因恢复而消失；
- 证据入口、时间线、Coverage 与 Compare 永远不让位给装饰。

Phase 0 同时比较：

1. 正交剖面式技术蚁巢（推荐主候选）；
2. 2.5D 等距蚁巢工厂（验证遮挡与标签成本）；
3. 密集工程示意图（理解度/信息密度控制组，也可能成为高密度监控模式）。

三个方向必须承担相同信息义务。不能让某个候选通过少展示信息显得更漂亮。

## 5. Phase 0 实验合同

**结论：先证明理解增益，再建设 VisualModel，最后才比较引擎。**

公开控制材料：`visual_rich_v1.json` v1.0.0，44 个事件。

八个机制问题覆盖：任务所有权与 handoff、memory 进入 context、RateLimit 失败与显式恢复、context overflow 与有损 compaction、inferred decision、estimated cost、artifact→memory、终态与 NOT OBSERVED。

错误推断编码覆盖：

- 时间邻接误当因果；
- 没观察到误当没发生；
- capture/transport 状态误当 run lifecycle；
- 装饰动画误当真实执行；
- inferred claim 误当 observed fact；
- recovered 误当历史删除；
- estimated/incompatible measurement 误当可直接比较；
- handoff/ownership 混淆。

执行顺序：

1. 以 1 名 Agent 工程师和 1 名技术型学习者试测 Canvas 仪器、评分与任务；
2. 生成三套等信息量静态方向，以 Canvas 为基线，由另 8 人（4+4）在 W/X/Y/Z 静态材料轮换下完成五秒识别、单色、高对比和错误推断筛选；
3. 为 Canvas 与前两名方向制作 X/Y/Z 三份人工核验的等构 fixture；
4. 正式比较使用 12 人（6 名 Agent 工程师、6 名技术型学习者），每人体验 Canvas 与两候选；每层覆盖六种条件顺序并平衡 interface×fixture；
5. 原子评分、最多三次提交、20 分钟右删失、双盲评分与第三人分歧裁决全部在招募前冻结；
6. 只有前序指标仍打平时，复用正式参与者，以 12 / 28 / 64 / 128 可见对象探测稳定密度失效；
7. 一名 Agent、一台机器、5–7 个语义动作做资产管线小试；
8. 发布原始数据并明确 select/revise/keep-Canvas。

正式形成性样本为 12 人；另有 2 名试测者和 8 名静态筛选者，三类 cohort 不混用。该样本只用于排除明显错误和选择需继续验证的方向，不能宣称已证明“比 README+日志+源码快 50%”。确认性样本量应在得到 Phase 0 方差后计算。

## 6. 实现顺序与采用门槛

**结论：实现顺序必须防止引擎反向拥有领域状态。**

1. Headless `VisualModel` 与稳定序列化快照；
2. 现有 Canvas 改为消费 `VisualModel`；
3. PixiJS 8.19.0 WebGL 同场景竖切；
4. Phaser 4.2.1 使用相同模型、atlas、字体、视口、LOD、DOM mirror 与 fixture；
5. 发布原始报告后再决定完整迁移。

Phaser 只有在 truth/accessibility 完全等价的前提下，才按 `VISUAL_SYSTEM.md` 的初始治理值参与决策：两档硬件 p95 frame time 至少领先 20%，或实现/维护投入至少降低 30%，且 bundle/内存不超过 PixiJS 15%。这些数字仍是待 Phase 3 校准的初始值，不能当成行业事实。

## 7. 成本、失败模式与停止条件

**结论：主成本在人类理解实验、工程和资产审查，不在图像 API。**

| 工作 | 规划量，待验证 |
|---|---:|
| 剩余 Phase 0 仪器、三份 fixture、方向与报告 | 8–14 工程日 |
| Phase 0 美术/UX 与代表资产 | 4–7 美术/UX 日 |
| Phase 0 招募、主持、匿名化、双评分与裁决 | 5–8 研究/主持日；覆盖 2 名试测、8 名筛选、12 名正式参与者；现金成本另行询价 |
| VisualModel 与动画合同 | 7–12 工程日 |
| PixiJS 竖切 | 10–16 工程日 |
| Phaser 同场景基准 | 4–7 工程日 |
| 从当前到引擎决策 | 29–49 工程日 + 4–7 美术/UX 日 + 5–8 研究/主持日 |

主要失败模式：

- 好看但更难理解：机制题和错误推断是硬门槛；
- AI 资产相似性、权属或脏标记不清：只作概念，必须人工重绘/清理、登记来源和 hash；
- Blender 清理时间超过原创：一个角色小试后立即停止；
- Phaser 因内置 tween 让 demo 更快而“假赢”：比较全项目交付与维护成本；
- 引擎 ticker/scene 成为领域状态：架构违规，停止迁移；
- 本机 DLP 改写 PNG：候选审查和 golden 晋级继续依赖 immutable Linux CI artifact；
- 生成图服务不可用：2026-07-18 内置图像生成连续两次网络失败，无产物；不得未经用户确认切换到需要 API key 的 CLI fallback。

## 8. 推荐定位文案

**结论：对外不说“更炫的 Agent Graph”，而说“每个视觉判断都能回到证据”。**

英文：

> Agent Anthill is a truth-aware, time-travel execution observatory for AI agents — every visual claim links back to evidence.

中文：

> 不是另一个 Trace 看板，而是一座能区分“发生了什么、凭什么这样判断、哪里仍未知”的 Agent 时光观测站。

## 9. 开放问题

**结论：以下问题必须用 Phase 0 数据回答，不能在设计文档里猜。**

1. 三种方向中，哪一种实际降低 TCMM 和 W1–W8 错误推断？
2. 当前 28 对象上限之后，哪一个密度点出现稳定识别下降？
3. Blender→Pixelorama 是否真的比原创 sprite 省人工？
4. PixiJS 8.19.0 accessibility overlay 与项目自有 DOM mirror 如何分工最稳？
5. 低端硬件、浏览器矩阵和真实辅助技术的阻塞门槛是什么？
6. 是否需要提供“工程示意图高密度模式”与“蚁巢学习模式”双视图？

## 10. Sources and freshness

**结论：核心选型基于官方文档、官方 registry 和官方 GitHub；竞争空位是标明边界的推断。**

- [PixiJS npm package](https://www.npmjs.com/package/pixi.js?activeTab=versions) — retrieved 2026-07-18 — latest 8.19.0、MIT、依赖与采用信号
- [PixiJS 8.19.0 registry metadata](https://registry.npmjs.org/pixi.js/8.19.0) — retrieved 2026-07-18 — exact tarball、integrity 与 shasum
- [PixiJS renderer guide](https://pixijs.com/8.x/guides/components/renderers) — retrieved 2026-07-18 — WebGL recommended、WebGPU experimental、Canvas 文档状态
- [PixiJS accessibility](https://pixijs.com/8.x/guides/components/accessibility) — retrieved 2026-07-18 — opt-in DOM overlay
- [PixiJS culler](https://pixijs.com/8.x/guides/components/application/culler-plugin) — retrieved 2026-07-18 — culling 非默认启用
- [PixiJS 8.16.0 release](https://pixijs.com/blog/8.16.0) — retrieved 2026-07-18 — experimental Canvas renderer 与 fallback 表述
- [Phaser 4 releases](https://phaser.io/download/phaser4) — retrieved 2026-07-18 — 4.2.1 于 2026-07-09 发布
- [Phaser 4.2.1 registry metadata](https://registry.npmjs.org/phaser/4.2.1) — retrieved 2026-07-18 — exact tarball、integrity 与 shasum
- [Phaser 4 changelog](https://github.com/phaserjs/phaser/blob/master/changelog/v4/4.0/CHANGELOG-v4.0.0.md) — retrieved 2026-07-18 — 全新 WebGL renderer 与 breaking changes
- [Pixelorama CLI](https://pixelorama.org/user_manual/cli/) — retrieved 2026-07-18 — headless/spritesheet/JSON 导出能力
- [Langfuse GitHub](https://github.com/langfuse/langfuse) — retrieved 2026-07-18 — Stars、功能、许可与活跃度
- [Langfuse Agent Graphs](https://langfuse.com/docs/observability/features/agent-graphs) — retrieved 2026-07-18 — graph 模式与 timing/nesting 推图边界
- [Arize Phoenix GitHub](https://github.com/Arize-ai/phoenix) — retrieved 2026-07-18 — Stars、Trace/Eval/Experiment、ELv2
- [Phoenix tracing concepts](https://arize.com/docs/phoenix/tracing/concepts-tracing/what-are-traces) — retrieved 2026-07-18 — Project/Trace/Span 数据模型
- [AgentOps GitHub](https://github.com/AgentOps-AI/agentops) — retrieved 2026-07-18 — Stars、MIT、execution graph
- [AgentOps dashboard](https://docs.agentops.ai/v2/usage/dashboard-info) — retrieved 2026-07-18 — Session Drawer、Waterfall 与事件详情
- [Agent Anthill v0.7.0](https://github.com/BaoBao1996121/agent-flow-visualizer/releases/tag/v0.7.0) — published 2026-07-18 — 当前真值基础
- [Phase 0 issue #10](https://github.com/BaoBao1996121/agent-flow-visualizer/issues/10) — created 2026-07-18 — 公开实验范围与预注册
- [Phase 0 preregistration amendment v2.2](https://github.com/BaoBao1996121/agent-flow-visualizer/issues/10#issuecomment-5011144923) — registered 2026-07-18 before recruitment — 平衡设计、评分、Evidence、故障边界、任务和成本修订
- [Committed Phase 0 plan v2.2](https://github.com/BaoBao1996121/agent-flow-visualizer/blob/355b762019f42b43b4dd30980d8c97f5e698a022/docs/PHASE0_VISUAL_EVIDENCE_PLAN.md) — merged 2026-07-18; protected-main CI [29643772301](https://github.com/BaoBao1996121/agent-flow-visualizer/actions/runs/29643772301) passed 9/9 — 不可变协议与合并后验证

Consistency: PixiJS/Phaser 版本与官方 npm registry 一致；PixiJS Canvas 状态在官方 release blog 与 renderer guide 间部分冲突，按实验性能力处理。竞争项目的 GitHub REST 快照与官方产品文档一致。

Unverified: 尚未登录三家竞品云产品逐页穷举；尚无真实参与者理解度数据、低端硬件数据、真实辅助技术矩阵或资产管线耗时。

## 11. Pattern forge 判断

**结论：暂不写入 Pattern Library。**

“认识论视觉语法（observed / inferred / unknown + evidence route）”具备复用潜力，但目前只有 Anthill 的实现合同，尚无 Phase 0 用户数据。待它在理解度实验中降低错误推断后，再提炼为跨项目模式，避免把未经验证的项目观点过早固化成通用规律。
