> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 异步监控回调模式实验

> 验证"启动异步任务 → Agent 继续工作 → 任务完成自动通知"模式在三种实现方式下的可行性

## 实验列表

| 文件 | 方式 | 依赖 |
|------|------|------|
| `01_handcrafted.py` | 手搓 Agent（纯 Python asyncio） | 无框架依赖 |
| `02_langgraph.py` | LangGraph interrupt + checkpoint | `langgraph`, `langchain-openai` |
| `03_claude_sdk.py` | Claude Agent SDK hooks | `anthropic` |

## 运行方式

```bash
# 手搓版（无需 API key）
python 01_handcrafted.py

# LangGraph 版
export OPENAI_API_KEY=sk-xxx  # 或其他 LLM provider
python 02_langgraph.py

# Claude SDK 版
export ANTHROPIC_API_KEY=sk-ant-xxx
python 03_claude_sdk.py
```
