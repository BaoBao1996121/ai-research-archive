$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pip install pillow imageio imageio-ffmpeg pytest
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m viral_lab.main --provider mock --trend-source hn --media-provider template --video-renderer moviepy --max-trends 1
