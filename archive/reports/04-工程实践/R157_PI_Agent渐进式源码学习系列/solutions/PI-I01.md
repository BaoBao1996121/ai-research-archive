> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I01 参考答案

> 先完成练习再阅读。重点是协议边界与可预测行为，不是背类型名。

## A. 三种形态

| 项目 | 分类 | 理由 |
|---|---|---|
| `Context` | 输入快照 | 调用模型前准备的系统提示、历史消息与工具 |
| `tools` | 输入快照的一部分 | 告诉模型可表达哪些 Tool Call |
| `text_delta` | 形成过程 | 只是一段增量，不能单独代表完整回复 |
| `toolcall_delta` | 形成过程 | Tool Call 参数的增量片段 |
| `AssistantMessage` | 终态快照，也可作为 partial 的类型载体 | 最终承载完整内容与停止原因 |
| `done.message` | 终态快照 | 成功终止事件携带的完整消息 |
| `stopReason` | 终态语义；partial 时可暂为 `pending` | 决定 Loop 下一步行为 |

字段可以跨层出现。例如 `partial` 与最终消息都带 `content`，但前者会随事件更新，后者在 terminal event 后才可视为完成。

## B. 事件文法

```text
Text:     start → text_start → text_delta → text_end → done
ToolCall: start → toolcall_start → toolcall_delta → toolcall_end → done
Failure:  start → ... → error
```

1. 不等价。`text_end` 只结束一个文本内容块；消息后面仍可能有其他内容块，整条流由 `done/error` 终止。
2. `toolUse` 表示模型成功生成了一个需要宿主执行的行动意图。失败的是运行时请求或生成时，才进入 `error/aborted`。
3. 一条 Assistant 可包含多个文本、思考或 Tool Call 块；`contentIndex` 指明 delta 更新哪个块。

## C. 非法 `pending`

可加入的测试形态：

```typescript
test("pending cannot be a final scripted response", async () => {
  const model = new ScriptedModel([{
    role: "assistant",
    content: [{ type: "text", text: "42" }],
    stopReason: "pending",
  }]);
  await assert.rejects(async () => {
    for await (const _event of model.stream({ messages: [] })) { /* drain */ }
  }, /cannot be pending/);
});
```

抛错前顺序是 `start → text_start → text_delta → text_end`，没有 `done/error`。这是 Mini Pi 主动暴露“脚本夹具写错”的方式；真 Pi 的 `StreamFunction` 契约要求请求、模型或运行时失败进入 `error` 终止事件及错误 Assistant Message，而不是从已启动的流随意抛出。

## D. 错误协议

Mini Pi `ScriptedModel` 对该响应发出：

```text
start → error(reason=error, error.errorMessage="network disconnected")
```

消费者在 `for await` 中检查 `event.type === "error"`，从 `event.error` 获取终态消息。真 Pi 的 `AssistantMessageEventStream.result()` 对 `error` 分支同样返回 `event.error`；“返回错误消息”不代表把失败当成功，而是把失败纳入同一条可观察终止协议。

## E. 新 Provider

一种合理映射：

```text
start
→ text_start(contentIndex=0)
→ text_delta("4")
→ text_delta("2")
→ text_end("42")
→ done(reason="stop", message.content="42")
```

1. Agent Loop 不应增加供应商名称分支；变化应收敛在 Adapter/Provider 注册与分派层。
2. `normal` 映射为统一的 `stop`。
3. 会影响宿主语义或后续请求连续性的元数据应保留，例如 response id、签名、Usage；纯传输封装字段可在 Adapter 内消化。判断原则不是“厂商专属就删除”，而是“上层是否需要它维持正确语义、成本核算或可诊断性”。

## F. 固定源码

1. [`AssistantMessageEvent`](https://github.com/earendil-works/pi/blob/063fb963c5c33d099faa593d17e60e0a875430cd/packages/ai/src/types.ts#L491-L503) 的终止分支是 `done` 与 `error`：前者带 `message`，后者带 `error`，两者的值都是 Assistant Message。
2. [`AssistantMessageEventStream`](https://github.com/earendil-works/pi/blob/063fb963c5c33d099faa593d17e60e0a875430cd/packages/ai/src/utils/event-stream.ts#L69-L82) 把两类事件都识别为完成事件，并分别提取 `message` 或 `error` 作为 `result()` 的结果。
3. [`compat.ts` L275–288](https://github.com/earendil-works/pi/blob/063fb963c5c33d099faa593d17e60e0a875430cd/packages/ai/src/compat.ts#L275-L288) 在 `streamSimple()` 内选择内建 Provider 或按 API 解析的 Provider；两个分支都返回 `AssistantMessageEventStream`，所以调用方类型不变。
4. 真 Pi 额外包含：`thinking`/image 内容、API 与 Provider 标识、模型与 response id、Usage/成本、timestamp、diagnostics、签名等。答出任意五类即可。

## G. 与 PI-I00 交错

按子系统：

- Model：`model:start`、所有 `model:*_start/delta/end`、`model:done`。
- Tool：`tool_execution_start/end`。
- Agent：`agent_start/end`、`turn_start`、`message_end:*`、`tool_batch_end`。

按数据性质：

- Transcript 最终写入的是 User、两条 Assistant 与 Tool Result；在 Trace 中对应可见的完成点是 `message_end:assistant/toolResult`。
- `model:*`、Agent 生命周期和 Tool 生命周期是观察事件，不作为独立消息逐条塞入模型上下文。

`model:done` 表示统一模型流已得到终态 Assistant Message；`message_end:assistant` 表示 Agent 已把该终态纳入自身消息生命周期。前者属于模型协议，后者属于 Agent 事件，所以相邻但不重复。

## H. Teach-back 示例

Provider Adapter 把各厂商原始数据统一成 `Context` 输入与以 `done/error` 终止的 Assistant 事件流，让 Agent Loop 只依据统一 `stopReason` 决定停止或调用工具。它不应抹掉维持语义所需的能力，例如 thinking 签名或 Usage；但厂商的 chunk 字段名、结束码写法等不应泄漏进 Loop。这样新增或升级 Provider 时，控制策略无需跟着改。

