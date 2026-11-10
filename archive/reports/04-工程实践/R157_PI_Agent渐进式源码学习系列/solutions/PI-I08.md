> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I08 参考答案

> 一句话结论：正确答案必须同时说明“为什么继续”、 “重放了什么”以及“哪份历史仍在”，只说“做了摘要”不够。

## E08-1 · 三路分类

| 情况 | 分类 | 压缩 | 退避/重放 |
|---|---|---:|---|
| HTTP 529 | ordinary retry | 否 | 按 retry policy 指数退避并继续，直到 `maxRetries` |
| `context_length_exceeded` | overflow recovery | 是 | 不走普通 retry；compact 后重试一次 |
| 成功响应但 usage 130K/128K | successful-over-window cleanup | 是 | 已成功响应不重放，只为后续回合腾空间 |
| usage = 111,616 | 不动作 | 否 | 触发式是严格 `>` |
| usage = 111,617 | threshold compaction | 是 | 已完成响应不重放 |
| 取消后，新 Prompt 前发现越线 | pre-prompt threshold compaction | 是 | 不重放被取消响应；压缩完成后继续提交新的用户 Prompt |

同一 overflow 恢复链最多一次 compact-and-retry。普通 retry 次数由 retry settings 决定，不能套用这个“一次”上限。

## E08-2 · 预算边界

```text
128,000 - 16,384 = 111,616  → tokens > 111,616 才触发
200,000 - 16,384 = 183,616  → tokens > 183,616 才触发
floor(0.8 × 16,384) = floor(13,107.2) = 13,107
```

`keepRecentTokens` 是向后累计的目标，不是精确结果。实际 cut point 要落在合法消息上，还会把 Assistant Tool Call 与后续 Tool Result 一起留下，因此 recent tail 可以超过 20K。

默认值来自上游配置，不是同模型、同语言、同仓库基准。要称“最优”，至少要实测压缩频率、恢复成功率、延迟/调用成本和多次压缩保真率。

## E08-3 · Cut Point 与 Tool Pair

从后往前：A3=3K，R2 累计到 7K，A2 后累计到 13K。A2 是合法 cut point，所以：

```text
firstKeptEntry = index 5 / A2
recent tail = A2 + R2 + A3 = 13K
```

index 6 的 Tool Result 不能作为起点，否则模型看到 R2 却看不到产生它的 Tool Call T2。若 cut point 落在一个非 turn-start 的 Assistant，且能向前找到该 turn 的 User 起点，就是 split turn；早期 prefix 单独摘要，suffix 保留。

## E08-4 · 双视图重建

`getBranch()` 沿 parentId 返回整条路径：

```text
U1, A1, R1, U2, A2, R2, C1, U3, A3
```

`buildSessionContext()` 使用最新 Compaction：

```text
CompactionSummary(S1), U2, A2, R2, U3, A3
```

U1/A1/R1 仍在原 JSONL 路径，但模型不会自动回读。S1 写错路径时，磁盘可供人工/工具审计，当前模型上下文仍会先接受错误摘要。

JSONL 记录“对话中报告了什么”，不是外部系统的事务日志。命令可能已经成功但回执未落盘，也可能回执成功后外部状态又被改动；没有 idempotency key、effect ledger 和 reconciliation，就不能推出 exactly-once。

## E08-5 · 两次压缩

1. C2 的 `boundaryStart` 优先定位到 C1 的 `firstKeptEntryId=U2`。
2. S1 作为 `<previous-summary>` 传给摘要模型，提示它更新旧检查点。
3. 找不到 U2 时，从 C1 后一个路径条目开始。
4. S1 的错误会成为生成 S2 的显式输入；如果 recent entries 没有足够反证，错误可继续保留或被放大。

一个可用的确定性 Artifact：

```yaml
schemaVersion: 1
goal: migrate-postgres-to-mysql
orderedSteps:
  - create-and-verify-backup
  - run-schema-migration
  - verify-row-count-and-checksum
  - switch-read-traffic
invariants:
  backupDeletionAllowed: false
state: schema-migration-pending
```

摘要只引用文件和版本；恢复时程序先校验 Schema/invariants，再让模型叙述。Artifact 仍需更新纪律和版本控制，但不会因措辞变化把顺序写反。

## E08-6 · Overflow 只恢复一次

```text
attempt 1 overflow
  → error Assistant 已写 JSONL
  → _overflowRecoveryAttempted = true
  → 从内存 context 移除最后 error（磁盘不删）
  → compaction_start(reason=overflow)
  → append CompactionEntry
  → compaction_end(willRetry=true)
  → agent.continue()
attempt 2 overflow
  → 第二个 error 仍写 JSONL
  → 检测 _overflowRecoveryAttempted=true
  → compaction_end(result=undefined, willRetry=false, errorMessage=...)
  → 停止
```

