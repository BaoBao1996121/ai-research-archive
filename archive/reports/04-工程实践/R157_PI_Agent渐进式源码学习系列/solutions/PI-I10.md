> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I10 参考答案

> 一句话结论：正确答案围绕稳定 Session 语义、入口特定协议和显式生命周期，而不是把所有输出强行做成一样。

## E10-1

> 结论：队列、compaction 与 transcript 属于 Core；解析、确认、渲染和重绑属于外围职责。

| 项 | 归属 |
|---:|---|
| 1 | 输入 Adapter |
| 2 | AgentSession Core |
| 3 | 输出 Presenter |
| 4 | AgentSession Core |
| 5 | Runtime 生命周期 |
| 6 | 输出 Presenter |
| 7 | AgentSession Core |
| 8 | 输入/协议 Adapter |

最危险的重复项是 2、4、7：它们定义会话行为和因果顺序。5 若每个长驻入口各自随意实现，也会造成监听器泄漏；但其正确归属仍是 Runtime/Host 生命周期，而非 Agent Loop。

## E10-2

> 结论：先把入口输出投影为 Core artifact，再比较。

示意：

```text
normalize(print):
  final assistant = stdout text
  return {messages:[assistant], toolExchanges:[], stopReason:"stop"}

normalize(jsonEvents):
  discard deltas/timestamps/acks/render events
  collect message_end and paired tool events
  derive final assistant and stopReason
  return {messages, toolExchanges, stopReason}
```

真实实现不能仅从 Print stdout 重建完整 Tool 轨迹；因此严格等价测试应同时读取共享 Session transcript，或使用 JSON/SDK 两个能暴露全事件的入口。Print 只能验证其可观察契约子集。

## E10-3

> 结论：`success=true` 是接纳确认，文件副作用可能尚未发生。

正确等待至少需要该 run 的 settled/completion 语义，并确保没有待执行 Tool、retry、compaction 或 queued continuation。只看某次 `agent_end` 可能早于 Session 后处理；课程建议为宿主暴露单一 `settled` 事件或 `waitForIdle()`，并把 run id 贯穿事件，避免误收另一次任务的结束事件。

## E10-4

> 结论：decoder 先保留跨 chunk 字节，再只按 LF 切 record；JSON parser 在完整 record 上工作。

- U+2028：保留在字符串中，不切帧；
- UTF-8 跨 chunk：使用增量 decoder，不能分别 `toString()` 丢失字符；
- CRLF：按 LF 切后可移除记录末尾单个 CR；
- EOF 无 LF：若 buffer 非空，作为最后一条 record 交给 parser。

Framing 负责 chunk、UTF-8 与 record 边界；JSON parse 负责语法、对象形状和未知字段。空行是否允许是协议层决策，不应由 framing 悄悄吞掉。

## E10-5

> 结论：预期只观察 `A,C`，旧 Session 必须 unsubscribe 且 dispose 一次。

断言：

```text
renderedEvents == [A, C]
old.subscribeCount == 1
old.unsubscribeCount == 1
old.disposeCount == 1
new.subscribeCount == 1
new.unsubscribeCount == 0   # 直到最终 host dispose
runtime.session == new
```

若看到 `B`，说明旧监听器泄漏；若 `C` 重复，说明 rebind 重复订阅；若切换失败却旧 Session 已销毁，则替换事务的异常路径不完整。

## E10-6

> 结论：选型由语言、生命周期和边界决定。

| 场景 | 推荐 | 拒绝理由 |
|---|---|---|
| Node 桌面应用 | SDK | RPC 增加无必要的进程/序列化/协议维护 |
| Python IDE | RPC | SDK 是 TS/Node 直接 API，跨语言不自然 |
| CI 最终 Release Note | Print | 全事件 JSON 增加消费复杂度 |
| Shell 保存全事件 | JSON | Print 丢失中间事件 |
| 不可信租户 | RPC + 每租户容器/VM/低权限身份 | RPC 子进程本身不限制文件、网络和凭据 |

## E10-7

> 结论：可行方案是异步创建 run、SSE 订阅事件、Host 持有 Session，而 HTTP 层不接触 Loop。

参考契约：

```text
POST /sessions/{sessionId}/runs {requestId, prompt}
→ 202 {runId, acceptedAt}

GET /runs/{runId}/events?after={cursor}
→ SSE: {cursor, runId, sessionId, type, payload}

POST /runs/{runId}/abort
→ 202 {accepted:true}
```

`requestId` 做幂等接纳，`runId` 标识一次执行，`sessionId` 标识可持续会话。事件存储至少覆盖重连窗口；abort 必须验证调用者拥有该 run。Session replace 要先停止旧订阅，再绑定新对象；等价测试用同一 Fake Model 比较 SDK 与 HTTP 的 canonical transcript。

## 最小掌握答案

> 结论：入口共享的是真实业务状态和控制流，差异留在传输、呈现和生命周期；这仍不自动提供权限隔离、幂等或成本预算。
