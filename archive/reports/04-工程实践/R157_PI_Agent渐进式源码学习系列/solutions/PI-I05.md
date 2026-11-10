> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I05 参考答案

> 一句话结论：AgentSession 的核心价值是让能力、历史与恢复策略围绕同一个 Core Agent 保持可解释的一致性。

## E05-1

| 职责 | 首要 owner |
|---|---|
| transcript、`pendingToolCalls` | `Agent` |
| Skill/Prompt Template 展开 | `AgentSession` |
| Provider auth、headers/env | `ModelRuntime` |
| transient retry | `AgentSession` |
| Tool Registry 与 System Prompt 同步 | `AgentSession` |
| new/resume teardown 旧 Session | `AgentSessionRuntime` |
| cwd-bound services、diagnostics | `AgentSessionRuntime` |
| steer/follow-up | `Agent`（Session 提供产品入口与 UI 跟踪） |
| `message_end` 写 SessionManager | `AgentSession` |
| Provider `streamSimple` 路由 | `ModelRuntime` |

最容易混淆的是 `AgentSession` 与 `AgentSessionRuntime`。错误示例是调用 `runtime.prompt(text)`：Runtime 持有 `runtime.session`，它的职责是替换整套运行环境，不是代理每个 Prompt。

## E05-2

主顺序：

1. try extension command；
2. emit input hook；
3. expand skill/template；
4. 若 streaming：queue steer/follow-up 并返回；
5. 若非 streaming：validate model/auth；
6. pre-prompt compaction check；
7. build user + nextTurn messages；
8. emit before_agent_start；
9. agent.prompt；
10. post-run retry/compaction decision；
11. 条件成立时 agent.continue，并回到 10；
12. agent_settled。

前三步两分支共用；第 4 步是 streaming 分支，第 5–9 步是启动新 Run 的非 streaming 分支；10–12 属于 `_runAgentPrompt` 外层结算。

public `prompt()` 负责解释/验证输入，private `_runAgentPrompt()` 负责运行与恢复，直到一次产品请求 settled。

## E05-3

合格断言包括：

```ts
// 伪代码/待实现，未运行
assert.deepEqual(agent.tools.map(t => t.name), ["read", "edit"]);
assert.deepEqual(parseAvailableToolNames(agent.systemPrompt), ["read", "edit"]);
assert.equal(parseGuidelines(agent.systemPrompt).includes(BASH_ONLY_RULE), false);
assert.equal(agent.tools.some(t => t.name === "unknown"), false);
assert.deepEqual(nextTurnSnapshot.tools.map(t => t.name), ["read", "edit"]);
assert.equal(nextTurnSnapshot.systemPrompt, agent.systemPrompt);
```

使用结构化的 `parseAvailableToolNames` 或带边界的章节解析，比全文 `includes("bash")` 更可靠，因为 Prompt 的文档路径或示例可能合法出现单词 bash。

mutation 只改 tools 时，第一条通过、Prompt 与 next-turn coherence 断言失败，准确暴露 advertised/callable 漂移。

## E05-4

1. `input` 先于 Skill/模板展开，所以后者看到转换后的文本。
2. 基础 User Message 先加入；pending next-turn messages 随后；`before_agent_start` 返回的 custom messages 再追加。
3. `message_end` Extension replacement 通过 in-place 同步后，A' 进入 Agent state、后续 events 与 Session history。
4. P1 是本 Turn override；`_runAgentPrompt` finally 清的是 override 标记。settled 后 `agent.state.systemPrompt` 可能暂时仍显示 P1，但下一独立 Prompt 若无新 override，会在 `before_agent_start` 处理后重置为 base，因此 P1 不进入下一次 Core Run。
5. `tool_call` Hook 返回 block 时，工具业务函数不执行，管线产生错误 ToolResult。

## E05-5

| 时刻 | Agent Context | Session audit |
|---|---|---|
| 529 `message_end` | 追加 error Assistant | append error Assistant |
| `agent_end` | error 仍在尾部 | 已保留 |
| `_prepareRetry` | 删除尾部 error | 不删除 |
| backoff | 等待 | 历史不变 |
| `agent.continue` | 从清理后的 Context 继续 | 仍可审计失败 |
| success `message_end` | 追加 success Assistant | append success Assistant |
| `agent_settled` | 稳定 | 稳定 |

持久化前吞错会失去故障审计、成本计数与调试证据；留在重试 Context 尾部则模型可能把错误回复当作对话事实，且 `continue()` 的尾部角色/语义会不正确。

## E05-6

| 情况 | 分类 | 自动继续要点 |
|---|---|---|
| HTTP 529、rate limit | 普通 retry | 指数退避预算允许时 continue |
| 当前模型 context overflow | overflow compaction | 删除 Context 错误、压缩、最多一次恢复 |
| 成功但 usage 超窗口 | overflow compaction 的成功响应分支 | 可压缩但不重放已完成回答 |
| 接近阈值、回答成功 | threshold compaction | 压缩，通常不自动 continue |
| 用户 abort | 不自动恢复 | 交还用户决定 |
| overflow 恢复过一次仍失败 | 不再自动恢复 | 防无限 compact-and-retry |

所有已发 `message_end` 的错误/回复都可保留 Session 历史；Agent Context 是否删除取决于恢复分支。Compaction 增加摘要调用和失真风险，普通 retry 增加调用与退避延迟。

## E05-7

`Agent.subscribe` 接受 async listener 并逐个 await；`AgentSession.subscribe` 的 listener 类型是 `(event) => void`，`_emit` 直接调用，不等待 Promise。

所以关键 durability 不应依赖外部 async `AgentSession.subscribe`。Pi 内部把 async `_handleAgentEvent` 注册到下层 `Agent.subscribe`；它内部 await Extension，再执行 `message_end` 持久化，因此属于 Core Run settlement。

测试应给两个 listener 各自一个 deferred gate：Agent listener gate 未放行时 prompt 不 settle；Session listener 若返回 Promise，单靠该 Promise 不会阻止内部 `_emit` 返回。测试需要捕获未处理 Promise，避免把异步 throw 当同步断言。

## E05-8

正确状态机是：

```text
before-switch hook
→ shutdown event
→ synchronous host UI detach
→ old session.dispose()
→ create cwd-bound services/session
→ apply new session/services/diagnostics
→ host rebind
→ replaced-session callback
```

只改 `cwd` 会让 ResourceLoader、tools 的工作目录、SessionManager、trust context、extensions、model/session services 等仍绑定旧环境，形成“字段是新的，依赖图是旧的”。

创建失败应向调用者传播；不能复用已 dispose 的旧实例冒充成功。

## E05-9

一种合理分类：

| 调用 | 类型 | 主要风险 |
|---|---|---|
| Tool Call 请求 | 主回答 | 输入 Context Token、工具延迟 |
| final 请求 | 主回答 | 输入再次携带历史与 ToolResult |
| transient 后 continuation | 普通 retry | 重复输入 Context、退避尾延迟 |
| compaction summary | 压缩 | 额外输入旧历史、摘要失真 |
| summary transient retry | 压缩重试 | 再次支付摘要输入与延迟 |

不能仅说“用户只问了一次所以一次调用”。成本预算应同时统计主回答模型调用、Provider retry、Agent-level continuation、compaction/summarization 调用；它们的重叠方式需靠真实 Trace 计数，本题不推断具体 Token。
