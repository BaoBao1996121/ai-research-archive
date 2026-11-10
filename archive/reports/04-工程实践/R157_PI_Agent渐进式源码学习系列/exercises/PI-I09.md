> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# PI-I09 练习：把 Extension 当作代码依赖审计

> 一句话结论：这组练习不考 API 背诵，而考你能否追踪加载顺序、失败传播、资源生命周期和真实权限边界。

Mini Pi 的 I09 Host 尚未实现、尚未实测。先完成纸面 Trace 和测试规格，不要把预期行为写成“已通过”。

## E09-1 · Trust 与发现矩阵

在以下资源同时存在时，分别写出“Project Trust 未决定 / 拒绝 / 接受”三个阶段会加载什么：

```text
~/.pi/agent/extensions/global.ts
.pi/extensions/project.ts
pi -e ./cli.ts
.pi/settings.json → packages: [npm:@team/guard@1.2.3]
./misc/extensions/deep/nested/index.ts
```

回答：

1. 哪些 Extension 可参与 `project_trust`？
2. 项目包缺失时，何时可能自动安装？
3. 默认发现是否递归到 `deep/nested`？怎样用 manifest 显式声明？
4. `-e` 是临时生命周期还是权限沙箱？

## E09-2 · 加载与绑定 Trace

三个 Extension factories 按顺序 A、B、C：

- A 注册 `context`、Tool `lookup`、Provider `corp`；
- B 的 factory 抛 `new Error("bad factory")`；
- C 注册 Command `/audit` 和 `tool_result`。

画出 `Jiti import → factory → LoadExtensionsResult → ExtensionRunner.bindCore()`：

- 最终有哪些 Extension/Tool/Command/Provider？
- B 的错误放在哪里？C 是否仍加载？
- A 的 Provider 在 factory 阶段立即进入 ModelRegistry，还是先排队？
- 如果 Provider flush 也抛错，Agent 是否还能启动？需要什么诊断？

## E09-3 · 普通 Hook 的错误隔离

`context` handlers 按加载顺序：

```text
A: messages + ["A"]
B: throw Error("B failed")
C: messages + ["C"]
```

先预测最终 messages、error event 与 C 收到的输入。然后把顺序换成 C→B→A，比较结果。解释：

- 为什么“错误隔离”不等于“顺序无关”？
- 哪些 Hook 适合链式变换，哪些应只观测？
- 如何给一个变换 Hook 写幂等性测试？

## E09-4 · `tool_call` 必须 fail closed

Schema 已验证 `{path:string}`。两个 `tool_call` handlers：

```text
A: event.input.path = 42
B: throw Error("policy unavailable")
```

回答并设计断言：

1. B 能否看到 A 的 mutation？
2. Core 会不会自动再次 Schema validate？
3. B 抛错时 execute 计数应该是多少？模型收到什么类型的结果？
4. 如果删掉 B，A 改坏的参数是否可能进入 execute？
5. 设计“课程 hardening”的最终参数重校验，但明确它不是当前 Pi 默认事实。

## E09-5 · 注册冲突

A 与 B 都注册：

- Tool `read`；
- Command `audit`；
- Shortcut `ctrl+x`；
- Provider `corp`。

分别预测解析结果与诊断：

- 哪个 Tool 定义生效？
- 两个 Command 如何被调用？
- Shortcut 与 built-in restricted shortcut 冲突时怎样处理？
- Provider 重复注册失败时错误走哪条通道？
- 为什么团队扩展不能依赖“恰好的加载顺序”作为版本兼容策略？

## E09-6 · Mode-aware UI 与权限门

权限 Extension 在 `tool_call` 里调用 `ctx.ui.confirm()`。为 TUI、RPC、JSON、Print 四种 mode 填表：

| mode | `ctx.hasUI` | confirm 是否有真实交互 | 无 UI 时默认 allow/deny/abort |
|---|---:|---|---|
| TUI | ? | ? | ? |
| RPC | ? | ? | ? |
| JSON | ? | ? | ? |
| Print | ? | ? | ? |

