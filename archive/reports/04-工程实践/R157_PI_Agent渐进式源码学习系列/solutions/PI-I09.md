> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I09 参考答案

> 一句话结论：Extension 的可靠性来自明确的加载/错误/清理契约，安全性则来自对代码来源和进程外边界的治理。

## E09-1 · Trust 与发现矩阵

| 阶段 | 会加载 | 不会加载 |
|---|---|---|
| Trust 未决定 | global.ts、CLI `-e ./cli.ts`、inline/user 级资源 | project.ts、项目 settings 中的 package Extension |
| 拒绝 | 继续只有 global/CLI 等信任根 | 项目 Extension/受保护设置/项目 package |
| 接受 | global/CLI + project.ts + 启用的项目 package | 被配置禁用或发现规则不匹配的路径 |

global/CLI Extension 可参与 `project_trust`；项目 Extension 不能在决定自身是否可信前参与决定。缺失的项目包只有在项目信任后才可按项目设置自动安装。

默认发现只看直接 `.ts/.js` 和一级子目录的 `index`/manifest，不无限递归。要加载 `deep/nested/index.ts`，可在 `deep/package.json` 的 `pi.extensions` 显式声明 `./nested/index.ts`，或把确切路径作为配置/CLI 输入。

`-e` 的 temporary 只表示本次运行/临时目录；代码仍在 Pi 进程内以当前用户权限执行。

## E09-2 · 加载与绑定 Trace

```text
A import/factory → registries 写入，Provider corp 进入 pending queue
B import/factory → throw → errors += {path:B,...}
C import/factory → registries 写入
ExtensionRunner.bindCore → flush A/corp → 后续注册改为立即生效
```

最终 Extension 为 A、C；Tool `lookup`、Command `audit`、A/C 的 handlers 存在。B 不进入 extensions 数组，但错误留在 `LoadExtensionsResult.errors`，C 继续加载。

Provider 在 factory 阶段尚未绑定 ModelRegistry，因此先排队。flush 时单个注册若抛错，Runner 发 `register_provider` ExtensionError 并继续绑定；Agent 可继续启动，但该 Provider 不应出现在有效模型能力中，诊断必须含 extension path、event 和错误文本。

## E09-3 · 普通 Hook 的错误隔离

顺序 A→B→C：

```text
final = original + [A] + [C]
error = {extension:B, event:context, error:"B failed"}
C receives = original + [A]
```

顺序 C→B→A 得到 `original + [C] + [A]`。错误被隔离，但链式结果仍按加载顺序演化，所以不顺序无关。

纯日志、指标更适合只观测；Context/Prompt/Provider payload 修改天然是 middleware，应记录顺序并尽量限制重叠职责。幂等测试可对同一输入调用 transform 两次，断言第二次不重复插入 marker/消息；若变换设计上非幂等，应把“一回合只调用一次”写进契约并测试调用计数。

## E09-4 · `tool_call` 必须 fail closed

1. B 看到 A 把 `path` 改成 Number，因为 handler 共享可变 `event.input`。
2. 当前 Pi 不会在 mutation 后自动 Schema re-validation。
3. B 抛错向 beforeToolCall 传播，工具 Pipeline 将其变成 error ToolResult；execute 计数为 0。
4. 删除 B 后，`path=42` 可能进入 execute；行为取决于工具实现，不能依赖它“自然抛错”作为 validation。

课程 hardening：所有 `tool_call` handlers 完成后，把最终 args 作为新对象重新过原 Tool Schema；失败则返回关联 `toolCallId` 的 error ToolResult，execute=0。代价是兼容性变化和一次本地校验；这不是固定提交的默认事实。

## E09-5 · 注册冲突

