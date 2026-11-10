from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import time
import traceback
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from viral_lab.main import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "gui"


@dataclass
class Job:
    job_id: str
    config: dict[str, Any]
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    run_id: str | None = None
    run_dir: Path | None = None
    report: dict[str, Any] | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "config": self.config,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "run_id": self.run_id,
            "run_dir": str(self.run_dir) if self.run_dir else None,
            "report": self.report,
            "artifacts": self.artifacts,
            "logs": self.logs[-80:],
            "error": self.error,
        }


class GuiState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jobs: dict[str, Job] = {}

    def create_job(self, config: dict[str, Any]) -> Job:
        job = Job(job_id=f"job_{uuid4().hex[:10]}", config=config)
        with self.lock:
            self.jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self.lock:
            return self.jobs.get(job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        with self.lock:
            jobs = sorted(self.jobs.values(), key=lambda item: item.created_at, reverse=True)
            return [job.to_dict() for job in jobs[:20]]

    def update(self, job: Job, **changes: Any) -> None:
        with self.lock:
            for key, value in changes.items():
                setattr(job, key, value)


STATE = GuiState()


def normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    preset = str(raw.get("preset", "manual"))
    config: dict[str, Any] = {
        "provider": "mock",
        "trend_source": _choice(raw.get("trend_source"), {"mock", "file", "hn", "hackernews"}, "hn"),
        "trend_file": str(raw.get("trend_file") or "config/trends.sample.json"),
        "media_provider": _choice(raw.get("media_provider"), {"dry_run", "template"}, "template"),
        "video_renderer": _choice(raw.get("video_renderer"), {"manifest", "moviepy"}, "moviepy"),
        "max_trends": _clamp_int(raw.get("max_trends"), default=1, minimum=1, maximum=6),
    }

    if preset == "real_api":
        config.update(
            {
                "trend_source": "hn",
                "media_provider": "template",
                "video_renderer": "moviepy",
                "max_trends": _clamp_int(raw.get("max_trends"), default=1, minimum=1, maximum=3),
            }
        )
    elif preset == "local_safety":
        config.update(
            {
                "trend_source": "file",
                "trend_file": str(raw.get("trend_file") or "config/trends.sample.json"),
                "media_provider": "template",
                "video_renderer": "moviepy",
                "max_trends": _clamp_int(raw.get("max_trends"), default=2, minimum=1, maximum=4),
            }
        )
    elif preset == "manifest":
        config.update(
            {
                "trend_source": "mock",
                "media_provider": "dry_run",
                "video_renderer": "manifest",
                "max_trends": _clamp_int(raw.get("max_trends"), default=4, minimum=1, maximum=6),
            }
        )

    return config


def run_artifacts(run_dir: Path) -> dict[str, Any]:
    package_names = [
        "caption.txt",
        "hashtags.txt",
        "publish_checklist.md",
    ]
    return {
        "videos": sorted(path.name for path in run_dir.glob("video_*.mp4")),
        "panels": sorted(path.name for path in run_dir.glob("panel_*.png")),
        "audio": sorted(path.name for path in run_dir.glob("voiceover_*.wav")),
        "package_files": [name for name in package_names if (run_dir / name).exists()],
        "publish_packages": sorted(path.name for path in run_dir.glob("publish_pkg_*.json")),
        "report": "run_report.json" if (run_dir / "run_report.json").exists() else None,
        "event_log": "event_log.jsonl" if (run_dir / "event_log.jsonl").exists() else None,
    }


def start_job(raw_config: dict[str, Any]) -> Job:
    config = normalize_config(raw_config)
    job = STATE.create_job(config)
    thread = threading.Thread(target=_run_job, args=(job,), daemon=True)
    thread.start()
    return job


def _run_job(job: Job) -> None:
    STATE.update(job, status="running", started_at=time.time(), logs=[*job.logs, "Pipeline started."])
    try:
        trend_file = job.config["trend_file"] if job.config["trend_source"] == "file" else None
        result = run_pipeline(
            provider=job.config["provider"],
            trend_source=job.config["trend_source"],
            trend_file=trend_file,
            media_provider=job.config["media_provider"],
            video_renderer=job.config["video_renderer"],
            output_dir=DEFAULT_OUTPUT_DIR,
            max_trends=job.config["max_trends"],
        )
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        artifacts = run_artifacts(result.run_dir)
        logs = [
            *job.logs,
            f"Run complete: {result.run_id}",
            f"Events: {sum(report.get('event_counts', {}).values())}",
        ]
        STATE.update(
            job,
            status="succeeded",
            finished_at=time.time(),
            run_id=result.run_id,
            run_dir=result.run_dir,
            report=report,
            artifacts=artifacts,
            logs=logs,
        )
    except Exception as exc:  # pragma: no cover - surfaced through GUI.
        STATE.update(
            job,
            status="failed",
            finished_at=time.time(),
            error=str(exc),
            logs=[*job.logs, traceback.format_exc()],
        )


class GuiHandler(BaseHTTPRequestHandler):
    server_version = "P08Gui/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_text(HTML_PAGE, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/runs":
            self._send_json({"jobs": STATE.list_jobs()})
            return
        if parsed.path.startswith("/api/jobs/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            job = STATE.get(job_id)
            if not job:
                self._send_json({"error": "job not found"}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(job.to_dict())
            return
        if parsed.path.startswith("/artifacts/"):
            self._send_artifact(parsed.path)
            return
        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8") if length else "{}"
        raw = json.loads(payload or "{}")
        job = start_job(raw)
        self._send_json(job.to_dict(), HTTPStatus.ACCEPTED)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_artifact(self, path: str) -> None:
        _, _, tail = path.partition("/artifacts/")
        job_id, _, filename = tail.partition("/")
        job = STATE.get(job_id)
        if not job or not job.run_dir or not filename:
            self._send_json({"error": "artifact not found"}, HTTPStatus.NOT_FOUND)
            return
        safe_name = Path(filename).name
        artifact_path = (job.run_dir / safe_name).resolve()
        run_dir = job.run_dir.resolve()
        if run_dir not in artifact_path.parents and artifact_path != run_dir:
            self._send_json({"error": "unsafe artifact path"}, HTTPStatus.BAD_REQUEST)
            return
        if not artifact_path.exists() or not artifact_path.is_file():
            self._send_json({"error": "artifact not found"}, HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(artifact_path.name)[0] or "application/octet-stream"
        body = artifact_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), GuiHandler)
    print(f"P08 GUI running at http://{host}:{port}")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the P08 local GUI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    run_server(args.host, args.port)
    return 0


def _choice(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or default)
    return text if text in allowed else default


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


HTML_PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>P08 Agent Lab Console</title>
  <style>
    :root {
      --bg: #f5f7fa;
      --panel: #ffffff;
      --text: #18202f;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #0f766e;
      --accent-2: #7c3aed;
      --danger: #b42318;
      --ok: #027a48;
      --shadow: 0 18px 45px rgba(17, 24, 39, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--text);
      background: var(--bg);
    }
    header {
      height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }
    h1 {
      font-size: 21px;
      margin: 0;
      letter-spacing: 0;
    }
    .subtitle {
      color: var(--muted);
      font-size: 13px;
      margin-top: 3px;
    }
    main {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 18px;
      padding: 18px;
      min-height: calc(100vh - 72px);
    }
    section, aside {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: 8px;
    }
    aside {
      padding: 18px;
      align-self: start;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(320px, 440px) 1fr;
      gap: 18px;
      padding: 18px;
    }
    .stack { display: grid; gap: 14px; }
    .field { display: grid; gap: 6px; }
    label {
      color: #344054;
      font-size: 13px;
      font-weight: 600;
    }
    select, input {
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      font-size: 14px;
      background: #fff;
      color: var(--text);
    }
    .buttons {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      margin: 16px 0;
    }
    button {
      min-height: 40px;
      border: 1px solid transparent;
      border-radius: 6px;
      padding: 0 12px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      color: #fff;
      background: var(--accent);
    }
    button.secondary { background: #334155; }
    button.ghost {
      color: var(--text);
      background: #fff;
      border-color: var(--line);
    }
    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
    }
    .metric strong {
      display: block;
      font-size: 26px;
      margin-bottom: 4px;
    }
    .metric span {
      color: var(--muted);
      font-size: 12px;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #eef2ff;
      color: #3730a3;
      font-size: 13px;
      font-weight: 700;
    }
    .status.succeeded { background: #ecfdf3; color: var(--ok); }
    .status.failed { background: #fef3f2; color: var(--danger); }
    video {
      width: 100%;
      max-height: 72vh;
      background: #0f172a;
      border-radius: 8px;
      border: 1px solid var(--line);
    }
    .empty {
      min-height: 420px;
      display: grid;
      place-items: center;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 30px;
    }
    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .links a {
      text-decoration: none;
      color: #0f766e;
      background: #ecfdf3;
      border: 1px solid #a6f4c5;
      border-radius: 999px;
      padding: 7px 10px;
      font-size: 13px;
      font-weight: 700;
    }
    pre {
      max-height: 260px;
      overflow: auto;
      background: #111827;
      color: #e5e7eb;
      padding: 14px;
      border-radius: 8px;
      font-size: 12px;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    h2 {
      font-size: 16px;
      margin: 0 0 12px;
    }
    .note {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }
    @media (max-width: 980px) {
      main, .workspace { grid-template-columns: 1fr; }
      header { height: auto; padding: 16px; align-items: flex-start; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>P08 Agent Lab Console</h1>
      <div class="subtitle">真实 API 选题 · 多 Agent 编排 · 视频发布包生成</div>
    </div>
    <div id="status" class="status">Idle</div>
  </header>
  <main>
    <aside>
      <h2>运行配置</h2>
      <div class="stack">
        <div class="field">
          <label for="trendSource">选题来源</label>
          <select id="trendSource">
            <option value="hn">Hacker News 真实 API</option>
            <option value="file">本地样例文件</option>
            <option value="mock">内置 mock 数据</option>
          </select>
        </div>
        <div class="field">
          <label for="maxTrends">选题数量</label>
          <input id="maxTrends" type="number" min="1" max="6" value="1" />
        </div>
        <div class="field">
          <label for="mediaProvider">媒体生成</label>
          <select id="mediaProvider">
            <option value="template">模板图片 + 占位音频</option>
            <option value="dry_run">仅生成 prompt JSON</option>
          </select>
        </div>
        <div class="field">
          <label for="videoRenderer">视频渲染</label>
          <select id="videoRenderer">
            <option value="moviepy">生成 MP4</option>
            <option value="manifest">仅生成 manifest</option>
          </select>
        </div>
        <div class="field">
          <label for="trendFile">本地样例文件</label>
          <input id="trendFile" value="config/trends.sample.json" />
        </div>
      </div>
      <div class="buttons">
        <button onclick="runPreset('real_api')">运行真实 API 成片</button>
        <button class="secondary" onclick="runPreset('local_safety')">运行本地安全演示</button>
        <button class="ghost" onclick="runPreset('manifest')">快速生成 Manifest</button>
        <button class="ghost" onclick="runManual()">按当前配置运行</button>
      </div>
      <p class="note">真实 API 按钮会访问 Hacker News 官方 Firebase API。系统仍只生成 dry-run 发布包，不会真实发布到任何平台。</p>
    </aside>
    <section class="workspace">
      <div class="stack">
        <div>
          <h2>运行概览</h2>
          <div class="metric-grid" id="metrics"></div>
        </div>
        <div>
          <h2>产物文件</h2>
          <div class="links" id="links"></div>
        </div>
        <div>
          <h2>事件日志</h2>
          <pre id="logs">点击左侧按钮开始运行。</pre>
        </div>
      </div>
      <div class="stack">
        <h2>视频预览</h2>
        <div id="preview" class="empty">生成 MP4 后会在这里显示。</div>
        <h2>报告 JSON</h2>
        <pre id="report">{}</pre>
      </div>
    </section>
  </main>
  <script>
    let activeJob = null;
    let poller = null;

    function manualConfig() {
      return {
        trend_source: document.getElementById('trendSource').value,
        max_trends: document.getElementById('maxTrends').value,
        media_provider: document.getElementById('mediaProvider').value,
        video_renderer: document.getElementById('videoRenderer').value,
        trend_file: document.getElementById('trendFile').value
      };
    }

    function runPreset(preset) {
      const config = manualConfig();
      config.preset = preset;
      startRun(config);
    }

    function runManual() {
      const config = manualConfig();
      config.preset = 'manual';
      startRun(config);
    }

    async function startRun(config) {
      setBusy(true);
      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const job = await response.json();
      activeJob = job.job_id;
      renderJob(job);
      if (poller) clearInterval(poller);
      poller = setInterval(refreshJob, 1200);
      refreshJob();
    }

    async function refreshJob() {
      if (!activeJob) return;
      const response = await fetch(`/api/jobs/${activeJob}`);
      const job = await response.json();
      renderJob(job);
      if (job.status === 'succeeded' || job.status === 'failed') {
        clearInterval(poller);
        setBusy(false);
      }
    }

    function renderJob(job) {
      const status = document.getElementById('status');
      status.textContent = job.status || 'Idle';
      status.className = `status ${job.status || ''}`;

      const counts = (job.report && job.report.event_counts) || {};
      document.getElementById('metrics').innerHTML = [
        metric('Events', Object.values(counts).reduce((a, b) => a + b, 0)),
        metric('Trends', counts.TrendDetected || 0),
        metric('Rejected', counts.RiskRejected || 0),
        metric('Published', counts.PublicationDryRun || 0)
      ].join('');

      document.getElementById('logs').textContent = (job.logs || []).join('\n') || '运行中...';
      document.getElementById('report').textContent = JSON.stringify(job.report || job, null, 2);
      renderLinks(job);
      renderPreview(job);
    }

    function metric(label, value) {
      return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`;
    }

    function renderLinks(job) {
      const links = [];
      const add = (name, label) => links.push(`<a href="/artifacts/${job.job_id}/${name}" target="_blank">${label}</a>`);
      const artifacts = job.artifacts || {};
      (artifacts.videos || []).forEach((name, index) => add(name, `视频 ${index + 1}`));
      if (artifacts.report) add(artifacts.report, '运行报告');
      if (artifacts.event_log) add(artifacts.event_log, '事件日志');
      (artifacts.package_files || []).forEach(name => add(name, name));
      (artifacts.panels || []).slice(0, 3).forEach((name, index) => add(name, `分镜 ${index + 1}`));
      document.getElementById('links').innerHTML = links.join('') || '<span class="note">暂无产物</span>';
    }

    function renderPreview(job) {
      const videos = (job.artifacts && job.artifacts.videos) || [];
      const preview = document.getElementById('preview');
      if (videos.length) {
        preview.className = '';
        preview.innerHTML = `<video controls src="/artifacts/${job.job_id}/${videos[0]}"></video>`;
      } else {
        preview.className = 'empty';
        preview.textContent = '生成 MP4 后会在这里显示。';
      }
    }

    function setBusy(isBusy) {
      document.querySelectorAll('button').forEach(button => button.disabled = isBusy);
    }
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
