"""
共享配置：自动从项目根目录 .env 文件加载 API Key 和模型设置。

用法：
    from config import client, MODEL

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "你好"}]
    )
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 自动查找项目根目录的 .env 文件（从当前文件向上找）
_project_root = Path(__file__).resolve().parent
while _project_root != _project_root.parent:
    if (_project_root / ".env").exists():
        break
    _project_root = _project_root.parent

load_dotenv(_project_root / ".env")

# ━━━ 导出配置 ━━━
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL = os.getenv("MODEL", "qwen-plus")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

if not API_KEY or API_KEY.startswith("sk-你的"):
    print("⚠️  请先编辑项目根目录的 .env 文件，填入你的 DASHSCOPE_API_KEY")
    print(f"   配置文件位置：{_project_root / '.env'}")
