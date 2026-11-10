"""评测引擎。

支持三种使用方式：
- 单配方评测：python eval/run_eval.py --config configs/baseline.yaml
- 对比评测：  python eval/run_eval.py --compare configs/baseline.yaml configs/v4_full.yaml
- CI Gate：   python eval/run_eval.py --config ... --gate baseline.json --threshold 0.05

输出指标：
- pass_rate: must_contain 全部命中的 case 比例
- recall_keywords: ground_truth_keywords 平均召回率
- judge_score: LLM-as-judge 平均 0-5 分
- weighted: 加权综合分
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline.factory import build_pipeline, load_config, config_fingerprint
from pipeline.llm import build_llm

console = Console()


JUDGE_PROMPT = """你是严谨的评估官。请按 0-5 分评估「候选回答」相对于「参考答案」的质量。
评分维度：
- 正确性（事实是否一致）
- 完整性（是否覆盖参考答案的关键点）
- 不胡编（不能凭空捏造资料中没有的内容）

只输出一个 0-5 的整数和一句话理由，格式：
分数：N
理由：...

【问题】
{q}

【参考答案】
{ref}

【候选回答】
{cand}

【评估】"""


def llm_judge(judge_llm, q: str, ref: str, cand: str) -> tuple[int, str]:
    out = judge_llm.complete(JUDGE_PROMPT.format(q=q, ref=ref, cand=cand), max_tokens=200)
    score = 0
    reason = out
    for line in out.splitlines():
        if "分数" in line or "score" in line.lower():
            for ch in line:
                if ch.isdigit():
                    score = int(ch)
                    break
            break
    return min(score, 5), reason.strip()


def evaluate_case(case: dict, result: dict, judge_llm=None) -> dict:
    answer = result.get("answer", "")
    must = case.get("must_contain") or []
    must_not = case.get("must_not_contain") or []
    keywords = case.get("ground_truth_keywords") or []

    must_hit = all(k.lower() in answer.lower() for k in must) if must else True
    must_not_hit = all(k.lower() not in answer.lower() for k in must_not) if must_not else True
    kw_hit = sum(1 for k in keywords if k.lower() in answer.lower())
    kw_recall = kw_hit / len(keywords) if keywords else 1.0

    judge_score = None
    judge_reason = None
    if judge_llm and case.get("reference_answer"):
        try:
            judge_score, judge_reason = llm_judge(judge_llm, case["question"], case["reference_answer"], answer)
        except Exception as e:
            judge_reason = f"judge 失败: {e}"

    pass_ok = must_hit and must_not_hit

    return {
        "id": case["id"],
        "question": case["question"],
        "answer": answer,
        "pass": pass_ok,
        "must_hit": must_hit,
        "must_not_hit": must_not_hit,
        "kw_recall": kw_recall,
        "judge_score": judge_score,
        "judge_reason": judge_reason,
        "retrieved_docs": result.get("retrieved_docs", []),
    }


def run_eval(cfg_path: str, eval_set_path: str, *, use_judge: bool = True, build_idx: bool = True) -> dict:
    cfg = load_config(cfg_path)
    pipe = build_pipeline(cfg, build_indices=build_idx)
    cases = yaml.safe_load(Path(eval_set_path).read_text(encoding="utf-8"))

    judge_llm = None
    if use_judge:
        import os
        judge_cfg = {
            "model": os.environ.get("JUDGE_MODEL", "qwen3:8b"),
            "base_url": os.environ.get("JUDGE_BASE_URL", "${OLLAMA_BASE_URL}"),
            "api_key": os.environ.get("JUDGE_API_KEY", "${OLLAMA_API_KEY}"),
            "temperature": 0.0,
        }
        try:
            judge_llm = build_llm(judge_cfg)
            console.print(f"[dim]Judge LLM: {judge_cfg['model']}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Judge 不可用: {e}[/yellow]")

    results = []
    for i, case in enumerate(cases):
        console.print(f"[dim]({i+1}/{len(cases)}) {case['id']}: {case['question'][:50]}...[/dim]")
        try:
            r = pipe.answer(case["question"])
            results.append(evaluate_case(case, r, judge_llm=judge_llm))
        except Exception as e:
            console.print(f"[red]case {case['id']} 失败: {e}[/red]")
            results.append({"id": case["id"], "question": case["question"], "answer": "", "pass": False, "error": str(e)})

    # 汇总
    n = len(results)
    pass_rate = sum(1 for r in results if r.get("pass")) / n
    kw_avg = sum(r.get("kw_recall", 0) for r in results) / n
    judge_scores = [r["judge_score"] for r in results if r.get("judge_score") is not None]
    judge_avg = sum(judge_scores) / len(judge_scores) if judge_scores else None

    summary = {
        "config": cfg_path,
        "config_fingerprint": config_fingerprint(cfg),
        "timestamp": datetime.now().isoformat(),
        "total": n,
        "pass_rate": round(pass_rate, 4),
        "kw_recall_avg": round(kw_avg, 4),
        "judge_avg": round(judge_avg, 4) if judge_avg is not None else None,
        "cases": results,
    }
    return summary


def print_summary(summary: dict):
    console.rule(f"[bold cyan]Eval 报告 · {Path(summary['config']).name}")
    console.print(f"总数: {summary['total']}  通过率: [bold]{summary['pass_rate']*100:.1f}%[/bold]  关键词召回: {summary['kw_recall_avg']*100:.1f}%  Judge: {summary['judge_avg']}")
    tbl = Table(show_lines=False)
    tbl.add_column("ID", width=6)
    tbl.add_column("Pass", width=5)
    tbl.add_column("KwR", width=6)
    tbl.add_column("Judge", width=6)
    tbl.add_column("Question", overflow="fold")
    for r in summary["cases"]:
        ok = "✅" if r.get("pass") else "❌"
        kr = f"{r.get('kw_recall', 0)*100:.0f}%"
        js = str(r.get("judge_score", "-"))
        tbl.add_row(r["id"], ok, kr, js, r["question"][:60])
    console.print(tbl)


def compare(a_summary: dict, b_summary: dict):
    console.rule("[bold magenta]Compare")
    a_map = {c["id"]: c for c in a_summary["cases"]}
    b_map = {c["id"]: c for c in b_summary["cases"]}
    better = []
    worse = []
    same = []
    for cid in a_map:
        a = a_map[cid]
        b = b_map.get(cid, {})
        a_pass, b_pass = a.get("pass"), b.get("pass")
        a_j = a.get("judge_score") or 0
        b_j = b.get("judge_score") or 0
        if (b_pass and not a_pass) or b_j > a_j:
            better.append((cid, a, b))
        elif (a_pass and not b_pass) or a_j > b_j:
            worse.append((cid, a, b))
        else:
            same.append(cid)
    console.print(f"[green]变好: {len(better)}[/green]  [red]变坏: {len(worse)}[/red]  持平: {len(same)}")
    console.print(f"通过率 {a_summary['pass_rate']*100:.1f}% → {b_summary['pass_rate']*100:.1f}%")
    console.print(f"Judge  {a_summary['judge_avg']} → {b_summary['judge_avg']}")
    if better:
        console.print("\n[bold green]变好的 case:[/bold green]")
        for cid, _a, _b in better[:5]:
            console.print(f"  ✅ {cid}")
    if worse:
        console.print("\n[bold red]变坏的 case（必须看！）:[/bold red]")
        for cid, a, b in worse[:5]:
            console.print(f"  ❌ {cid}: {a['question']}")


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", "-c")
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--eval-set", default="eval/eval_set.yaml")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--gate", help="基线 json 路径，启用 CI Gate")
    ap.add_argument("--threshold", type=float, default=0.05)
    args = ap.parse_args()

    Path("eval/results").mkdir(exist_ok=True, parents=True)

    if args.compare:
        s1 = run_eval(args.compare[0], args.eval_set, use_judge=not args.no_judge, build_idx=not args.no_build)
        s2 = run_eval(args.compare[1], args.eval_set, use_judge=not args.no_judge, build_idx=not args.no_build)
        Path(f"eval/results/{Path(args.compare[0]).stem}.json").write_text(json.dumps(s1, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(f"eval/results/{Path(args.compare[1]).stem}.json").write_text(json.dumps(s2, ensure_ascii=False, indent=2), encoding="utf-8")
        print_summary(s1)
        print_summary(s2)
        compare(s1, s2)
        return

    if not args.config:
        console.print("[red]需要 --config 或 --compare[/red]"); return

    s = run_eval(args.config, args.eval_set, use_judge=not args.no_judge, build_idx=not args.no_build)
    out_path = Path(f"eval/results/{Path(args.config).stem}_{int(time.time())}.json")
    out_path.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[dim]结果已保存: {out_path}[/dim]")
    print_summary(s)

    if args.gate:
        baseline = json.loads(Path(args.gate).read_text(encoding="utf-8"))
        delta_pass = s["pass_rate"] - baseline["pass_rate"]
        delta_judge = (s.get("judge_avg") or 0) - (baseline.get("judge_avg") or 0)
        console.print(f"\nGate 检查: Δpass={delta_pass:+.2%}  Δjudge={delta_judge:+.2f}")
        if delta_pass < -args.threshold:
            console.print(f"[red bold]❌ GATE FAILED: pass_rate 下降超过 {args.threshold:.0%}[/red bold]")
            sys.exit(1)
        if delta_judge < -0.3:
            console.print("[red bold]❌ GATE FAILED: judge 平均分下降超过 0.3[/red bold]")
            sys.exit(1)
        console.print("[green bold]✅ GATE PASSED[/green bold]")


if __name__ == "__main__":
    main()
