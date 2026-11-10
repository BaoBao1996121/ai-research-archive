"""benchmark.py — 测 Qwen3.6 / Qwen3 本地推理性能并对比。

测三个指标:
    1. TTFT  (Time To First Token，首 token 延迟)
    2. TPS   (Tokens Per Second，吐字速度)
    3. 端到端延迟

用法:
    python benchmark.py                                    # 默认对比 35b vs 8b
    python benchmark.py --models qwen3.6:35b qwen3:8b     # 多模型对比
    python benchmark.py --models qwen3.6:35b --rounds 5
"""
from __future__ import annotations

import argparse
import time
from statistics import mean, median

from openai import OpenAI

PROMPTS = [
    "请用 200 字介绍 Transformer 架构的核心思想。",
    "写一段 Python 代码：实现快速排序，含注释。",
    "对比 RAG 和 Fine-tuning 的适用场景。",
]


def build_extra_body(model: str, num_ctx: int = 8192) -> dict:
    options = {"num_ctx": num_ctx}
    if model.startswith("qwen3.6"):
        return {
            "options": options,
            "chat_template_kwargs": {"enable_thinking": False},
        }
    options["think"] = False
    return {"options": options}


def bench_round(client: OpenAI, model: str, prompt: str) -> dict:
    t_start = time.perf_counter()
    t_first = None
    n_tokens = 0
    pieces: list[str] = []

    sys_prompt = "你是技术助手。" if model.startswith("qwen3.6") else "你是技术助手。/nothink"

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=400,
        temperature=0.7,
        stream=True,
        extra_body=build_extra_body(model),
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            if t_first is None:
                t_first = time.perf_counter()
            n_tokens += 1
            pieces.append(delta)

    t_end = time.perf_counter()
    text = "".join(pieces)
    return {
        "ttft": (t_first - t_start) if t_first else float("inf"),
        "total_s": t_end - t_start,
        "out_chars": len(text),
        "out_chunks": n_tokens,
        "tps_chunks": n_tokens / (t_end - t_first) if t_first else 0,
        "preview": text[:80].replace("\n", " "),
    }


def bench_model(client: OpenAI, model: str, rounds: int) -> dict:
    print(f"\n--- Benchmark {model} × {rounds} rounds ---")
    all_r = []
    for i in range(rounds):
        for j, prompt in enumerate(PROMPTS):
            print(f"  R{i+1}·P{j+1} ... ", end="", flush=True)
            try:
                r = bench_round(client, model, prompt)
            except Exception as e:
                print(f"FAIL: {e}")
                continue
            all_r.append(r)
            print(f"TTFT={r['ttft']:.2f}s  TPS={r['tps_chunks']:.1f}  chars={r['out_chars']}")
    if not all_r:
        return {"model": model, "ttft": None, "tps": None, "n": 0}
    return {
        "model": model,
        "ttft": median([r["ttft"] for r in all_r]),
        "tps": median([r["tps_chunks"] for r in all_r]),
        "n": len(all_r),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["qwen3.6:35b", "qwen3:8b"])
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    print(f"=== Multi-Model Benchmark ===")
    print(f"Models: {args.models}  Rounds: {args.rounds}\n")

    summaries = []
    for m in args.models:
        try:
            summaries.append(bench_model(client, m, args.rounds))
        except Exception as e:
            print(f"[跳过] {m} 失败: {e}")
            summaries.append({"model": m, "ttft": None, "tps": None, "n": 0})

    print("\n=== 汇总对比 ===")
    print(f"{'模型':<24} {'TTFT 中位':<14} {'TPS 中位':<14} 样本数")
    print("-" * 64)
    for s in summaries:
        ttft = f"{s['ttft']:.2f}s" if s["ttft"] else "N/A"
        tps = f"{s['tps']:.1f}" if s["tps"] else "N/A"
        print(f"{s['model']:<24} {ttft:<14} {tps:<14} {s['n']}")
    print(f"\n注: TPS 基于 chunk 计数，不是严格 token。精确值看 ollama --verbose。")


if __name__ == "__main__":
    main()

