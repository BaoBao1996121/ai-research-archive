"""
Iter 7 进阶: 状态图 Agent — LangGraph 模式手搓实现（~350 行核心代码）
=====================================================================
基础版差距：Orchestrator 无持久化状态，任务执行是一次性的线性流程。
进阶补全：实现 LangGraph 风格的状态图——节点 + 条件边 + 持久化检查点。

Claude Code 对照：
  - AgentTool.ts 中子 Agent 有自己的状态（消息历史、工具结果）
  - 主循环本身就是一个隐式状态机：推理 → 工具调用 → 等待确认 → 继续
  - 但没有显式的状态图——这是 LangGraph 的主要贡献

LangGraph 核心抽象（本文件手搓实现，不依赖 LangGraph 库）：
  - State:      带类型的全局状态字典，在节点间共享
  - Node:       处理节点——接收 State，执行操作，返回更新
  - Edge:       边——决定下一步去哪个节点（可以是条件边）
  - StateGraph: 编排器——构建图 + 按边执行节点 + 管理状态
  - Checkpoint: 持久化检查点——保存/恢复执行进度

依赖：pip install openai
运行：python iter7_adv_stateful_agent.py
"""

import json
import time
import os
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from pathlib import Path
from config import client, MODEL

FAST_MODEL = "qwen-turbo"


# ╔══════════════════════════════════════════════════════════════╗
# ║  核心抽象 1: State（全局状态，在节点间共享）                    ║
# ╚══════════════════════════════════════════════════════════════╝

