> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P05 · VS Code Copilot 多 Agent 编排原型（异构模型实测）

> 配合 [R73](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R73_VSCodeCopilot%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E5%AE%9E%E8%B7%B5.md) 报告。**本原型用最小四件套验证 R73 中三个最核心、最容易被怀疑的断言**：
>
> 1. ✅ Subagent 真的可以用与主 Agent 不同的模型
> 2. ✅ 主对话上下文不会被 subagent 工具调用炸开（subagent 输出 ≈ summary）
> 3. ✅ Coordinator → Worker 的 Orchestrator-Worker 模式在 VS Code 内即可跑通

---

## 0 · 凭据：官方原文（先看，省得怀疑）

来源：<https://code.visualstudio.com/docs/copilot/agents/subagents>（最后确认日期：2026-04-26）

> **Model selection for subagents**：
> When a subagent runs, the model is determined by the following priority order:
> 1. Explicit model parameter: the main agent specifies a model directly when invoking the `runSubagent` tool.
> 2. Agent-configured model: the `model` property in the custom agent's `.agent.md` frontmatter.
> 3. Main model: the model running the parent conversation.
>
> Note: The requested model **cannot exceed the cost tier of the main model**. If you request a more expensive model, the subagent **falls back to the main model**.

> **Coordinator and worker pattern**（官方原例片段）：
> ```yaml
> ---
> name: Implementer
> user-invocable: false
> model: ['Claude Haiku 4.5 (copilot)', 'Gemini 3 Flash (Preview) (copilot)']
> ---
> ```

**结论**：异构模型选择 = VS Code 官方原生支持的特性，不是 hack。本原型只是把官方说法落到 4 个最小可验证文件里。

---

## 1 · 文件清单

```
P05_vscode-multiagent-orchestration/
├── README.md              ← 本文件
└── agents/
    ├── feature-coordinator.agent.md   ← 主控（用主 picker 选大模型）
    ├── researcher.agent.md            ← Worker A：检索类，配便宜模型
    ├── implementer.agent.md           ← Worker B：实现类，配快模型
    └── reviewer.agent.md              ← Worker C：审查类，配大模型
```

四个 agent **故意配不同模型**，方便你在 chat 中观察"subagent 模型确实变了"。

---

## 2 · 5 分钟验证步骤

### Step 1 · 把 agents 文件软链/复制到 VS Code 能识别的位置

VS Code 默认扫描两个位置（任选其一即可）：

