> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I05 练习：为 Agent 外层补上产品控制面

> 一句话结论：本组练习要求你同时守住能力一致性、持久化时序和恢复语义，避免把 `AgentSession` 写成一个只会转发 `prompt` 的壳。

> 实验状态：当前 Mini Pi 尚无 I05 实现。代码均为**伪代码/待实现设计题**，不得宣称已运行或测试通过；答案文件只在完成 Exit Ticket 后打开。

## E05-1 · 四对象所有权

把下列职责分配给 `Agent`、`AgentSession`、`AgentSessionRuntime` 或 `ModelRuntime`。每项只能有一个首要 owner：

- transcript 与 `pendingToolCalls`；
- Skill/Prompt Template 展开；
- Provider auth 与 headers/env 合并；
- transient retry；
- Tool Registry 与 System Prompt 同步；
- new/resume 时 teardown 旧 Session；
- cwd-bound services 与 diagnostics；
- steer/follow-up 队列；
- `message_end` 写 SessionManager；
- Provider `streamSimple` 路由。

然后指出哪两个对象最容易因名字相似被混淆，并给一个错误调用示例。

## E05-2 · Prompt 主链排序

将下列卡片排序，并把“仅 streaming 分支”“仅非 streaming 分支”“两者共用”标出来：

```text
emit input hook
expand skill/template
try extension command
queue steer/follow-up
validate model/auth
pre-prompt compaction check
build user + nextTurn messages
emit before_agent_start
agent.prompt
post-run retry/compaction decision
agent.continue (conditional)
agent_settled
```

解释 public `prompt()` 与 private `_runAgentPrompt()` 的分界。

## E05-3 · Prompt/Tool Coherence Test

初始 registry 有 `read,bash,edit`，三者都有 prompt snippet。调用：

```ts
// 伪代码/待实现
session.setActiveToolsByName(["read", "edit"]);
```

设计断言同时验证：

1. Agent Tools API 中只剩两个 callable tools；
2. System Prompt 的 available tools 不含 `bash`；
3. `bash` 专属 guideline 不出现；
4. unknown tool name 被忽略；
5. 下一 Turn Context 使用新工具和新 Prompt 的同一个快照。

再设计一个 mutation，故意只更新 tools 不重建 prompt；写出测试应怎样失败。不要只用全文字符串“不包含 bash”，说明如何降低误报。

## E05-4 · Extension Hook 时序

给定：

- `input` Hook 把 “fix” 转成 “fix src/a.ts”；
- Skill 命令展开会附加 `<skill>...`；
- `before_agent_start` 追加 custom message C，并临时把 system prompt 改成 P1；
- `message_end` Hook 把 Assistant 文本 A 改成 A'；
- Tool Hook 可以 block `write`。

回答：

1. Skill 展开看到的是 “fix” 还是转换后的文本？
2. Core Agent 首次输入消息顺序是什么？
3. 哪个 Assistant 版本进入 Agent state、Session history 与下游 events？
4. P1 是否应进入下一次独立用户 Prompt？
5. blocked tool 是否还应执行？

每个答案标出对应 Hook 边界。

## E05-5 · Retry 的双视图

第一次 Assistant 返回 retryable 529，第二次成功。画两列：

```text
Agent Context view | Session audit view
```

至少标出：

- 第一次 error `message_end`；
- SessionManager append；
- `agent_end`；
- `_prepareRetry` 删除；
- backoff；
- `agent.continue`；
- 成功 `message_end`；
- `agent_settled`。

回答：为什么不能在持久化前就吞掉第一次错误？为什么又不能把它留在重试 Context 尾部？

## E05-6 · Retry 与 Compaction 分类

把以下情况分给 “普通 retry”“overflow compaction”“threshold compaction”“不自动恢复”：

- HTTP 529；
- rate limit；
- 当前模型明确 context overflow；
- 成功响应但 reported usage 已超过配置窗口；
- context 接近阈值但当前回答成功；
- 用户主动 abort；
- overflow 已经 compact-and-retry 过一次仍失败。

为每类写：

- 是否删除 Agent Context 尾部错误；
- 是否保留 Session 历史；
- 是否自动 `continue()`；
- 额外模型调用与失真风险。

## E05-7 · 两种 subscribe 契约

比较：

```ts
// 伪代码/待实现
agent.subscribe(async event => await durableWrite(event));
session.subscribe(async event => await durableWrite(event));
```

问题：

1. 哪一个订阅 API 的类型/实现会等待 Promise？
2. 哪一个不应承载必须在 prompt resolve 前完成的关键落盘？
3. Pi 内部 Session persistence 为什么仍能处于 awaited barrier？
4. 设计一个 deferred Promise 测试来证明两者差异。

## E05-8 · Runtime 替换故障注入

设计 `switchSession` 的**伪代码/待实现**状态机，要求：

1. 先给 Extension 发 shutdown/switch 事件；
2. 同步撤下 host-owned UI binding；
3. dispose 旧 Session；
4. 用目标 cwd/session manager 重建 services 与 Session；
5. apply 新 runtime；
6. rebind host；
7. 若新 runtime 创建失败，不伪装为成功。

再解释为什么不能在旧 `AgentSession` 实例上只改 `cwd` 字段。

## E05-9 · 成本预算

一次用户 Prompt 发生：

- 主回答两次模型调用（第一次 Tool Call，第二次 final）；
- transient error 后整体 continuation 一次；
- threshold compaction 一次；
- compaction summary 自己 transient retry 一次。

不要计算 Token 具体数值；画调用分类表，至少区分主回答、重试、压缩、压缩重试。指出哪些调用可能重复输入大 Context，哪些风险是延迟、成本或摘要失真。

## Hint ladder

- Hint 1：public `prompt` 结束 preflight 后才进入 `_runAgentPrompt`。
- Hint 2：`setActiveToolsByName` 同时设置 `agent.state.tools` 和重建 base prompt。
- Hint 3：Session 的异步内部 handler 是 `Agent.subscribe` 的 listener。
- Hint 4：普通 retry 与 overflow recovery 的判断函数不同。
- Hint 5：`AgentSessionRuntime` 的关键词是 replace/teardown/recreate/rebind，不是 Prompt。
- Hint 6：ModelRuntime 的关键词是 auth/provider/request/stream，不是 Session tree。

## Exit Ticket

闭卷完成两张图：

1. `Prompt → preflight → Agent Run → event persistence → post-run recovery → settled`；
2. `Tool Definitions → callable tools + system prompt`。

再用一句话区分 `AgentSessionRuntime` 与 `ModelRuntime`。三项都正确才打开答案。

