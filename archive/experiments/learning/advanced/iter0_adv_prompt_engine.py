"""
Iter 0 进阶: Prompt 模板引擎 — 动态 Prompt 组装（~120 行核心代码）
===================================================================
基础版差距：System Prompt 是硬编码字符串，无法根据上下文动态变化。
进阶补全：Prompt 模板引擎——支持变量替换、条件渲染、模板组合。

Claude Code 对照：
  - system prompt 是动态组装的：基础指令 + 环境信息 + 用户设置 + 工具描述
  - 不同场景（首次对话 vs 续聊 vs 特定工具模式）使用不同的 prompt 模板
  - 生产级 Agent 的 prompt 从来不是一个静态字符串

依赖：pip install openai jinja2
运行：python iter0_adv_prompt_engine.py
"""

import os
import time
from string import Template
from config import client, MODEL


# ╔══════════════════════════════════════════════════════════════╗
# ║  方案 1: string.Template（零依赖，只能变量替换）               ║
# ╚══════════════════════════════════════════════════════════════╝

BASIC_TEMPLATE = Template("""你是 $role。

## 当前环境
- 时间: $time
- 用户: $user_name

## 你的任务
$task_instruction

## 输出格式
$output_format""")


def build_prompt_basic(role: str, user_name: str, task: str,
                       output_format: str = "Markdown") -> str:
    """用 string.Template 做最简单的变量替换"""
    return BASIC_TEMPLATE.substitute(
        role=role, time=time.strftime("%Y-%m-%d %H:%M"),
        user_name=user_name, task_instruction=task,
        output_format=output_format,
    )


# ╔══════════════════════════════════════════════════════════════╗
# ║  方案 2: Jinja2 模板引擎（生产级：条件 + 循环 + 过滤器）       ║
# ╚══════════════════════════════════════════════════════════════╝

try:
    from jinja2 import Environment, BaseLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
    print("⚠️ 未安装 jinja2，方案2 将跳过。安装: pip install jinja2")


# Claude Code 的 system prompt 就是这样动态拼装的
SYSTEM_TEMPLATE_J2 = """\
你是一个{{ role }}。

## 当前环境
- 时间: {{ current_time }}
- 工作目录: {{ cwd }}
{% if user_prefs %}

## 用户偏好
{% for key, value in user_prefs.items() -%}
- {{ key }}: {{ value }}
{% endfor %}
{%- endif %}

## 可用工具
{% if tools -%}
{% for t in tools -%}
- **{{ t.name }}**: {{ t.desc }}
{% endfor %}
{%- else -%}
（无可用工具）
{%- endif %}

## 行为规则
{% if strict_mode -%}
- 严格模式：只使用工具获取信息，不要猜测
- 每个回答必须标注信息来源
{%- else -%}
- 标准模式：可以结合已有知识回答
{%- endif %}
{% if max_words %}
回答控制在 {{ max_words }} 字以内。
{%- endif %}"""


class PromptEngine:
    """
    Prompt 模板引擎：根据运行时上下文动态组装 System Prompt。

    核心思想：prompt = 模板 + 上下文变量
    - 模板定义结构和规则
    - 变量在运行时注入（时间、用户、工具列表、模式切换等）

    这就是 Claude Code 的 context.ts 在做的事——
    不同的是它用 TypeScript 字符串拼接，我们用 Jinja2 模板。
    """
    def __init__(self):
        if not HAS_JINJA2:
            raise RuntimeError("需要安装 jinja2: pip install jinja2")
        self.env = Environment(loader=BaseLoader())
        self.templates: dict[str, str] = {}
        self.global_vars: dict = {}

    def register(self, name: str, template_str: str):
        self.templates[name] = template_str

    def set_global(self, key: str, value):
        self.global_vars[key] = value

    def render(self, name: str, **kwargs) -> str:
        if name not in self.templates:
            raise KeyError(f"模板 '{name}' 未注册")
        ctx = {
            "current_time": time.strftime("%Y-%m-%d %H:%M"),
            "cwd": os.getcwd(),
            **self.global_vars, **kwargs,
        }
        return self.env.from_string(self.templates[name]).render(**ctx)


