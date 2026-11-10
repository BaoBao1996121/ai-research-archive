> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 5 大多 Agent 编排范式 · P05 实测手册

> 这份手册告诉你**怎么用 P05 现有的 6 个 .agent.md 跑通市面上常见的所有多 Agent 编排范式**。
> 配套故意埋雷的 [`buggy_user_service.py`](buggy_user_service.py)（含 8 类问题：SQL注入/N+1/O(n²)/反序列化/明文密码/魔法数字/吞异常/超长函数）作为长尾任务测试材料。
>
> **使用方式**：每种范式有"触发提示词"——直接复制到 VS Code Copilot Chat 切到 `feature-coordinator` 模式下粘贴运行。
> 跑完后用 [`tools/ccreq_parser.py`](../tools/ccreq_parser.py) 自动对账实际命中的模型（无需人工复制 Output）：
>
> ```bash
> python tools/ccreq_parser.py --last 10 --since "2026-04-26 10:00"
> ```
>
> ⚠️ **重要协议变更（2026-04-26）**：经 A/B 实测，**MODEL_SELF_REPORT 协议不可靠**（漏报率 33%-67%，跨 Sonnet/Haiku 都失守）。
> 模型身份验证一律以 ccreq 日志为准，SELF_REPORT 仅作辅助信号。详见 [R73 § A/B 实测结果](../../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R73_VSCodeCopilot%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E5%AE%9E%E8%B7%B5.md)。

---

## 范式速查表

| # | 范式 | 拓扑 | P05 演示方式 | 用什么 agent |
|---|------|------|--------------|--------------|
| 1 | **Orchestrator-Worker** | 1 主 → N 工 | feature-coordinator 派任务给 worker，worker 不知道彼此 | researcher / implementer / reviewer |
| 2 | **Chain（顺序管道）** | A → B → C 串行 | coordinator 顺序调 3 个 agent，前者输出当后者输入 | researcher → implementer → reviewer |
| 3 | **Parallel（专家小组）** | A ‖ B ‖ C → merger | coordinator 同时派 3 个独立维度的 reviewer，自己合并 | security-reviewer ‖ performance-reviewer ‖ reviewer |
| 4 | **Router（条件路由）** | 看任务类型选 worker | coordinator 自己判断，调 1 个最匹配的 worker | 视任务调单个 agent |
| 5 | **Evaluator-Optimizer（迭代优化）** | implement → review → fix → review → ... | coordinator 控制循环，最多 N 轮 | implementer ↔ reviewer 迭代 |

---

## 范式 1 · Orchestrator-Worker

**特点**：经典分布式系统范式。Coordinator 知道全局，worker 各做各的，不互相通信。

**触发提示词**：
```
请 feature-coordinator 派 researcher → implementer → reviewer 三步走，
在 examples/ 下新建 hello_v3.py，含函数 thank_you(name: str) -> str 返回 "Thanks, {name}!"。
完成后告诉我每个 subagent 第一行报的模型。
```

**预期行为**：3 个 worker 顺序串行，每段独立 ccreq。

**EDD 验证点**：
- ✅ Output 日志显示 3 次 `tool/runSubagent-*`
- ✅ 跑完后 `python tools/ccreq_parser.py --last 3` 能看到 3 个 agent 名与模型的准确映射
- ✅ 主对话 token 不暴涨（worker 上下文隔离）

---

## 范式 2 · Chain（顺序管道）

**特点**：与范式 1 几乎同构，但**强调每步输入是上一步的明确输出**——像 Unix pipeline。

**触发提示词**：
```
对 examples/buggy_user_service.py 做安全分析管道：
1. researcher 列出文件中所有"看起来在处理用户输入或外部数据"的函数（不要分析对错，只列）
2. 把列表传给 reviewer，让它对每个函数做综合审查
3. 把 reviewer 输出传给 implementer，让它在原文件最后加一段注释 "# REVIEW SUMMARY:" 概述前一步发现

每步 subagent 输出后，coordinator 调用 `tools/ccreq_parser.py --last 3` 拿实际模型。
完成后报告每段用了什么模型（以 ccreq 为准）+ 总耗时。
```

**预期行为**：与范式 1 相同的 3 段，但任务被设计成强依赖（implementer 必须用 reviewer 的输出）。

**EDD 验证点**：
- ✅ implementer 输出中**真的引用了** reviewer 的发现，而不是凭空写注释
- ⚠️ 检查 implementer（Haiku）是否能准确转述 reviewer（Sonnet）的发现——这是 **跨模型信息保真度**实测

