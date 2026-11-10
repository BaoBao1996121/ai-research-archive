> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I08 练习：证明压缩能继续，但不能证明摘要无损

> 一句话结论：这组练习要求你同时追踪恢复决策、模型可见上下文、完整 JSONL 和额外模型调用。

除非题目明确要求，不要先看参考答案。Mini Pi 的 I08 代码尚未实现；纸面 Trace 不能作为测试通过证据。

## E08-1 · 三路分类

把以下情况分别归到 `threshold compaction`、`overflow recovery`、`ordinary retry`、`successful-over-window cleanup` 或“不动作”：

1. 128K 模型返回 HTTP 529；
2. Provider 返回 `context_length_exceeded`；
3. `stopReason=stop`，但 usage 报告 130K/128K；
4. usage 为 111,616，默认 reserve 为 16,384；
5. usage 为 111,617；
6. 用户取消生成，下一次提交 Prompt 前检测到旧上下文已越 threshold。

每项写出：是否压缩、是否退避、是否自动重放上一请求、最多几次 overflow recovery。

## E08-2 · 预算边界

分别计算 128,000、200,000 Context Window 在默认 `reserveTokens=16,384` 下的严格触发线。回答：

- 正好等于 `window - reserve` 是否触发？
- `keepRecentTokens=20,000` 是否代表压缩后上下文必定恰好 20,000 tokens？
- 默认摘要最大输出是多少？给出计算过程。
- 为什么这些值只能称“上游默认/初始值”，不能称“实测最优值”？

## E08-3 · Cut Point 与 Tool Pair

给定按时间排列的 Context-visible entries 与估算 tokens：

| index | entry | tokens |
|---:|---|---:|
| 1 | User U1 | 3,000 |
| 2 | Assistant A1，含 Tool Call T1 | 1,000 |
| 3 | Tool Result R1 | 8,000 |
| 4 | User U2 | 2,000 |
| 5 | Assistant A2，含 Tool Call T2 | 6,000 |
| 6 | Tool Result R2 | 4,000 |
| 7 | Assistant A3 | 3,000 |

`keepRecentTokens=10,000`。按 Pi 的“从后往前累计，达到预算后找合法 cut point”规则：

1. `firstKeptEntry` 是谁？
2. recent tail 估算共多少 token？为什么不等于 10,000？
3. 如果算法允许从 index 6 开始，会破坏哪个不变量？
4. 如果单个 U2 turn 已超过预算，什么条件下会成为 split turn？

## E08-4 · 双视图重建

已有 JSONL 路径：

```text
U1 → A1 → R1 → U2 → A2 → R2 → C1(summary=S1, firstKept=U2) → U3 → A3
```

分别写出：

- `getBranch()` 能看到的条目；
- `buildSessionContext()` 给模型的内容；
- S1 错写文件路径时，旧 A1/R1 是否仍在磁盘、模型是否自动看到；
- 为什么“JSONL 仍完整”不能证明 Bash 外部副作用可 exactly-once 恢复。

## E08-5 · 两次压缩

第一次 Compaction C1 的 `firstKeptEntryId=U2`、summary=S1。之后新增 U3/A3/R3/U4/A4，并触发 C2。

回答：

1. C2 的候选 summarization boundary 从哪里开始？
2. 摘要请求是否会拿到 S1？以什么角色出现？
3. 若当前分支找不到 U2，fallback 从哪里开始？
4. S1 中的事实错误可能如何传播到 S2？
5. 设计一个确定性 Artifact 来阻止“数据库迁移顺序”在连续摘要中漂移。

## E08-6 · Overflow 只恢复一次

画出下面脚本的事件序列：

```text
attempt 1 → overflow error
compaction → success
attempt 2 → overflow error
```

至少包括：错误消息在 JSONL/内存中的去向、`compaction_start/end`、`willRetry`、`_overflowRecoveryAttempted` 与最终用户可见结果。解释为什么不能再做第三次 compact-and-retry。

## E08-7 · 摘要调用失败

分别分析：

1. threshold compaction 的摘要第一次 transient stream drop，第二次成功；
2. overflow recovery 的摘要永久失败；
3. split turn 中 history summary 成功，turn-prefix summary 永久失败。

每项回答：是否 append CompactionEntry、是否重放 Agent、原 JSONL 是否被删除、增加了多少次摘要调用（按题面已给出的尝试次数）、操作员下一步是什么。

## E08-8 · 脏摘要检测

Fake Summarizer 返回：

```markdown
## Goal
把 PostgreSQL 迁移到 SQLite

## Key Decisions
- 已删除备份，可直接覆盖生产库

<modified-files>
src/db.js
</modified-files>
```

但原始事实是“PostgreSQL→MySQL；备份不可删除；修改 `src/db.ts`”。设计一个不调用第二个 LLM 的验证器：

- 哪些字段能与 Artifact/Session details 做确定性比对？
- 哪些自然语言事实仍无法可靠自动判真？
- 验证失败时是拒绝 compaction、标红告警、还是继续但注入纠错消息？给出你的推荐与代价。

## E08-9 · Branch Summary

树如下：

```text
        B → C → D   (old leaf)
A  ────┤
        E → F       (target)
```

1. common ancestor 是谁？
2. 要摘要哪些条目？
3. Branch Summary 与 Compaction 的触发、写入 Entry、目标分别是什么？
4. 如果 B→D 中包含旧 Branch Summary，它的 file details 怎样参与累计？
5. 为什么 Branch Summary 仍不能恢复旧分支上的外部命令副作用？

## E08-10 · 待实现的测试规格

为未来 `iter08-compaction.test.ts` 写至少 8 个测试名和 Arrange/Act/Assert。必须覆盖：

- threshold 边界；
- ordinary retry 不压缩；
- overflow 只恢复一次；
- Tool Pair；
- split turn；
- 两次压缩；
- 脏摘要；
- 摘要永久失败；
- branch summary。

明确哪些断言验证 Core 忠实复刻，哪些是课程 hardening。不要写“测试通过”，因为实现尚不存在。

## Hint ladder

- Hint 1：先写四个计数器：`agentAttempts`、`summaryAttempts`、`retrySleeps`、`compactionEntries`。
- Hint 2：`reserveTokens` 参与触发，`keepRecentTokens` 参与 cut point；不要把两者相加后当作同一预算。
- Hint 3：模型上下文由最新 Compaction 投影，磁盘 entries 不因 compaction 被删除。
- Hint 4：`toolResult` 不是合法 cut point；可以从含 Tool Call 的 Assistant 开始保留。
- Hint 5：普通 transient retry 先于 compaction 检查，Context Overflow 明确不走普通 retry。
- Hint 6：确定性验证器可以查路径集合和结构化状态，不能可靠证明任意自然语言摘要为真。

## Exit Ticket

闭卷用不超过 120 字解释：为什么“摘要 + 完整 JSONL”仍然不是 Durable Workflow Recovery？再画一条只允许一次的 overflow 恢复箭头。
