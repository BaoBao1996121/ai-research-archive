"""
Multi-Agent Orchestrator — 最小可运行原型
=========================================
演示 Collector → Researcher → Reporter 三 Agent 协作模式。

关联: Agent研究/reports/AI-Agent学习路线与项目整合全景报告.md (G-E)
理论: Agent研究/reports/Agent架构深度研究报告.md → 多 Agent 编排
模式: Google ADK 五大模式 → Delegate + Sequential

用法:
    # 设置环境变量
    set OPENAI_API_KEY=your-key
    set OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

    python multi_agent_orchestrator.py [--model qwen3.5-plus] [--topic "MCP tools"]
"""

import json
import os
import sys
import argparse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# 自动加载项目根目录 .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# ============================================================
# 配置
# ============================================================

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "qwen3.5-plus")


# ============================================================
# Agent 基础设施
# ============================================================

@dataclass
class AgentMessage:
    """Agent 之间传递的消息"""
    role: str          # collector / researcher / reporter / orchestrator
    content: str       # 结构化 JSON 或自然语言
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Agent:
    """最小 Agent 抽象：system prompt + LLM 调用 + 输出解析"""

    def __init__(self, name: str, system_prompt: str, model: str = None):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or DEFAULT_MODEL
        self.call_count = 0

    def run(self, user_input: str, context: str = "") -> AgentMessage:
        """执行 Agent: 发送 prompt → 获取 LLM 响应 → 包装为 AgentMessage"""
        self.call_count += 1
        print(f"\n  🤖 [{self.name}] 开始执行 (第 {self.call_count} 次调用)")

        full_prompt = user_input
        if context:
            full_prompt = f"上下文信息:\n{context}\n\n当前任务:\n{user_input}"

        response = call_llm(full_prompt, self.system_prompt, model=self.model)

        msg = AgentMessage(
            role=self.name,
            content=response,
            metadata={
                "model": self.model,
                "call_number": self.call_count,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(f"  ✅ [{self.name}] 完成 ({len(response)} 字符)")
        return msg


def call_llm(prompt: str, system: str = "", model: str = None, temperature: float = 0.7) -> str:
    """调用 LLM API"""
    if model is None:
        model = DEFAULT_MODEL

    try:
        from openai import OpenAI
        client = OpenAI()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ❌ LLM 调用失败: {e}")
        return f"[ERROR] {e}"


# ============================================================
# 三个专业 Agent
# ============================================================

COLLECTOR_PROMPT = """你是一个 AI 开源项目信号采集员 (Collector Agent)。

你的职责：
1. 根据用户指定的主题，模拟搜索 GitHub Trending 和相关来源
2. 列出 5-8 个值得关注的项目
3. 为每个项目提供: 项目名、URL(可模拟)、Star 数(估算)、一句话描述、热度评分(1-10)

输出格式：JSON 数组，每个元素包含:
- name: 项目名
- url: GitHub URL
- stars: Star 数量(估算)
- description: 一句话描述
- hot_score: 热度评分 1-10
- language: 主要编程语言

只输出 JSON，不要其他内容。"""

RESEARCHER_PROMPT = """你是一个 AI 技术深度研究员 (Researcher Agent)。

你的职责：
1. 接收 Collector 提供的项目列表
2. 选择热度最高的 3 个项目进行深度分析
3. 为每个项目分析:
   - 核心创新点（它做了什么之前做不好的事？）
   - 技术架构（用了什么关键技术？）
   - 适用场景（什么时候该用它？什么时候不该？）
   - 风险评估（成熟度、维护状况、依赖风险）
   - 与 Agent 开发的关联（对我们的 Agent 项目有什么启发？）

输出格式：JSON 数组，每个元素包含:
- name: 项目名
- innovation: 核心创新点
- architecture: 技术架构摘要
- use_cases: 适用场景
- risks: 风险评估
- agent_relevance: 与 Agent 开发的关联
- recommendation: 推荐等级 (强烈推荐/推荐/观望/不推荐)

只输出 JSON，不要其他内容。"""

REPORTER_PROMPT = """你是一个研究报告撰写员 (Reporter Agent)。

你的职责：
1. 接收 Collector 的项目列表和 Researcher 的深度分析
2. 整合为一篇结构清晰的中文研究报告

报告格式：
# GitHub AI 每日热门 — {日期}

## 📊 今日概览
(简要总结今日趋势)

## 🔥 重点项目深度分析
(对每个深度分析的项目写一段)

## 📋 今日完整项目列表
(表格形式列出所有项目)

## 💡 对我们 Agent 项目的启发
(总结与 Agent 开发相关的洞察)

---
*由 Multi-Agent 协作系统自动生成*

输出完整的 Markdown 报告内容。"""


# ============================================================
# Orchestrator — 调度引擎
# ============================================================

class Orchestrator:
    """编排器：按 Sequential 模式协调三个 Agent"""

    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL
        self.collector = Agent("Collector", COLLECTOR_PROMPT, self.model)
        self.researcher = Agent("Researcher", RESEARCHER_PROMPT, self.model)
        self.reporter = Agent("Reporter", REPORTER_PROMPT, self.model)
        self.trace = []  # 完整调用链

    def run(self, topic: str = "AI Agent 工具") -> str:
        """执行完整的 Collector → Researcher → Reporter 流水线"""
        print(f"\n{'='*60}")
        print(f"🦞 Multi-Agent Orchestrator")
        print(f"{'='*60}")
        print(f"主题: {topic}")
        print(f"模型: {self.model}")
        print(f"Agent 链: Collector → Researcher → Reporter")
        print(f"{'='*60}")

        # Phase 1: 采集
        print(f"\n{'─'*40}")
        print("📡 Phase 1: 信号采集")
        collector_msg = self.collector.run(
            f"请搜索最近 GitHub 上关于「{topic}」的热门项目，列出 5-8 个值得关注的。"
        )
        self.trace.append(asdict(collector_msg))

        # Phase 2: 深度研究
        print(f"\n{'─'*40}")
        print("🔬 Phase 2: 深度研究")
        researcher_msg = self.researcher.run(
            "请对以下项目列表中热度最高的 3 个进行深度分析。",
            context=f"Collector 采集到的项目列表:\n{collector_msg.content}"
        )
        self.trace.append(asdict(researcher_msg))

        # Phase 3: 报告生成
        print(f"\n{'─'*40}")
        print("📝 Phase 3: 报告生成")
        reporter_msg = self.reporter.run(
            f"请整合以下信息生成一篇完整的研究报告。日期: {datetime.now().strftime('%Y-%m-%d')}",
            context=(
                f"Collector 采集的项目列表:\n{collector_msg.content}\n\n"
                f"Researcher 的深度分析:\n{researcher_msg.content}"
            )
        )
        self.trace.append(asdict(reporter_msg))

        # 输出统计
        total_calls = (
            self.collector.call_count +
            self.researcher.call_count +
            self.reporter.call_count
        )
        print(f"\n{'='*60}")
        print(f"✅ 编排完成")
        print(f"   总 LLM 调用: {total_calls} 次")
        print(f"   Agent 链: Collector({self.collector.call_count}) → "
              f"Researcher({self.researcher.call_count}) → "
              f"Reporter({self.reporter.call_count})")
        print(f"{'='*60}")

        return reporter_msg.content

    def save_trace(self, output_dir: str = "."):
        """保存完整的调用链（用于调试和学习）"""
        trace_path = os.path.join(output_dir, "orchestrator_trace.json")
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "total_agents": 3,
                "total_calls": sum(a.call_count for a in [
                    self.collector, self.researcher, self.reporter
                ]),
                "trace": self.trace,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📁 调用链已保存: {trace_path}")
        return trace_path


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Orchestrator 最小原型")
    parser.add_argument("--topic", default="AI Agent 工具",
                        help="搜索主题 (default: AI Agent 工具)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"LLM 模型 (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", default=".",
                        help="输出目录 (default: 当前目录)")
    parser.add_argument("--save-report", action="store_true",
                        help="保存生成的报告到文件")
    args = parser.parse_args()

    # 运行编排器
    orchestrator = Orchestrator(model=args.model)
    report = orchestrator.run(topic=args.topic)

    # 保存调用链
    orchestrator.save_trace(args.output)

    # 可选：保存报告
    if args.save_report:
        report_path = os.path.join(
            args.output,
            f"{datetime.now().strftime('%Y-%m-%d')}-multi-agent-report.md"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📄 报告已保存: {report_path}")

    # 打印报告
    print(f"\n{'='*60}")
    print("📋 生成的报告:")
    print(f"{'='*60}")
    print(report[:2000])
    if len(report) > 2000:
        print(f"\n... (共 {len(report)} 字符, 完整报告见 trace)")


if __name__ == "__main__":
    main()
