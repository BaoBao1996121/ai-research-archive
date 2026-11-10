"""
Iter 2 进阶: MCP 外部工具 — 让 Agent 调用外部服务（~200 行核心代码）
====================================================================
基础版差距：工具硬编码在 Agent 进程内，无法动态接入外部工具。
进阶补全：实现 MCP (Model Context Protocol) 模式——工具在外部进程/服务中，
         Agent 通过协议动态发现和调用。

Claude Code 对照：
  - Claude Code 通过 MCP 协议接入外部工具服务器
  - MCP 本质是 JSON-RPC 2.0（tools/list + tools/call）
  - 好处：Agent 和工具解耦，新增工具不改 Agent 代码

本文件实现：
  1. MCPServer — 外部工具服务器（可独立进程运行）
  2. MCPClient — Agent 侧的客户端（发现 + 调用）
  3. Agent 使用 MCPClient 动态接入外部工具

依赖：pip install openai
运行：python iter2_adv_mcp_tools.py
"""

import json
import subprocess
import sys
import os
from config import client, MODEL


# ╔══════════════════════════════════════════════════════════════╗
# ║  MCP 协议核心：JSON-RPC 2.0 消息格式                         ║
# ╚══════════════════════════════════════════════════════════════╝

def jsonrpc_request(method: str, params: dict = None, id: int = 1) -> dict:
    """构造一个 JSON-RPC 2.0 请求"""
    msg = {"jsonrpc": "2.0", "method": method, "id": id}
    if params:
        msg["params"] = params
    return msg


def jsonrpc_response(result, id: int = 1) -> dict:
    """构造一个 JSON-RPC 2.0 响应"""
    return {"jsonrpc": "2.0", "result": result, "id": id}


def jsonrpc_error(code: int, message: str, id: int = 1) -> dict:
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": id}


# ╔══════════════════════════════════════════════════════════════╗
# ║  MCP Server：外部工具服务器                                   ║
# ╚══════════════════════════════════════════════════════════════╝

class MCPServer:
    """
    一个简化版 MCP 服务器——工具的"供应商"。

    真正的 MCP 服务器通过 stdio（标准输入/输出）或 SSE 与客户端通信。
    这里为了教学，我们用内存调用模拟协议交互，但消息格式完全遵循 MCP/JSON-RPC。

    关键概念：
    - tools/list：客户端发现服务器提供了哪些工具
    - tools/call：客户端调用某个工具
    - 服务器是独立的——可以是另一个进程、另一台机器上的服务
    """
    def __init__(self, name: str):
        self.name = name
        self._tools: dict[str, dict] = {}  # name → {schema, handler}

    def register_tool(self, name: str, description: str, parameters: dict, handler):
        self._tools[name] = {
            "schema": {"name": name, "description": description,
                       "inputSchema": parameters},
            "handler": handler,
        }

    def handle_request(self, request: dict) -> dict:
        """处理一个 JSON-RPC 请求，返回 JSON-RPC 响应"""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", 1)

        if method == "initialize":
            return jsonrpc_response({
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": self.name, "version": "1.0"},
                "capabilities": {"tools": {}},
            }, req_id)

        elif method == "tools/list":
            tools = [t["schema"] for t in self._tools.values()]
            return jsonrpc_response({"tools": tools}, req_id)

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            if tool_name not in self._tools:
                return jsonrpc_error(-32601, f"工具不存在: {tool_name}", req_id)
            try:
                result = self._tools[tool_name]["handler"](**arguments)
                return jsonrpc_response({"content": [{"type": "text", "text": result}]}, req_id)
            except Exception as e:
                return jsonrpc_error(-32000, str(e), req_id)

        return jsonrpc_error(-32601, f"未知方法: {method}", req_id)


# ╔══════════════════════════════════════════════════════════════╗
# ║  MCP Client：Agent 侧的工具消费者                             ║
# ╚══════════════════════════════════════════════════════════════╝

class MCPClient:
    """
    MCP 客户端——Agent 通过它发现和调用外部工具。

    在真正的 MCP 中，客户端通过 stdio/SSE 发送 JSON-RPC 消息到服务器进程。
    这里为了教学，直接内存调用服务器，但保持协议格式一致。
    """
    def __init__(self, server: MCPServer):
        self.server = server
        self._initialized = False

    def initialize(self) -> dict:
        """MCP 握手"""
        resp = self.server.handle_request(jsonrpc_request("initialize"))
        self._initialized = True
        return resp["result"]

    def list_tools(self) -> list[dict]:
        """发现服务器提供的工具"""
        resp = self.server.handle_request(jsonrpc_request("tools/list"))
        return resp["result"]["tools"]

    def call_tool(self, name: str, arguments: dict) -> str:
        """调用一个工具"""
        resp = self.server.handle_request(
            jsonrpc_request("tools/call", {"name": name, "arguments": arguments})
        )
        if "error" in resp:
            return json.dumps({"error": resp["error"]["message"]}, ensure_ascii=False)
        return resp["result"]["content"][0]["text"]

    def get_openai_tools(self) -> list[dict]:
        """将 MCP 工具 Schema 转换为 OpenAI Function Calling 格式"""
        mcp_tools = self.list_tools()
        return [
            {"type": "function", "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"],
            }}
            for t in mcp_tools
        ]


# ╔══════════════════════════════════════════════════════════════╗
# ║  创建外部工具服务器（模拟独立进程中的工具）                    ║
# ╚══════════════════════════════════════════════════════════════╝