class State(dict):
    """
    Agent 的全局状态——本质就是一个字典，但增加了：
    1. 类型提示（方便 IDE 补全）
    2. 变更追踪（知道哪些字段被改了）
    3. 可序列化（用于持久化）

    LangGraph 的 State 还支持 Reducer（定义多个节点写同一字段时如何合并），
    这里简化为"后写入覆盖"。
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._changes: set = set()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._changes.add(key)

    def get_changes(self) -> dict:
        return {k: self[k] for k in self._changes if k in self}

    def clear_changes(self):
        self._changes.clear()


# ╔══════════════════════════════════════════════════════════════╗
# ║  核心抽象 2: Node（处理节点）                                  ║
# ╚══════════════════════════════════════════════════════════════╝

# Node 是一个函数：接收 State，返回要更新的字段字典
NodeFn = Callable[[State], dict]


# ╔══════════════════════════════════════════════════════════════╗
# ║  核心抽象 3: Edge（条件路由）                                  ║
# ╚══════════════════════════════════════════════════════════════╝

# 简单边：固定目标节点
# 条件边：根据 State 决定下一个节点
ConditionalEdgeFn = Callable[[State], str]  # 返回下一个节点名


# ╔══════════════════════════════════════════════════════════════╗
# ║  核心抽象 4: Checkpoint（持久化检查点）                        ║
# ╚══════════════════════════════════════════════════════════════╝

class CheckpointStore:
    """
    状态持久化——保存执行进度，支持中断后恢复。

    LangGraph 用这个实现"Human-in-the-loop"：
    执行到需要人类审批的节点 → 保存检查点 → 人类确认后 → 恢复执行。
    """
    def __init__(self, path: str = "checkpoints"):
        self.dir = Path(path)
        self.dir.mkdir(exist_ok=True)

    def save(self, graph_id: str, state: State, current_node: str):
        data = {"state": dict(state), "current_node": current_node,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        (self.dir / f"{graph_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  💾 检查点已保存: {graph_id} @ {current_node}")

    def load(self, graph_id: str) -> Optional[tuple[State, str]]:
        f = self.dir / f"{graph_id}.json"
        if not f.exists():
            return None
        data = json.loads(f.read_text(encoding="utf-8"))
        state = State(**data["state"])
        print(f"  💾 检查点已恢复: {graph_id} @ {data['current_node']}")
        return state, data["current_node"]

    def delete(self, graph_id: str):
        f = self.dir / f"{graph_id}.json"
        if f.exists():
            f.unlink()


# ╔══════════════════════════════════════════════════════════════╗
# ║  核心抽象 5: StateGraph（状态图编排器）                        ║
# ╚══════════════════════════════════════════════════════════════╝

END = "__end__"  # 特殊节点：表示流程结束


class StateGraph:
    """
    状态图编排器：定义节点和边，按图执行。

    用法：
        graph = StateGraph()
        graph.add_node("research", research_node)
        graph.add_node("analyze", analyze_node)
        graph.add_node("write", write_node)
        graph.add_edge("research", "analyze")  # 固定边
        graph.add_conditional_edge("analyze", route_fn)  # 条件边
        graph.set_entry("research")
        result = graph.run(initial_state)

    这就是 LangGraph 的核心 API（简化版）。
    """
    def __init__(self, checkpoint_store: CheckpointStore = None):
        self.nodes: dict[str, NodeFn] = {}
        self.edges: dict[str, str] = {}                    # node → next_node
        self.conditional_edges: dict[str, ConditionalEdgeFn] = {}  # node → route_fn
        self.entry: str = ""
        self.checkpoints = checkpoint_store

    def add_node(self, name: str, fn: NodeFn):
        self.nodes[name] = fn

    def add_edge(self, from_node: str, to_node: str):
        self.edges[from_node] = to_node

    def add_conditional_edge(self, from_node: str, route_fn: ConditionalEdgeFn):
        self.conditional_edges[from_node] = route_fn

    def set_entry(self, node_name: str):
        self.entry = node_name

    def run(self, state: State, graph_id: str = "default", max_steps: int = 20) -> State:
        """执行状态图"""
        # 检查是否有检查点可恢复
        current = self.entry
        if self.checkpoints:
            restored = self.checkpoints.load(graph_id)
            if restored:
                state, current = restored

        print(f"\n🔄 状态图开始: 入口={current}")

        for step in range(max_steps):
            if current == END:
                print(f"\n🏁 状态图完成（{step} 步）")
                if self.checkpoints:
                    self.checkpoints.delete(graph_id)
                return state

            if current not in self.nodes:
                raise ValueError(f"未知节点: {current}")

            # 执行节点
            print(f"\n  📍 Step {step+1}: [{current}]")
            node_fn = self.nodes[current]
            updates = node_fn(state)

            # 更新状态
            if updates:
                for k, v in updates.items():
                    state[k] = v

            # 保存检查点
            if self.checkpoints:
                self.checkpoints.save(graph_id, state, current)

            # 决定下一个节点
            if current in self.conditional_edges:
                current = self.conditional_edges[current](state)
                print(f"  → 条件路由到: [{current}]")
            elif current in self.edges:
                current = self.edges[current]
                print(f"  → 下一步: [{current}]")
            else:
                print(f"  → 无出边，结束")
                current = END

        print("  ⚠️ 达到最大步数限制")
        return state


# ╔══════════════════════════════════════════════════════════════╗
# ║  示例：多步研究 Agent（状态图实现）                            ║
# ╚══════════════════════════════════════════════════════════════╝

def llm_call(prompt: str, model: str = FAST_MODEL) -> str:
    """辅助函数：单次 LLM 调用"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content


# 节点 1: 任务规划
def plan_node(state: State) -> dict:
    """分析用户需求，制定研究计划"""
    task = state.get("task", "")
    plan = llm_call(f"你是一个研究助手。请为以下任务制定一个 3 步研究计划，"
                    f"每步用一句话描述。只返回计划，不要其他内容。\n\n任务: {task}")
    print(f"    计划: {plan[:100]}...")
    return {"plan": plan, "step": 0}


# 节点 2: 执行研究
def research_node(state: State) -> dict:
    """执行当前研究步骤"""
    step = state.get("step", 0)
    plan = state.get("plan", "")
    history = state.get("findings", [])

    context = f"研究计划:\n{plan}\n\n已完成的发现:\n" + "\n".join(history) if history else ""
    finding = llm_call(
        f"{context}\n\n请执行计划中的第 {step+1} 步研究。"
        f"给出 2-3 个关键发现，每个不超过一句话。",
    )
    print(f"    发现: {finding[:100]}...")
    return {"findings": history + [f"[步骤{step+1}] {finding}"], "step": step + 1}


