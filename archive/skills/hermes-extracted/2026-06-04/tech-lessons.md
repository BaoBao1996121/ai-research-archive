> 脱敏节选 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 技术经验 · 2026-06-04

> 生成时间: 2026-06-04 22:15 (增量补充)

---

## MCP Server 端到端验证方法

**评分**: 7/10 | **标签**: MCP, VS Code, 调试, 工具链

**摘要**: 通过 Python 子进程直接启动 MCP Server 脚本，用 httpx 发送 JSON-RPC 请求，可以比依赖 VS Code 自动发现更快地验证 MCP Server 配置是否正确。

### 💡 验证 MCP Server 连接时，跳过 VS Code 自动发现，直接用 Python 子进程启动脚本 + httpx 发送 list_tools 请求，可以在 30 秒内确认配置是否正确，而不必重启 VS Code。

- **适用场景**: 配置 MCP Server 后需要快速验证，不想反复重启 VS Code。
- **行动建议**: 1. 用 subprocess 启动 MCP Server 脚本。2. 通过 stdin/stdout 发送 JSON-RPC 请求（{"jsonrpc":"2.0","id":1,"method":"tools/list"}）。3. 读取响应中的 tools 列表确认注册成功。4. 发送 tools/call 请求测试实际调用。

### 💡 MCP Server 端到端验证已通过但 VS Code Copilot 仍不显示工具，说明问题不在 MCP Server 配置本身，而在 VS Code 的 MCP Client 集成层——可能是 JSONL 传输超时、stdin 关闭时序或 Copilot Chat 的 MCP 发现机制有 bug。

- **适用场景**: 排查 VS Code Copilot MCP Tool 注册失败时。
- **行动建议**: 先用 Python 子进程验证 MCP Server 本身可用，再检查 .vscode/mcp.json 格式是否与官方文档一致，特别注意 inputs 和 args 数组的格式。如果都正确但 Copilot 仍不显示，考虑升级 VS Code 或使用 subagent 路由作为替代方案。

---

## VS Code Copilot Agent 的 `tools:` 白名单需要显式包含 `mcp` 才能注册 MCP 工具

**评分**: 7/10 | **标签**: VS Code, Copilot, MCP, Agent配置

**摘要**: Copilot Chat 的 Agent Mode 在 `.agent.md` 中有 `tools:` 字段定义工具白名单，默认列表可能不包含 `mcp`。即使 MCP Server 配置正确且端到端验证通过，Agent Mode 也不会暴露 MCP 工具除非白名单中显式包含 `mcp`。

### 💡 VS Code Copilot Agent Mode 的 MCP 工具可见性受 `.agent.md` 中的 `tools:` 白名单控制。如果白名单没有 `mcp`，即使 MCP Server 配置正确、端到端验证通过，Agent 会话的工具列表中也不会出现 MCP 工具。

- **适用场景**: VS Code Copilot Agent Mode 下使用 MCP 工具时。
- **行动建议**: 1. 检查 `.agent.md`/`.instructions.md` 中的 `tools:` 白名单。2. 添加 `mcp` 到该列表。3. 需要新建会话才能让配置生效（不会热加载）。