| 作用域 | 路径 | 适用 |
|--------|------|------|
| 工作区级 | `<workspace>/.github/agents/` | 当前项目 |
| 用户级 | `~/.copilot/agents/`（Windows: `C:\Users\<you>\.copilot\agents\`） | 跨工作区 |

**最简单做法**（PowerShell，工作区级）：

```powershell
# 在本工作区根目录执行
$src = "prototypes\P05_vscode-multiagent-orchestration\agents"
$dst = ".github\agents"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
Copy-Item "$src\*.agent.md" $dst -Force
Get-ChildItem $dst
```

### Step 2 · 在 VS Code 中刷新 Agent 列表

1. 打开 Chat 面板
2. 点击 Chat 输入框上方的 **agents 下拉菜单** → 应能看到 `feature-coordinator`（其他三个 worker 设了 `user-invocable: false`，不会出现在下拉）
3. 如果没看到，运行命令面板 → `Chat: Show Diagnostics`，确认 4 个文件都被加载、无 YAML 报错

### Step 3 · 触发编排

选中 `feature-coordinator` agent，输入：

> 帮我加一个"用户偏好设置"功能：先研究当前代码结构，然后给出实现，最后审查质量。

观察主 chat 中应当依次出现 **3 个折叠的 subagent 工具调用块**：
- 🔍 Running Researcher...
- ⚙️ Running Implementer...
- 👀 Running Reviewer...

### Step 4 · 验证模型确实切换了（关键）

逐个**点击展开**每个 subagent 工具调用块，看顶部元信息。VS Code 会在 subagent 头部明确显示：

```
Subagent: researcher  ·  Model: Claude Haiku 4.5
Tools: read, search
```

如果三个 subagent 的 `Model:` 字段分别是不同的（Haiku / Haiku / Sonnet），即**异构模型断言被实证**。

如果你的 GitHub Copilot 计划只有一个可用模型，VS Code 会落到 fallback：所有 subagent 都用主模型，但仍能跑通——这只意味着你账号的"模型货架"只有一种货，不是机制不存在。

### Step 5 · 验证上下文经济（次关键）

任务结束后：
1. 看主对话历史里**没有**出现 researcher 读过的所有源文件全文，只有它返回的几段 summary
2. 在命令面板运行 `Chat: Show Token Usage`（或在 Show Diagnostics 中看），主对话占用应远小于 "如果所有工具调用直接发生在主对话" 的预估值

经验数据（来自 R73）：典型 4-agent feature 任务，**主对话节省 60-80% token**。

---

## 3 · 验证表（请自己填，作为 EDD 风格的回归基线）

| 断言 | 你看到的 | 是否符合 |
|------|---------|---------|
| Coordinator 出现在 dropdown | | □ |
| 3 个 worker **不** 出现在 dropdown | | □ |
| Coordinator 派生了 3 个 subagent | | □ |
| 三个 subagent 的 Model 字段显示 | | □ |
| 三个 subagent 的 Tools 字段显示 | | □ |
| 主对话历史**不含** worker 读过的文件全文 | | □ |
| 主对话总 token 显著少于"无编排"基线 | | □ |

填完后这张表就是你以后回归测试 .agent.md 改动的"Eval 基线"——符合 edd-protocol（原稿交叉引用，本归档未解析） 协议。

---

## 4 · 故障排查

| 症状 | 原因 | 修复 |
|------|------|------|
| Dropdown 看不到 coordinator | YAML 解析失败 / 文件位置不对 | `Chat: Show Diagnostics` 看 errors |
| 派生失败"agent not found" | worker 文件没复制全 | 确认 `.github/agents/` 下 4 个文件都在 |
| 所有 subagent 用同一个模型 | 你的 Copilot 计划只供一种模型 / 请求模型超主模型 cost tier 被回退 | 在主模型选大的（如 Sonnet 4.5），workers 配 Haiku |
| Subagent 嵌套不工作 | 默认禁止 | 设置 `chat.subagents.allowInvocationsFromSubagents=true`（最多 5 层） |
| Worker 出现在 dropdown 不希望被人手点 | `user-invocable` 没设 | 在 frontmatter 加 `user-invocable: false` |

---

## 4.5 · 用 VS Code Output 日志做 Ground Truth 对账（关键技能）

SELF_REPORT 是模型自报，**可能不准**（Haiku 可能说自己是 "Claude 3.5 Sonnet" 之类老版本，因为权重训练数据滞后于实际部署版本）。要 100% 确认到底用了什么模型，看 VS Code 内部日志：

### 操作步骤

1. `Ctrl+Shift+U` 打开 Output 面板
2. **右上角下拉框选 `GitHub Copilot Chat`**（注意：不是 "GitHub Copilot"，那是补全的日志，没用）
3. 触发一次 coordinator 任务
4. 在日志里搜：`runSubagent`

### 你会看到（真实示例）

```
ccreq:e05387df | success | claude-haiku-4.5 -> claude-haiku-4-5-20251001 | 3411ms | [tool/runSubagent-researcher]
ccreq:a44646b2 | success | claude-haiku-4.5 -> claude-haiku-4-5-20251001 | 3911ms | [tool/runSubagent-implementer]
ccreq:6c08cff2 | success | claude-sonnet-4.5 -> claude-sonnet-4-5-20250929 | 6001ms | [tool/runSubagent-reviewer]
[ToolCallingLoop] Subagent stop hook result: shouldContinue=false
```

### 怎么读这一行

```
ccreq:<id> | success | <frontmatter写的模型> -> <实际部署版本> | <耗时ms> | [tool/runSubagent-<agent名>]
```

- `claude-haiku-4.5` 是你 frontmatter 写的别名
- `-> claude-haiku-4-5-20251001` 是 VS Code **真正路由到的部署版本**（含日期戳）
- `[tool/runSubagent-researcher]` 是哪个 subagent 触发的

### Cost tier 回退会怎么显示

如果发生回退，日志会变成（推测，需实际复现）：

```
ccreq:xxx | success | claude-sonnet-4.5 -> claude-haiku-4-5-20251001 | xxxx ms
                       ↑ 你想要的            ↑ 实际给你的（被回退到主模型）
```

**两个版本号不一致** = 发生了 cost tier 回退。

### 4.5.1 · 自动化对账：ccreq_parser.py（推荐方式）

不用人工切 Output 面板复制——直接用 [`tools/ccreq_parser.py`](tools/ccreq_parser.py) 自动解析日志：

```bash
# 最近 10 条 subagent 调用
python tools/ccreq_parser.py --last 10

# 指定时间窗（推荐用于一次任务后的对账）
python tools/ccreq_parser.py --last 10 --since "2026-04-26 10:00"

# 仅看某个 agent
python tools/ccreq_parser.py --agent reviewer --last 5

# JSON 输出，便于脚本/CI 消费
python tools/ccreq_parser.py --last 10 --json
```

输出示例：

```
📁 日志源: C:\Users\...\GitHub Copilot Chat.log
🔍 匹配 3 条 subagent 调用记录