---

## 范式 3 · Parallel（专家小组）⭐ 长尾测试重点

**特点**：N 个 reviewer **同时**审查同一份代码，每个负责一个维度，最后由 coordinator 合并。

**触发提示词**（这是真正的长尾压力测试）：
```
对 examples/buggy_user_service.py 做"专家小组并行审查"：

请 feature-coordinator 同时（并行）派出三个 reviewer：
- security-reviewer 只看安全
- performance-reviewer 只看性能  
- reviewer 看综合质量（风格/正确性/可维护性）

等三个都返回后，coordinator 自己合并成一份按维度分类的最终报告，明确标注：
- 每个发现归属哪个 reviewer
- 三个 reviewer 找到的总数 + 重叠数
- 没人发现但你（coordinator）认为应该提的"盲点"

跑完后使用 `tools/ccreq_parser.py --last 3` 查询三个 reviewer 用的实际模型。
```

**预期行为**：Output 日志会出现 3 段几乎同时启动的 `runSubagent-*-reviewer`。

**EDD 验证点**：
- ✅ **维度独立性**：security-reviewer 不该报性能问题；performance 不该报安全问题——如果越界，说明边界提示词不够强
- ✅ **覆盖率**：8 个埋雷至少要发现 6 个（≥ 75%）
- ✅ **重叠率**：三个 reviewer 的发现重叠率应 ≤ 30%（否则说明分工无价值）
- ⚠️ **真并发？**：VS Code 当前的 runSubagent 是否真的并行调用，还是顺序？通过 Output 日志的时间戳判断

---

## 范式 4 · Router（条件路由）

**特点**：Coordinator 看任务类型，**只派一个最合适的** worker，其他不碰。

**触发提示词**：
```
我有以下三个任务，你判断每个该派哪个 subagent，并执行：

任务 A: "examples/buggy_user_service.py 第 17-25 行 login 函数有什么安全问题？"
任务 B: "examples/buggy_user_service.py 中 process_orders 嵌套循环能不能优化？"
任务 C: "buggy_user_service.py 顶部模块 docstring 写的是什么意思？"

你的工作：
1. 给每个任务分配最匹配的 worker（security-reviewer / performance-reviewer / researcher）
2. 用一句话说明分配理由
3. 实际派出 subagent 执行
4. 汇总三个结果

不要派给所有 worker，派错了不优雅。
```

**预期行为**：3 段独立的 subagent 调用，但每段是不同 agent。

**EDD 验证点**：
- ✅ 路由准确率：3 个任务都派到了"理论上最合适"的 worker
- ✅ 没有冗余调用
- ⚠️ 如果 coordinator 把任务 B 派给 reviewer 而不是 performance-reviewer，说明它没读懂"性能"这个语义信号——记录为 router 失败案例

---

## 范式 5 · Evaluator-Optimizer（迭代优化）

**特点**：implement → evaluate → 如果不通过 → 反馈回 implementer 修 → 再 evaluate → ... 最多 N 轮。

**触发提示词**（Anthropic 论文中的经典范式）：
```
我要把 examples/buggy_user_service.py 中 login 函数改造成"安全版本"。流程：

1. implementer 写一个新文件 examples/login_safe.py，修复 login 函数的所有问题
2. security-reviewer 审查 login_safe.py，给出 🔴/🟠/🟢 分级
3. 如果还有 🔴 高危，把 reviewer 的反馈回传给 implementer，让它再改
4. 再 review。最多 3 轮迭代
5. 3 轮后还有 🔴 → 报告"无法收敛"，列出剩余问题

每轮调用后 coordinator 用 `tools/ccreq_parser.py --last 6` 报告模型。
最终给我：迭代轮数 + 每轮的发现数变化 + 最终代码 + 每段用的模型。
```

**预期行为**：Output 日志可能出现 6+ 段（implementer 2-3 次 + reviewer 2-3 次交替）。

**EDD 验证点**：
- ✅ **真的迭代了**而不是一次过：检查 ccreq 数量
- ✅ **收敛性**：每轮 🔴 数量是否单调下降
- ⚠️ **死循环防护**：超 3 轮是否真的停下来——这是 R73 中"目前靠自然语言'最多 N 次'，遵循度需 EDD 评估"那条开放问题的实证

---

## 综合 EDD 回归基线表

