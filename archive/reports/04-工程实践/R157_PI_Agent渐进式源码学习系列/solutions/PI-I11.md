> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I11 参考答案

> 一句话结论：参考答案给出可强制的最小边界；具体业务仍需重新做资产、法规和 SLO 评审。

## E11-1

> 结论：Schema、主体权限、OS 边界和资源装载是四个不同维度。

| 项 | 分类 |
|---:|---|
| 1 | Validation |
| 2 | Authorization |
| 3 | Isolation |
| 4 | Project-resource trust |
| 5 | Validation / Hook 信任边界加固 |
| 6 | Authorization / 最小下游权限 |
| 7 | Isolation / 文件系统 containment |

4 只阻止未信任项目的本地配置/扩展被加载；内置 Tool 仍可能按宿主权限访问资源，已加载的全局/CLI Extension 也有进程权限，因此不能替代其他控制。

## E11-2

> 结论：推荐只暴露 `list_tree(commit)`、`read_blob(commit,path)`、`emit_report(reportId,body)` 三个窄 Tool。

策略示例：

```text
tenant-user × read_blob × repo/commit/path
  if repo belongs to tenant AND commit == pinnedCommit AND path matches allowlist → allow

agent × emit_report × tenant/reportId
  if body <= sizeBudget AND reportId belongs to run → allow

agent × shell × * → deny
agent × network_fetch × * → deny
agent × write_repo × * → deny
```

注入场景及控制：

| 场景 | Prevention | Containment | Detection |
|---|---|---|---|
| README 要求读 `~/.aws` | 不提供通用 read/path；commit blob API | 容器无 home/secret 挂载 | deny event + attack fixture |
| 源码要求 curl 外传 | 无 network/Bash Tool | egress deny | DNS/network deny metrics |
| 文本伪装审批指令 | Approval 由可信 UI 从结构化动作生成 | 只读身份 | 审批 actor/action 审计 |

## E11-3

> 结论：题设总 attempts 的保守乘法上界是 24 次 Provider 请求和 12 次通知请求；生产上仍应以共享计数与实际 Trace 为准。

1. `2 × 3 × 4 = 24` 次 Provider network attempts。
2. 题设保守上界为 `2 × 3 × 2 = 12` 次通知请求；Provider 内部网络 retry 通常不会自行重放 Tool，但 Session/Gateway 是否重走到 Tool 取决于失败点与实现，所以只能用 action id、实际 Trace 和共享计数证明更低。
3. Gateway 生成 run budget：原子计数 `providerAttempts < 8`；所有 Provider 层共用。通知由 Gateway 生成固定 action/idempotency key，下游同 key 只提交一次。
4. 可重试：明确的临时网络失败、限流，且剩余 deadline/budget 足够；直接失败：鉴权、Schema、Policy deny、预算耗尽；unknown side effect：先按 action key 查询/reconcile。

## E11-4

> 结论：Action record 是事实源，Session 只引用它。

```text
planned(k1)
→ executing(k1)
→ downstream create(idempotencyKey=k1)
→ committed(k1, downstreamId) | failed(k1, class) | unknown(k1)
```

宿主而非模型生成 `k1`。恢复时：planned 可重新调度；executing/unknown 先查询下游 `getByIdempotencyKey(k1)`；存在则补 committed，不存在且错误可重试才重发；committed 不再执行。Session ToolResult 写 `actionId=k1` 与结果摘要，不能成为唯一状态源。

## E11-5

> 结论：默认最小化，调查所需的关联字段与敏感 payload 分开保存。

| 字段 | 建议 |
|---|---|
| Prompt 原文 | 默认不记录或加密短期受控存储；主日志只存 hash/reference |
| repo URL | 租户内标识/摘要，必要时完整但访问受控 |
| commit SHA | 完整，通常非秘密且用于可复现 |
| OAuth token | 永不记录 |
| Tool 参数 | 结构化 allowlisted 字段；敏感字段删减 |
| Policy decision | 完整记录规则/版本/理由，不复制 secret |
| 文件内容 | 默认不记录；存 blob hash/path/commit |
| usage | 完整数值 |
| user id | 内部稳定 pseudonymous id |
| 错误堆栈 | 受控诊断日志，先做 secret redaction |

保留期由数据所有者、安全/隐私与法规共同决定；平台工程负责技术执行。课程不提供通用天数。

## E11-6

> 结论：一个合格集合同时覆盖正确性、边界、概率性质量和故障恢复。

示例：

```text
Unit: path escape deny; budget atomically exhausts; JSONL corrupt line policy; retry classification
Integration: container cannot read host secret; egress denied; crash then action reconcile
Behavioral: finds seeded bug; cites correct line; abstains when evidence absent
Security/Fault: malicious README cannot invoke forbidden capability; provider timeout storm remains within 8 attempts
```

每项发布门由团队设定。确定性安全不变量应 100% 通过；Behavioral 指标需记录模型、数据集、重复次数、区间与成本，不能只报单次百分比。

## E11-7

> 结论：A 直接用，B 加固用，C 暂不让 Pi 承担完整生产编排。

| 场景 | 推荐 | 主要成本 |
|---|---|---|
| A | 直接 Pi；高风险任务可加容器 | 人工监督、模型 Token、简单维护 |
| B | 加固 Pi：SDK/RPC + 窄 Tool + 容器 + 审计 | 平台集成、镜像/策略/Eval 维护、Token |
| C | 暂不选 Pi 作完整平台；若选只作隔离 Harness 内核 | durable workflow、强授权、审计、支付幂等、安全团队与合规成本过高 |

若 C 已有成熟工作流/政策平台，可把 Pi 限定为无权决策的推理组件；否则原样采用的总风险和人力不经济。

## E11-8

> 结论：参考防线要求控件失效时 fail closed，并保持可调查。

1. 云凭据不挂载，read Tool 只读 pinned commit blob；
2. Extension 固定版本/哈希、审批来源；高风险 executor 不加载第三方同进程代码；
3. action id reconcile 后再决定 retry；
4. 审计不可用时高影响动作暂停，低风险动作是否降级由显式策略决定；
5. Budget service 不可用默认拒绝新 Run，不能假装无限额；
6. 审批 UI 由可信代码显示原始结构化动作、主体、资源和 diff，不把模型摘要当唯一证据。

## 最终答辩答案

> 结论：Pi 提供清楚的模型、Loop、Session、Tool、Extension 与入口接缝；生产宿主仍必须拥有身份、强制授权、隔离、总预算、幂等动作状态和分层评估。
