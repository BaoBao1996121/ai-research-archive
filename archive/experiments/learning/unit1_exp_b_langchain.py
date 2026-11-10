"""
实验 B: LangChain ChatOpenAI + Tool Calling
参考: uDocWriter/src/llms/llm.py

学习目标:
  1. 理解 LangChain ChatOpenAI 的初始化和调用方式
  2. 掌握 Tool Calling 的完整流程：定义工具 → 绑定 → 调用 → 执行 → 回传
  3. 对比 httpx 直调，感受框架带来的抽象层

运行方式:
  1. pip install langchain-openai langchain-core python-dotenv
  2. python unit1_exp_b_langchain.py

依赖: langchain-openai, langchain-core, python-dotenv
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv(Path(__file__).parent / ".env")


# === Step 1: 定义工具 ===
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。城市名用中文。"""
    # 模拟天气数据
    weather_data = {
        "上海": "晴，25°C，东南风 3 级",
        "北京": "多云，22°C，北风 2 级",
        "深圳": "阵雨，28°C，南风 4 级",
    }
    return weather_data.get(city, f"{city}：暂无数据")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式。输入标准数学表达式字符串。"""
    try:
        # 安全评估：仅允许数学运算
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：仅支持数学运算符"
        result = eval(expression)  # noqa: S307 — 学习演示用，生产环境应使用 ast.literal_eval 或 numexpr
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def demo_basic_chat():
    """演示 1: 基本对话（无工具）"""
    print("=== 演示 1: 基本对话 ===")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    result = llm.invoke([HumanMessage(content="用一句话解释 LangChain")])
    print(f"回答: {result.content}")
    print(f"Token 用量: {result.usage_metadata}")
    print()


def demo_tool_calling():
    """演示 2: Tool Calling 完整流程"""
    print("=== 演示 2: Tool Calling ===")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    # 绑定工具
    tools = [get_weather, calculate]
    llm_with_tools = llm.bind_tools(tools)

    # 第一轮：LLM 决定调用哪个工具
    print("用户: 上海今天天气怎么样？")
    ai_msg = llm_with_tools.invoke([
        HumanMessage(content="上海今天天气怎么样？")
    ])

    print(f"LLM 响应内容: {ai_msg.content or '(空，因为要调用工具)'}")
    print(f"Tool Calls: {ai_msg.tool_calls}")

    if ai_msg.tool_calls:
        # 第二轮：执行工具，把结果回传给 LLM
        tool_call = ai_msg.tool_calls[0]
        print(f"\n执行工具: {tool_call['name']}({tool_call['args']})")

        # 根据工具名找到对应函数并执行
        tool_map = {"get_weather": get_weather, "calculate": calculate}
        tool_result = tool_map[tool_call["name"]].invoke(tool_call["args"])
        print(f"工具返回: {tool_result}")

        # 把工具结果回传
        final = llm_with_tools.invoke([
            HumanMessage(content="上海今天天气怎么样？"),
            ai_msg,
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"]),
        ])
        print(f"\nLLM 最终回答: {final.content}")

    print()


def demo_multi_tool():
    """演示 3: 多工具场景"""
    print("=== 演示 3: 复合问题 ===")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    llm_with_tools = llm.bind_tools([get_weather, calculate])

    result = llm_with_tools.invoke([
        HumanMessage(content="帮我算一下 123 * 456 等于多少")
    ])

    print(f"Tool Calls: {result.tool_calls}")
    if result.tool_calls:
        for tc in result.tool_calls:
            print(f"  → {tc['name']}({tc['args']})")
    print()


def main():
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "YOUR_KEY_HERE":
        print("❌ 请先在 .env 中填入 OPENAI_API_KEY")
        return

    print("=" * 50)
    print("实验 B: LangChain ChatOpenAI + Tool Calling")
    print("=" * 50)
    print()

    demo_basic_chat()
    demo_tool_calling()
    demo_multi_tool()

    print("=" * 50)
    print("✅ 实验完成！")
    print()
    print("思考题：")
    print("1. bind_tools 做了什么？LLM 是怎么知道有哪些工具的？")
    print("2. Tool Calling 的完整消息流：User → AI(tool_calls) → Tool → AI(content)")
    print("3. 和 httpx 直调相比，LangChain 多了哪些抽象？值得吗？")
    print("4. 如果工具执行出错，应该怎么处理？")


if __name__ == "__main__":
    main()