- Tool：Runner 按 Extension load order 取首个同名定义；`read` 的第一个注册生效，冲突仍应有 diagnostics。
- Command：重复名称会解析为 `audit:1`、`audit:2` 等唯一 invocation name，而不是静默丢弃第二个。
- Shortcut：若 built-in 标记禁止覆盖，Extension shortcut 被跳过；可覆盖的 built-in 或 Extension 间冲突会产生诊断，Extension map 的后写者可能成为最终绑定。
- Provider：load-time registrations 按队列 flush。若第二个注册触发 ModelRegistry/Provider action 错误，Runner 发 `register_provider` error，其他绑定继续；若实现允许 override，则按 Provider API 的覆盖语义，不应假设必然报错。

加载顺序会随全局/项目设置、包过滤和版本变化。把它当兼容策略会导致 silent behavior drift；团队 Extension 应使用命名空间、显式冲突测试和固定 load manifest。

## E09-6 · Mode-aware UI 与权限门

| mode | `ctx.hasUI` | 真实交互 | 高副作用默认策略 |
|---|---:|---|---|
| TUI | true | 本地终端对话框 | 等用户确认；取消/超时 deny |
| RPC | true | 由 RPC 客户端实现对话 | 有界超时；无响应 deny/abort |
| JSON | false | 无，UI 方法 no-op/默认 | deny，或要求显式非交互 policy token |
| Print | false | 无 | deny，或要求显式非交互 policy token |

不能把 `confirm()` 的默认返回值当批准。建议权限 Hook 先检查 `ctx.hasUI`：有 UI 时带超时确认；无 UI 时对破坏性类别 fail closed，并允许调用方通过经过审计的配置/一次性批准令牌显式放行。

## E09-7 · Reload 资源泄漏

在“每代 factory/session_start 各运行一次”的简化假设下，初始启动加三次 reload 后会有 4 个 timer、4 个 watcher。新 Runner 只替换未来事件路由，无法撤销旧闭包已注册到 Node event loop/OS 的资源。

安全生命周期：

```text
factory         只注册，不启动长生命周期资源
session_start   若不存在则创建 timer/watcher，并保存 handle
session_shutdown 幂等 clear/close/abort；等待完成；handle 置空
```

cleanup 调两次必须不抛错、不重复 close 造成副作用、最终资源计数仍为 0。`await ctx.reload()` 后旧 Command 调用帧还在运行，但其 Extension 状态已 shutdown；立即 return 避免访问旧状态或重复注册。

测试可注入 ResourceTracker：每次 start `active++`，shutdown `active--` 且禁止负数；连续 reload 后始终 `active===1`，最终 shutdown 后为 0。guarded old ctx 调用应失败；预先抽出的 raw SessionManager 不能自动失效，因此代码审查/封装测试要禁止在 replacement 后使用它。

## E09-8 · Unload 能力盘点

固定 `ExtensionAPI` 有显式 `unregisterProvider`；没有对称的 `unregisterTool`、`unregisterCommand` 或 `unloadExtension`。`setActiveTools()` 可以让 Tool 对模型暂时不可用，但 Tool definition 和 Extension 其他 handlers 仍在 Runner 中。

停用 Extension 的通常步骤：禁用/删除全局或项目资源配置（或包过滤），触发 reload，确认新 Extension set/registry 不含它。逻辑停用验收：未来事件、Command、Tool、Provider 都不再解析到旧 Extension。资源回收验收：旧 timer/socket/watcher/process 全部关闭、句柄计数为 0、无旧闭包继续写 Session。

从 Registry 移除不能逆转全局 monkey patch、第三方模块单例、已启动子进程或已发生的外部写入；这些需要 Extension cleanup、进程重启或外部补偿。

## E09-9 · 第三方 Package 威胁模型

推荐决策：不安装 `@latest`。先选择精确版本并核验 registry provenance/tarball/lockfile；若可选 Git 来源，优先审查后固定 commit hash。重点审查：Extension factory、install scripts、依赖树、WebSocket 目的地、Header mutation、环境变量读取、动态 import/download 和更新机制。

权限建议：

