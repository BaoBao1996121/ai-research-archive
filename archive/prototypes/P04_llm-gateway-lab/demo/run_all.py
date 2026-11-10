"""run_all · 串联跑完所有 demo，输出 JSON 报告。

用法:
  python -m demo.run_all --mode dry
  python -m demo.run_all --mode local
  python -m demo.run_all --mode full --out output/report.json
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

# Windows GBK 终端 / 管道兼容：强制 stdout/stderr 为 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from demo import smoke_test, fallback, semantic_cache, virtual_key, load_balance


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["dry", "local", "full"], default="dry")
    p.add_argument("--out", default="output/report.json", help="报告输出路径")
    args = p.parse_args()

    results = []
    for fn in (smoke_test.main, fallback.main, semantic_cache.main, virtual_key.main, load_balance.main):
        try:
            results.append(fn(args.mode))
        except Exception as e:
            results.append({"demo": fn.__module__.split(".")[-1], "ok": False, "error": str(e)})

    # 汇总
    print()
    print("═" * 72)
    print(f"  汇总（mode={args.mode}）")
    print("═" * 72)
    for r in results:
        status = "✅" if r.get("ok") else ("⏭ 跳过" if r.get("skipped") else "❌")
        print(f"  {status}  {r.get('demo', '?')}")

    Path(os.path.dirname(args.out) or ".").mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"mode": args.mode, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\n  报告已写入: {args.out}")


if __name__ == "__main__":
    main()
