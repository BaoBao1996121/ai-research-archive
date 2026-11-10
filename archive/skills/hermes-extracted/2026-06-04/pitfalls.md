> 脱敏节选 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 踩坑记录 · 2026-06-04

> 生成时间: 2026-06-04 22:15 (增量补充)

---

## MCP Server 验证通过但 VS Code Copilot 不显示工具

**评分**: 6/10 | **标签**: MCP, VS Code, 调试, Copilot

**摘要**: 通过 Python 子进程验证 MCP Server 端到端正常（工具注册成功、LLM 调用返回合法结果），但 VS Code Copilot Chat 仍不显示工具，表明问题在 VS Code 的 MCP Client 集成层。

### 💡 MCP Server 端到端验证通过（Python 子进程 + httpx JSON-RPC 请求成功返回 tool list 和 tool call 结果），但 VS Code Copilot 仍不显示该工具——说明根因不在 Server 配置而在 VS Code 的 MCP Client 层。可能原因包括：JSONL 传输超时、stdin 关闭时序、或 Copilot Chat 的 MCP 发现机制 bug。

- **适用场景**: 配置 VS Code MCP Server 后，工具在终端验证正常但 Copilot Chat 不可见。
- **行动建议**: 1. 先排除 Server 端问题（用 Python 子进程验证）。2. 确认 .vscode/mcp.json 符合 VS Code 最新 MCP 规范。3. 升级 VS Code 到最新版本。4. 如果仍然不显示，考虑使用 subagent 路由作为替代方案。

---

## Windows 上 Hermes CLI 安装但不在 PATH 中

**评分**: 5/10 | **标签**: Windows, 安装, PATH, 环境配置

**摘要**: Hermes 安装在 `C:\Users\<user>\AppData\Local\hermes\venv\Scripts\hermes.exe` 但 `where hermes` 找不到，说明该路径未加入系统 PATH。

### 💡 Windows 上通过安装器安装的 Hermes CLI 不在默认 PATH 中，需要通过完整路径 `& "C:\Users\<user>\AppData\Local\hermes\venv\Scripts\hermes.exe"` 调用，或手动将该路径加入 PATH 环境变量。

- **适用场景**: Windows 上首次安装 Hermes Agent 并尝试在终端使用时。
- **行动建议**: 1. 检查安装路径是否为 `C:\Users\<user>\AppData\Local\hermes\venv\Scripts\hermes.exe`。2. 设置环境变量 `PATH=%PATH%;C:\Users\<user>\AppData\Local\hermes\venv\Scripts`。3. 在 PowerShell 中调用时注意 & 运算符后需要空格。

---

## VS Code Copilot Subagent 缺少文件系统工具

**评分**: 7/10 | **标签**: Copilot, Subagent, 工具权限, 文件搜索

**摘要**: 通过 MCP 注册的 subagent（如 local-researcher）在 Copilot Chat 中没有文件搜索工具（file_search、grep_search），只能使用 session_store_sql 查询历史会话。

### 💡 Copilot Subagent 的工具集与主模型不同：subagent 可能没有文件系统操作工具（file_search、grep_search），即使主模型有这些能力。在调用 subagent 做文件搜索前，先确认其 tool list。

- **适用场景**: 使用 Copilot subagent 执行文件分析或搜索任务时。
- **行动建议**: 1. 在路由到 subagent 前，先确认它有哪些工具可用。2. 对于需要文件搜索的任务，不建议交给有限工具的 subagent。3. 如果 subagent 工具不足，可以回退到在主模型会话中执行搜索，或将搜索结果作为 context 传入 subagent。

---

## VS Code Agent Mode 的 `tools:` 白名单限制导致 MCP 工具不可见

**评分**: 7/10 | **标签**: VS Code, Copilot, MCP, 配置限制

**摘要**: 花了一个 Session 的时间排查 MCP Server 端到端验证通过但 Copilot 不显示工具的问题，最终根因居然是 `.agent.md` 的 `tools:` 白名单没有包含 `mcp`。这个白名单不是 VS Code 默认提示的配置项。

### 💡 MCP 工具在 VS Code Copilot Agent Mode 中的可见性需要满足三个条件：1) MCP Server 正确启动并通过端到端验证；2) `.vscode/mcp.json` 格式正确；3) **`.agent.md` 的 `tools:` 白名单包含 `mcp`**。第 3 点很少有人提到，是排查时最容易被忽略的环节。

- **适用场景**: VS Code Copilot Agent Mode 下 MCP 工具不可见时。
- **行动建议**: 排查 MCP 工具不显示时，前三步应该改为：1) 检查 `.agent.md`/`.instructions.md` 的 `tools:` 白名单 → 2) 端到端验证 MCP Server → 3) 检查 mcp.json 格式。

---

## Copilot Codex 没有 workspace 文件搜索能力

**评分**: 6/10 | **标签**: Codex, Copilot, 文件搜索, 工具限制

**摘要**: Copilot Codex 环境下（Session 2 末尾验证），subagent 只有 `session_store_sql` 这一个工具，无法搜索工作区文件。这与在 Obsidian Vault 编辑器（支持 file_search、grep_search）中的体验完全不同。

### 💡 VS Code Copilot 的 Agent Mode 工具集严重依赖于具体的工作区和 Agent Type（Codex vs Copilot vs Copilot Edits）。Codex 环境下的 subagent 可能比 Copilot Chat 环境少很多工具。切换代码编辑工具时，不要假设工具集一致。

- **适用场景**: 在 Codex 或 Copilot Edits 中使用 subagent 时。
- **行动建议**: 1. 跨 Agent Type 工作时，先运行 `@workspace` 确认工具清单。2. Codex 下需要文件搜索时，在主会话中用终端命令代替。3. 为不同 Agent Type 维护不同的工具预期。
