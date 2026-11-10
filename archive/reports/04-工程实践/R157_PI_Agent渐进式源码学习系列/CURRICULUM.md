> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# PI Agent 12 Iter 课程契约

> 一句话结论：路线按“协议内核→Harness 编排→持久化/扩展→入口/生产”递进，每个阶段都用一次更深的 Whole Game 验收。

## 阶段图

```mermaid
flowchart LR
  A["阶段 A · 观察与内核<br/>I00–I03"] --> B["阶段 B · 状态与会话<br/>I04–I06"]
  B --> C["阶段 C · 持久化与扩展<br/>I07–I09"]
  C --> D["阶段 D · 多入口与生产<br/>I10–I11"]
```

## 交付状态与证据边界

> 结论：12 个 Iter 的课程、练习和答案已经齐备，但“内容已交付”与“学习者已掌握”“代码已实现”是三种不同状态。

| 范围 | 教学文档 | 练习 / 答案 | Mini Pi 代码 | 动态证据 |
|---|---|---|---|---|
| I00–I03 | 已交付 | 已交付 | 已实现 | 10/10 累计测试与 strict TypeScript 检查已在 Batch 1 实测 |
| I04–I10 | 已交付 | 已交付 | 待实现 | 源码锚点和文档结构已审校；不得写成测试通过 |
| I11 | 已交付 | 已交付 | 不以单一 Lab 代替生产平台 | Capstone 规格已交付；真实隔离、故障演练和模型 Eval 待具体环境验证 |

教学可先完整进行源码预测、Trace、设计与故障诊断；若要获得 M1 行为证据，I04–I10 仍需沿现有 Lab 做 RED→GREEN，I11 需在选定部署环境执行 Capstone。

## 阶段 A · 观察与内核（PI-I00–03）

> 结论：先拥有一个能跑完整 Turn 的最小系统，再逐层拆开模型协议、Loop 与工具管线。

| Iter | 输入 | 新增产物 | 阶段验收 |
|---|---|---|---|
| I00 | 确定性 `20+22` 任务 | 可观察 Whole Game Trace | 5 分钟闭卷画主链 |
| I01 | Scripted responses | 中立 Message/Context/Event 协议 | 换响应类型，上层 vocabulary 不变 |
| I02 | Tool Call + ToolResult | 模型—工具续轮、截断拒绝、预算护栏 | 从 Trace 预测下一状态 |
| I03 | 多 Tool Call | 验证/Hook/并发/串行/错误消息化 | 10 个累计测试全绿 + 工具管线答辩 |

## 阶段 B · 状态与会话（PI-I04–06）

> 结论：把一次函数调用升级成可交互会话，并证明资源、提示词和实际工具来自一致能力快照。

| Iter | 核心增量 | 必须制造的失败 | 掌握证据 |
|---|---|---|---|
| I04 | AgentState reducer、订阅屏障、Steering/Follow-up queue | 工具执行期间注入 Steering | 两个工具先完成；Steering 下一 Turn；Follow-up 最后 |
| I05 | AgentSession、Prompt/Tool compilation | Prompt 声称有工具但实际未注册 | 用一个 capability snapshot 同源生成提示与工具 |
| I06 | ResourceLoader、AGENTS.md、Skills、Project Trust | 未加载/被覆盖/不可信/未注入四类故障 | 能从证据定位到加载、合并、信任或编译层 |

阶段 Whole Game：用 Session 重跑 I00，观察输入、能力加载、AgentState 与事件；关闭某能力后 Prompt 与 Tool 列表必须一起变化。

## 阶段 C · 持久化与扩展（PI-I07–09）

> 结论：让 Agent 能恢复、压缩和扩展，同时保留 append-only 历史与信任边界。

| Iter | 核心增量 | 必须制造的失败 | 掌握证据 |
|---|---|---|---|
| I07 | JSONL entry、parentId、leaf/branch、resume | 从中间节点分叉后继续 | 重放两条分支而不改历史行 |
| I08 | Token budget、compaction cut point、retry | 超窗、半个 tool pair、脏摘要 | 随机事件流下 Context 合法且预算受控 |
| I09 | Extension loader、hooks、custom tool/provider | 扩展抛错、权限越界、卸载 | 失败隔离、可卸载、威胁分析 |

阶段 Whole Game：恢复旧 Session，切分支，触发一次 compaction，再装载/卸载一个扩展；最终 transcript 可解释且可重放。

## 阶段 D · 多入口与生产（PI-I10–11）

> 结论：最后才引入入口适配和生产约束，检验核心不变量能否跨 UI、协议与故障场景保持一致。

| Iter | 核心增量 | 必须制造的失败 | 掌握证据 |
|---|---|---|---|
| I10 | Print/JSON/RPC/SDK/TUI adapter | 同任务在两个入口输出不一致 | 新增入口不复制 Loop，transcript 一致 |
| I11 | sandbox、budget、observability、eval | 超时、断连、越权、重试风暴、脏 Session | 运行演练、风险清单、架构答辩全部通过 |

## 支架渐隐

> 结论：按掌握证据撤支架，不按章节编号机械减少讲解。

| 阶段 | 初始支架建议 | 学习者主要动作 | 说明 |
|---|---:|---|---|
| I00–02 | 高 | 运行、预测、跟踪、解释 | 完整 worked example |
| I03–05 | 中 | 补代码、修测试、画状态 | completion problems |
| I06–09 | 低 | 诊断、辨析、扩展 | 只给测试/接口/Hint |
| I10–11 | 最低 | 独立迁移、故障演练、答辩 | 先不提供完整实现 |

“高/中/低”是课程设计初始值，不是论文给出的精确阈值；入口测验表现好可提前撤支架，反之应恢复 worked example。

## 累计验收门

> 结论：每个阶段只有行为、解释与迁移三类证据都成立，才进入下一阶段。

```text
Gate A: tests + closed-book trace + one new failure case
Gate B: state/session reconstruction + capability consistency
Gate C: resume/compact/extension fault exercise
Gate D: multi-entry invariant + production threat model + eval
```

测试通过不自动代表架构理解；Teach-back 流利也不代表能实现。两者必须交叉验证。
