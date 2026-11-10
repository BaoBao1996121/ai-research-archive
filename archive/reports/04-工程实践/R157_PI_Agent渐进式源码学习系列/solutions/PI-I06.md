> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I06 参考答案

> 一句话结论：正确答案不是一张固定路径表，而是一条可解释的决策链：候选来源 → 显式/自动 → scope → trust → active capability → Prompt/Tool 双边输出。

## E06-1 · Context Files 层级排序

加载内容与顺序：

```text
G → R → P → A
```

- `agentDir/AGENTS.md` 先作为 global context。
- 祖先扫描按文件系统根到 cwd 排序，所以 `/workspace/CLAUDE.md`、`/workspace/repo/AGENTS.md`、cwd 的 `AGENTS.md` 依次进入。
- cwd 同时有 `AGENTS.md` 和 `CLAUDE.md` 时，候选数组先命中 AGENTS，函数立即返回，`C` 不加载。
- `Project Trust=false` 不改变 Context Files；Trust 不保护 AGENTS/CLAUDE。
- `--no-context-files` 后这组全部为空。

“Concatenate”指跨层级选中的文件按序拼接；源码在单个目录只选择候选优先级最高的一份，两者不矛盾。

## E06-2 · Trust 矩阵

| 资源 | true | false | 原因 |
|---|---|---|---|
| AGENTS.md | 加载 | 加载 | Context Files 不受 Trust gate，除非关闭 context discovery |
| `.pi/settings.json` | 加载 | 忽略 | project settings 受 Trust |
| `.pi/SYSTEM.md` | 替换 Prompt | 忽略 | project system prompt 只有 trusted 时发现 |
| project deploy Extension | 加载/执行 factory | 不加载 | project executable resource 受 Trust |
| project Skill/Prompt/Theme | 加载 | 不自动加载 | project auto resources 受 Trust |
| global audit Extension | 加载 | 加载 | user/global scope 不由当前项目 Trust 决定 |
| CLI temporary Extension | 加载 | 加载 | 用户显式本次输入，预信任阶段也可参与 `project_trust` |
| CLI explicit Skill | 加载 | 加载 | additional explicit path 与 auto-discovery 分开合并 |

最后一项假设 flags 确实由调用方映射为 `additionalSkillPaths`；这是 CLI 公开契约与 ResourceLoader 合并路径的一致解释。

## E06-3 · `--no-*`

1. 关闭 Extension 自动发现；显式 `audit.ts` 仍加载。
2. 关闭 Skill 自动发现/默认加载；显式 `pdf/SKILL.md` 仍加载。
3. 关闭 Prompt Template 自动发现；显式 `review.md` 仍加载。
4. 关闭 AGENTS/CLAUDE Context Files；显式 append system prompt 是另一输入，仍追加。

`--no-*` 的语义是缩小隐式候选面，不是撤销用户在同一命令里明确给出的路径。项目 Trust 仍决定项目 settings/auto resources；显式 CLI 路径属于临时输入。

## E06-4 · 安全分类

| 控制 | 主要分类 | 说明 |
|---|---|---|
| 未批准不执行 project Extension | Discovery/Trust | 控制项目代码是否进入进程 |
| `path` 必须为 string | Validation | 只校验形状，不限制资源权限 |
| `read` 只能访问 `/workspace` | Authorization | path policy；若靠 mount 实现也属于 Isolation |
| Bash 无网络容器 | Isolation | OS/虚拟化边界 |
| 删除前确认 | Authorization | 人工批准具体副作用 |
| AGENTS 仍进 Prompt | Discovery | Context loading；也是 Prompt Injection 输入面 |
| Extension 锁定 commit | Supply-chain control | 降低更新漂移，不证明代码安全 |
| 10 分钟短期凭据 | Isolation/credential minimization | 限制泄露时间与权限范围 |

## E06-5 · Coherence Test

最小断言：

```text
初始 request.tools 包含 bash
初始 systemPrompt 包含 bash snippet 与 bash guideline
排除后 request.tools 不包含 bash
排除后 systemPrompt 不包含 bash snippet，也不包含仅由 bash 产生的 guideline
排除前后 read 都存在于 request.tools 与 Prompt
```

Manifest hash 可取：排序后的 tool name、canonical schema、normalized snippet、normalized guidelines、active/disabled 状态与版本。重放时记录同一 hash 可证明“当时模型看到的 Prompt 能力描述与 API Tool 集来自同一快照”；它不能证明 Tool 执行是安全或幂等的。

## E06-6 · 冲突与来源

顺序：

```text
A project settings
> B project auto
> C user settings
> D package
```

高优先级只表示冲突解决的覆盖顺序。项目资源可能更不可信；package 也可能恶意，因此 precedence 不是风险等级。

诊断至少包括：resource type、logical name、winner path/source/scope、loser path/source/scope、precedence rule、是否 enabled。Extension 动态贡献同名资源时，测试应固定 Extension 加载顺序，断言 winner 与 collision diagnostic，且 reload 后结果不漂移。

## E06-7 · 故障定位

一种高信号顺序：

1. 确认 `deploy` 是 Skill 名还是 Extension Tool 名；Skill 可见不代表 Tool 注册。
2. 查看 project Trust 决策与 `--approve/--no-approve`。
3. 查看 Extension 是否进入 `getExtensions()`，是否有 load/factory error。
4. 查看 Extension 是否真的 `registerTool("deploy")`。
5. 查看 `--tools/--exclude-tools/--no-tools` 与 SDK allowed/excluded sets。
6. 查看 Active Tool Registry 是否含 deploy。
7. 查看最终 request `tools` 是否含 deploy。
8. 查看 System Prompt snippet/guideline；若只有 Prompt 有，判定 coherence bug 或旧 override。

## E06-8 · 威胁模型示例

| 层 | 控制 | 残余风险 | 成本 |
|---|---|---|---|
| Discovery | `--no-approve`、关闭 project Extension/package、审阅 AGENTS | 普通源码/构建输出仍可 Prompt Inject | 审阅时间、能力减少 |
| Trust/Authorization | allowlist 只读工具；写/执行需 policy 或人工确认 | 模型可在允许范围内做错误操作 | 交互延迟、策略维护 |
| Isolation | 一次性容器/VM；只挂工作区副本；默认断网；短期最小凭据 | 挂载目录仍可被破坏，允许网络仍可能外泄 | 启动时间、镜像与网络运维 |
| Audit/Recovery | diff、命令/Tool ledger、外部副作用 idempotency key、可丢弃工作副本 | 第三方 API 不支持幂等时仍需人工处置 | 存储、实现与复核成本 |

关键点：`--no-approve` 只阻止 project `.pi` 资源，不会收回当前用户权限，也不会阻止仓库内容影响模型。

## Exit Ticket

```text
Project Trust 能保证项目本地配置/可执行资源在批准前不被自动加载，不能保证工具被限制在 cwd 或宿主权限被隔离。
能力一致性要求模型请求的 Tool schema 与 System Prompt 的能力说明从同一 Active Tool Registry 生成。
```
