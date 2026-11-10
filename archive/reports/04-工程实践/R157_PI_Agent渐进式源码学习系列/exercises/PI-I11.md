> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I11 练习：从“能跑”审到“可控”

> 一句话结论：这组练习要求把每个风险落到强制边界、故障证据和成本所有者。

## E11-1 · 三种控制

> 结论：为每项控制标出 validation、authorization、isolation 或 project-resource trust。

1. `path` 必须是 string；
2. 用户 Alice 能读 repo A 但不能读 repo B；
3. Bash 容器无公网出口；
4. `.pi/extensions` 未获信任时不装载；
5. Tool 参数必须在 Hook 改写后重新过 Schema；
6. 下游 Git 服务只给 read scope；
7. 工作区只读挂载。

解释为什么 4 不能替代 2、3、6、7。

## E11-2 · 威胁图与策略矩阵

> 结论：为“自动生成代码审阅报告”建立资产、主体、动作和决定点。

业务约束：多租户；仓库可能恶意；只允许读取指定 commit；报告写入独立对象存储；禁止任意 Shell、网络抓取和修改仓库。

交付：

- 信任域图；
- Tool allowlist；
- 5 条 `subject × action × resource × condition → decision`；
- 3 个 Prompt Injection 场景；
- 每个场景的 prevention、containment、detection。

## E11-3 · 重试放大

> 结论：先算最坏网络请求和副作用次数，再决定谁拥有重试。

为避免 `retry` 与 `attempt` 术语混淆，题目直接给总 attempts：Gateway 最多 2 个 run attempts；每个 Gateway attempt 最多 3 个 Session attempts；每个 Session attempt 最多 4 个 Provider network attempts。保守假设每个 Session attempt 都可能在失败前提交 2 个通知 Tool 请求。

1. 不共享计数时，最多 Provider network attempts？
2. 在上述保守假设下，若通知 Tool 非幂等，最多通知动作请求？实际实现可能更低，为什么仍不能直接假设？
3. 设计共享预算，令 Provider attempts 总数 ≤ 8、通知有效提交 ≤ 1。
4. 哪些错误可重试，哪些要直接失败或 reconcile？

## E11-4 · 崩溃歧义

> 结论：分别处理“提交前崩溃”“提交后回执前崩溃”“记录结果后崩溃”。

为 `create_draft_release` 画状态机：

```text
planned → executing → committed | failed | unknown
```

指定幂等键生成者、下游查询接口、恢复动作和 Session entry 如何引用 action id。不得使用“看到 transcript 没有 ToolResult 就重试”作为唯一规则。

## E11-5 · 敏感可观察性

> 结论：既要能调查越权，也不能把 secrets 再复制进日志。

给出以下字段的记录策略：Prompt 原文、repo URL、commit SHA、OAuth token、Tool 完整参数、Policy decision、文件内容、模型 usage、用户 id、错误堆栈。

每项选择：完整 / 摘要 / 哈希或引用 / 不记录；写出保留期与访问控制需要由谁决定。

## E11-6 · Eval 金字塔

> 结论：为同一代码审阅 Agent 设计至少 12 个测试，覆盖四层。

- 4 个确定性 Unit；
- 3 个 Integration；
- 3 个 Behavioral Eval；
- 2 个 Security/Fault 演练。

每个写：输入、预期不变量、指标、失败后的发布决策。不要只用“答案看起来不错”。

## E11-7 · 是否采用 Pi

> 结论：为三个组织作出唯一主推荐，并估算总成本维度。

A. 个人研究者，可信本地仓库；B. 10 人内部团队，有容器平台；C. 金融多租户服务，无 Agent 安全团队、要求强审计和可恢复付款。

每个场景选：直接 Pi / 加固 Pi / Pi 只作 Harness 内核 / 暂不选 Pi。列出 Token/API、平台运维、人力、安全与迁移成本，不要求虚构金额。

## E11-8 · Capstone 红队答辩

> 结论：按 [CAPSTONE.md](../CAPSTONE.md) 完成方案后，用反例攻击自己的设计。

至少回答：

1. 恶意 README 诱导读取云凭据；
2. Extension 包更新后加入外传代码；
3. Provider 超时但下游动作已成功；
4. 日志系统故障；
5. Budget service 不可用；
6. 用户在审批 UI 中看到模型伪造的“安全摘要”。

## Hint ladder

> 结论：提示只提供判断框架，不替你选择资产和阈值。

- H1：Project Trust 是装载决策，不是执行权限。
- H2：强安全边界应在 Pi 进程之外或下游系统之内。
- H3：`unknown` 是合法状态；先 reconcile，不要猜。
- H4：预算至少在 Provider 与 Tool 之前各检查一次，并共享 run 级计数。
- H5：Behavioral Eval 测概率性表现；Policy deny、parser、budget 适合确定性测试。

## Exit Ticket

> 结论：闭卷写出“为什么 Pi 可作为生产 Harness 内核但不等于生产平台”，必须包含权限、耐久、预算和评估四个因果节点。
