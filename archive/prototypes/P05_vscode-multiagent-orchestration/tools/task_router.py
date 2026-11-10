"""task_router.py · 任务画像 → 推荐 subagent

P05 动态模型选择路径 A 的最小可执行 Spike。

机制：基于"任务描述关键词 + 输入大小估算"做静态规则路由，
输出"推荐 agent name + 该 agent 实际绑定的模型 tier"。

Coordinator 在派发 subagent 前先调用本工具，把推荐结果写进派发理由
（让模型选择从黑箱变成可审计的决策链）。

设计哲学（参见 R73 协议降级章节）：
- 双标签协议保证"实际命中模型 = agent.md model[0]" 100% 一致
- 因此"动态选模型" = "动态选 agent"——只要 agent 名选对了，模型就对了
- 不需要 runSubagent 的 explicit model 参数（VS Code 当前是否支持仍未充分验证）

用法：
    python task_router.py "审查 login 函数的 SQL 注入风险"
    python task_router.py --json "优化 process_orders 嵌套循环"
    python task_router.py --explain "列出文件中所有处理外部输入的函数"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# 与 feature-coordinator.agent.md 的查表保持同步
AGENT_REGISTRY = {
    "researcher": {
        "model": "claude-haiku-4-5-20251001",
        "tier": "fast",
        "strengths": ["代码检索", "信息提取", "结构化转述", "无评价信息整理"],
    },
    "implementer": {
        "model": "claude-haiku-4-5-20251001",
        "tier": "fast",
        "strengths": ["按规范写代码", "格式转换", "短函数实现"],
    },
    "reviewer": {
        "model": "claude-sonnet-4-5-20250929",
        "tier": "strong",
        "strengths": ["综合质量审查", "代码风格", "可维护性", "正确性"],
    },
    "security-reviewer": {
        "model": "claude-sonnet-4-5-20250929",
        "tier": "strong",
        "strengths": ["安全漏洞", "SQL 注入", "认证授权", "加密"],
    },
    "performance-reviewer": {
        "model": "claude-haiku-4-5-20251001",
        "tier": "fast",
        "strengths": ["复杂度分析", "性能瓶颈", "算法优化"],
    },
}

# 任务画像规则（关键词 → 推荐 agent，匹配优先级 = 顺序）
#
# 设计原则：动作动词优先级 > 领域名词。
# 因为"实现一个安全版本"的核心动作是 implement，"安全"只是修饰。
# Spike 实测发现的反例（v1）：把 security 规则放在 implementer 前会误派"实现安全函数"任务。
ROUTING_RULES = [
    # 动作动词（高优先级）：决定任务在做什么
    (r"(实现|创建|写一个|写一段|编写|生成|构造|新建.*文件|追加|插入)",
     "implementer", "命中实现/写代码动作"),
    # 综合审查类（reviewer 必须在 security/performance 之前以截获"综合代码审查"）
    (r"(综合.{0,4}审查|综合.{0,4}评审|代码审查|代码评审|可维护性|代码风格|质量审查)",
     "reviewer", "命中综合审查关键词"),
    # 领域名词（专科 reviewer）
    (r"(安全|漏洞|sql\s*注入|认证|授权|加密|password|hash|jwt|xss|csrf)",
     "security-reviewer", "命中安全语义关键词"),
    (r"(性能|优化.*循环|复杂度|嵌套循环|耗时|算法.*慢|n\^2|big\s*o)",
     "performance-reviewer", "命中性能语义关键词"),
    # 信息提取（兜底前最后一道）
    (r"(列出|查找|找到|提取|搜索|哪些|多少|读取|摘要|总结)",
     "researcher", "命中信息提取关键词"),
]

# 输入大小阈值（用于在多个候选中做 tier 升级）
LARGE_INPUT_TOKEN_THRESHOLD = 30_000  # 估算 tokens，1 token ≈ 4 字符


@dataclass
class RoutingResult:
    task_summary: str
    recommended_agent: str
    model: str
    tier: str
    reason: str
    matched_rule: Optional[str]
    input_size_chars: int
    estimated_tokens: int
    upgraded_due_to_size: bool


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：英文 ~4 char/token，中文 ~1.5 char/token，混合按 3 估算。"""
    return max(1, len(text) // 3)


def route(task: str, input_payload: str = "") -> RoutingResult:
    """对任务做画像，返回推荐 agent。"""
    task_lower = task.lower()
    matched_rule = None
    chosen = None
    reason = ""

    for pattern, agent, rule_reason in ROUTING_RULES:
        if re.search(pattern, task_lower, flags=re.IGNORECASE):
            chosen = agent
            reason = rule_reason
            matched_rule = pattern
            break

    if chosen is None:
        # 兜底：纯文本理解类任务用 researcher
        chosen = "researcher"
        reason = "未命中任何规则，兜底用 researcher（信息处理通用）"

    # tier 升级判定：输入超阈值且当前是 fast tier 时，升级到 strong
    full_text = task + "\n" + input_payload
    estimated = estimate_tokens(full_text)
    upgraded = False

    if (
        estimated >= LARGE_INPUT_TOKEN_THRESHOLD
        and AGENT_REGISTRY[chosen]["tier"] == "fast"
        and chosen in ("researcher", "implementer")
    ):
        upgrade_map = {"researcher": "reviewer", "implementer": "reviewer"}
        chosen = upgrade_map[chosen]
        reason += f"；输入估算 {estimated} tokens 超过 {LARGE_INPUT_TOKEN_THRESHOLD}，升级到 strong tier"
        upgraded = True

    info = AGENT_REGISTRY[chosen]
    return RoutingResult(
        task_summary=task[:80] + ("..." if len(task) > 80 else ""),
        recommended_agent=chosen,
        model=info["model"],
        tier=info["tier"],
        reason=reason,
        matched_rule=matched_rule,
        input_size_chars=len(full_text),
        estimated_tokens=estimated,
        upgraded_due_to_size=upgraded,
    )


def main():
    parser = argparse.ArgumentParser(description="任务路由器 · 推荐 subagent")
    parser.add_argument("task", nargs="?", help="任务描述")
    parser.add_argument("--input-file", help="可选：实际数据文件路径，用于估算输入大小")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--explain", action="store_true", help="输出详细决策链")
    args = parser.parse_args()

    if not args.task:
        parser.print_help()
        return 1

    payload = ""
    if args.input_file:
        p = Path(args.input_file)
        if p.exists():
            payload = p.read_text(encoding="utf-8", errors="ignore")

    result = route(args.task, payload)

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    elif args.explain:
        print(f"任务摘要      : {result.task_summary}")
        print(f"推荐 agent    : {result.recommended_agent}")
        print(f"绑定模型      : {result.model}  ({result.tier} tier)")
        print(f"路由理由      : {result.reason}")
        if result.matched_rule:
            print(f"命中规则      : /{result.matched_rule}/")
        print(f"输入大小      : {result.input_size_chars} 字符 (~{result.estimated_tokens} tokens)")
        print(f"升级触发      : {'是' if result.upgraded_due_to_size else '否'}")
    else:
        # 短格式，给 coordinator 一行用
        suffix = " (size-upgraded)" if result.upgraded_due_to_size else ""
        print(f"-> {result.recommended_agent} · {result.model}  [{result.reason}]{suffix}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
