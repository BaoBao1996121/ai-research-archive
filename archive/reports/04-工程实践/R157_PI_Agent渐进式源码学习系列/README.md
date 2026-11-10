---
title: PI Agent 渐进式源码学习系列
aliases: [R157, PI Agent 学习系列, Mini Pi, PI Agent 源码课程]
tags: [ai-agent, pi-agent, source-code, typescript, tutorial, retrieval-practice, tdd]
date: 2026-07-31
updated: 2026-07-31
report_id: R157
category: 工程实践
status: documentation-complete
tokens: "~120K estimated"
batch_status: all-iter-docs-delivered-lab-i03
source_repo: https://github.com/earendil-works/pi
source_commit: 063fb963c5c33d099faa593d17e60e0a875430cd
related: [R24, R44, R78, R156]
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# PI Agent 渐进式源码学习系列

> 一句话结论：这不是把源码报告拆成 12 篇，而是一条“先看完整系统、再累计手搓 Mini Pi、每步用测试与闭卷解释证明掌握”的学习路径。

## 0. 交互网页版

> 结论：优先从网页版进入课程；Markdown 文档仍作为可检索、可长期保存的完整底稿。

- 公开站点：[PI Agent 源码训练场](https://pi-agent-source-lab.linlvming2025.chatgpt.site)（无需 ChatGPT 登录）
- 学习交互：12 Iter 路线、架构图、Event Trace 步进器、章节测验、H0–H6 提示阶梯、全文搜索与下一课推荐。
- 内容范围：完整讲义、练习、答案与 Capstone 均可按需展开；固定源码链接继续指向课程提交 `063fb963`。
- 进度边界：学习记录保存在当前浏览器的 `localStorage`，不会跨设备同步；I00–I03 有已运行 Lab 证据，I04–I10 是待实现实验规格，I11 是生产设计与 Capstone 规格。

## 1. 这套系列新增了什么

> 结论：在既有 R24、R44、R78 与 R156 基础上，本系列新增固定 Pi 源码标本、同语言 TypeScript Lab 和可验证的学习证据。

工作区已经有：

- R24：通用 Agent 从零路线；
- R44：Python/Qwen 渐进实战；
- R78：累计式“手搓记忆系统”范式；
- R156：Pi 核心架构与源码地图。

所以这里不再重复“什么是 LLM/ReAct/工具注册表”。课程设计让 12 个 PI Iter 围绕同一个 Mini Pi 累计增长，并统一包含运行前预测、固定源码断点、故障注入、Mini Pi/真 Pi 对照、Teach-back 与延迟复习；其中 I00–I03 已实际执行 RED→GREEN，I04–I11 交付的是后续 RED 规格、实现题与验收标准，尚未冒充代码完成。

## 2. 源码基线与时效

> 结论：课程固定在可复现提交上，同时单独记录上游漂移，不用会变化的 main 分支行号冒充永久证据。

| 项目 | 值 |
|---|---|
| 上游仓库 | [`earendil-works/pi`](https://github.com/earendil-works/pi) |
| 课程标本 | [`063fb963c5c33d099faa593d17e60e0a875430cd`](https://github.com/earendil-works/pi/tree/063fb963c5c33d099faa593d17e60e0a875430cd) |
| 本地源码 | `C:/Users/USER\Documents\Codex\2026-07-28\new-chat-2\work\pi` |
| 最新远端检查 | 2026-07-31：`74caa2649f10ed71b4378ce69f5d9fbfd2466ca5` |

漂移检查事实：固定提交之后，`packages/agent/src/agent-loop.ts`、`agent/types.ts`、`agent.ts` 没有新提交触碰；`ai/types.ts` 增加了 Provider compatibility 字段，`main.ts`/`agent-session.ts` 有后续修改。因此 Iter02–03 的核心断点仍具有较高稳定性，Iter00–01 仍以固定提交为唯一行号依据。最新分支不等于课程标本；未来升级要先运行 `SOURCE_MAP` 漂移审计。

## 3. 从哪里开始

> 结论：先运行完整游戏，再做预测；不要从 8 万行仓库第一页开始顺序阅读。

```powershell
cd "C:/Users/USER\Documents\Codex\2026-07-28\new-chat-2\outputs\PI-Agent-Learning-Series\lab"
.\run-demo.ps1
.\run-tests.ps1
```

然后按这个顺序：

1. [PI-I00 · Whole Game](lessons/PI-I00-Whole-Game.md)
2. [PI-I01 · 统一模型协议](lessons/PI-I01-%E7%BB%9F%E4%B8%80%E6%A8%A1%E5%9E%8B%E5%8D%8F%E8%AE%AE.md)
3. [PI-I02 · 最小 Agent Loop](lessons/PI-I02-%E6%9C%80%E5%B0%8FAgentLoop.md)
4. [PI-I03 · 工具执行管线](lessons/PI-I03-%E5%B7%A5%E5%85%B7%E6%89%A7%E8%A1%8C%E7%AE%A1%E7%BA%BF.md)
5. [PI-I04 · Agent 状态与消息队列](lessons/PI-I04-Agent%E7%8A%B6%E6%80%81%E4%B8%8E%E6%B6%88%E6%81%AF%E9%98%9F%E5%88%97.md)
6. [PI-I05 · AgentSession 与能力编译](lessons/PI-I05-AgentSession%E4%B8%8E%E8%83%BD%E5%8A%9B%E7%BC%96%E8%AF%91.md)
7. [PI-I06 · 资源加载与信任边界](lessons/PI-I06-%E8%B5%84%E6%BA%90%E5%8A%A0%E8%BD%BD%E4%B8%8E%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C.md)
8. [PI-I07 · JSONL 会话树与恢复](lessons/PI-I07-JSONL%E4%BC%9A%E8%AF%9D%E6%A0%91%E4%B8%8E%E6%81%A2%E5%A4%8D.md)
9. [PI-I08 · Compaction 与恢复](lessons/PI-I08-Compaction%E4%B8%8E%E6%81%A2%E5%A4%8D.md)
10. [PI-I09 · Extension Runtime](lessons/PI-I09-Extension-Runtime.md)
11. [PI-I10 · 多入口同一内核](lessons/PI-I10-%E5%A4%9A%E5%85%A5%E5%8F%A3%E5%90%8C%E4%B8%80%E5%86%85%E6%A0%B8.md)
12. [PI-I11 · 生产加固与评估](lessons/PI-I11-%E7%94%9F%E4%BA%A7%E5%8A%A0%E5%9B%BA%E4%B8%8E%E8%AF%84%E4%BC%B0.md)

每课先打开 `exercises/`，最后才打开 `solutions/`。全系列学完后做 [Capstone：受控代码审阅 Agent](CAPSTONE.md)。若只是源码定位，可直接用 [SOURCE_MAP.md](SOURCE_MAP.md)；若想理解为什么这样教，读 [TEACHING_DESIGN.md](TEACHING_DESIGN.md)。

## 4. 12 个 Iter 的完整路线

> 结论：四次回到同一个“完整 Agent”，每次把观察层次从协议推进到会话、入口与生产边界。

| Iter | 核心问题 | Mini Pi 增量 | 掌握证据 | 状态 |
|---:|---|---|---|---|
| PI-I00 | 一条 Prompt 穿过哪些层？ | 端到端可观察 Trace | 闭卷重画主链 | ✅ 文档 + Lab |
| PI-I01 | 多家模型怎样共享上层？ | Message/Context/Event + ScriptedModel | 换假 Provider 不改 Loop | ✅ 文档 + Lab |
| PI-I02 | Tool Call 怎样推动下一轮？ | 最小 Loop + fail-closed + turn budget | 预测下一事件与停止原因 | ✅ 文档 + Lab |
| PI-I03 | 工具怎样校验、并发、回填？ | Tool Pipeline + hooks + 双顺序 | 四类故障测试与信任边界解释 | ✅ 文档 + Lab |
| PI-I04 | 事件怎样归约成 AgentState？ | 状态机、Steering、Follow-up | 从乱序日志重建合法状态 | ✅ 文档 · Lab 待实现 |
| PI-I05 | 谁组装 Prompt、工具与一次会话？ | AgentSession、同源 capability compilation | 解释 Prompt/Tool 不一致故障 | ✅ 文档 · Lab 待实现 |
| PI-I06 | AGENTS.md、Skill 与资源怎样进入 Context？ | ResourceLoader、优先级、Trust | 定位加载/覆盖/注入层错误 | ✅ 文档 · Lab 待实现 |
| PI-I07 | 会话为何是 JSONL 树而非数组？ | append-only entries、branch、resume | 重放与分叉且不改历史 | ✅ 文档 · Lab 待实现 |
| PI-I08 | 上下文超窗怎样恢复？ | compaction、retry、budget | 脏摘要/断裂工具对下仍合法 | ✅ 文档 · Lab 待实现 |
| PI-I09 | 怎样扩展而不 Fork 核心？ | Extension runtime、hooks、custom tool/provider | 可卸载、失败隔离、威胁分析 | ✅ 文档 · Lab 待实现 |
| PI-I10 | TUI/Print/JSON/RPC/SDK 为什么共享内核？ | 多入口 adapter | 新增入口且不复制 Loop | ✅ 文档 · Lab 待实现 |
| PI-I11 | 怎样从“能跑”走到“可上线”？ | sandbox、预算、观测、Eval | 故障演练 + 架构答辩 | ✅ 文档 · Capstone 规格 |

详细依赖、产出物和分阶段验收见 [CURRICULUM.md](CURRICULUM.md)。

## 5. 学习循环

> 结论：每个 Iter 使用 TRACE——这是本课程对多种证据型教学法的工程化组合，不是一个已经独立验证的新理论。

```text
T · Trace       先观察最小完整任务
R · Retrieve    合上材料，从记忆提取旧知识
A · Attempt     先预测、先写失败测试、先尝试
C · Compare     对照 Mini Pi / 真 Pi，并自我解释因果
E · Extend      撤除支架，做故障注入与迁移题
```

它组合了检索练习、间隔学习、worked examples/fading、自我解释、主动学习/ICAP、Whole Game 与认知学徒制。证据强弱、外推限制、Hint ladder 和 12 Iter 教学法映射见 [TEACHING_DESIGN.md](TEACHING_DESIGN.md)。“费曼学习法”在这里仅作为闭卷解释＋找缺口＋修正的便捷标签，其有效成分来自 retrieval 与 self-explanation；不把流行标签当独立证据。

## 6. 完成不等于看完

> 结论：测试证明行为，Teach-back 证明解释，迁移任务才证明能在新情境使用。

一课完成至少需要：

- 核心测试全绿，而且亲眼见过目标 RED；
- 不看文档画出状态/事件图；
- 能同时说出“机制、为什么、边界”；
- 完成一个变体或故障定位，不是原样重跑；
- 24 小时后能回忆关键不变量。

7 天迁移题完成后才建议标记为 `mastered`。学习记录模板见 [PROGRESS.md](PROGRESS.md)。

## 7. 目录

> 结论：课程、练习、答案、源码地图与可运行 Lab 分开，避免一打开题目就泄漏答案。

```text
PI-Agent-Learning-Series/
├── README.md
├── CURRICULUM.md
├── TEACHING_DESIGN.md
├── SOURCE_MAP.md
├── CONCEPT_MAP.md
├── GLOSSARY.md
├── PROGRESS.md
├── CAPSTONE.md
├── ENVIRONMENT.md
├── ASSUMPTIONS.md
├── lessons/
├── exercises/
├── solutions/
└── lab/
    ├── src/
    ├── tests/
    ├── examples/
    ├── run-demo.ps1
    ├── run-tests.ps1
    └── TDD_LOG.md
```

## 8. 成本与局限

> 结论：全套文档可以零 API 成本学习，但可运行 Lab 只覆盖 I00–03，后八章的实现、真实 Provider Eval 与生产演练仍需要后续投入。

- PI-I00–03 不调用真实模型，API 调用与 Token 成本均为 0；事件完全可复现。
- PI-I04–11 已交付课程、独立练习和参考答案；其中课程新增的 Mini Pi 实现片段/代码题均明确标为伪代码、设计题或待实现，不计入已通过测试；引用的上游固定提交源码仍是真实证据。
- Lab 无第三方 npm 依赖，使用 Node.js 原生 TypeScript type stripping 与 `node:test`。
- 原生运行会剥离类型但不做完整静态类型检查；生产项目仍应使用 TypeScript checker 与 lint。
- 当前 Lab 主动省略 Auth、Usage、Thinking/Image、Steering/Follow-up、Session、Compaction、Extension、TUI 与 sandbox；不能把后续课程文档误解成这些模块已经在 Mini Pi 中实现。
- 教学组合大量证据来自记忆实验、数学或高校 STEM 课堂；迁移到成人自学 TypeScript 源码课程是有依据的推断，尚未做本课程 A/B 验证。
- 分层 Hint、错误夹具和延迟复习的制作工作量高于普通文章；具体倍率没有实测，不在此虚构。

## 9. 完整文档交付边界

> 结论：12 个 Iter 的教学文档、练习、答案和 Capstone 已全部交付；工程实现仍保持诚实边界——累计 Lab 只到 PI-I03。

当前包含 12 篇课程、12 份练习、12 份参考答案、Capstone、源码地图、教学设计和累计 Lab。I04–11 可以先做闭卷预测、源码走读、纸面 Trace、故障分析与架构答辩；若继续工程化，下一增量应从 I04 状态/队列沿同一 Lab 骨架实现，并按 TDD 逐章推进，不能把文档示例冒充运行证据。
