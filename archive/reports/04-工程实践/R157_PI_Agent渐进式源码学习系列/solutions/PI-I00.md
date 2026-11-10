> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I00 参考答案

> 先完成练习再阅读。参考答案用于校准不变量，不要求逐字一致。

## A. 检索题

1. `user`：提出任务；`assistant(toolCall)`：模型表达调用 `add` 的意图；`toolResult`：宿主程序返回真实执行结果；`assistant(text)`：模型基于工具结果生成面向用户的回复。
2. 第一条 Assistant Message 是行动请求，不是最终自然语言答案；第二条才看过 Tool Result，能把结果与原问题结合。工具可以直接算出 `42`，但通常不负责决定如何解释、格式化或继续推理。
3. Transcript 是下一轮模型可见的语义内存；Event Trace 是运行过程的观察信号，供 UI、日志与测试消费。

## B. 首轮直接文本

1. 模型调用 1 次。
2. Transcript 为 `user → assistant(text)`。
3. `tool_execution_start`、`tool_batch_end`、第二个 `turn_start` 都消失；`agent_end` 仍必须出现。
4. 第二个脚本响应保留在 `ScriptedModel` 队列里，永远不会被本次 Loop 消费。因为首个 Assistant 没有 Tool Call，Loop 正常停止。

## C. 源码寻宝

1. 真 Pi 在 `runLoop()` 的 [`agent-loop.ts` L218–220](https://github.com/earendil-works/pi/blob/063fb963c5c33d099faa593d17e60e0a875430cd/packages/agent/src/agent-loop.ts#L218-L220) 把每个结果同时放入 `currentContext.messages` 和本次返回的 `newMessages`。
2. 控制变量是 `hasMoreToolCalls`。每轮先在 L206 设为 `false`；存在 Tool Call 且执行批次没有要求终止时，L216 将它设为 `!executedToolBatch.terminate`。因此“有调用”本身还不够，批次终止策略也会影响是否继续。
3. 正常路径在 [`agent-loop.ts` L270–274](https://github.com/earendil-works/pi/blob/063fb963c5c33d099faa593d17e60e0a875430cd/packages/agent/src/agent-loop.ts#L270-L274)；`error/aborted` 在 [L196–200](https://github.com/earendil-works/pi/blob/063fb963c5c33d099faa593d17e60e0a875430cd/packages/agent/src/agent-loop.ts#L196-L200) 提前发出 `turn_end` 与 `agent_end`。错误路径不能继续执行可能不可信的 Tool Call，因此提前返回。

## D. 反转响应

1. 测试先在 `modelCalls` 断言失败：expected `2`，actual `1`。在它之前的 `answer` 断言仍通过，因为第一条响应正好是 `"The answer is 42."`。
2. `add` 执行次数没有独立排在前面的断言；测试按源码顺序先检查答案、调用次数，再检查 role 与 Trace。
3. 根因不变量：只有 Assistant Message 含 Tool Call 时 Loop 才进入工具分支并发起下一轮；普通文本使本次运行停止，未消费响应不会自动触发下一轮。

## E. 六阶段压缩示例

| 阶段 | 输入 | 输出 | 会否触发下一模型调用 |
|---|---|---|---|
| 1. Agent 启动 | User Message | 初始 Context | 是，开始第 1 Turn |
| 2. 模型提出行动 | Context(user) | Assistant(toolCall) | 先执行工具 |
| 3. 工具执行 | Tool Call | Tool Result | 是，结果回灌后继续 |
| 4. Context 扩展 | 先前三条消息 | Context + toolResult | 是，第 2 Turn |
| 5. 模型形成答案 | 扩展 Context | Assistant(text) | 否，无 Tool Call |
| 6. Agent 结束 | 最终 Assistant | Transcript + agent_end | 否 |

其他压缩方式也可以，但必须保留“Tool Result 回灌”和“无 Tool Call 才停止”。

## F. 无执行器

推荐第 2 种：生成 `isError=true` 的 Tool Result。

- 可恢复性：模型能看到结构化失败，可能改用其他工具或向用户解释限制。
- 可观察性：失败保留在 Transcript 和事件中，便于复盘。
- 安全边界：不能假装执行成功，也不应把未执行的指令当普通文本；但错误消息化不等于无限重试，仍需轮数上限与策略约束。

Mini Pi 的 `agent-loop.ts` 正是把“没有 executor”转为错误 Tool Result；真 Pi 对“工具不存在”也在工具准备阶段构造错误结果，而不是让 Provider 执行工具。

## G. Teach-back 示例

LLM 只生成 `toolCall` 这类结构化意图，不拥有宿主进程的执行权。Agent Loop 做三件事：识别并校验调用、让工具在程序里执行、把结果作为 `toolResult` 回灌，于是消息成为 `user → assistant(toolCall) → toolResult → assistant`。当新的 Assistant 不再含 Tool Call 时停止；若工具不存在，则应回灌错误结果，而不是伪装成功。

