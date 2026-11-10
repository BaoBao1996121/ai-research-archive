> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I03 练习：让工具管线在失败中长出来

> 一句话结论：这组练习要求同时证明安全不变量、时间顺序和上下文顺序。

## E03-1 · 校验门

创建 `positive` 工具，只接受 `{value: 正数}`。传入 `-1`，在 execute 中递增计数。

验收：计数为 0；结果 `isError=true`；错误文本能定位 `value`。

## E03-2 · 异常消息化

让工具抛出 `new Error("boom")`。

验收：批次 Promise 不 reject；得到关联原 `toolCallId` 的错误 ToolResult。

## E03-3 · 双顺序

先写下预测，再运行 30ms 的 slow 与 1ms 的 fast：

- `completionOrder` 是什么？
- `results.map(toolCallId)` 是什么？
- 若直接在 Promise resolve 时 `messages.push`，哪个不变量会被破坏？

## E03-4 · 整批串行

给 slow 标记 `executionMode: "sequential"`，用 `active/maxActive` 检测重叠。

验收：`maxActive === 1`，包括同批另一个默认 parallel 工具。

## E03-5 · Hook 信任边界

Schema 要求 `value:number`，before hook 在校验后把它改成 String。分别运行：

1. 默认 Pi-faithful 模式；
2. `revalidateAfterBeforeHook:true`。

解释两种结果，并明确哪一个是 Pi 当前事实、哪一个是课程强化。

## E03-6 · 安全分类

把下面控制分别归为 validation、authorization 或 isolation：

- `path` 必须是 string；
- 当前用户能否读取 `/secrets`；
- Bash 在无网络容器里运行；
- Tool Call 因 `stopReason=length` 被拒绝；
- Extension Hook 输出再次过 Schema。

## Hint ladder

- Hint 1：先看失败测试的 execute 计数或顺序数组。
- Hint 2：预检失败也需要一个与原 call 对应的 Finalized 结果。
- Hint 3：并发执行可用 Promise；结果数组的构造时机决定源顺序能否保留。
- Hint 4：整批模式在执行任何工具前由所有 Tool Call 与 Tool metadata 决定。

## Exit Ticket

闭卷画出工具状态机，再写一句“参数校验为什么不是沙箱”。