def create_weather_server() -> MCPServer:
    """天气查询服务器"""
    server = MCPServer("weather-server")

    def get_weather(city: str) -> str:
        # 模拟天气 API
        data = {"北京": "晴 25°C", "上海": "多云 22°C", "深圳": "小雨 28°C"}
        weather = data.get(city, f"{city}: 暂无数据")
        return json.dumps({"city": city, "weather": weather}, ensure_ascii=False)

    server.register_tool(
        "get_weather", "查询城市天气",
        {"type": "object", "properties": {
            "city": {"type": "string", "description": "城市名"}
        }, "required": ["city"]},
        get_weather,
    )
    return server


def create_math_server() -> MCPServer:
    """数学计算服务器"""
    server = MCPServer("math-server")

    def calculate(expression: str) -> str:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return json.dumps({"error": "不允许的字符"})
        return json.dumps({"result": eval(expression)})

    def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
        conversions = {
            ("km", "mile"): 0.621371, ("mile", "km"): 1.60934,
            ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
            ("celsius", "fahrenheit"): lambda v: v * 9/5 + 32,
            ("fahrenheit", "celsius"): lambda v: (v - 32) * 5/9,
        }
        key = (from_unit.lower(), to_unit.lower())
        if key not in conversions:
            return json.dumps({"error": f"不支持 {from_unit} → {to_unit}"}, ensure_ascii=False)
        factor = conversions[key]
        result = factor(value) if callable(factor) else value * factor
        return json.dumps({"result": round(result, 4), "unit": to_unit}, ensure_ascii=False)

    server.register_tool(
        "calculate", "计算数学表达式",
        {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]},
        calculate,
    )
    server.register_tool(
        "unit_convert", "单位换算",
        {"type": "object", "properties": {
            "value": {"type": "number", "description": "数值"},
            "from_unit": {"type": "string", "description": "原单位"},
            "to_unit": {"type": "string", "description": "目标单位"},
        }, "required": ["value", "from_unit", "to_unit"]},
        unit_convert,
    )
    return server


# ╔══════════════════════════════════════════════════════════════╗
# ║  Agent 循环（通过 MCP 动态发现和使用外部工具）                 ║
# ╚══════════════════════════════════════════════════════════════╝

class MCPAgent:
    """
    使用 MCP 协议连接外部工具服务器的 Agent。

    与基础版的区别：
    - 工具不再硬编码在 Agent 里
    - 通过 MCPClient 动态发现外部服务器的工具
    - 新增工具只需改服务器，不动 Agent 代码
    - 支持同时连接多个服务器（每个服务器提供不同领域的工具）
    """
    def __init__(self):
        self.clients: list[MCPClient] = []
        self._all_tools_schema: list[dict] = []
        self._tool_client_map: dict[str, MCPClient] = {}

    def connect(self, server: MCPServer):
        """连接一个 MCP 服务器"""
        c = MCPClient(server)
        info = c.initialize()
        print(f"  🔌 已连接: {info['serverInfo']['name']} v{info['serverInfo']['version']}")

        # 发现工具
        tools = c.get_openai_tools()
        for t in tools:
            name = t["function"]["name"]
            self._all_tools_schema.append(t)
            self._tool_client_map[name] = c
            print(f"     ├ 工具: {name} — {t['function']['description']}")

        self.clients.append(c)

    def run(self, user_message: str, max_turns: int = 10) -> str:
        """Agent 主循环"""
        messages = [
            {"role": "system", "content": f"你是一个AI助手。可用工具: {', '.join(self._tool_client_map.keys())}"},
            {"role": "user", "content": user_message},
        ]
        for turn in range(max_turns):
            print(f"  ⚡ 第 {turn+1} 轮...")
            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=self._all_tools_schema,
            )
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return msg.content or ""

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                print(f"  🔧 [{fn_name}] → MCP Server")

                # 通过 MCP 协议调用外部工具
                if fn_name in self._tool_client_map:
                    result = self._tool_client_map[fn_name].call_tool(fn_name, fn_args)
                else:
                    result = json.dumps({"error": f"未知工具: {fn_name}"})

                print(f"  📋 ← {result[:80]}")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return "⚠️ 达到最大轮次"


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 2 进阶: MCP 外部工具")
    print("=" * 60)

    # 创建外部工具服务器
    print("\n📦 启动 MCP 服务器...")
    weather_server = create_weather_server()
    math_server = create_math_server()

    # Agent 连接多个服务器
    print("\n🤖 Agent 连接外部工具...")
    agent = MCPAgent()
    agent.connect(weather_server)  # 天气工具
    agent.connect(math_server)     # 数学工具

    print(f"\n  总计 {len(agent._tool_client_map)} 个外部工具可用")

    # 测试：跨服务器工具协作
    print(f"\n{'='*60}")
    print("📝 测试: 使用多个外部服务器的工具")
    result = agent.run(
        "帮我查一下北京和上海的天气，然后算一下 25 摄氏度等于多少华氏度"
    )
    print(f"\n🤖 回答:\n{result}")

    # ━━━ 总结 ━━━
    print(f"\n{'='*60}")
    print("📚 MCP 模式核心价值:")
    print("  1. 解耦：Agent 和工具分离，独立开发/部署")
    print("  2. 动态发现：Agent 运行时自动发现可用工具")
    print("  3. 可扩展：新增工具只改服务器，不动 Agent")
    print("  4. 标准化：所有工具遵循同一协议（JSON-RPC 2.0）")
    print()
    print("  真正的 MCP 使用 stdio/SSE 传输，工具服务器是独立进程。")
    print("  安装 mcp SDK: pip install mcp")
    print("  官方文档: https://modelcontextprotocol.io/")
