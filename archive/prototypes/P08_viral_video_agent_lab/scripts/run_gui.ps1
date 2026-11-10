$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pip install pillow imageio imageio-ffmpeg pytest
.\.venv\Scripts\python.exe -m viral_lab.gui --host 127.0.0.1 --port 8787
