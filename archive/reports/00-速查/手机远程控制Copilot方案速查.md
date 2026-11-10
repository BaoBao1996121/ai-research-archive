> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 手机远程控制 VS Code Copilot 方案速查

> 核心问题：如何在手机上给电脑上的 Copilot 发消息、让它干活、看到反馈？
> 创建日期：2026-05-12
> 信息来源：VS Code 官方文档、GitHub 官方文档、GitHub Blog

---

## 方案总览

| 方案 | 一句话 | 手机体验 | 能否操控本地 VS Code | 成本 | 推荐场景 |
|------|--------|----------|---------------------|------|---------|
| **A. VS Code Tunnel** | 手机浏览器打开 vscode.dev，直连电脑 VS Code | 完整 VS Code 网页版 | **能** — 直接操作电脑上的文件和终端 | 免费 | **通用首选** |
| **B. Copilot Cloud Agent** | 手机上建 Issue 指派给 Copilot，它自动干活出 PR | GitHub 网页/App | 否 — 在 GitHub Actions 云端执行 | Copilot Pro 起 | 异步任务分派 |
| **C. 远程桌面** | RDP/ToDesk/向日葵 | 看到完整桌面 | 能 — 等于人在电脑前 | 免费~付费 | 应急/复杂操作 |
| **D. SSH + CLI Agent** | 用 Termux/SSH 客户端连到电脑，跑 Claude Code 等 CLI | 纯命令行 | 间接 — 只能操作 CLI 工具 | 免费 | 极客/CLI 控 |

**推荐**：方案 A 是你要找的东西。它让你在手机浏览器里打开一个**完整的 VS Code**，直接和 Copilot Chat 对话，用 Agent Mode 让它改代码、跑命令，和坐在电脑前体验一致。

---

## 方案 A：VS Code Remote Tunnels（强烈推荐）

### 这是什么

VS Code 内置的隧道功能。电脑上开启后，手机浏览器访问 `vscode.dev/tunnel/你的机器名`，就能远程操作电脑上的 VS Code，包括 Copilot Chat、Agent Mode、终端。

### 设置步骤（一次性，5 分钟）

**电脑端（只做一次）**：

```powershell
# 方法 1：命令行启动（推荐，可设置为开机自启）
code tunnel

# 首次运行会要求用 GitHub 账号登录授权
# 登录后输出一个 URL：https://vscode.dev/tunnel/<machine_name>
```

或者在 VS Code 里：
1. 点击左下角账户图标
2. 选择 **Turn on Remote Tunnel Access...**
3. 用 GitHub 账号授权

**手机端**：
1. 手机浏览器打开 `https://vscode.dev/tunnel/<machine_name>`
2. 用同一个 GitHub 账号登录
3. 完成 — 你看到的就是电脑上的 VS Code

### 你能做什么

- 打开 Copilot Chat（Ctrl+Shift+I 或侧边栏）
- 使用 Agent Mode 让 Copilot 改代码、创建文件、跑终端命令
- 查看文件、编辑代码、看终端输出
- 使用所有已安装的扩展（大部分在 web 版可用）

### 注意事项

- 电脑必须开着且 tunnel 保持运行（可以设为服务/开机自启）
- 手机浏览器 Safari/Chrome 均可，但屏幕小操作不如平板舒服
- 网络延迟取决于你的网络环境，通过微软 Azure 中继，国内可能有延迟
- 纯 UI 扩展在 web 版不可用（但 Copilot 完全可用）

### 开机自启设置（可选）

```powershell
# 方法：创建计划任务，开机时启动 tunnel
$action = New-ScheduledTaskAction -Execute "code" -Argument "tunnel --accept-server-license-terms"
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "VSCodeTunnel" -Action $action -Trigger $trigger -Description "VS Code Remote Tunnel"
```

---

## 方案 B：GitHub Copilot Cloud Agent（异步任务分派）

### 这是什么

不是连接你本地的 VS Code，而是在 GitHub 云端有一个独立的 Copilot Agent。你在手机上给它分配 Issue，它自动分析代码库、写代码、跑测试、开 PR。

### 怎么用

1. 手机装 **GitHub Mobile** App（或用浏览器打开 github.com）
2. 在仓库里创建 Issue，描述你要做的事
3. 将 Issue 的 Assignee 设为 **Copilot**
4. Copilot 自动开始工作，创建 draft PR
5. 你在手机上可以看到 PR 进度、留评论让它迭代

也可以通过 **Slack / Microsoft Teams** 直接给 Copilot 发消息派活。

### 适用场景

- 修 bug、写测试、改文档、清理技术债
- 不需要实时交互的任务（"去做这件事，做完告诉我"）
- 代码必须在 GitHub 仓库里

### 和方案 A 的本质区别

| | 方案 A（Tunnel） | 方案 B（Cloud Agent） |
|---|---|---|
| 工作位置 | 你电脑上 | GitHub 云端 |
| 交互模式 | 实时对话 | 异步指派 |
| 操作范围 | 电脑上的任何文件/项目 | 仅 GitHub 仓库 |
| 需要电脑在线 | 是 | 否 |
| Copilot 计划 | Free 也能用 Chat | Pro 起 |

---

## 方案 C / D 简述

**远程桌面**：ToDesk、向日葵、RDP——装 App 就能看到电脑桌面，操作 VS Code。优点是什么都能干；缺点是手机上操作桌面 UI 体验很差，流量也大。适合偶尔应急。

**SSH + CLI**：如果你用 Claude Code 这类 CLI 工具，手机装 Termux（Android）或 Blink Shell（iOS），SSH 到电脑上直接运行。纯命令行，无 GUI。适合 CLI 重度用户。

---

## 我的推荐

**日常用方案 A**。设好 tunnel 后，手机浏览器一打开就是完整的 Copilot 体验，和在电脑前没有本质区别。延迟是唯一的 trade-off，如果网络不好可以备一个方案 C。

**如果你的代码在 GitHub 上**，方案 B 是很好的补充——通勤路上想到一个 bug，直接在 GitHub App 里建个 Issue 扔给 Copilot，到公司时 PR 已经在等你 review 了。

---

## 来源

- [VS Code Server 文档](https://code.visualstudio.com/docs/remote/vscode-server) — 2026-05-06 更新
- [VS Code Remote Tunnels 博客](https://code.visualstudio.com/blogs/2022/12/07/remote-even-better) — 2022-12-07
- [GitHub Copilot Cloud Agent 文档](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent) — 2026 年
- [Copilot Coding Agent 101 博客](https://github.blog/ai-and-ml/github-copilot/github-copilot-coding-agent-101-getting-started-with-agentic-workflows-on-github/) — 2025-09-11，更新 2026-01-14
