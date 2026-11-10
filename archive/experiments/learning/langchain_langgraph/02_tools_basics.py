"""
LangChain & LangGraph 学习脚本 02 —— Tools + bind_tools

对应文档：第三章 3.4~3.5
学习目标：
  1. 用 @tool 装饰器定义工具
  2. 理解 Tool 的 docstring 就是给 LLM 看的"使用说明书"
  3. 用 bind_tools 让 LLM 自主决策"要不要调工具"
  4. 理解 LLM 只负责"决策"，不负责"执行"

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\02_tools_basics.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).resolve().parent
while _root != _root.parent:
    if (_root / ".env").exists():
        break
    _root = _root.parent
load_dotenv(_root / ".env")

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

model = ChatOpenAI(
    model=os.getenv("MODEL", "qwen-plus"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 用 @tool 定义工具
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 类比 C#：@tool 就像给方法加了一个 [Description("...")] Attribute
# LLM 通过读这个描述来决定什么时候调用它

@tool
def search_weather(city: str) -> str:
    """查询指定城市的天气。当用户问某个城市的天气时使用。

    Args:
        city: 城市名称，如"北京"、"上海"
    """
    weather_data = {
        "北京": "晴，25°C，湿度 40%",
        "上海": "多云，22°C，湿度 65%",
        "深圳": "阵雨，28°C，湿度 80%",
    }
    return weather_data.get(city, f"未找到 {city} 的天气数据")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式的结果。当用户需要做数学运算时使用。

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
    """
    try:
        # 安全限制：只允许数字和基本运算符
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return f"不支持的表达式: {expression}"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


print("=" * 60)
print("📚 示例 1：查看 Tool 的元信息")
print("=" * 60)

# LLM 通过这些信息决定何时调用工具
print(f"工具名: {search_weather.name}")
print(f"描述:   {search_weather.description}")
print(f"参数:   {search_weather.args}")
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. bind_tools —— 告诉 LLM "你可以使用这些工具"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("📚 示例 2：bind_tools —— LLM 的工具决策")
print("=" * 60)

# bind_tools 把工具的 schema（名字+描述+参数）注入到 LLM 的请求中
# 类比 C++：就像给函数指针表加了几个新条目
model_with_tools = model.bind_tools([search_weather, calculate])

# 测试 1：需要查天气的问题
print("--- 测试 1：需要工具 ---")
response = model_with_tools.invoke("北京今天天气怎么样？")
print(f"回复内容: {response.content or '(无文本，LLM 决定调工具)'}")
print(f"工具调用: {response.tool_calls}")
print()

# 关键理解：
# - response.content 可能为空（LLM 决定调工具而不是直接回答）
# - response.tool_calls 包含 LLM "想要"调用的工具信息
# - 但是！LLM 并没有真正执行工具——它只是说"我要调这个"

# 测试 2：不需要工具的问题
print("--- 测试 2：不需要工具 ---")
response = model_with_tools.invoke("解释一下什么是递归")
print(f"回复内容: {response.content[:100]}...")
print(f"工具调用: {response.tool_calls}")
print()

# 测试 3：需要计算的问题
print("--- 测试 3：数学计算 ---")
response = model_with_tools.invoke("帮我算 15 * 37 + 28")
print(f"回复内容: {response.content or '(无文本，LLM 决定调工具)'}")
print(f"工具调用: {response.tool_calls}")
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 手动执行工具 —— 完成 "决策→执行" 的闭环
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("📚 示例 3：手动执行 LLM 决策的工具调用")
print("=" * 60)

# 建立工具名 → 工具函数的映射
tools_map = {
    "search_weather": search_weather,
    "calculate": calculate,
}

# 让 LLM 决策
response = model_with_tools.invoke("北京天气怎么样？另外帮我算 100 / 7")

print("LLM 的决策:")
for tc in response.tool_calls:
    print(f"  → 调用 {tc['name']}({tc['args']})")

print("\n手动执行工具:")
for tc in response.tool_calls:
    tool_fn = tools_map[tc["name"]]
    result = tool_fn.invoke(tc["args"])
    print(f"  → {tc['name']}({tc['args']}) = {result}")

print("""
┌─────────────────────────────────────────────────────────┐
│ 💡 关键洞察                                             │
│                                                         │
│ LLM 的角色是"决策者"，不是"执行者"：                     │
│   1. LLM 看到问题 + 可用工具列表                        │
│   2. LLM 决定："这个问题需要调 search_weather"           │
│   3. LLM 返回 tool_calls（但不执行！）                   │
│   4. 你的代码负责真正执行工具                            │
│   5. 把执行结果塞回消息列表，再次调用 LLM                │
│   6. LLM 综合工具结果，给出最终回答                      │
│                                                         │
│ 这个 "思考→行动→观察→再思考" 循环就是 ReAct 模式        │
│ 下一个脚本我们用 create_react_agent 自动化这个循环       │
└─────────────────────────────────────────────────────────┘
""")

print("✅ 脚本 02 完成！下一步：03_hello_agent.py")
