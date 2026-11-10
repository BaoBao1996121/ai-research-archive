> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../../ARCHIVE_POLICY.md)。

# PI-I06 练习：从资源候选集推导最终能力

> 一句话结论：不要靠“应该会加载”作答；每题都要标出 discovery、trust、explicit input、capability compilation 属于哪一层。

## 使用方式

先独立完成，再打开 [参考答案](../solutions/PI-I06.md)。本批没有 I06 自动化 Lab；任何手工推导都不能写成“测试通过”。若你实现练习代码，请先写失败测试并保留 RED→GREEN 证据。

## E06-1 · Context Files 层级排序

给定：

```text
agentDir/AGENTS.md                  内容 G
/workspace/CLAUDE.md               内容 R
/workspace/repo/AGENTS.md          内容 P
/workspace/repo/app/AGENTS.md      内容 A
/workspace/repo/app/CLAUDE.md      内容 C
cwd=/workspace/repo/app
```

回答：

1. 哪些文件被加载？
2. 最终顺序是什么？
3. 为什么 `C` 不出现？
4. Project Trust=false 是否改变这个答案？
5. 加上 `--no-context-files` 后又是什么？

必须用一句话解释“官方文档说 concatenate 与单目录只取第一候选为何不矛盾”。

## E06-2 · Trust 矩阵

项目包含：

```text
AGENTS.md
.pi/settings.json
.pi/SYSTEM.md
.pi/extensions/deploy.ts
.pi/skills/release/SKILL.md
.pi/prompts/review.md
.pi/themes/corp.json
```

另有全局 `~/.pi/agent/extensions/audit.ts`，启动 flags 为：

```text
-e ./temporary.ts --skill ./lesson/SKILL.md
```

分别填写 Project Trust=true/false：

| 资源 | true | false | 原因 |
|---|---|---|---|
| AGENTS.md | ? | ? | |
| `.pi/settings.json` | ? | ? | |
| `.pi/SYSTEM.md` | ? | ? | |
| project deploy Extension | ? | ? | |
| project Skill/Prompt/Theme | ? | ? | |
| global audit Extension | ? | ? | |
| CLI temporary Extension | ? | ? | |
| CLI explicit Skill | ? | ? | |

## E06-3 · `--no-*` 不是“全部拒绝”

预测下面四条命令的资源结果：

```text
1. pi --no-extensions -e ./audit.ts
2. pi --no-skills --skill ./pdf/SKILL.md
3. pi --no-prompt-templates --prompt-template ./review.md
4. pi --no-context-files --append-system-prompt ./guardrails.md
```

对每条写出：关闭的是自动发现、显式资源，还是另一类输入。若你认为某个路径还受 Project Trust 影响，必须指出源码位置，而不是猜测。

## E06-4 · Trust、Authorization、Isolation 分类

将每项放入最主要的一层，允许一项有辅助层：

- 未批准前不执行 `.pi/extensions/deploy.ts`；
- `read` 参数必须有字符串 path；
- `read` 只能访问 `/workspace`；
- Bash 在无网络容器里运行；
- 每次删除前弹确认；
- `AGENTS.md` 仍能进入 Prompt；
- Extension 包来源锁定到 commit；
- 工具进程只拿 10 分钟短期凭据。

分类候选：Discovery/Trust、Validation、Authorization、Isolation、Supply-chain control。

## E06-5 · Prompt/Tool Coherence Test

设计一个最小行为测试：

1. Tool Definition 注册 `bash`，同时提供 `promptSnippet` 和 guideline；
2. Active Tools 初始含 bash；
3. 运行时动态排除 bash；
4. 重新编译请求。

写出至少四条断言，必须同时覆盖：

- API 请求的 Tool schema；
- System Prompt 的 Available tools；
- System Prompt 的 bash guideline；
- 非 bash 工具未被误删。

进阶：定义一个 manifest hash 的输入字段，说明它怎样帮助重放审计。

## E06-6 · 资源冲突与来源追踪

四个同名 Skill `review`：

```text
A project settings path
B project auto-discovered
C user settings path
D package resource
```

1. 按固定提交的 precedence 排序。
2. 为什么“高优先级”不等于“更安全”？
3. 诊断至少应输出哪些字段，才能让用户知道谁覆盖了谁？
4. 若 Extension `resources_discover` 再贡献一个 `review`，你会如何测试确定性？

## E06-7 · 故障定位演练

现象：启动页看得到 `deploy` Skill，却没有 `deploy` Tool；Prompt 中仍写“使用 deploy 工具”。请按优先级提出排查步骤，不超过 8 步。

要求覆盖：

- Skill 与 Tool 不是同一种资源；
- Project Trust；
- Extension load diagnostics；
- Active Tool allow/deny list；
- 最终 request tools 与 System Prompt 对比。

## E06-8 · 威胁模型

场景：无人值守处理来自外部贡献者的仓库，宿主机有 SSH key、云凭据和企业网络访问。

提交一个四层控制表：

| 层 | 控制 | 残余风险 | 成本 |
|---|---|---|---|
| Discovery | | | |
| Trust/Authorization | | | |
| Isolation | | | |
| Audit/Recovery | | | |

不能把 `--no-approve` 写成唯一安全措施。

## Hint ladder

- Hint 1：`loadContextFileFromDir()` 每个目录遇到第一候选就 return。
- Hint 2：`noExtensions` 分支仍保留 `cliEnabledExtensions`；Skills/Prompts/Themes 也要看 additional paths。
- Hint 3：Project Trust gate 的对象是 project `.pi` settings/resources/packages/extensions；Context Files 是例外。
- Hint 4：`_refreshToolRegistry()` 和 `_rebuildSystemPrompt()` 是 Coherence Test 的两个观察面。
- Hint 5：如果答案出现“Trust 后 Bash 只能读 cwd”，立刻回到威胁模型重做。

## Exit Ticket

闭卷完成两句话：

```text
Project Trust 能保证 ______，不能保证 ______。
能力一致性要求 ______ 与 ______ 从 ______ 生成。
```