- 只注入该 Provider 所需的短期 token，不给 SSH agent、Docker socket、整个 home；
- 只挂载工作目录的必要子集；不需要外网则禁网，需要 WebSocket 时 allowlist 目的地；
- 此包会读凭据并联网，若来源不是组织内完全可信，选择把整个 Pi 放容器/VM，或重构为受协议限制的独立服务；
- 更新前重新审 diff/lockfile，保存旧制品与配置，先在隔离环境跑 reload/failure/security 测试，再灰度；回滚固定到旧 hash/version。

Project Trust 能阻止仓库在未批准前加载项目 package；不能审计包、限制同进程权限、阻止获准代码外传，也不保护 global/CLI 信任根。

“每个小 UI Extension 都放独立 micro-VM”技术上更隔离，但集成 UI/Session API、IPC、镜像、调试、升级的人力和延迟可能大于风险收益，经济上不划算。更合理的是按风险分层：可信 UI in-process；不可信解析/高副作用执行隔离。成本维度至少记录镜像维护、启动延迟、IPC 协议、凭据管理、监控和升级测试。

## E09-10 · 接缝选择

| 能力 | 推荐 | 理由与边界 |
|---|---|---|
| 状态栏颜色 | in-process Extension | 需要直接 UI 接缝，副作用低；仍要 cleanup renderer |
| 解析不可信 PDF | subprocess/container | 解析器攻击面高；Extension 只做编排和结果校验 |
| `rm -rf` 确认 | Extension UX + OS sandbox | Hook 可减少误操作，但恶意/故障 Extension 可绕过；真正限制靠挂载/权限 |
| 公司 Provider Gateway | trusted Extension + remote service | Extension 注册 Provider；鉴权、审计、配额放 Gateway |
| 不可信仓库执行测试 | container/VM | 隔离文件、进程、网络、凭据；Extension 路由 Tool operations |
| 偶发 native crash 的 LSP | subprocess | crash containment 与重启；Extension 维护协议/状态 |
| Turn Trace 到本地 JSONL | in-process Extension | 事件带宽高、逻辑简单；需限制敏感内容和文件权限 |

## E09-11 · 测试规格示例

| 测试名 | 核心断言 | 性质 |
|---|---|---|
| `rejects_project_extension_before_trust` | pre-trust set 不含 project path | Pi-faithful |
| `continues_loading_after_factory_throw` | B error，C 仍注册 | Pi-faithful |
| `keeps_current_context_after_transform_throw` | A 结果传给 C | Pi-faithful |
| `blocks_tool_when_tool_call_handler_throws` | execute=0，error ToolResult | Pi-faithful |
| `chains_mutations_in_load_order` | B 看到 A mutation | Pi-faithful |
| `revalidates_final_mutated_arguments` | mutation 破坏 Schema 后 execute=0 | course-hardening |
| `uses_first_tool_registration_and_reports_conflict` | selected=A，diagnostic 含 A/B | Pi-faithful |
| `namespaces_duplicate_commands` | `audit:1`,`audit:2` 可解析 | Pi-faithful |
| `flushes_provider_registration_on_bind` | bind 前 pending，bind 后有效 | Pi-faithful |
| `denies_destructive_tool_without_ui` | JSON/Print execute=0 | course-hardening |
| `reloads_with_single_live_watcher` | 每代 active=1，shutdown 后 0 | lifecycle hardening |
| `rejects_guarded_old_context_after_replacement` | old ctx 调用抛 stale error | Pi-faithful |
| `rejects_unpinned_third_party_package` | policy 拒绝 `@latest`/浮动 ref | course-hardening |

这些是待实现规格，不是测试结果。

## Exit Ticket 参考

Permission Extension 与 Pi 同进程、同用户权限运行，能改善确认与审计体验，却能被其他 Extension、宿主权限或自身故障绕过，所以不是强安全边界。Reload-safe 的三个不变量：factory 不开长资源；start/shutdown 成对且 cleanup 幂等；reload 后旧 Context、raw state 和异步任务不再被使用。
