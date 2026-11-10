> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# LangChain & LangGraph 渐进式学习脚本

基于 `reports/LangChain与LangGraph从入门到实战完全指南.md` 提取的独立可运行脚本。

## 环境要求

- Python 3.13
- 项目根目录 `.env` 中配置了 `DASHSCOPE_API_KEY`
- LLM：通义千问（Qwen）via DashScope OpenAI 兼容接口

## 脚本列表（按学习顺序）

| # | 文件 | 对应章节 | 学什么 |
|---|------|---------|--------|
| 01 | `01_chat_model.py` | 第三章 3.2-3.3 | ChatModel 统一接口 + Messages 消息格式 |
| 02 | `02_tools_basics.py` | 第三章 3.4-3.5 | 定义 Tool + bind_tools 让 LLM 决策 |
| 03 | `03_hello_agent.py` | 第四章 | 用 create_react_agent 快速创建 Agent |
| 04 | `04_langgraph_agent.py` | 第六章 | 手搓 LangGraph ReAct Agent（核心！） |
| 05 | `05_memory_agent.py` | 第七章 7.2 | Checkpoint 持久化记忆 |
| 06 | `06_hitl_agent.py` | 第七章 7.3 | Human-in-the-Loop 人工审批 |
| 07 | `07_streaming_agent.py` | 第七章 7.4 | 流式输出（逐字/逐步） |
| 08 | `08_research_assistant.py` | 第八章 | 完整实战项目：研究助手 |

## 运行方式

```bash
cd F:\AI2025\Agent研究
.\.venv\Scripts\python.exe experiments\learning\langchain_langgraph\01_chat_model.py
```

## 关键差异：文档 vs 脚本

文档中使用 `anthropic:claude-sonnet-4-6`，本脚本全部改为 Qwen（DashScope）：
- 使用 `ChatOpenAI` + DashScope 兼容接口
- 模型：`qwen-plus`（平衡效果和成本）
- API Key 从 `.env` 自动加载
