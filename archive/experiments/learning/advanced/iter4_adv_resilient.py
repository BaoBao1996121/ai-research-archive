"""
Iter 4 进阶: 弹性 Agent — retry + fallback + 熔断（~200 行核心代码）
====================================================================
基础版差距：API 调用失败就直接报错，没有错误恢复机制。
进阶补全：指数退避重试 + 模型降级链 + 熔断器 + 超时控制。

Claude Code 对照：
  - QueryEngine.ts: 内置重试逻辑，区分可重试错误 vs 不可重试错误
  - 429 (Rate Limit) / 529 (Overloaded) → 自动重试
  - 400 (Bad Request) → 不重试，直接报错
  - 模型降级：主模型不可用时自动切换到备选模型

依赖：pip install openai
运行：python iter4_adv_resilient.py
"""

import json
import time
import random
from functools import wraps
from config import client, MODEL

FAST_MODEL = "qwen-turbo"  # 降级用的便宜模型


# ╔══════════════════════════════════════════════════════════════╗
# ║  组件 1: 指数退避重试装饰器                                   ║
# ╚══════════════════════════════════════════════════════════════╝

# 可重试的错误类型（参考 Claude Code 的分类）
RETRYABLE_STATUS = {429, 500, 502, 503, 529}  # Rate limit / Server error / Overloaded
NON_RETRYABLE_STATUS = {400, 401, 403, 404}   # Bad request / Auth / Not found


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0,
                       max_delay: float = 30.0, jitter: bool = True):
    """
    指数退避重试装饰器。

    策略：每次重试等待时间翻倍（1s → 2s → 4s → ...），加随机抖动避免惊群效应。

    为什么需要抖动（jitter）？
    如果 100 个客户端同时遇到 429，都在 1s 后重试 → 又全部 429。
    加随机抖动让重试时间错开，减少并发冲突。
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e)

                    # 判断是否可重试
                    is_retryable = any(str(code) in error_str for code in RETRYABLE_STATUS)
                    if not is_retryable:
                        print(f"  ❌ 不可重试的错误: {error_str[:100]}")
                        raise

                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        if jitter:
                            delay *= (0.5 + random.random())  # 0.5x ~ 1.5x 随机抖动
                        print(f"  🔄 重试 {attempt+1}/{max_retries}（等待 {delay:.1f}s）: {error_str[:60]}")
                        time.sleep(delay)
                    else:
                        print(f"  💀 重试耗尽 ({max_retries} 次): {error_str[:60]}")
            raise last_error
        return wrapper
    return decorator


# ╔══════════════════════════════════════════════════════════════╗
# ║  组件 2: 模型降级链（Fallback Chain）                         ║
# ╚══════════════════════════════════════════════════════════════╝

class ModelFallbackChain:
    """
    模型降级链：主模型失败时自动切换到备选。

    典型链路：GPT-4 → GPT-3.5 → 本地模型
    或：qwen-plus → qwen-turbo → 静态回复

    Claude Code 没有直接的降级链（因为它只用 Claude），
    但这是生产 Agent 系统的标配——不能因为一个模型出问题就整个系统宕机。
    """
    def __init__(self, models: list[str]):
        self.models = models
        self.failures: dict[str, int] = {m: 0 for m in models}

    def call(self, messages: list[dict], tools: list[dict] = None) -> tuple:
        """尝试每个模型，直到成功"""
        last_error = None
        for model in self.models:
            try:
                kwargs = {"model": model, "messages": messages}
                if tools:
                    kwargs["tools"] = tools
                print(f"  🎯 尝试模型: {model}")
                response = client.chat.completions.create(**kwargs)
                self.failures[model] = 0  # 成功，重置失败计数
                return model, response
            except Exception as e:
                self.failures[model] += 1
                last_error = e
                print(f"  ⚠️ {model} 失败 (累计 {self.failures[model]} 次): {str(e)[:60]}")

        # 所有模型都失败 → 返回静态降级响应
        print("  💀 所有模型都不可用，返回降级响应")
        raise last_error


# ╔══════════════════════════════════════════════════════════════╗
# ║  组件 3: 熔断器（Circuit Breaker）                            ║
# ╚══════════════════════════════════════════════════════════════╝

class CircuitBreaker:
    """
    熔断器模式：连续失败达到阈值后，暂时"熔断"（不再尝试），
    过一段时间后进入"半开"状态（试探性地尝试一次）。

    状态机：
    CLOSED（正常）→ 连续失败 N 次 → OPEN（熔断，直接拒绝）
    → 等待 reset_timeout → HALF_OPEN（试探一次）
    → 成功 → CLOSED / 失败 → OPEN

    为什么需要？避免对已经宕掉的服务反复重试，浪费时间和资源。
    """
    CLOSED = "CLOSED"      # 正常通行
    OPEN = "OPEN"          # 熔断，直接拒绝
    HALF_OPEN = "HALF_OPEN"  # 试探

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0

    def can_execute(self) -> bool:
        if self.state == self.CLOSED:
            return True
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = self.HALF_OPEN
                print(f"  🔶 熔断器半开（试探）")
                return True
            return False
        return True  # HALF_OPEN

    def record_success(self):
        self.failure_count = 0
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            print(f"  🟢 熔断器恢复正常")

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            print(f"  🔴 熔断器触发！连续失败 {self.failure_count} 次")


# ╔══════════════════════════════════════════════════════════════╗
# ║  组装：弹性 Agent 循环                                       ║
# ╚══════════════════════════════════════════════════════════════╝

TOOLS = [
    {"type": "function", "function": {
        "name": "calculator", "description": "计算数学表达式",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "unreliable_api", "description": "一个不稳定的外部 API（50% 概率失败）",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "查询内容"}
        }, "required": ["query"]}}},
]


def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})


@retry_with_backoff(max_retries=2, base_delay=0.5)
def unreliable_api(query: str) -> str:
    """模拟一个 50% 概率失败的外部 API"""
    if random.random() < 0.5:
        raise Exception("Status 503: Service temporarily unavailable")
    return json.dumps({"data": f"关于 '{query}' 的查询结果", "status": "ok"}, ensure_ascii=False)


TOOL_MAP = {"calculator": calculator, "unreliable_api": unreliable_api}


def resilient_agent(user_message: str, max_turns: int = 5) -> str:
    """带完整弹性机制的 Agent 循环"""
    # 模型降级链
    chain = ModelFallbackChain([MODEL, FAST_MODEL])
    # 熔断器
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout=10)

    messages = [
        {"role": "system", "content": "你是一个AI助手。可以使用 calculator 和 unreliable_api 工具。"},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        print(f"\n  ⚡ 第 {turn+1} 轮...")

        # 检查熔断器
        if not breaker.can_execute():
            return "⚠️ 服务暂时不可用（熔断器已触发），请稍后重试"

        try:
            used_model, response = chain.call(messages, TOOLS)
            breaker.record_success()
        except Exception as e:
            breaker.record_failure()
            return f"⚠️ 所有模型都不可用: {e}"

        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print(f"  ✅ 完成（使用 {used_model}）")
            return msg.content or ""

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            print(f"  🔧 {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:60]})")
            try:
                result = TOOL_MAP[fn_name](**fn_args)
            except Exception as e:
                result = json.dumps({"error": str(e), "fallback": "工具暂时不可用"}, ensure_ascii=False)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "⚠️ 达到最大轮次"


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 4 进阶: 弹性 Agent — retry + fallback + 熔断")
    print("=" * 60)

    # 测试 1: 正常调用（应该顺利完成）
    print("\n📝 测试 1: 正常计算任务")
    result = resilient_agent("帮我算 123 * 456 + 789")
    print(f"\n🤖 {result}")

    # 测试 2: 使用不稳定 API（触发重试）
    print(f"\n{'='*60}")
    print("📝 测试 2: 调用不稳定 API（可能触发重试）")
    result = resilient_agent("帮我查询一下 'AI Agent 最新进展'")
    print(f"\n🤖 {result}")

    print(f"\n{'='*60}")
    print("📚 弹性机制总结:")
    print("  retry     — 临时故障自动重试，指数退避 + 抖动")
    print("  fallback  — 主模型挂了自动降级到备选模型")
    print("  breaker   — 连续失败触发熔断，避免无效重试")
    print("  分类错误   — 429/503 可重试，400/401 不可重试")
    print()
    print("  Claude Code 的做法:")
    print("  - 429 → 指数退避重试")
    print("  - 529 → 过载，等待后重试")
    print("  - 400 → 请求有误，不重试，尝试修正 prompt")