# 节点 3: 质量评估
def evaluate_node(state: State) -> dict:
    """评估研究质量，决定是否需要补充研究"""
    findings = state.get("findings", [])
    findings_text = "\n".join(findings)
    evaluation = llm_call(
        f"评估以下研究发现的质量。回答 SUFFICIENT 或 INSUFFICIENT，"
        f"并用一句话说明理由。\n\n{findings_text}",
    )
    is_sufficient = "SUFFICIENT" in evaluation.upper() or state.get("step", 0) >= 3
    print(f"    评估: {'充分' if is_sufficient else '需补充'} — {evaluation[:80]}...")
    return {"evaluation": evaluation, "is_sufficient": is_sufficient}


# 节点 4: 撰写报告
def report_node(state: State) -> dict:
    """整合研究发现，撰写最终报告"""
    task = state.get("task", "")
    findings = "\n".join(state.get("findings", []))
    report = llm_call(
        f"基于以下研究发现，为原始任务撰写一份简要报告（200 字以内）。"
        f"\n\n任务: {task}\n\n发现:\n{findings}",
    )
    print(f"    报告: {report[:100]}...")
    return {"report": report}


# 条件路由：评估后决定去向
def evaluate_router(state: State) -> str:
    if state.get("is_sufficient", False):
        return "report"    # 研究充分 → 写报告
    return "research"      # 不充分 → 继续研究


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 7 进阶: 状态图 Agent — LangGraph 模式")
    print("=" * 60)

    # 创建检查点存储
    checkpoint_dir = os.path.join(os.path.dirname(__file__), "checkpoints")
    store = CheckpointStore(checkpoint_dir)

    # 构建状态图
    #
    #   [plan] → [research] → [evaluate] → (充分?) → [report] → END
    #                  ↑            |
    #                  └── (不充分) ←┘
    #
    graph = StateGraph(checkpoint_store=store)
    graph.add_node("plan", plan_node)
    graph.add_node("research", research_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("report", report_node)

    graph.add_edge("plan", "research")
    graph.add_edge("research", "evaluate")
    graph.add_conditional_edge("evaluate", evaluate_router)
    graph.add_edge("report", END)

    graph.set_entry("plan")

    # 运行
    print("\n📝 任务: 分析 AI Agent 的三种主要编排模式")
    initial_state = State(task="分析 AI Agent 的三种主要编排模式（Pipeline、DAG、State Machine），"
                              "比较它们的适用场景和优缺点")

    final_state = graph.run(initial_state, graph_id="research_task_1")

    print(f"\n{'='*60}")
    print("📄 最终报告:")
    print("=" * 60)
    print(final_state.get("report", "（无报告）"))
    print(f"\n📊 执行统计:")
    print(f"  研究步骤: {final_state.get('step', 0)}")
    print(f"  发现数量: {len(final_state.get('findings', []))}")

    # 展示状态图的优势
    print(f"\n{'='*60}")
    print("📚 状态图模式总结:")
    print("  State     — 全局状态字典，在节点间共享和传递")
    print("  Node      — 处理节点，接收 State 返回更新")
    print("  Edge      — 固定边 or 条件边（根据 State 路由）")
    print("  Checkpoint — 持久化检查点，支持中断/恢复")
    print()
    print("  vs 基础版 Orchestrator:")
    print("  ✅ 可持久化：任务中断后可恢复（检查点）")
    print("  ✅ 可循环：评估不过关 → 自动重做（条件边）")
    print("  ✅ 可观测：每一步的状态变化都可追踪")
    print("  ✅ 可组合：节点可复用，图可嵌套")
    print()
    print("  LangGraph 额外提供:")
    print("  - State Reducer（多节点写同一字段的合并策略）")
    print("  - Human-in-the-loop（在特定节点暂停等人类输入）")
    print("  - Streaming（逐步输出状态变化）")
    print("  - SubGraph（图嵌套图，用于复杂工作流）")
