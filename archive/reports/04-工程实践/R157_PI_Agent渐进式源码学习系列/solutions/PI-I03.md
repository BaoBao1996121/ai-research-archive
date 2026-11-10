> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I03 参考答案

> 一句话结论：可靠管线既要让失败可恢复，又要让并发不改变模型看到的因果顺序。

## E03-1 / E03-2

lookup、prepare、validate、before 的任何失败都应直接产生 error ToolResult；execute 与 after 的异常也转为 error ToolResult。两类都不应让整个 Agent Promise reject。

## E03-3

```text
completionOrder = [fast, slow]
model-facing results = [slow, fast]
```

直接在 resolve 时 push 会让 transcript 依赖调度和网络时延，破坏确定性重放与 Tool Call 对应关系。

## E03-4

只要同批任一 Tool metadata 标记 sequential，Pi 选择整个串行分支。它没有把单个 sequential 工具放进独立 lane。

## E03-5

默认模式会执行被 Hook 改坏的参数，这是当前 Pi 行为的忠实展示；开启二次校验后会得到错误 ToolResult，execute 计数不增加。后者是课程 hardening，不是上游事实。

## E03-6

| 控制 | 分类 |
|---|---|
| `path` 是 string | validation |
| 用户能否读 `/secrets` | authorization |
| 无网络容器 | isolation |
| length Tool Call 拒绝 | 输入完整性 / fail-closed（不是权限） |
| Hook 后再次 Schema | validation / 信任边界强化 |

生产安全需要三类控制协同；只做 Schema validation 仍能用合法字符串访问不该访问的路径。
