> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# 01 · LangGraph + Redis Checkpoint — Agent 状态持久化

> **状态**：⚡ 骨架 + README（依赖 `langgraph-checkpoint-redis ≥ 0.4.1` 和 Redis ≥ 8.0，API 仍在快速迭代，跑通需自行核对版本）

## Why 这一章

Agent 跑到一半挂了怎么办？传统应用重启 = 重头来。Agent 应用因为 **每步都消耗 Token（钱）**，重头来不可接受。Checkpoint = 每步存档，崩溃后从最近存档恢复。

LangGraph 是目前最流行的 Agent 编排框架（[现代智能体编排框架深度调研报告](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) 中详细对比），它原生支持多种 Checkpoint backend：
- InMemory（demo 用）
- SQLite（单机）
- Postgres（生产）
- **Redis**（本章主角，性能最好但内存成本高）

## 跑法

```powershell
# 1. 装依赖（独立装，避免污染主环境）
pip install langgraph langgraph-checkpoint-redis

# 2. 跑
python 01_checkpoint/main.py
```

## 核心代码骨架

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
from typing import TypedDict
import os

class State(TypedDict):
    counter: int
    messages: list

def increment(state: State) -> State:
    return {"counter": state["counter"] + 1, "messages": state["messages"] + [f"step {state['counter']+1}"]}

# 关键：用 RedisSaver 替代 InMemorySaver
checkpointer = RedisSaver.from_conn_string(os.getenv("REDIS_URL"))

graph = StateGraph(State)
graph.add_node("inc", increment)
graph.set_entry_point("inc")
graph.add_conditional_edges(
    "inc",
    lambda s: END if s["counter"] >= 5 else "inc",
)
app = graph.compile(checkpointer=checkpointer)

# 第一次跑：thread_id="user-001"
config = {"configurable": {"thread_id": "user-001"}}
result = app.invoke({"counter": 0, "messages": []}, config)
print(result)  # counter=5

# 模拟崩溃：另起进程，同样 thread_id 继续
# 状态会自动从 Redis 恢复，不会从 0 重新开始
```

## 验证 Checkpoint 真的存到 Redis 了

```bash
redis-cli
> KEYS *checkpoint*
1) "checkpoint:user-001:..."
> TYPE checkpoint:user-001:...
"hash"
> HGETALL checkpoint:user-001:...
```

## 关键概念

| 概念 | 说明 |
|------|------|
| `thread_id` | 一个对话/会话的唯一 ID，所有 checkpoint 按它分组 |
| `checkpoint_id` | 单步 checkpoint 的 ID，按时间戳生成 |
| `RedisSaver` | LangGraph 提供的 Redis backend |
| Time Travel | 可指定 `checkpoint_id` 回到任意历史步骤继续跑 |

## 与其他 Backend 对比

| Backend | 写延迟 | 适用规模 | 何时选 |
|---------|-------|---------|-------|
| InMemory | < 0.1ms | 单进程 demo | 写测试用 |
| SQLite | 1-5ms | 单机 | 单用户桌面 Agent |
| Postgres | 5-20ms | 团队级 | 关心强一致性、要 SQL 查询历史 |
| **Redis** | **< 1ms** | **生产级** | **追求最低延迟，能接受全内存成本** |

## 已知坑

| 坑 | 解法 |
|----|------|
| `langgraph-checkpoint-redis` 要 Redis ≥ 8.0 | 用本 Lab 的 docker-compose（已是 8.x） |
| Checkpoint 数据爆炸（每步都存全 state） | 用 LangGraph 的 message reducer 避免重复存历史 |
| `thread_id` 跨用户串了 | 加用户前缀：`thread_id = f"u{user_id}-{session_id}"` |

## TODO

- [ ] 完整实现一个"网页摘要 Agent"，跑到一半 Ctrl+C，重启从断点继续
- [ ] 加入 Time Travel 演示（恢复到第 3 步重跑）
- [ ] 测量 Redis vs Postgres 在 1000 个并发 thread 下的延迟差异

## 关联

- 主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §2.1
- [现代智能体编排框架深度调研报告](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) 中 LangGraph 章节
- LangGraph 官方文档：https://langchain-ai.github.io/langgraph/concepts/persistence/
