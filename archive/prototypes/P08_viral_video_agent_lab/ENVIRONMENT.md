> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# P08 Environment Checklist

Date: 2026-06-24

## Current Status

- Python: 3.13.1, verified with `python --version`.
- Existing project files: `README.md`, `VALIDATION.md`, `PRODUCTION_GUIDE.md`, historical `output/` artifacts.
- Empty/missing implementation areas before this session: `src/viral_lab/`, `tests/`, `config/`, `scripts/`.
- Available global packages before local install:
  - `PIL`: available.
  - `numpy`: available.
  - `pytest`: missing.
  - `moviepy`: missing.

## External Dependencies

| Dependency | Purpose | Verification |
|---|---|---|
| Python 3.13 | Runtime | Verified locally |
| Pillow | Template comic card rendering | Verified locally |
| imageio + imageio-ffmpeg | MP4 encoding fallback | To be installed in project venv |
| pytest | Regression tests | To be installed in project venv |
| OpenAI API | Optional live provider | Not required for demo; not verified |

## Demo Strategy

The immediate target is a no-key template demo:

```powershell
python -m viral_lab.main --provider mock --trend-source file --trend-file config\trends.sample.json --media-provider template --video-renderer moviepy --max-trends 1
```

This should produce a real MP4, `run_report.json`, and `event_log.jsonl` without calling external APIs.