给出你的权限门策略。要求：不能因为 UI no-op 就默许高副作用 Tool；还要说明 RPC 客户端不响应确认时的超时行为。

## E09-7 · Reload 资源泄漏

坏扩展在 factory 中启动 timer，在 `session_start` 又启动 watcher，没有 `session_shutdown`。连续 `/reload` 三次。

1. 预计 timer/watcher 数怎样增长？为什么新 Runner 不能自动清掉它们？
2. 重写生命周期：factory、session_start、session_shutdown 各做什么？
3. cleanup 连续调用两次时必须满足什么？
4. 为什么 `await ctx.reload()` 后旧 Command handler 必须立即 return？
5. 怎样测试 reload 前后只有一个活跃 watcher，且旧 Context/SessionManager 不再被使用？

## E09-8 · Unload 能力盘点

查固定 `ExtensionAPI`，列出：

- 哪种资源有显式 `unregister`？
- Tool/Command 是否有对称 unregister？
- 想停用一个 Extension，需要经过哪些配置与 reload 步骤？
- 已经捕获的闭包、第三方模块全局状态、子进程能否由“从 Registry 移除”逆转？

最后给“逻辑停用”和“资源回收”各写一个独立验收条件。

## E09-9 · 第三方 Package 威胁模型

你准备安装：

```text
npm:@acme/pi-helper@latest
```

它含一个 preinstall script、12 个 transitive dependencies、读取 `OPENAI_API_KEY`、启动 WebSocket，并注册 Provider Header Hook。写一份安装前决策：

- 版本/制品怎样固定？
- 要审哪些源码、lockfile、脚本和远程端点？
- 暴露哪些目录、凭据与网络？
- 在宿主进程、容器、子进程三种方案中选哪个，为什么？
- 更新与回滚怎样做？
- Project Trust 能降低哪些风险，不能降低哪些？

至少列出一个“技术可行但经济不划算”的方案，并估算维护维度，而不是只说更安全。

## E09-10 · 接缝选择

为下面能力选择 in-process Extension、subprocess/RPC、remote service 或 OS sandbox，可组合：

1. 改状态栏颜色；
2. 解析不可信 PDF；
3. 给 `rm -rf` 增加确认；
4. 公司统一 Provider Gateway；
5. 在不可信仓库执行测试；
6. 运行会偶发 native crash 的语言服务器；
7. 记录 Turn Trace 到本地 JSONL。

每项写出：为何这样选、Extension 仍保留什么角色、失败与权限边界在哪里。

## E09-11 · 待实现测试规格

为未来 `iter09-extension-runtime.test.ts` 写至少 10 个测试，覆盖：

- trust gate；
- factory throw；
- ordinary hook throw；
- `tool_call` throw；
- mutation 顺序；
- tool/command conflict；
- provider delayed bind；
- mode-aware UI；
- reload cleanup；
- stale context/raw object；
- package source policy。

每个测试标 `Pi-faithful` 或 `course-hardening`。没有 RED/GREEN 记录前不得写“通过”。

## Hint ladder

- Hint 1：把 Extension 看成五个 Map 加一个共享 Runtime，而不是一个远端插件服务。
- Hint 2：load error、普通 Hook error、`tool_call` error 的传播路径不同。
- Hint 3：未来事件改由新 Runner 处理，不代表旧 JS side effects 被回滚。
- Hint 4：Project Trust 发生在项目 Extension 加载前，但 global/CLI Extension 已经是信任根的一部分。
- Hint 5：`temporary`、`hot reload`、`stale guard` 都不等于 OS 权限隔离。
- Hint 6：权限门无 UI 时应有显式默认策略，通常对高副作用操作 fail closed。

## Exit Ticket

闭卷写出一句话：为什么 Permission Extension 能改善误操作 UX，却不能成为强安全边界？再列出 reload-safe Extension 的三个生命周期不变量。
