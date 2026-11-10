> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P05 跨机器部署 · 5 分钟把双标签编排在另一台电脑跑起来

> 目标读者：你在另一台 Windows 电脑上拿到这份共享知识库，想立刻在生产环境验证"双标签 + ccreq 对账"工作流。
> 假设：另一台机器已装 VS Code + GitHub Copilot Chat 扩展 + Python 3.10+。

## 0 · 你需要带过去的最小文件集

整个 P05 体系只依赖以下 3 类文件，全部已在共享知识库里：

| 类别 | 路径 | 数量 |
|---|---|---|
| Subagent 定义 | `prototypes/P05_vscode-multiagent-orchestration/agents/*.agent.md` | 6 个 |
| Coordinator（含双标签 + 路由查询协议） | `.github/agents/feature-coordinator.agent.md` | 1 个 |
| 工具 | `prototypes/P05_vscode-multiagent-orchestration/tools/{ccreq_parser,task_router}.py` | 2 个 |

**零外部依赖**：两个工具都是纯 Python stdlib，不需要 `pip install` 任何东西。

## 1 · 在新机器上启用（3 步）

### Step 1 · 把 agents 文件挂到 VS Code 能识别的位置

```powershell
# 在共享知识库根目录执行
$src = "prototypes\P05_vscode-multiagent-orchestration\agents"
$dst = ".github\agents"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
Copy-Item "$src\*.agent.md" $dst -Force

# coordinator 单独到根 .github
Copy-Item "$src\..\..\..\.github\agents\feature-coordinator.agent.md" $dst -Force
```

或者把 agents 放到用户级（跨工作区可用）：

```powershell
$dst = "$HOME\.copilot\agents"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
Copy-Item "prototypes\P05_vscode-multiagent-orchestration\agents\*.agent.md" $dst -Force
Copy-Item ".github\agents\feature-coordinator.agent.md" $dst -Force
```

### Step 2 · 在 VS Code 中确认加载成功

1. 重启 VS Code（或运行命令面板 → `Developer: Reload Window`）
2. Chat 面板的 agents 下拉里应能看到 `feature-coordinator`
3. 5 个 worker（`researcher` / `implementer` / `reviewer` / `security-reviewer` / `performance-reviewer`）因为设了 `user-invocable: false`，不会出现在下拉
4. 如有黄色错误，命令面板 → `Chat: Show Diagnostics` 看 YAML 报错

### Step 3 · 验证两个工具能跑

```powershell
# 路径自适应（无需配 PATH，直接用相对路径）
python prototypes\P05_vscode-multiagent-orchestration\tools\ccreq_parser.py --last 3
python prototypes\P05_vscode-multiagent-orchestration\tools\task_router.py "审查 SQL 注入风险"
```

预期输出：
- `ccreq_parser.py` 列出最近 3 条 subagent 调用（如果还没用过 subagent 会显示 0 条，这是正常的）
- `task_router.py` 输出 `-> security-reviewer · claude-sonnet-4-5-20250929  [命中安全语义关键词]`

## 2 · 跨机器可移植性已验证的事实

| 项 | 是否跨机器 | 说明 |
|---|---|---|
| `ccreq_parser.py` 的日志路径 | ✅ | 用 `os.environ["APPDATA"]`，Windows 标准变量，自动适配每台机器的用户 |
| `task_router.py` 的规则 | ✅ | 纯 Python 字符串匹配，无外部状态 |
| agent.md 的 `model:` 字段 | ✅ | 字段名是 VS Code 协议的一部分，跨机器一致 |
| 双标签命中率 | ⚠️ 待目标机验证 | 需在目标机器复跑一次 5 范式，确认 ccreq `MODEL_RESOLVED` 与 agent.md `model[0]` 仍 100% 一致 |

## 3 · 第一次验证脚本（建议在目标机跑这一段）

```powershell
# 在 VS Code Chat 切到 feature-coordinator agent，粘贴以下 prompt：
```

```
我想在这台电脑上验证 P05 双标签机制是否还成立。请：

1. 派 researcher 列出 prototypes/P05_vscode-multiagent-orchestration/examples/buggy_user_service.py 中所有处理外部输入的函数
2. 派 reviewer 给出 must-fix 清单
3. 每段调用前预填 [预期] 标签（从 agent.md 读 model 首项）
4. 每段调用后跑 ccreq_parser.py --latest-of <agent> 填 [实际] 标签
5. 最终汇总：双标签是否 2/2 一致？如果不一致，说明这台机器的 cost-tier 行为与源机器不同
```

预期：双标签 2/2 一致 → 工具链跨机器无缝工作。

## 4 · 可能的差异点（提前提醒）

- **GitHub Copilot 计划等级**：如果目标机的账号是 Free/Individual 计划，可能不开放 Sonnet 4.5，会触发 cost-tier 回退（Sonnet → Haiku）。这种情况下双标签会显示**预期 ≠ 实际**——这正是机制要发现的问题，不是工具 bug
- **VS Code 版本**：ccreq 日志格式来自 2026-04 Insiders 版本。如果目标机 VS Code 比较旧或更新，日志正则可能要微调（在 `ccreq_parser.py` 的 `CCREQ_RE` 处）
- **APPDATA 多用户**：如果目标机是共享账户，多个 VS Code 实例的日志会混在 `%APPDATA%\Code\logs\` 同一棵树下，`find_latest_log()` 按 mtime 挑最新，通常没问题

## 5 · 出问题往哪查

| 症状 | 查这里 |
|---|---|
| Coordinator 不在下拉里 | `Chat: Show Diagnostics` |
| ccreq_parser 找不到日志 | `Get-ChildItem $env:APPDATA\Code\logs -Recurse -Filter "GitHub Copilot Chat.log"` 看是否存在 |
| ccreq_parser 输出 0 条 | 可能日志已被 VS Code 翻篇，跑一次 subagent 任务后再试 |
| 双标签不一致 | 看 R73 §"Cost tier 回退"——多半是计划等级触发回退 |
| 路由结果不对 | 在 `task_router.py` 的 `ROUTING_RULES` 里调正则。原则：动作动词优先级 > 领域名词 |

## 6 · 这套体系背后的研究链（如要深入）

| 文档 | 看什么 |
|---|---|
| [`reports/04-工程实践/R73_VSCodeCopilot多Agent编排实践.md`](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R73_VSCodeCopilot%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E5%AE%9E%E8%B7%B5.md) | 为什么这么设计、A/B 实测细节、5 范式回归基线表 |
| [`prototypes/P05_vscode-multiagent-orchestration/README.md`](README.md) | 5 分钟 IDE 内验证步骤 + ccreq 日志读法 + 双标签协议 |
| [`prototypes/P05_vscode-multiagent-orchestration/examples/PATTERNS.md`](examples/PATTERNS.md) | 5 大编排范式触发提示词 + EDD 验证点 |
| `sessions/2026-04/2026-04-26_subagent动态模型选择议题.md`（原稿引用文件未随本次归档发布） | 下一步：动态模型选择三路径 |
| `DELIVERABLES_INDEX.md`（原稿引用文件未随本次归档发布） | D53 + D55 完整产物注册 |

---

## 一句话总结

**所有所需文件都在共享知识库里，跨机器零额外依赖**：复制 7 个文件到位 → 重启 VS Code → 跑一次验证 prompt 看双标签是否 2/2 一致即可。
