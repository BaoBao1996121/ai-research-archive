> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I00 练习：从 Trace 反推 Agent Loop

> 规则：先闭卷提交预测，再运行；不要边看答案边填。建议把答案写在独立笔记中，保留第一次版本。

## A. 检索而非重读

1. 写出成功执行一次 `add` 后的四条 Transcript role，给每条补一句语义。
2. 为什么同一次用户任务里会出现两条 Assistant Message？
3. 用一句话区分 Transcript 与 Event Trace。

## B. 运行前预测

假设 `ScriptedModel` 的第一个响应改为普通文本 `"42"`，`stopReason="stop"`：

1. 模型会被调用几次？
2. Transcript role 顺序是什么？
3. 下列事件哪些不会出现：`tool_execution_start`、`tool_batch_end`、第二个 `turn_start`、`agent_end`？
4. 第二个脚本响应会怎样？

写完后再用临时副本验证，不要改正式答案文件。

## C. 源码寻宝

只使用固定提交 `063fb963c5c33d099faa593d17e60e0a875430cd`：

1. 在真 Pi 的 `packages/agent/src/agent-loop.ts` 中找到 Tool Result 同时进入 `currentContext.messages` 与 `newMessages` 的位置，记录函数名和行号。
2. 找到“没有更多 Tool Call 时退出内层循环”的控制变量。它在什么情况下被重新设为 `true`？
3. 找到 `agent_end` 的正常结束位置，以及错误/中止的提前结束位置。说明它们为什么不是同一条路径。

## D. 故障注入

在临时副本中把 `lab/src/whole-game.ts` 的：

```typescript
new ScriptedModel([request, answer])
```

改成：

```typescript
new ScriptedModel([answer, request])
```

然后执行：

```powershell
cd "C:/Users/USER\Documents\Codex\2026-07-28\new-chat-2\outputs\PI-Agent-Learning-Series"
.\lab\run-tests.ps1 -Iter iter00
```

记录：

1. 第一条失败断言的 expected 与 actual。
2. 为什么测试先在这里失败，而不是先报“没有执行 add”。
3. 用一个控制流不变量概括根因。

验证后恢复文件。

## E. Trace 压缩

把 20 个观察标签压缩为不超过 6 个阶段。每个阶段必须说明：

- 输入消息；
- 输出消息；
- 是否可能触发下一次模型调用。

限制：不能只写“开始、处理中、结束”这类无语义阶段。

## F. 迁移题

假设工具执行器不存在，但模型仍产生 `toolCall:add`。你认为更好的行为是哪一种，为什么？

1. 直接抛异常并丢失 Transcript；
2. 生成 `isError=true` 的 Tool Result，再交给模型解释；
3. 把 Tool Call 当普通文本显示给用户。

回答时分别讨论可恢复性、可观察性和安全边界。这里只要求设计判断，不要求改代码。

## G. Teach-back 提交

不用“闭环”“编排”等抽象词，向初学者解释：

> LLM 为什么不会自己执行工具？Agent Loop 到底多做了哪三件事？

要求包含一条 role 序列、一个停止条件、一个失败例子。按课程 Rubric 自评 0～3。

## 24h / 7d 卡片

### 24h

- 闭卷写四条 role。
- 闭卷写两个循环不变量。
- 只在写完后运行 `run-demo.ps1` 核对。

### 7d

- 从空白画出模型→工具→模型时序图。
- 将 PI-I01 的 `start/delta/done` 嵌回本课 Trace。
- 回答：为什么“20 个事件”不等于“20 条上下文消息”？

