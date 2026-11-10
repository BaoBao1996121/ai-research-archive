> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I04 练习：用时间线证明状态与队列语义

> 一句话结论：本组练习不要求背字段，而要求你从事件前缀重建状态，并证明排队、取消和结算是三件不同的事。

> 实验状态：当前 Mini Pi 尚无 I04 实现。代码题均为**伪代码/待实现设计题**，不得记录为“测试通过”；先提交预测、Trace 和测试设计，再看答案。

## E04-1 · 闭卷 reducer 表

初始状态：

```text
messages=[]
streamingMessage=undefined
pendingToolCalls={}
errorMessage=undefined
isStreaming=true
```

依次收到：

```text
message_start(A0)
message_update(A1)
message_update(A2)
message_end(A3 with toolCall R)
tool_execution_start(R)
tool_execution_end(R)
message_start(ToolResult R)
message_end(ToolResult R)
turn_end(A3, [ToolResult R])
agent_end(...)
```

为每一步填写：

1. `messages.length`；
2. `streamingMessage`；
3. `pendingToolCalls`；
4. `errorMessage`；
5. 此时 listener 能观察到归约前还是归约后的状态。

额外说明：为什么 `message_update` 不能追加 transcript？

## E04-2 · Listener Barrier

设计一个受控 Promise：第二个 listener 在 `agent_end` 上等待你手动 release。

写出**伪代码/待实现**测试的 Arrange / Act / Assert，证明：

- 两个 listeners 按订阅顺序运行；
- release 前 `prompt()` 和 `waitForIdle()` 都未完成；
- listener 内看到的 `state` 已完成本事件归约；
- release 后二者完成。

不要使用真实 timeout 作为唯一断言；说明如何用 deferred Promise 让测试确定化。

## E04-3 · steer 不是硬中断

场景：Assistant 已发 Tool Call，`slowWrite` 正在执行；此时收到用户输入“不要写了”。

分别推演：

1. 调用 `steer("不要写了")`；
2. 调用 `abort()`，但 `slowWrite` 忽略 AbortSignal；
3. 调用 `abort()`，且 `slowWrite` 主动检查 AbortSignal。

每种情况都回答：

- 当前工具是否必然停止；
- 新消息是否进入 transcript；
- 下一次模型调用何时可能看到它；
- 哪个结论是 Pi Core 保证，哪个取决于工具实现。

## E04-4 · 两个队列、两种模式

在同一个 Assistant Turn 中依次入队：

```text
steering: S1, S2
follow-up: F1, F2
```

分别对以下组合画出模型看到的用户消息批次：

| Case | steeringMode | followUpMode |
|---|---|---|
| A | all | all |
| B | one-at-a-time | all |
| C | all | one-at-a-time |
| D | one-at-a-time | one-at-a-time |

必须标出：

- steering drain point；
- Agent “本来要停止”的位置；
- 每次 drain 后队列剩余内容；
- 为什么 queue mode 不改变 FIFO 和两类队列的语义优先级。

## E04-5 · pendingToolCalls 的语义陷阱

`tool_execution_start` 已发出，随后发生：

1. tool lookup 失败；
2. Schema validation 失败；
3. `beforeToolCall` block；
4. 工具函数真正执行并成功。

对每种情况回答：

- start 时 `pendingToolCalls` 是否应包含 call id；
- 最终哪个事件负责删除；
- UI 文案写“工具正在执行业务代码”是否准确；
- 更准确的状态文案是什么。

## E04-6 · 故障注入设计

从下列破坏中任选两个，写“预期失败 → 最小修复 → 回归断言”：

- `message_update` 也 push 到 `messages`；
- listener 不 await，直接 fire-and-forget；
- `tool_execution_end` 忘记从 Set 删除 id；
- 每次 drain 总是取全部，忽略 `one-at-a-time`；
- 在工具批次中途轮询 steering；
- follow-up 与 steering 共用一个队列。

要求指出被破坏的不变量，不能只写“结果不对”。

## E04-7 · Teach-back

用不超过 180 字解释：

1. `agent_end` 为什么不等于 idle；
2. steering 为什么不是 interrupt；
3. `pendingToolCalls` 为什么是事件投影而不是线程采样。

让同伴按 0–4 分 Rubric 评分；低于 3 分时只重讲缺失边界。

## Hint ladder

- Hint 1：`processEvents` 的 switch 在 listeners 循环之前。
- Hint 2：`agent_end` 后还要等 listener，再由 `finishRun` 清 active run。
- Hint 3：steering 在 Turn 结束后 poll；follow-up 在内层循环本来结束后 poll。
- Hint 4：`one-at-a-time` 只改变一次 drain 取几条，不改变队列类型。
- Hint 5：I03 中 start 在 lookup/validation 之前，所以 pending 不等于业务函数占用 CPU。

## Exit Ticket

闭卷画出：

```text
event → reducer → state → awaited listeners → next event
```

再在图上添加 steering、follow-up 与 abort。若三条箭头落在同一点，说明仍未掌握边界。
