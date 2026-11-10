> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I07 练习：从 JSONL 物理行恢复一棵会话树

> 一句话结论：每道题都要分别写出 file order、tree path、model context 和 side-effect state，少一层就容易把“恢复”说过头。

## 使用方式

先独立完成，再看 [参考答案](../solutions/PI-I07.md)。本批没有 I07 SessionStore 实现或自动化测试；手工推导只能标“推演”，不能标“实测通过”。若实现，请用临时副本，不要破坏真实 Session 文件。

## E07-1 · 三种顺序

给定：

```jsonl
{"type":"session","version":3,"id":"S","timestamp":"T0","cwd":"/repo"}
{"type":"message","id":"u1","parentId":null,"timestamp":"T1","message":{"role":"user","content":"root"}}
{"type":"message","id":"a1","parentId":"u1","timestamp":"T2","message":{"role":"assistant","content":[{"type":"text","text":"base"}]}}
{"type":"message","id":"u2","parentId":"a1","timestamp":"T3","message":{"role":"user","content":"branch A"}}
{"type":"message","id":"a2","parentId":"u2","timestamp":"T4","message":{"role":"assistant","content":[{"type":"text","text":"answer A"}]}}
{"type":"message","id":"u3","parentId":"a1","timestamp":"T5","message":{"role":"user","content":"branch B"}}
{"type":"message","id":"a3","parentId":"u3","timestamp":"T6","message":{"role":"assistant","content":[{"type":"text","text":"answer B"}]}}
```

1. 列出 file order。
2. 画 tree。
3. reload 后 active leaf 是谁？
4. active path 是什么？
5. 模型 Context 是否包含 branch A？
6. branch A 是否仍可 `/tree` 访问？

## E07-2 · 纯 branch 的持久化陷阱

在 E07-1 reload 后执行：

```text
session.branch(a1)
立即退出，不 append
再次打开文件
```

预测 leaf。然后改成：

```text
session.branch(a1)
appendMessage(u4 parent=a1)
退出并再次打开
```

再次预测 leaf 与 tree。解释为什么 leaf 不需要单独写一个 mutable pointer。

## E07-3 · `/tree`、`/fork`、`/clone`、`--fork`

填写：

| 操作 | 同/新文件 | 复制哪些 Entry | 编辑器初始内容 | Header parentSession |
|---|---|---|---|---|
| `/tree` 选择旧 User | | | | |
| `/fork` 选择旧 User | | | | |
| `/clone` | | | | |
| CLI `--fork source` | | | | |

补充说明 `position="before"` 与 `position="at"` 的区别。

## E07-4 · Compaction Context 投影

逻辑路径：

```text
u1 → a1 → u2 → a2 → u3 → a3 → c1 → u4 → a4
```

其中 `c1`：

```json
{
  "type":"compaction",
  "summary":"Earlier: root + branch decision",
  "firstKeptEntryId":"u3"
}
```

写出：

1. 完整 JSONL/tree 仍有哪些旧 Entry？
2. `buildContextEntries()` 返回什么顺序？
3. 模型消息中旧 `u1/a1/u2/a2` 如何出现？
4. 为什么这不等于长期语义记忆？

## E07-5 · 损坏矩阵

分别预测并标注“源码事实”或“推断，待实测”：

1. 文件最后半行是 `{"type":"message"`；
2. 第一条有效 JSON 是 message，不是 Header；
3. 中间一条 malformed line 被后续 Entry 的 `parentId` 引用；
4. 未知 type `future_event`，但有合法 id/parentId；
5. 两个 Entry 使用同一 id；
6. A.parentId=B 且 B.parentId=A。

每项写：load、tree、context、人工恢复策略。

## E07-6 · Replay 不重做副作用

时间线：

```text
t1 append assistant(toolCall pay, id=call-7)
t2 payment API 成功扣款
t3 进程崩溃
t4 ToolResult 尚未 append
t5 reload session
```

回答：

1. JSONL 能证明什么、不能证明什么？
2. 能否直接再次执行 pay？
3. 设计 `idempotencyKey` 与外部 operation ledger 的最小字段。
4. 恢复状态至少有哪些：safe-to-retry / completed / unknown-needs-review？

## E07-7 · Unknown/Orphan hardening

为课程版 SessionStore 设计一组 diagnostics，不照搬上游静默行为。至少包括：

- malformed line number；
- missing/invalid Header；
- duplicate id；
- unknown type；
- missing parent；
- parent cycle；
- future version。

为每类决定：reject、warn-and-skip、quarantine、read-only，并说明理由。

## E07-8 · Compaction vs Memory

对照表至少写六行：

| 维度 | Compaction Entry | 长期语义记忆 |
|---|---|---|
| 触发 | | |
| 查询 | | |
| 跨会话 | | |
| provenance | | |
| 更新/冲突 | | |
| 遗忘/删除 | | |
| 成本 | | |

最后提出一条组合方案：哪些事实留 Session，哪些写项目 Artifact，哪些进可检索 Memory。

## Hint ladder

- Hint 1：`_buildIndex()` 每看到一个非 Header Entry 就覆盖 leaf。
- Hint 2：branch 只改内存；下一条物理末行编码“当前分支”。
- Hint 3：`buildSessionPath()` 沿 parentId 走，不按数组相邻关系走。
- Hint 4：`sessionEntryToContextMessages()` 没有 Tool executor。
- Hint 5：坏行跳过不代表后代 parent 链仍完整。
- Hint 6：Compaction 是一个 LLM 生成摘要进入 Context，不是语义查询 API。

## Exit Ticket

闭卷补全：

```text
Pi Session reload 恢复 ______，不会恢复 ______。
active leaf 来自 ______；branch 的持久化来自 ______。
Compaction 解决 ______，不保证 ______。
```
