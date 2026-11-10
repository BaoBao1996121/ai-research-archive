> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# Mini Pi TDD 证据日志

> 结论：Iter 00–03 的 10 个行为测试都由下列 RED→GREEN 循环驱动或保护，最终全绿；这不是“先写完代码再补测试”。

| Cycle | RED：观察到的失败 | GREEN：最小修正 | 最终证据 |
|---|---|---|---|
| PI-I01.1 文本事件 | `ScriptedModel.stream()` 抛出 `TODO Iter01` | 产生 `start → text_start → text_delta → text_end → done` | 文本协议测试通过 |
| PI-I01.2 工具事件 | 抛出 `TODO Iter01: tool-call streaming` | 增加统一 `toolcall_*` 事件 | Iter01 2/2 通过 |
| PI-I02.1 Loop | 两项测试都抛出 `TODO Iter02` | 追加 Assistant、执行工具、回灌 ToolResult、续轮 | 基础 Loop 2/2 通过 |
| PI-I02.2 Fail-closed | 截断 Tool Call 被错误执行，`1 !== 0` | `stopReason=length` 时只生成错误 ToolResult | Iter02 3/3 通过 |
| PI-I03.1 Validation/Error | 工具管线抛出 `TODO Iter03` | 校验、异常捕获、错误消息化 | 基础管线通过 |
| PI-I03.2 双顺序 | 串行实现给出 `slow → fast` 完成序 | 预检后并发执行，`Promise.all` 保持结果源顺序 | 完成序 `fast → slow`；结果序 `slow → fast` |
| PI-I03.3 Sequential override | 两工具重叠，`maxActive: 2 !== 1` | 任一工具声明 sequential 时整批串行 | override 测试通过 |
| PI-I03.4 Hook hardening | 开启二次校验后仍执行，`false !== true` | Hook 后可选再次 `validate()` | faithful/hardened 对照通过 |
| PI-I00 Integration | Whole Game 抛出 `TODO Iter00` | 装配 ScriptedModel、Loop、Tool Pipeline | 端到端 1/1 通过 |
| 严格类型 QA | `AgentTool<T>` 异构数组方差错误；事件回调意外返回 `number` | 对齐真 Pi 的 `AgentTool<any>[]` 容器；回调显式返回 void | TypeScript 5.9.3 `--strict --noEmit` 通过 |

最终命令：

```powershell
.\run-tests.ps1
```

最终结果（2026-07-31 实测）：`tests 10, pass 10, fail 0`。

额外静态证据：TypeScript 5.9.3 严格模式 `tsc --noEmit` 通过；该检查不改变 Lab 的零安装运行路径。
