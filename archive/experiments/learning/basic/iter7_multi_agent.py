"""
Iter 7: 多 Agent 协作 — 团队作战（~300 行核心代码）
===================================================
目标：一个 Agent 能力有上限。多个专业 Agent 协作解决复杂任务。
新增：Agent 类 + Orchestrator 编排器 + 子 Agent 专业化 + 结果聚合
学到：Orchestrator-Workers 模式、Agent 即工具、任务分解与聚合。

Claude Code 对照：
  - AgentTool.ts: "Agent as a Tool"——把子 Agent 包装成一个可调用的工具
  - 子 Agent 有自己的 system prompt、工具集、权限——与主 Agent 隔离
  - toolOrchestration.ts: 并发调度，独立工具并行、同文件工具串行

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter7_multi_agent.py
"""

import os
import json
from config import client, MODEL

FAST_MODEL = "qwen-turbo"  # Worker 用便宜模型降成本


# ━━━ 单个 Agent（可复用组件） ━━━
class Agent:
    """
    一个独立的 Agent 实例：自己的 system prompt + 工具集 + 模型。

    Claude Code 的 AgentTool 做了类似的事——子 Agent 是一个"工具"，
    由主 Agent 调用，拿到结果后继续推理。
    """
    def __init__(self, name: str, system_prompt: str,
                 tools: list[dict] = None, tool_map: dict = None,
                 model: str = FAST_MODEL):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_map = tool_map or {}
        self.model = model

    def run(self, task: str, max_turns: int = 5) -> str:
        """执行任务，返回最终文本回复"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]

        for turn in range(max_turns):
            kwargs = {"model": self.model, "messages": messages}
            if self.tools:
                kwargs["tools"] = self.tools

            response = client.chat.completions.create(**kwargs)
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return msg.content or ""

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                if fn_name in self.tool_map:
                    result = self.tool_map[fn_name](**fn_args)
                    r = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                else:
                    r = json.dumps({"error": f"未知工具: {fn_name}"})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": r})

        return "⚠️ Agent 达到最大轮次"


# ━━━ 工具定义 ━━━
CALC_TOOLS = [{"type": "function", "function": {
    "name": "calculator", "description": "计算数学表达式",
    "parameters": {"type": "object", "properties": {
        "expression": {"type": "string", "description": "数学表达式"}
    }, "required": ["expression"]}}}]

def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})


# ━━━ 创建专业 Agent ━━━
researcher = Agent(
    name="researcher",
    system_prompt="""你是一个技术调研专家。你的任务是分析技术问题并给出深度见解。
回答要求：1) 先给一句话结论 2) 列出 3-5 个关键要点 3) 给出推荐。
回答控制在 300 字以内。""",
    model=FAST_MODEL,
)

analyst = Agent(
    name="analyst",
    system_prompt="""你是一个数据分析师。你擅长数学计算和数据分析。
当需要精确计算时使用 calculator 工具。回答要简洁准确。""",
    tools=CALC_TOOLS,
    tool_map={"calculator": calculator},
    model=FAST_MODEL,
)

writer = Agent(
    name="writer",
    system_prompt="""你是一个技术写作专家。你的任务是将研究结果和数据分析整理为清晰的报告。
格式要求：使用 Markdown，包含标题、要点列表和结论。控制在 500 字以内。""",
    model=FAST_MODEL,
)


# ━━━ 编排器（Orchestrator） ━━━
class Orchestrator:
    """
    编排多个专业 Agent 完成复杂任务。

    模式：Orchestrator-Workers（Anthropic 五大模式之一）
    1. Orchestrator 分析任务 → 分解为子任务
    2. 分配给合适的 Worker Agent
    3. 收集结果 → 交给 Writer Agent 整合
    4. 返回最终报告
    """
    def __init__(self):
        self.agents = {}

    def register(self, agent: Agent):
        self.agents[agent.name] = agent

    def run(self, user_request: str) -> str:
        print(f"\n🎯 收到任务: {user_request[:100]}")

        # Step 1: 任务分解
        agent_list = ", ".join(f"'{name}'" for name in self.agents)
        plan_prompt = f"""你是一个任务分配者。可用的专家有: {agent_list}。

