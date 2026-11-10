> 脱敏节选 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 可复用模式 · 2026-06-04

> 生成时间: 2026-06-04 22:15 (增量补充)

---

## MCP Server 的三层验证模式

**评分**: 7/10 | **标签**: MCP, 调试, 验证模式, 工具链

**摘要**: 配置 MCP Server 后使用"脚本可执行 → JSON-RPC 探测 → VS Code 集成验证"三层递进验证，帮助分离服务端和客户端问题（不保留速度倍数断言）。

### 模式描述

```python
# 层1：脚本可执行性
subprocess.run(["python", "mcp_server.py"], capture_output=True, timeout=5)

# 层2：JSON-RPC 端到端验证
proc = subprocess.Popen(["python", "mcp_server.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
# tools/list
proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n")
# tools/call（测试 LLM 调用）
proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {...}}) + "\n")

# 层3：VS Code 可见性（层1/2通过后再做）
# 重启 VS Code，查看 tools 列表
```

### 何时使用

- 配置新的 MCP Server 后需要快速确认是否工作
- 排查 MCP 工具在 Copilot Chat 中不显示的问题
- 需要区分"Server 端配置错误"和"Client 端集成 bug"

---

