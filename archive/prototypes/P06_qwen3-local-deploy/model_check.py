"""model_check.py — 列出本地已拉取的 Qwen 模型，给出推荐。

用法:
    python model_check.py
"""
from __future__ import annotations

import sys

import requests

OLLAMA_HOST = "http://localhost:11434"

PRIORITY = [
    # (model_pattern, role, recommendation)
    ("qwen3.6:35b", "🏆 甜点 (MoE 36B/3B 激活)", "首选 — 多模态 + 中速 + 8-15 t/s"),
    ("qwen3.6:27b", "🥈 能力上限 (28B 稠密)", "SWE-bench 77.2，跑 coding 任务，2-5 t/s"),
    ("qwen3:8b",    "🚀 保底基线", "全装显存 35-45 t/s，普通对话/Agent 首选"),
    ("qwen3:4b-instruct-2507", "🥉 长文极速", "256K 上下文 + 60+ t/s"),
    ("qwen3:30b-a3b", "🟡 上一代 MoE", "Qwen3 时代的 MoE 备选"),
]


def list_models():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        r.raise_for_status()
        return r.json().get("models", [])
    except Exception as e:
        print(f"[FAIL] 连接 Ollama 失败：{e}")
        sys.exit(1)


def main():
    print("=== 本地 Qwen 模型速查 ===\n")
    models = list_models()
    if not models:
        print("尚未拉取任何模型。建议执行：\n  ollama pull qwen3.6:35b   # 或 qwen3:8b 作起步")
        return

    have = {m["name"]: m for m in models}
    have_names = list(have.keys())

    print(f"{'名称':<32} {'大小':<10} {'修改时间':<22}")
    print("-" * 70)
    for m in models:
        size_gb = m.get("size", 0) / (1024**3)
        modified = m.get("modified_at", "")[:19]
        print(f"{m['name']:<32} {size_gb:>6.1f} GB  {modified}")

    print("\n=== 推荐排序（按 8GB 显卡价值） ===\n")
    for pattern, role, rec in PRIORITY:
        matched = [n for n in have_names if n == pattern or n.startswith(pattern + ":")
                   or n == pattern + ":latest"]
        mark = "✅ 已有" if matched else "⬜ 未拉"
        print(f"  {mark:<8} {pattern:<28} {role}")
        print(f"           └─ {rec}")
        if not matched:
            print(f"           └─ 拉取: ollama pull {pattern}")
        print()


if __name__ == "__main__":
    main()
