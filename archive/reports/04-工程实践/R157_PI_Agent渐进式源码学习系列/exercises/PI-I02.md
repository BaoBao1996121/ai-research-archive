> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I02 练习：先预测，再运行

> 一句话结论：这组练习测的是你能否预测和修复 Loop，不是能否抄出 `while`。

## 规则

1. 先提交纸面/文本预测，再运行测试。
2. 每次只改一个行为，先看到 RED。
3. 最多按 Hint 1→4 逐级打开；最后才看 `solutions/PI-I02.md`。

## E02-1 · 事件与消息排序

把下列动作排序，并标出 Turn 边界：

```text
append final assistant
execute tool batch
model call #2
append assistant(toolCall)
append toolResult
model call #1
```

迁移问：如果一条 AssistantMessage 同时有两个 Tool Call，这一 Turn 在第一个工具结束后就结束吗？

## E02-2 · 破坏回灌

复制 `iter02-agent-loop.test.ts` 中的工具续轮案例，暂时让 Loop 不把 ToolResult 放进 `messages`。先预测哪个断言失败，再运行。

验收：第二次模型请求必须看到 `[user, assistant, toolResult]`。

## E02-3 · 截断副作用

构造 `stopReason: "length"` 的 `write` Tool Call，execute 内递增计数。要求：

- execute 计数为 0；
- 生成 `isError=true` ToolResult；
- 模型获得第二次机会重新发完整调用。

## E02-4 · 无限工具模型

写一个每次都返回 Tool Call 的确定性 ModelAdapter，将 `maxTurns` 设为 3。

验收：恰好 3 次模型调用后 `reason === "maxTurns"`。解释这与真 Pi 的 `shouldStopAfterTurn` 有什么不同。

## E02-5 · 违反 terminal 契约

写一个只发 `start/text_delta`、随后结束迭代器的 ModelAdapter。

验收：Loop 明确报 `Model stream ended without done or error`，而不是悄悄提交半条消息。

## Hint ladder

- Hint 1：看断言中的 `model.calls[1].messages`，不要先看实现。
- Hint 2：唯一可靠的循环输入是 transcript，不是局部变量。
- Hint 3：`length` 分支必须发生在 `executeTools()` 之前。
- Hint 4：伪代码：`terminal → append assistant → calls? → results → append → continue`。

## Exit Ticket

闭卷写三句话：一个核心不变量、一个最容易混淆点、一个尚未解决的问题。