# ╔══════════════════════════════════════════════════════════════╗
# ║  方案 3: Prompt 积木组合器（最灵活，适合多租户/AB测试）        ║
# ╚══════════════════════════════════════════════════════════════╝

class PromptComposer:
    """
    积木式 Prompt 组合：选择需要的片段，拼成完整 prompt。

    实际生产中常用于：
    - 不同客户/租户使用不同的 prompt 组合
    - A/B 测试不同的 prompt 策略
    - 根据任务类型动态调整 prompt 结构
    """
    def __init__(self):
        self.fragments: dict[str, str] = {}

    def add(self, name: str, template: str):
        self.fragments[name] = template

    def compose(self, names: list[str], **kwargs) -> str:
        parts = []
        for n in names:
            if n in self.fragments:
                try:
                    parts.append(self.fragments[n].format(**kwargs))
                except KeyError as e:
                    parts.append(f"[缺少变量: {e}]")
        return "\n".join(parts)


# ━━━ 辅助 ━━━
def chat(user_message: str, system_prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 0 进阶: Prompt 模板引擎")
    print("=" * 60)

    # ━━━ 演示 1: string.Template ━━━
    print("\n📝 方案 1: string.Template — 变量替换")
    prompt = build_prompt_basic(
        role="技术分析专家", user_name="开发者",
        task="分析用户提出的技术问题，给出专业建议。",
        output_format="先一句话结论，再 3 个要点展开",
    )
    print(f"  生成的 Prompt ({len(prompt)} 字):\n  ---\n{prompt}\n  ---")
    result = chat("Python 的 GIL 对 Agent 开发有什么影响？", prompt)
    print(f"\n🤖 回答:\n{result}")

    # ━━━ 演示 2: Jinja2 模板 ━━━
    if HAS_JINJA2:
        print(f"\n{'='*60}")
        print("📝 方案 2: Jinja2 — 条件渲染 + 循环")

        engine = PromptEngine()
        engine.register("main", SYSTEM_TEMPLATE_J2)
        engine.set_global("role", "AI 架构顾问")

        # 场景 A: 严格模式
        p_strict = engine.render("main",
            tools=[{"name": "search_docs", "desc": "搜索技术文档"},
                   {"name": "calculator", "desc": "数学计算"}],
            user_prefs={"语言": "中文", "风格": "简洁技术风"},
            strict_mode=True, max_words=300,
        )
        print(f"\n  [严格模式] ({len(p_strict)} 字):\n{p_strict}")

        # 场景 B: 轻松模式（无工具）
        p_casual = engine.render("main",
            tools=[], user_prefs={},
            strict_mode=False, max_words=None,
        )
        print(f"\n  [轻松模式] ({len(p_casual)} 字):\n{p_casual}")

        result = chat("如何选择 Agent 框架？", p_strict)
        print(f"\n🤖 回答:\n{result}")

    # ━━━ 演示 3: 积木组合 ━━━
    print(f"\n{'='*60}")
    print("📝 方案 3: Prompt 积木组合")

    composer = PromptComposer()
    composer.add("role", "你是一个{role}，专注于{domain}领域。")
    composer.add("rules", "\n## 输出规则\n{rules}")
    composer.add("fewshot", "\n## 示例\n{examples}")
    composer.add("limit", "\n## 约束\n- 回答不超过 {max_words} 字\n- 使用中文")

    p = composer.compose(
        ["role", "fewshot", "limit"],
        role="命名顾问", domain="API 设计",
        examples="Q: 获取用户列表 → GET /users\nQ: 创建订单 → POST /orders",
        max_words=200,
    )
    print(f"  组合结果:\n{p}")
    result = chat("帮我设计一个查询商品评价的 API 端点", p)
    print(f"\n🤖 回答:\n{result}")

    print(f"\n{'='*60}")
    print("📚 总结:")
    print("  string.Template — 零依赖，变量替换，适合简单场景")
    print("  Jinja2         — 条件/循环/继承，生产级方案")
    print("  积木组合器      — 最灵活，适合多租户/A/B测试")
    print("  Claude Code 用类似方案 2+3 的混合体动态组装 system prompt")