第三次压缩没有新的进展证据，只会制造恢复循环、额外摘要成本和更多语义损失。正确动作是缩短上下文、换大窗口模型、人工修复摘要/Artifact 或拆任务。

## E08-7 · 摘要调用失败

### 1. Threshold：一次 transient 后成功

- 摘要调用 2 次；
- 成功后 append 1 个 CompactionEntry；
- threshold 不重放已完成 Agent 回合；
- 原 JSONL 条目不删除。

### 2. Overflow：摘要永久失败

- 总摘要尝试数是 `1 + 配置允许的 summarization retries`；题目没给 retry budget，不能编造具体数；
- 没有完整 `CompactionResult`，所以不 append CompactionEntry；
- 不重放 Agent；
- overflow error 已在 JSONL，其他历史未删除；内存中该 error 在进入恢复前已被移除；
- 操作员应缩短/拆分上下文、换模型，或用可信自定义摘要/Artifact 手工恢复。

### 3. Split turn：history 成功、prefix 永久失败

- history summary 已产生调用成本，但 `compact()` 整体未返回；
- 不 append 半成品 CompactionEntry；
- 摘要调用数为 `1 + prefix 的总尝试数`；
- 原 JSONL 保持；threshold 不重放，overflow 也因压缩失败而不重放。

## E08-8 · 脏摘要检测

可确定性校验：

- `<modified-files>` 是否属于 Session details/实际 diff 的集合；
- goal/status 是否等于 versioned Artifact 的枚举值；
- “不可删除备份”等 invariant 是否与 Artifact 布尔值冲突；
- 引用路径是否存在、扩展名是否匹配；
- summary 是否包含必须字段和 Artifact version/hash。

难以自动判真的部分：自由文本中的因果理由、需求含义、用户意图变化、某个设计判断是否合理。这些不能只靠字符串规则证明。

推荐：关键 invariant 冲突时拒绝脏摘要，改用“确定性 Artifact 投影 + recent tail”的 fallback，并向用户告警；次要路径差异可由确定性事实修正后再落盘。代价是要维护 Artifact Schema、同步逻辑和失败 UI；如果没有可信 fallback，宁可停下请求人工处理，也不要在高副作用任务中把已知错误摘要写成新事实。

这是课程 hardening，不是 Pi 当前默认行为。

## E08-9 · Branch Summary

1. common ancestor：A。
2. 摘要 B、C、D；按时间顺序提供给 summarizer。
3. Branch Summary 在 `/tree` 离开分支时保存旧分支上下文，写 `BranchSummaryEntry(fromId=oldLeaf)`；Compaction 为窗口管理写 `CompactionEntry(firstKeptEntryId=...)`。
4. Pi 生成的旧 Branch Summary 会从 `details.readFiles/modifiedFiles` 累计文件操作；extension 自定义 summary 的 details 不能盲按默认结构消费。
5. 摘要记录的是报告，不是命令事务。它没有外部系统的提交 ID、幂等键或对账结果。

## E08-10 · 测试规格示例

| 测试名 | Arrange / Act / Assert | 性质 |
|---|---|---|
| `does_not_compact_at_exact_threshold` | tokens=window-reserve；decision=noop | Pi 忠实 |
| `compacts_one_token_above_threshold_without_replay` | tokens=threshold+1；assert compaction=1, agent replay=0 | Pi 忠实 |
| `retries_529_without_compaction` | scripted 529→success；assert sleep>0, compaction=0 | Pi 忠实 |
| `compacts_and_retries_overflow_once` | overflow→overflow；assert agent attempts=2, compaction=1 | Pi 忠实 |
| `never_cuts_at_tool_result` | budget crosses at R2；assert firstKept=A2 | Pi 忠实 |
| `splits_oversized_single_turn` | one turn>keepRecent；assert prefix/history inputs and merged summary | Pi 忠实 |
| `second_compaction_uses_previous_kept_boundary` | C1+new entries；assert boundaryStart=firstKept(C1) | Pi 忠实 |
| `does_not_append_when_summarizer_fails` | permanent summary error；assert compactionEntries=0 | Pi 忠实 |
| `dirty_summary_fails_invariant_check` | summary contradicts Artifact；assert fallback/stop | 课程 hardening |
| `branch_summary_collects_abandoned_path_only` | A→B/C/D and A→E/F；assert [B,C,D] | Pi 忠实 |

这些是待实现规格；没有 RED/GREEN 运行记录前，不得标记通过。

## Exit Ticket 参考

Compaction 保留对话条目但让模型依赖有损摘要；JSONL 又没有外部副作用的幂等键、提交状态和对账。因此它能恢复“对话上下文”，不能证明命令 exactly-once，也不能自动纠正脏摘要。Overflow 只允许 `error → compact → retry once → stop`。
