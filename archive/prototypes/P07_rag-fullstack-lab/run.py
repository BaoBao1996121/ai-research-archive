"""单题问答入口。

用法：
    python run.py --config configs/baseline.yaml --question "PSEV 框架是什么？"
    python run.py --config configs/baseline.yaml --question "..." --no-build  # 索引已存在
    python run.py --config configs/baseline.yaml --reindex                     # 强制重建
    python run.py --config configs/baseline.yaml -i                            # 交互模式
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 让 pipeline 包可导入
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.factory import build_pipeline, load_config, config_fingerprint  # noqa


console = Console()


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", "-c", required=True)
    ap.add_argument("--question", "-q", default=None)
    ap.add_argument("--reindex", action="store_true", help="强制重建索引")
    ap.add_argument("--no-build", action="store_true", help="跳过索引构建（认为已存在）")
    ap.add_argument("-i", "--interactive", action="store_true")
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--top-n", type=int, default=5)
    args = ap.parse_args()

    cfg = load_config(args.config)
    fp = config_fingerprint(cfg)
    persist = Path(cfg.get("persist_dir", "./data")) / fp
    needs_build = args.reindex or (not persist.exists()) or (not any(persist.iterdir()) if persist.exists() else True)
    if args.no_build:
        needs_build = False

    console.rule(f"[bold cyan]配置 {Path(args.config).name}  指纹={fp}")
    console.print(f"[dim]索引目录: {persist}  build={needs_build}[/dim]")

    pipe = build_pipeline(cfg, build_indices=needs_build)

    def ask(q: str):
        console.rule(f"[bold green]Q: {q}")
        result = pipe.answer(q, k=args.top_k, top_n=args.top_n, return_trace=True)
        # 检索 trace
        tbl = Table(title="召回 top-N", show_lines=False)
        tbl.add_column("#", width=3)
        tbl.add_column("score", width=8)
        tbl.add_column("source", overflow="fold")
        tbl.add_column("preview", overflow="fold")
        for i, item in enumerate(result["trace"]["reranked_top"]):
            tbl.add_row(str(i+1), f"{item['score']:.3f}", item["source"], item["preview"])
        console.print(tbl)
        console.print(f"[dim]改写后查询: {result['trace']['queries']}[/dim]")
        console.print(f"[dim]context 字符数: {result['trace']['context_chars']}[/dim]")
        console.print(Panel(result["answer"], title="[bold]回答[/bold]", border_style="cyan"))

    if args.interactive:
        console.print("[bold yellow]交互模式。输入问题，:q 退出[/bold yellow]")
        while True:
            try:
                q = console.input("[bold]> [/bold]").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if q in (":q", "exit", "quit"):
                break
            if q:
                ask(q)
    elif args.question:
        ask(args.question)
    else:
        console.print("[red]必须给 --question 或 -i[/red]")


if __name__ == "__main__":
    main()
