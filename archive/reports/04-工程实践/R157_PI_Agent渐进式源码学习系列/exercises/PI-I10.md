> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I10 练习：证明入口薄，而不是看起来薄

> 一句话结论：这组练习用分类、协议反例和生命周期测试验证多入口共享内核。

## E10-1 · 三层归类

> 结论：先区分 Adapter、Core Port 与 Presenter，才能发现业务逻辑泄漏。

把下列职责归入“输入 Adapter / AgentSession Core / 输出 Presenter / Runtime 生命周期”：

1. 把 stdin JSON 解析成 `prompt`；
2. 判断是否需要 compaction；
3. 将 `text_delta` 画到终端；
4. 把 ToolResult 追加到会话；
5. `/resume` 后解绑旧订阅；
6. 将最终 Assistant 文本写 stdout；
7. 处理 Steering 队列；
8. 发出带 request id 的 command response。

指出哪两项若被四个入口重复实现，最容易产生语义漂移。

## E10-2 · 语义等价，不是字节等价

> 结论：为跨入口比较定义一个可执行的规范化规则。

给出以下两份输出：

下面的 JSON 事件是为了练习规范化而写的**教学简化 schema**，不是固定提交 `AgentSessionEvent` 的逐字段复制。

```text
Print stdout: 42
```

```json
{"type":"message_update","delta":"4","timestamp":101}
{"type":"message_update","delta":"2","timestamp":104}
{"type":"message_end","message":{"role":"assistant","content":"42"}}
{"type":"agent_end"}
```

写一个规范化函数的伪代码，使二者都得到同一个 `CanonicalRun`。至少保留：最终 Message、Tool Call/Result、stopReason；至少去掉：时间戳、渲染增量、入口确认。

## E10-3 · 两个时钟

> 结论：画出 command ack 与任务完成之间的竞态。

客户端发送 `prompt(req-7)`，收到 `success=true` 后立即读取 Agent 将要生成的文件。解释为什么可能读到旧内容。写出正确等待条件，并说明只等 `agent_end` 在 auto-retry/compaction 场景下是否总够。

## E10-4 · 严格 JSONL

> 结论：构造一个会骗过通用行读取器的合法 JSON record。

1. 在 JSON 字符串中包含 U+2028；
2. 将一个 UTF-8 字符拆到两个网络 chunk；
3. 输入使用 CRLF；
4. 最后一条记录没有 LF。

逐项说明正确 reader 应怎样处理。再列出 framing 与 JSON parse 各自负责的错误。

## E10-5 · Session rebind 泄漏

> 结论：测试要观察旧 Session 的副作用，而不只比较对象引用。

设计一个 Fake Session/Runtime 测试：

- old/new 都能 `subscribe()` 和发事件；
- switch 前 old 发 `A`；switch 后 old 发 `B`、new 发 `C`；
- 记录 subscribe/unsubscribe/dispose 次数。

写出全部断言及预期事件序列。

## E10-6 · 入口选型

> 结论：每个场景给一个明确推荐和一个拒绝理由。

分别选择 TUI、Print、JSON、RPC 或 SDK：

1. Node 桌面应用，需要深度定制工具和直接状态访问；
2. Python IDE 插件，需要长驻双向流；
3. CI 只需要最终 Release Note；
4. Shell 管道要保存每个 Agent 事件；
5. 不可信租户请求需要强 OS 隔离。

第 5 项不能只答“RPC”，还要补出真正的隔离层。

## E10-7 · 第五入口设计

> 结论：设计 HTTP `POST /runs` + SSE Adapter，但禁止导入 Agent Loop。

交付：

- 端口接口；
- request id / run id / session id 的关系；
- ack、event、settled 三类消息；
- 断线重连与事件游标；
- abort 的鉴权规则；
- Session 替换时的 rebind；
- 与 SDK 入口的规范化一致性测试。

## Hint ladder

> 结论：一次只打开一层提示。

- H1：Core 决定“发生什么”，Adapter 决定“怎样传进来/展示出去”。
- H2：RPC `success` 只代表 preflight 接受；业务完成来自后续事件。
- H3：跨入口等价性可比较 transcript，而不是 stdout。
- H4：rebind 测试必须让旧对象在切换后主动发事件。
- H5：HTTP 入口可返回 `202 Accepted + runId`，SSE 用单调 event cursor 续传。

## Exit Ticket

> 结论：闭卷用三句话解释为什么“一个 Session、多种 Adapter”比“四套 Loop”更可靠，再说出它仍未解决的一项生产问题。
