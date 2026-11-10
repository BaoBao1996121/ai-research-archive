> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I01 练习：统一模型与消息协议

> 规则：答案另存；先预测事件序列，再运行测试。遇到困难时先查固定提交源码断点，不要直接打开 `solutions/`。

## A. 三种形态分类

把下列项目归入“输入快照 / 形成过程 / 终态快照”，并说明理由：

- `Context`
- `text_delta`
- `AssistantMessage`
- `tools`
- `done.message`
- `toolcall_delta`
- `stopReason`

然后回答：同一字段能否同时出现在过程事件与终态消息中？举一例。

## B. 事件文法

闭卷补全：

```text
Text:     start → __________ → __________ → __________ → done
ToolCall: start → __________ → __________ → __________ → done
Failure:  start → ... → __________
```

再回答：

1. `text_end` 与 `done` 是否等价？
2. `done(reason=toolUse)` 为什么不是 `error`？
3. `contentIndex` 解决什么问题？

运行核对：

```powershell
cd "C:/Users/USER\Documents\Codex\2026-07-28\new-chat-2\outputs\PI-Agent-Learning-Series"
.\lab\run-tests.ps1 -Iter iter01
```

## C. 非法终态故障注入

在 `lab/tests/iter01-protocol.test.ts` 的临时副本里新增一个测试：构造带文本内容、但 `stopReason="pending"` 的脚本响应。

要求先预测：

1. 抛错前会依次发出哪些事件？
2. 是否会发 `done` 或 `error`？
3. 为什么这属于课程夹具错误，而不是真 Pi 推荐的运行时失败表达？

测试必须用 `assert.rejects` 捕获异常，并匹配错误消息中的 `cannot be pending`。验证后恢复正式文件。

## D. 错误也是协议数据

设计一个脚本响应：

- `role="assistant"`
- `content=[]`
- `stopReason="error"`
- `errorMessage="network disconnected"`

写出预期事件序列，并说明消费者如何在不使用 `try/catch` 处理模型运行时失败的情况下获得终态错误消息。

提示：比较 Mini Pi 的 `ScriptedModel` 行为与真 Pi `StreamFunction` 的注释契约；不要假设两者完全相同。

## E. 新 Provider 设计题

假设接入一个供应商，其原始流只有：

```text
begin
token("4")
token("2")
finish(reason="normal")
```

写出 Adapter 的统一输出。然后回答：

1. Agent Loop 是否应该新增该供应商的名称分支？
2. 原始 `normal` 应映射成哪个统一停止原因？
3. 哪些 Provider 专属元数据应保留，哪些可以只在 Adapter 内消化？给出判断原则。

## F. 固定源码核对

只使用提交 `063fb963c5c33d099faa593d17e60e0a875430cd`：

1. `AssistantMessageEvent` 的两个终止分支是什么？各自携带哪个字段？
2. `AssistantMessageEventStream.result()` 如何从这两个分支得到统一的 `AssistantMessage`？
3. `streamSimple()` 在哪一层选择 Provider？为什么这不要求调用方改变返回类型？
4. 真 Pi 的 `AssistantMessage` 比 Mini Pi 多出至少五类什么信息？

## G. 与 PI-I00 交错

给 PI-I00 的 20 个标签做两次分类：

1. 按子系统分为 Model / Agent / Tool；
2. 按数据性质分为“会进入 Transcript / 只用于观察”。

说明 `model:done` 与 `message_end:assistant` 为什么相邻但不重复。

## H. Teach-back 提交

用不超过 180 字解释：

> Provider Adapter 统一了什么，没有统一什么？为什么这让 Agent Loop 更稳定？

必须包含 `Context`、`done/error`、`stopReason`，并举一个“不应该泄漏进 Loop 的供应商差异”。按课程 Rubric 自评 0～3。

## 24h / 7d 卡片

### 24h

- 闭卷写出三种 Message role。
- 闭卷写出两条成功事件文法和一个失败终止事件。
- 解释 `toolUse` 为什么是“模型成功、Agent 未完”。

### 7d

- 把一个陌生供应商的 token 流映射成统一协议。
- 将协议事件嵌回 PI-I00 的模型→工具→模型控制流。
- 回答：如果没有 terminal event，`result()` 会遇到什么语义问题？

