> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# PI Agent 学习词汇表

> 一句话结论：术语按本课程和固定源码的具体含义使用，避免拿通用 Agent 黑话替代代码职责。

| 术语 | 本系列中的精确定义 | 常见误解 |
|---|---|---|
| Model | 模型能力、协议类型与计费等数据描述 | 以为它自己发网络请求 |
| Provider | 鉴权、模型列表、请求/流实现的运行单元 | 与 `api` 协议字段混为一谈 |
| Context | 一次模型请求可见的 system/messages/tools | 等同完整 Session 历史 |
| Transcript | 会话中按因果追加的消息轨迹 | Provider 本次一定看到全部内容 |
| AgentMessage | Agent 层可扩展消息 | 等同 pi-ai 的三种 Message role |
| ToolResult | 与 Tool Call ID 对应、回灌模型的正式消息 | 只是 UI 日志 |
| Turn | 一次 Assistant 响应及其整批工具结果 | 一整个用户任务 |
| Agent Run | 从一次 prompt/continue 到 `agent_end` | 只含一个模型请求 |
| AgentState | `Agent` 从事件流归约出的当前 streaming/message/tool/error 状态 | 永久 Session 历史 |
| AgentSession | 产品控制面：输入预处理、能力编译、持久化、retry/compaction 与事件汇聚 | Agent Loop 的另一个名字 |
| AgentSessionRuntime | 协调 new/resume/fork 时 Session teardown、替换与宿主 rebind | 只保存一个 Session 指针 |
| Steering | 当前工具批次结束后、下一次 Assistant 前注入的消息 | 硬中断正在执行的工具 |
| Follow-up | Agent 本来要停止时才检查的后续消息 | 与 Steering 同时机 |
| Request view | `transformContext/convertToLlm` 后给 Provider 的临时视图 | 会永久删除 transcript 历史 |
| ResourceLoader | 发现、合并并诊断 context、skill、prompt、extension、theme 等资源 | System Prompt 本身 |
| Project Trust | 是否装载项目本地设置、包和 Extension 的决策 | cwd 文件围栏或 OS sandbox |
| Session tree | append-only JSONL entries 通过 parent 构成的分支轨迹 | 长期语义记忆库 |
| Compaction | 在上下文预算下把旧轨迹压成可继续的摘要/边界 | 无损压缩 |
| Extension | 在显式 Hook/Tool/Provider 等扩展点改变 Harness 行为 | 天然可信或自动沙箱化 |
| Adapter | 把 TUI/CLI/JSONL/函数调用翻译到 Session port，并呈现事件 | 自己实现一套 Agent Loop |
| RPC ack | 某条命令通过 preflight、已接受/入队的协议确认 | Agent 任务已经 settled |
| Run Envelope | deadline、Provider/Tool/Token/费用等共享硬预算 | System Prompt 中的软提醒 |
| Action record | 独立记录外部动作 planned/executing/committed/failed/unknown 与幂等键 | 自然语言 ToolResult |
| Fail-closed | 输入完整性不确定时拒绝副作用，并返回可恢复错误 | 直接令进程崩溃 |
| Completion order | 工具实际完成的时间顺序 | 必须等于模型结果顺序 |
| Source order | Assistant 原 Tool Call 的顺序 | 等同实际完成顺序 |
| Teach-back | 闭卷解释机制、原因与边界，并能回应反例 | 照着原文复述 |
