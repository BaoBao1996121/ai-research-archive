> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I07 参考答案

> 一句话结论：JSONL 恢复的核心公式是 `last valid entry → leaf → parent chain → compaction-aware context`，公式里没有“重新执行 Tool”。

## E07-1 · 三种顺序

File order：

```text
Header, u1, a1, u2, a2, u3, a3
```

Tree：

```text
u1
└─ a1
   ├─ u2
   │  └─ a2
   └─ u3
      └─ a3  ← active leaf after reload
```

`_buildIndex()` 让最后一个非 Header Entry `a3` 成为 leaf。Active path 是 `u1 → a1 → u3 → a3`，所以模型 Context 不含 `u2/a2`；它们没有被删除，仍在完整 tree 中，可由 `/tree` 访问。

## E07-2 · branch 持久化

只 `branch(a1)` 后立即退出，没有任何文件记录 leaf 变化；再次打开仍取物理末行 `a3` 为 leaf。

若随后 append `u4(parent=a1)`：

```text
u1
└─ a1
   ├─ u2─a2
   ├─ u3─a3
   └─ u4  ← new physical last line / reload leaf
```

新 Entry 位于物理末尾，同时 parentId 指向选择的旧节点，于是 append-only 行本身编码了活动分支，不需修改旧 leaf pointer。代价是“只导航不续写”不会持久化。

## E07-3 · 操作差异

| 操作 | 同/新文件 | 复制/保留哪些 Entry | 编辑器初始内容 | Header parentSession |
|---|---|---|---|---|
| `/tree` 旧 User | 同文件 | 全树不变；leaf 移到该 User 的 parent | 原 User 文本，供修改 | 不新增 Header |
| `/fork` 旧 User | 新文件 | root→该 User 的 parent 的活动路径 | 原 User 文本，供修改 | 指向来源 Session |
| `/clone` | 新文件 | root→当前 active leaf | 空 | 指向来源 Session |
| CLI `--fork source` | 新文件 | 来源文件所有非 Header Entry | 按新会话继续 | 指向 source path |

`position="before"` 对 User Message 取 `selectedEntry.parentId` 并回填原文本；`position="at"` 把选中 Entry 本身作为目标 leaf。Clone 用当前 leaf + at。

## E07-4 · Compaction 投影

磁盘/tree 仍保留 `u1,a1,u2,a2,u3,a3,c1,u4,a4`。固定 `SessionManager.buildContextEntries()` 的顺序是：

```text
c1(summary), u3, a3, u4, a4
```

`u1/a1/u2/a2` 不再逐条进入模型，只通过 `c1.summary` 的有损文本间接出现。它不是长期语义记忆，因为没有语义查询、跨会话召回、事实 provenance、冲突更新/删除机制；它只是 active Context 的窗口检查点。

## E07-5 · 损坏矩阵

| 情况 | 预测 | 证据等级 | 恢复建议 |
|---|---|---|---|
| 尾部半行 | malformed line 被跳过；此前有效末行成为 leaf | 源码事实 | 复制原件，截去坏尾到新文件，再校验 |
| 首个有效 JSON 非 Header | loader 返回空；打开非空文件报 invalid session | 源码事实 | 不自动补；从备份/已知 metadata 新建 Header 到副本 |
| 中间坏行被后代引用 | 坏行跳过，后代成为 orphan；path 在缺 parent 处停止 | 源码事实组合 | quarantine 后代，人工重连需 provenance |
| unknown type + 合法结构 | 当前实现可能索引、成为 leaf，但 context 映射为空 | 源码事实组合；非兼容承诺 | warn/read-only；升级解析器后再写 |
| duplicate id | `byId` 后者覆盖前者，文件仍有两条，路径可能歧义 | 源码推断，未实测 | reject/quarantine，不自动选 winner |
| parent cycle | path walk 无 visited guard，可能不终止 | 源码推断，未实测 | 预检有环即 reject/read-only |

“能 load”不是“数据完整”。未知/损坏输入应在写操作前先跑独立 validator。

## E07-6 · 副作用窗口

JSONL 能证明 Assistant 生成了 `call-7`，但没有 ToolResult；它不能证明支付失败，也不能证明支付成功。直接重试可能重复扣款。

最小幂等方案：

```text
idempotencyKey = sessionId + toolCallId
operation ledger:
  key
  toolName
  argsHash
  state = started | completed | failed | unknown
  providerOperationId?
  resultHash?
  startedAt / completedAt
```

恢复：

- Provider 按同一 key 返回既有结果：`completed`，补写 ToolResult；
- 确认请求从未提交：`safe-to-retry`；
- Provider 无幂等查询、结果不明：`unknown-needs-review`，禁止自动重试。

## E07-7 · 课程 hardening

一种保守策略：

| 诊断 | 策略 | 理由 |
|---|---|---|
| malformed 尾行 | warn + skip tail，read-only 打开 | 常见 crash prefix；写前仍需修复副本 |
| malformed 中间行 | quarantine/reject writable | 可能断 parent chain |
| missing/invalid Header | reject | 无法确认会话身份/cwd/version |
| duplicate id | reject | parent 解析不唯一 |
| unknown type | warn + read-only | 可能是新版本语义，静默写回会丢信息 |
| missing parent | quarantine orphan | 不应猜 parent |
| parent cycle | reject | traversal 不可终止 |
| future version | read-only 或 reject writable | 防止旧 writer 破坏新格式 |

这是课程建议；固定提交比它宽容，不能倒写成上游行为。

## E07-8 · Compaction 与 Memory

| 维度 | Compaction Entry | 长期语义记忆 |
|---|---|---|
| 触发 | 窗口阈值或手工 compact | 事实抽取、用户/任务策略、显式写入等 |
| 查询 | 只按 active path 自动进入 Context | 关键词/向量/结构化条件召回 |
| 跨会话 | 默认不跨 Session | 通常按用户/项目跨会话 |
| provenance | Summary + Session path，事实级来源弱 | 应保留来源、时间、置信与版本 |
| 更新/冲突 | 后续 summary 可能覆盖叙述 | 需要 merge/conflict/invalidation 策略 |
| 遗忘/删除 | 随 Context projection；旧 Entry 仍在磁盘 | TTL、用户删除、法规与重要性策略 |
| 成本 | 压缩时额外 LLM 调用与 summary tokens | 写入抽取 + 索引 + 每轮检索/rerank tokens |

组合方案：对话与 ToolResult 留 Session；当前计划、约束、文件状态写项目 Artifact；跨会话偏好/稳定事实经 provenance 校验后进入可检索 Memory。敏感信息必须设置 scope、保留期与删除通道。

## Exit Ticket

```text
Pi Session reload 恢复 active-path 消息、模型与 thinking 设置，不会恢复外部工具副作用的确定状态。
active leaf 来自最后一个有效非 Header Entry；branch 的持久化来自随后追加且 parentId 指向旧节点的新末行。
Compaction 解决上下文窗口预算，不保证摘要无损或长期语义记忆。
```
