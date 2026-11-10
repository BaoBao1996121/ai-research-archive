> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# 学习实验代码 — 从零到生产级 Agent

从 ~50 行到 ~350 行，8 个迭代 × 2 个版本（基础 + 进阶），渐进式构建生产级 Agent。

## 学习路径

### 基础版：核心概念（iter0 ~ iter7）

每个文件一个核心概念，~50-300 行，最小可运行。

| 文件 | 核心概念 | 代码量 | Claude Code 对照 |
|------|---------|--------|-----------------|
| `iter0_enhanced_llm.py` | 单次 LLM 调用 | ~50行 | query.ts 单次调用 |
| `iter1_react_loop.py` | ReAct 主循环 | ~95行 | query.ts 主循环 |
| `iter2_tool_system.py` | 工具注册表 | ~170行 | tools/ 目录 |
| `iter3_context_engine.py` | 上下文 + 记忆 | ~220行 | context.ts + CLAUDE.md |
| `iter4_streaming.py` | 流式输出 | ~180行 | QueryEngine.ts |
| `iter5_safety.py` | 权限与安全 | ~200行 | permissions.ts |
| `iter6_compression.py` | 对话压缩 | ~220行 | services/compact/ |
| `iter7_multi_agent.py` | 多 Agent 协作 | ~300行 | AgentTool.ts |

### 进阶版：补全生产差距（iter0_adv ~ iter7_adv）

每个文件补全基础版与 Claude Code 之间的核心差距。

| 文件 | 补全内容 | 代码量 | 新增依赖 |
|------|---------|--------|---------|
| `iter0_adv_prompt_engine.py` | Prompt 模板引擎（Jinja2 + 积木组合） | ~120行 | jinja2 |
| `iter1_adv_async_agent.py` | async/await 并发 + 工具并行执行 | ~140行 | — |
| `iter2_adv_mcp_tools.py` | MCP 协议模式（外部工具服务器） | ~200行 | — |
| `iter3_adv_rag_context.py` | RAG 向量检索（TF-IDF + Embedding） | ~250行 | numpy(可选) |
| `iter4_adv_resilient.py` | retry + fallback + 熔断器 | ~200行 | — |
| `iter5_adv_hooks.py` | Hooks 可编程拦截 + 五层权限流水线 | ~250行 | — |
| `iter6_adv_tiered_compression.py` | 四级分层压缩（snip→micro→auto→reactive） | ~280行 | — |
| `iter7_adv_stateful_agent.py` | LangGraph 风格状态图 + 持久化检查点 | ~350行 | — |

## 基础版 → 进阶版差距一览

```
迭代   基础版做了什么           缺什么                进阶版补了什么
─────────────────────────────────────────────────────────────────
0     硬编码 System Prompt    无动态 prompt          Jinja2 模板引擎 + 积木组合
1     同步串行循环             无并发                 async/await + 工具并行
2     工具硬编码在进程内        无 MCP 外部工具        MCP 协议(JSON-RPC) + 多服务器
3     简单 KV 记忆             无向量检索             RAG 管线(TF-IDF + Embedding)
4     流式输出但无错误恢复      无 retry/fallback     指数退避 + 模型降级 + 熔断器
5     三级权限(SAFE/CONFIRM/   无 Hooks 可编程拦截    Hook 注册表 + 五层权限流水线
      DENY)
6     单级全量压缩             四级压缩差距大         snip → micro → auto → reactive
7     一次性 Orchestrator      无持久化状态           状态图 + 条件路由 + 检查点
```

## 运行前准备

1. 复制 `.env.example` 为 `.env`，填入 API Key
2. 基础依赖：`pip install openai python-dotenv`
3. 进阶依赖（按需）：`pip install jinja2 numpy`

## 推荐学习顺序

**第一遍**：按顺序跑完所有基础版（iter0 → iter7），建立核心概念。

**第二遍**：对照基础版，逐个学习进阶版，理解"从 demo 到生产"的差距：
- 先跑 `iter0_adv` 理解动态 prompt
- 再跑 `iter4_adv` 理解为什么需要弹性机制
- 最后跑 `iter7_adv` 理解状态图的威力

**合计**：~1,435 行基础 + ~1,790 行进阶 ≈ 3,225 行 Python，覆盖生产级 Agent 的核心能力。
