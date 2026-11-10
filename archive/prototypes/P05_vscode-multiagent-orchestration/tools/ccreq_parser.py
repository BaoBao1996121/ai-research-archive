"""
ccreq_parser.py — VS Code Copilot Chat 日志解析器

【目的】
从 VS Code Copilot Chat 日志中自动提取 subagent 调用与实际使用模型的对应关系。
解决 "MODEL_SELF_REPORT" 协议不可靠（实测漏报 33%-67%）的问题——
机制层日志 = 100% 可靠的 ground truth。

【日志格式】
TIMESTAMP [info] ccreq:HASH.copilotmd | STATUS | MODEL_REQ -> MODEL_RESOLVED | DURATIONms | [tool/runSubagent-AGENT_NAME]

【用法】
python ccreq_parser.py --last 10                  # 最近 10 条 subagent 调用
python ccreq_parser.py --last 10 --json           # JSON 输出
python ccreq_parser.py --since "2026-04-26 10:00" # 时间窗内
python ccreq_parser.py --agent reviewer           # 仅指定 agent
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

CCREQ_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[info\] "
    r"ccreq:(?P<hash>[a-f0-9]+)\.copilotmd \| "
    r"(?P<status>\w+) \| "
    r"(?P<model_req>[^|]+?) -> (?P<model_resolved>[^|]+?) \| "
    r"(?P<duration>\d+)ms \| "
    r"\[tool/runSubagent-(?P<agent>[\w\-]+)\]"
)


@dataclass
class CcreqRecord:
    timestamp: str
    request_hash: str
    status: str
    model_requested: str
    model_resolved: str
    duration_ms: int
    agent: str


def find_latest_log() -> Path:
    """定位最新的 GitHub Copilot Chat.log 文件。"""
    base = Path(os.environ["APPDATA"]) / "Code" / "logs"
    if not base.exists():
        raise FileNotFoundError(f"VS Code logs root not found: {base}")
    candidates = list(base.rglob("GitHub Copilot Chat.log"))
    if not candidates:
        raise FileNotFoundError("No 'GitHub Copilot Chat.log' found.")
    # 按最后修改时间挑最新
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_log(
    log_path: Path,
    agent_filter: str | None = None,
    since: datetime | None = None,
) -> list[CcreqRecord]:
    records: list[CcreqRecord] = []
    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = CCREQ_RE.search(line)
            if not m:
                continue
            d = m.groupdict()
            if agent_filter and d["agent"] != agent_filter:
                continue
            ts = datetime.strptime(d["ts"][:19], "%Y-%m-%d %H:%M:%S")
            if since and ts < since:
                continue
            records.append(
                CcreqRecord(
                    timestamp=d["ts"],
                    request_hash=d["hash"],
                    status=d["status"],
                    model_requested=d["model_req"].strip(),
                    model_resolved=d["model_resolved"].strip(),
                    duration_ms=int(d["duration"]),
                    agent=d["agent"],
                )
            )
    return records


def render_table(records: list[CcreqRecord]) -> str:
    if not records:
        return "(无匹配记录)"
    rows = [
        f"{r.timestamp[11:19]} | {r.agent:24s} | {r.model_resolved:32s} | "
        f"{r.duration_ms:>6}ms | {r.status}"
        for r in records
    ]
    header = (
        f"{'TIME':8s} | {'AGENT':24s} | {'MODEL_RESOLVED':32s} | "
        f"{'DUR':>8s} | STATUS"
    )
    sep = "-" * len(header)
    return "\n".join([header, sep, *rows])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", type=Path, help="指定日志文件路径（默认自动定位最新）")
    ap.add_argument("--last", type=int, default=10, help="最近 N 条（默认 10）")
    ap.add_argument("--agent", help="仅过滤指定 agent 名")
    ap.add_argument("--since", help="时间窗起点 'YYYY-MM-DD HH:MM'")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式")
    ap.add_argument(
        "--latest-of",
        help="只返回该 agent 最近 1 条的实际模型（短输出，便于 coordinator 取值）",
    )
    args = ap.parse_args()

    log_path = args.log or find_latest_log()
    since = (
        datetime.strptime(args.since, "%Y-%m-%d %H:%M")
        if args.since
        else None
    )

    # --latest-of: 极简模式，直接打印最近一条该 agent 的实际模型
    if args.latest_of:
        records = parse_log(log_path, agent_filter=args.latest_of, since=since)
        if not records:
            print(f"(no record for agent={args.latest_of})")
            return 1
        last = records[-1]
        print(f"{last.agent} -> {last.model_resolved}  ({last.duration_ms}ms, {last.timestamp[11:19]})")
        return 0

    records = parse_log(log_path, agent_filter=args.agent, since=since)
    records = records[-args.last :] if args.last > 0 else records

    if args.json:
        print(json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2))
    else:
        print(f"📁 日志源: {log_path}")
        print(f"🔍 匹配 {len(records)} 条 subagent 调用记录\n")
        print(render_table(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