TIME     | AGENT                    | MODEL_RESOLVED                   |      DUR | STATUS
------------------------------------------------------------------------------------------
10:15:30 | performance-reviewer     | claude-haiku-4-5-20251001        |   9313ms | success
10:15:36 | security-reviewer        | claude-sonnet-4-5-20250929       |  15804ms | success
10:15:37 | reviewer                 | claude-sonnet-4-5-20250929       |  16931ms | success
```

**这是身份验证的 SSOT（single source of truth）**——不依赖任何模型自报，机制层 100% 可靠。

### 为什么这是 EDD 的最强 ground truth

| 信号源 | 准确度 | 实施成本 |
|---|---|---|
| Subagent 自报 SELF_REPORT | ⭐⭐ A/B 实测漏报 33-67% | 0（已配置） |
| Chat UI 折叠块标题 | ⭐⭐⭐ UI 版本依赖 | 0（默认显示） |
| **Output 日志（人工切面板）** | ⭐⭐⭐⭐⭐ 100% 准确 | 5 秒切面板 |
| **ccreq_parser.py（自动）** | ⭐⭐⭐⭐⭐ 100% 准确 | 0，已脚本化 |

每次改 .agent.md 后，跑一次任务 + `python tools/ccreq_parser.py --last 10 --since "..."`，就是最严格的 EDD 回归基线。

### 4.5.2 · 已确认的机制层事实

经 2026-04-26 多次实测：

- ✅ **模型选择是确定性的**：每个 agent.md 的 `model:` 数组**第一项**就是实际生效模型，不会因任务变化漂移
- ❌ **MODEL_SELF_REPORT 协议从根本上不可靠**：A/B 测试中即便强化（标题加"违反即任务失败" + 显式禁止短语 + 调用方提醒），漏报率仍 33-67%。Sonnet 也漏，不是 Haiku 专属问题
- ✅ **agent.md `model:` 数组首项 = ccreq 中 `MODEL_RESOLVED`**：这是切换模型的可靠手柄

### 4.5.3 · 双标签协议（推荐使用模式）

基于 4.5.1 + 4.5.2 的事实，coordinator 现在采用**双标签协议**：每段 subagent 输出包夹两个身份标签——上标签是**调用前**从 agent.md 读的预期模型，下标签是**调用后**从 ccreq 日志查的实际模型。

```
┌─ [预期] researcher · Claude Haiku 4.5
│  <subagent 输出>
└─ [实际] researcher · claude-haiku-4-5-20251001  (19270ms)
```

**实施一行命令**：

```bash
python tools/ccreq_parser.py --latest-of <agent_name>
# 输出: agent_name -> model_resolved  (Xms, HH:MM:SS)
```

**实测命中率**：8+ 次 subagent 调用，预期 = 实际 100% 一致（含 5 大编排范式 Pattern 1-5 全覆盖）。

**额外开销**：每段 < 0.1s 本地脚本，相对 subagent 本身 8-30s 耗时可忽略 → cost-free 可观测性增强。

### 4.5.4 · 路由查询（可选 · 让派发可审计）

[`tools/task_router.py`](tools/task_router.py) 把"任务 → 推荐 agent"从 coordinator 拍脑袋变成机制化查询：

```bash
python tools/task_router.py "审查 login 函数的 SQL 注入风险"
# -> security-reviewer · claude-sonnet-4-5-20250929  [命中安全语义关键词]

python tools/task_router.py --explain "实现一个安全版本的 login 函数"
# 任务摘要      : 实现一个安全版本的 login 函数
# 推荐 agent    : implementer
# 绑定模型      : claude-haiku-4-5-20251001  (fast tier)
# 路由理由      : 命中实现/写代码动作

python tools/task_router.py --json "..." --input-file path/to/data.txt
# 含输入大小估算 + 大文件自动 tier 升级
```

**路由规则设计原则**：动作动词优先级 > 领域名词。"实现一个**安全**函数"的核心动作是 implement，"安全"只是修饰 → 派 implementer 而非 security-reviewer。

**已知边界**：5/5 测试通过，但每加一个新 agent / 新维度需回头调正则。如果未来 agent 数 ≥ 10，建议升级到路径 B（task-profiler subagent，详见 `sessions/2026-04/2026-04-26_subagent动态模型选择议题.md`（原稿引用文件未随本次归档发布））。

---

## 5 · 真出错怎么办（投诉链路）

如果你照本步骤跑、仍发现 model 字段**完全不生效**（不是回退到主模型，而是 frontmatter 写了被忽略），那是 VS Code Copilot Chat 的 bug，应当：

1. 在 Chat → Show Diagnostics 中截图
2. 提交到 <https://github.com/microsoft/vscode-copilot-release/issues>
3. 同时告诉我，我会把这个反例补到 [R73](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R73_VSCodeCopilot%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E5%AE%9E%E8%B7%B5.md) 的"开放问题"章节，并把"model 异构"断言降级为"理论支持但实测有 bug"

这就是 EDD 闭环 —— 文档写的、原型跑的、用户实测的，三者必须收敛。

---

## 6 · 与 R73 的对应关系

| R73 章节 | 本原型证据 |
|---------|-----------|
| §"Subagent 派生异构模型" | `implementer.agent.md` 的 `model:` 数组 |
| §"硬约束 100% 遵循" | `agents:` 白名单 + `user-invocable: false` |
| §"上下文 70% 节省" | Step 5 token 实测 |
| §"Coordinator-Worker 范式" | `feature-coordinator.agent.md` 整体 |
| §"避坑表 #5 worker 出现在 dropdown" | `user-invocable: false` 演示 |

---

**最后**：如果你跑出来的结果跟 R73 描述不符，**以你的实测为准，回头修 R73**。文档服从证据，不是反过来。