专家能力：
- researcher: 技术调研、分析趋势、给出建议
- analyst: 数学计算、数据分析、成本估算
- writer: 撰写报告、整理信息、格式化输出

请将以下用户需求分解为 2-4 个子任务，每个指定一个专家。
返回 JSON 数组格式: [{{"agent": "名称", "task": "具体任务描述"}}]
只返回 JSON，不要其他文字。

用户需求: {user_request}"""

        print("  📋 Step 1: 分解任务...")
        plan_response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": plan_prompt}],
            temperature=0.3,
        )
        plan_text = plan_response.choices[0].message.content

        # 解析计划
        try:
            # 提取 JSON（处理可能的 markdown 包装）
            json_text = plan_text
            if "```" in json_text:
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]
            subtasks = json.loads(json_text.strip())
        except (json.JSONDecodeError, IndexError):
            print(f"  ⚠️ 计划解析失败，使用默认分配")
            subtasks = [
                {"agent": "researcher", "task": user_request},
                {"agent": "writer", "task": f"基于以下信息撰写报告：{user_request}"},
            ]

        print(f"  📋 计划: {len(subtasks)} 个子任务")
        for i, st in enumerate(subtasks):
            print(f"     {i+1}. [{st['agent']}] {st['task'][:60]}...")

        # Step 2: 分发执行
        results = []
        for i, subtask in enumerate(subtasks):
            agent_name = subtask["agent"]
            task_desc = subtask["task"]

            if agent_name not in self.agents:
                print(f"  ⚠️ 未知 Agent: {agent_name}，跳过")
                continue

            print(f"\n  🤖 Step 2.{i+1}: [{agent_name}] 执行中...")
            # 给后续 agent 加上前面的结果作为上下文
            full_task = task_desc
            if results:
                context = "\n".join(f"[{r['agent']}的结果]: {r['result'][:300]}" for r in results)
                full_task = f"参考前面专家的结果:\n{context}\n\n你的任务: {task_desc}"

            result = self.agents[agent_name].run(full_task)
            results.append({"agent": agent_name, "task": task_desc, "result": result})
            print(f"  ✅ [{agent_name}] 完成 ({len(result)} 字)")

        # Step 3: 如果最后一个不是 writer，追加一个整合步骤
        if results and results[-1]["agent"] != "writer" and "writer" in self.agents:
            print(f"\n  📝 Step 3: [writer] 整合报告...")
            all_results = "\n\n".join(
                f"## {r['agent']} 的分析\n{r['result']}" for r in results
            )
            final = self.agents["writer"].run(
                f"请将以下多位专家的分析整合为一份完整报告：\n\n{all_results}"
            )
            return final

        # 返回最后一个结果
        return results[-1]["result"] if results else "没有可用的专家"


# ━━━ 组装 ━━━
orchestrator = Orchestrator()
orchestrator.register(researcher)
orchestrator.register(analyst)
orchestrator.register(writer)


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 7: 多 Agent 协作 — Orchestrator-Workers 模式")
    print(f"已注册 Agent: {list(orchestrator.agents.keys())}")
    print("=" * 60)

    # 测试 1: 需要多专家协作的复杂任务
    print("\n📝 测试 1: 技术调研 + 成本分析 + 报告撰写")
    result = orchestrator.run(
        "我想用 Qwen API 搭建一个企业级 AI 客服系统。"
        "请分析技术可行性、估算月度成本（假设日均 1 万次调用，每次约 500 token），"
        "并给出一份简要的可行性报告。"
    )
    print(f"\n{'='*60}")
    print("📄 最终报告:")
    print("=" * 60)
    print(result)

    # 测试 2: 简单任务（应该只派一个 agent）
    print(f"\n{'='*60}")
    print("📝 测试 2: 简单计算任务")
    result = orchestrator.run("帮我算一下，如果每月固定成本 2000 元，每次调用 0.002 元，日均 5000 次，总月度成本是多少？")
    print(f"\n📄 结果:\n{result}")
