> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I04 参考答案

> 一句话结论：可靠的 Agent 状态是事件前缀的确定投影；可靠的结算边界还必须等待订阅者副作用完成。

## E04-1

| 事件后 | messages | streamingMessage | pendingToolCalls | listener 看到 |
|---|---:|---|---|---|
| `message_start(A0)` | 0 | A0 | {} | 归约后 |
| `message_update(A1)` | 0 | A1 | {} | 归约后 |
| `message_update(A2)` | 0 | A2 | {} | 归约后 |
| `message_end(A3)` | 1 | undefined | {} | 归约后 |
| `tool_execution_start(R)` | 1 | undefined | {R} | 归约后 |
| `tool_execution_end(R)` | 1 | undefined | {} | 归约后 |
| `message_start(ToolResult R)` | 1 | ToolResult R | {} | 归约后 |
| `message_end(ToolResult R)` | 2 | undefined | {} | 归约后 |
| `turn_end` | 2 | undefined | {} | 归约后 |
| `agent_end` | 2 | undefined | {} | 归约后；尚未必 idle |

若 A3 没有 `errorMessage`，本 Trace 的 `errorMessage` 始终为 undefined。`message_update` 是同一条 Assistant 草稿的替换快照；每次 push 会制造多个伪造的最终消息。

## E04-2

一个合格的**伪代码/待实现**结构：

```ts
// 伪代码/待实现，未运行
const gate = deferred<void>();
const order: string[] = [];

agent.subscribe(async event => {
  if (event.type === "agent_end") order.push("L1");
});
agent.subscribe(async event => {
  if (event.type === "agent_end") {
    order.push("L2-start");
    await gate.promise;
    order.push("L2-end");
  }
});

const promptDone = observeSettlement(agent.prompt(user));
const idleDone = observeSettlement(agent.waitForIdle());
await eventReached("L2-start");

assert.deepEqual(order, ["L1", "L2-start"]);
assert.equal(promptDone.settled, false);
assert.equal(idleDone.settled, false);

gate.resolve();
await Promise.all([promptDone.promise, idleDone.promise]);
```

关键是用 gate 控制时序，而不是赌 10 ms 内“应该没完成”。Reducer 在 listener 之前执行，所以 listener 的状态断言应读取事件后的 state。

## E04-3

| 动作 | 当前工具 | 新消息 | 模型何时看到 |
|---|---|---|---|
| `steer` | 不被它取消；当前批次继续 | 入 steering 队列，稍后作为 user message 注入 | 正常路径在当前 Turn 完成后的下一次 Assistant 请求 |
| `abort` + 工具忽略 signal | 收到取消请求但可能继续到自然结束 | abort 本身不创建 user message | 不适用；运行以 aborted 路径收束 |
| `abort` + 工具响应 signal | 可在检查点停止 | abort 本身不创建 user message | 不适用；若要继续需新 Prompt/队列消息 |

Core 保证 `steer` 只 enqueue、`abort` 触发 AbortController；真正停止速度取决于模型 transport 与工具是否响应 signal。

## E04-4

设当前 Turn 的工具已全部结束：

- A：第一次 steering drain 注入 `[S1,S2]`；本来要停时第一次 follow-up drain 注入 `[F1,F2]`。
- B：steering 先注入 `[S1]`，下一 Turn 边界再注入 `[S2]`；随后 follow-up 一次注入 `[F1,F2]`。
- C：steering 一次注入 `[S1,S2]`；follow-up 第一次只注入 `[F1]`，再次本来要停时注入 `[F2]`。
- D：`S1`、`S2` 分属连续 steering drain；`F1`、`F2` 分属连续 stopping drain。

四种情况都保持各自 FIFO。模式只决定 batch size；steering 仍只在 Turn 边界消费，follow-up 仍只在本来停止时消费。

## E04-5

四种情况在 start 事件后都把 id 加入 `pendingToolCalls`。lookup/validation/block 会被工具管线转成错误结果并发 `tool_execution_end`，由 end 删除 id；成功执行也相同。

因此 “工具正在执行业务代码”过强。更准确的是“工具调用正在处理”或“已进入工具执行管线，尚未结束”。

## E04-6

示例一：

- 破坏：`message_update` push transcript；
- 预期失败：一条流式回复产生多个 Assistant 历史项；
- 不变量：只有 terminal `message_end` 追加最终消息；
- 修复：update 只替换 `streamingMessage`；
- 回归：三次 update 后 transcript 仍为 0，end 后恰为 1。

示例二：

- 破坏：listener fire-and-forget；
- 预期失败：`prompt`/`waitForIdle` 先于关键持久化完成；
- 不变量：Agent listener Promise 属于 run settlement；
- 修复：在订阅循环内顺序 await；
- 回归：deferred gate release 前两个 completion 都不 settle。

其他破坏分别对应：pending Set 最终为空、queue mode 的 batch size、steering 只在 Turn 边界、两类队列保持不同消费时机。

## E04-7

参考讲法：

> `agent_end` 只保证 Loop 不再发事件；Agent 还要等待订阅者，随后 `finishRun` 才变 idle。`steer` 只是把消息排到当前 Turn 后，不会取消正在流式输出或执行的工具；硬取消走 `abort`。`pendingToolCalls` 由 tool start/end 事件增删，表示调用仍在管线中，不是对线程或 CPU 的实时采样。

达到 3 分必须同时出现 listener barrier、Turn 边界和 start/end 投影。
