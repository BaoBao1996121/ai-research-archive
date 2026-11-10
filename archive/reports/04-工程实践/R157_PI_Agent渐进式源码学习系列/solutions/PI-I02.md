> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I02 参考答案

> 一句话结论：答案的共同中心是“完整 transcript 驱动下一轮”，任何旁路状态都不能替代消息因果链。

## E02-1

```text
Turn 1: model #1 → append assistant(toolCall) → execute full tool batch → append ToolResult
Turn 2: model #2 → append final assistant
```

两个 Tool Call 属于同一个工具批次；整批结果完成后 Turn 1 才结束。

## E02-2

第二次请求会缺少 `toolResult` role。模型只能看到自己请求了工具，却看不到环境返回；同时 transcript 也无法完整重放这次因果关系。

## E02-3

判断必须在调用执行器之前：对每个 Tool Call 构造错误 ToolResult，文本说明 token limit 可能截断参数，然后继续下一次模型请求。即使残缺 JSON 恰好可解析/校验，也不能推断语义完整。

## E02-4

课程版会在第 3 个 Turn 完成后返回 `maxTurns`。真 Pi Core 没有固定默认上限；可通过 `shouldStopAfterTurn` 在完整 Turn 边界优雅停止，或用 Abort 做强制取消。

## E02-5

正确结果是协议错误。若提交 partial message，调用方无法区分“供应商正常结束”与“连接中途消失”，还可能把未完成 Tool Call 当成可执行输入。