跑完 5 种范式后，填这张表，作为后续修改 .agent.md 的回归基线：

| 范式 | 期望 subagent 数 | 期望 ccreq 数 | 实测 | 总耗时 | ccreq 实际模型 | 维度越界数 | 备注 |
|------|---|---|---|---|---|---|---|
| 1 Orchestrator-Worker | 3 | 3-9 | 3 ✅ | - | 3/3 命中预期 | N/A | researcher→implementer→reviewer |
| 2 Chain | 3 | 3-9 | 3 ✅ | ~54s | 3/3 命中预期 | N/A | implementer 引用 reviewer 编号，跨模型保真度通过 |
| 3 Parallel | 3 (并行) | 3-6 | 3 ✅ | - | 3/3 命中预期 | 0 | 三 reviewer 严守维度边界 |
| 4 Router | 3 (各异) | 3-6 | 3 ✅ | ~46s | 3/3 命中预期 | 0 | 路由准确率 3/3 |
| 5 Evaluator-Optimizer | 4-6 (迭代) | 6-12 | 2 ⚠️ | ~32s | 2/2 命中预期 | N/A | 单轮收敛未触发循环上限 |

**双标签机制 100% 命中率**（截至 2026-04-26 8+ 个 subagent 调用），R73"agent.md model[0] 决定性"结论持续成立。

**剩余 EDD 缺口**：
- Pattern 5 单轮收敛意味着"max_iterations=3"硬约束遵循度未被实测覆盖。需构造让 implementer 故意写不完整的难任务（如"写一个能通过 100 轮 fuzzing 都不挂的版本"）来触发循环上限验证。


---

## 长尾任务的"陷阱清单"——观察这些遵守度漂移点

跑长任务时重点观察以下行为漂移（这些都是已知 LLM 弱点，跨模型遵守度差异大）：

| 漂移点 | 症状 | 严重度 | 应对 |
|------|------|------|------|
| **格式硬约束失守** | MODEL_SELF_REPORT 不在第一行 / JSON 输出语法错 | ⚠️ 已证伪 | **干脆不依赖**。已证明强化无效，身份验证一律走 ccreq_parser.py |
| **维度越界** | security-reviewer 开始评论代码风格 | 🟠 | body 里加"不要做什么"显式负面清单 |
| **任务范围蔓延** | implementer 自作主张加了不该加的功能 | 🔴 | "**不**要 argparse / logging / 单元测试"硬约束 |
| **跨 agent 信息丢失** | implementer 没引用 researcher 的发现，凭空发挥 | 🔴 | coordinator 转述时显式标注"上一步说 X，请基于 X 做 Y" |
| **迭代不收敛** | Evaluator-Optimizer 跑到 5 轮还在改 | 🟡 | 硬性 max_iterations 在 coordinator body 中显式写 3 |
| **自报模型不准** | Haiku 自称是 Claude 3.5 Sonnet | 🟢 | **已退役**。不再依赖 SELF_REPORT，所有身份走 ccreq_parser.py
| **沉默吞错** | subagent 卡住但 coordinator 报"完成" | 🔴 | coordinator body 加"如果任何 worker 返回为空或错误，必须停下报告" |

---

## 与 R73 的对应

| 范式 | R73 章节 | 实测产出归位 |
|------|---------|------------|
| 1, 2 | §3 三大编排模式之 Orchestrator-Worker | R73 实测附录已收 |
| 3 | §3.1 Parallel 子模式 | 待补 |
| 4 | §3.4 Router 子模式 | 待补 |
| 5 | §3.2 Evaluator-Optimizer | 待补 |

跑完 5 个范式后，把基线表填回 [P05/README.md §3](../README.md#3--%E7%9C%9F%E8%AF%A5%E7%9C%8B%E7%9A%84%E5%85%B3%E9%94%AE%E7%8E%B0%E8%B1%A1) 和 R73 实测附录。这是 EDD 闭环。

---

## 下一议题（不在本手册范围）

**动态模型选择**：能否根据"即将处理的数据特征 + 任务类型"自动决定 subagent 用什么模型？

例如：
- 任务输入 < 1k token + 任务类型 = "格式转换" → 派 Haiku
- 任务输入 > 50k token + 任务类型 = "深度推理" → 派 Sonnet/Opus
- 任务类型 = "安全审查" + 涉及加密代码 → 强制升级到 Sonnet+

这本质上是**Agent 调度器的 cost-aware routing**，已记录到 sessions log，作为后续独立研究议题。
