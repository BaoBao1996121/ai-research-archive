"""
doc2oral.py — 技术文档 → 口播文本转换器

用法：
  python doc2oral.py <markdown文件>                    # 默认 Qwen-Plus
  python doc2oral.py <markdown文件> --model qwen-max   # 指定模型
  python doc2oral.py <markdown文件> --batch             # 批量模式（处理同目录所有 .md）
  python doc2oral.py reports/                          # 处理整个目录

输出：在 output/oral/ 目录下生成同名 .txt 文件

依赖：pip install openai python-dotenv
配置：设置环境变量 DASHSCOPE_API_KEY 或在脚本同级目录放 .env 文件
"""

import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# ━━━ 加载配置 ━━━
# 依次查找：脚本同级 .env → 工作区根 .env → 环境变量
_script_dir = Path(__file__).resolve().parent
for env_path in [_script_dir / ".env", _script_dir.parent / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        break

# ━━━ 模型预设 ━━━
MODEL_PRESETS = {
    "qwen-plus": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "max_tokens": 8192,
    },
    "qwen-max": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-max",
        "max_tokens": 8192,
    },
    "qwen-long": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-long",
        "max_tokens": 8192,
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "max_tokens": 8192,
    },
    "gpt-4o": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "max_tokens": 16384,
    },
}

# ━━━ 输出目录 ━━━
OUTPUT_DIR = _script_dir.parent / "output" / "oral"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ━━━ Prompt 工程 ━━━

SYSTEM_PROMPT = """你是一位资深技术播客主播，正在录制一期让人通勤路上听的技术播客。

## 你的任务
把技术文档改写成适合耳朵听的口播文本。改写后的文本会被听书软件朗读，所以必须是纯粹的、自然的说话体。

## 改写铁律（按优先级排序）

### 1. 信息零丢失
- 原文的每个核心观点、数据、对比、结论都必须保留
- 数字和百分比原样保留，用口语包裹："延迟从 100 毫秒降到了 30 毫秒，整整快了三倍"
- 表格逐行转述为对比句式，不可跳过或笼统概括
- 代码逻辑转述为意图描述，不念代码本身

### 2. 严禁编造
- 不可编造原文中没有的数据、案例、人名
- 原文没有具体数字就说"文档提到"，不要凑数字
- 不确定的信息用"根据文档的说法"包裹

### 3. 听觉友好
- 去掉所有 Markdown 格式（标题符号、加粗、链接、代码块）
- 不要出现括号补充（听众没法"看到括号里的内容"），改成自然的插入语
- 不要说"如图所示""见下表""第 3.2 节"——听众看不到
- 专业术语首次出现时用大白话解释一遍
- 英文缩写要读全称再解释："RAG，全称 Retrieval Augmented Generation，就是让 AI 先去搜资料再回答的技术"

### 4. 节奏与结构
- 每讲完一个概念，用一句话收束，再过渡到下一个
- 用自然过渡而不是"第一点、第二点"的机械结构
- 适当加入："这里划重点""说到这个很有意思""你可能会好奇""换个角度想"
- 段落之间留出呼吸感，不要一口气堆砌信息
- 重要结论可以重复一遍加深印象

### 5. 不要做的事
- 不要加"大家好欢迎收听""让我们一起来学习吧"这种套话
- 不要堆砌感叹号
- 不要为了口语化而把信息稀释成废话
- 不要在结尾说"感谢收听"——你不知道这是不是最后一段

## 输出格式
直接输出改写后的口播文本。不要输出标题、分隔线、章节号、注释。
纯粹的、可以直接被听书软件朗读的文字。"""

PROMPT_FIRST = """这是一篇技术文档的【开头部分】。
用一两句话自然地引出今天要聊的话题（不要"大家好"式的开场），然后深入讲解这部分内容。

要求：详细覆盖所有关键信息，每个核心观点花几句话讲透。

---
{content}"""

PROMPT_MIDDLE = """这是同一篇文档的【中间部分】。延续之前的讲解节奏，继续讲。

要求：
- 用自然过渡衔接，不要重新开场
- 不要重复之前已讲过的内容
- 详细覆盖这部分的关键信息

---
{content}"""

PROMPT_LAST = """这是文档的【最后部分】。讲完这部分后做一个简短的要点回顾。

要求：
- 先正常讲这部分内容
- 讲完后用 3-5 句话回顾全文核心要点
- 最后一句给听众一个思考方向或行动建议

---
{content}"""

PROMPT_SINGLE = """把以下完整文档改写为口播文本。

要求：
- 自然引出话题
- 深入讲解核心内容，每个重要概念花几句话讲透
- 保留所有关键数据和对比
- 结尾回顾核心要点

---
{content}"""


# ━━━ 文档预处理 ━━━

def preprocess_markdown(text: str) -> str:
    """清理 Markdown 中不适合口播的元素"""
    # 去掉 YAML frontmatter
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
    # 去掉 Mermaid / 代码块（保留行内代码的文字）
    text = re.sub(r'```mermaid\n.*?```', '[此处原文有流程图，已省略]', text, flags=re.DOTALL)
    text = re.sub(r'```\w*\n.*?```', '[此处原文有代码示例，已省略]', text, flags=re.DOTALL)
    # 去掉图片链接
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # 去掉 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去掉 wikilink 但保留显示文字
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # 保留普通链接的显示文字
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


def split_by_sections(text: str, max_chunk_chars: int = 8000) -> list[str]:
    """按 Markdown 标题拆分文档为多块"""
    sections = re.split(r'\n(?=##?\s)', text)
    chunks = []
    current = ""

    for section in sections:
        if len(current) + len(section) <= max_chunk_chars:
            current += section
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(section) > max_chunk_chars:
                # 超长 section 按段落再拆
                paragraphs = section.split("\n\n")
                sub = ""
                for para in paragraphs:
                    if len(sub) + len(para) <= max_chunk_chars:
                        sub += para + "\n\n"
                    else:
                        if sub.strip():
                            chunks.append(sub.strip())
                        sub = para + "\n\n"
                if sub.strip():
                    chunks.append(sub.strip())
                current = ""
            else:
                current = section

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text]


# ━━━ LLM 调用 ━━━

def create_client(preset: str) -> tuple:
    cfg = MODEL_PRESETS.get(preset)
    if not cfg:
        print(f"未知模型预设: {preset}")
        print(f"可用: {', '.join(MODEL_PRESETS.keys())}")
        sys.exit(1)

    api_key = os.getenv(cfg["api_key_env"], "")
    if not api_key:
        print(f"错误: 环境变量 {cfg['api_key_env']} 未设置")
        print(f"请设置: $env:{cfg['api_key_env']} = 'your-key'")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    return client, cfg["model"], cfg["max_tokens"]


def generate_oral_text(
    content: str,
    client: OpenAI,
    model: str,
    max_tokens: int,
) -> str:
    """分块生成口播文本"""
    cleaned = preprocess_markdown(content)
    chunks = split_by_sections(cleaned)
    total = len(chunks)

    print(f"  文档 {len(content):,} 字 → 预处理后 {len(cleaned):,} 字 → {total} 个分块")

    results = []
    total_in = 0
    total_out = 0

    for i, chunk in enumerate(chunks):
        print(f"  [{i+1}/{total}] 生成中（{len(chunk):,} 字）...", end=" ", flush=True)

        if total == 1:
            user_prompt = PROMPT_SINGLE.format(content=chunk)
        elif i == 0:
            user_prompt = PROMPT_FIRST.format(content=chunk)
        elif i == total - 1:
            user_prompt = PROMPT_LAST.format(content=chunk)
        else:
            user_prompt = PROMPT_MIDDLE.format(content=chunk)

        t0 = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )

        text = resp.choices[0].message.content
        results.append(text)

        elapsed = time.time() - t0
        if resp.usage:
            total_in += resp.usage.prompt_tokens
            total_out += resp.usage.completion_tokens
            print(f"完成 ({elapsed:.1f}s, {resp.usage.completion_tokens} tokens)")
        else:
            print(f"完成 ({elapsed:.1f}s)")

    print(f"  Token 合计: 输入 {total_in:,} + 输出 {total_out:,} = {total_in + total_out:,}")

    return "\n\n".join(results)


# ━━━ 主流程 ━━━

def process_file(filepath: Path, preset: str, client, model, max_tokens) -> Path:
    """处理单个文件，返回输出路径"""
    print(f"\n{'='*60}")
    print(f"处理: {filepath.name}")

    content = filepath.read_text(encoding="utf-8")
    oral_text = generate_oral_text(content, client, model, max_tokens)

    # 输出文件名: 原名去掉 R数字_ 前缀，加 _口播 后缀
    stem = filepath.stem
    out_name = f"{stem}_口播.txt"
    out_path = OUTPUT_DIR / out_name

    # 写入头部信息 + 正文
    header = (
        f"# {stem} — 口播版\n"
        f"# 原文: {filepath.name}\n"
        f"# 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 模型: {model}\n"
        f"# 字数: 原文 {len(content):,} → 口播 {len(oral_text):,}\n"
        f"{'='*60}\n\n"
    )
    out_path.write_text(header + oral_text, encoding="utf-8")

    print(f"  输出: {out_path}")
    print(f"  字数: {len(content):,} → {len(oral_text):,} (比例 {len(oral_text)/max(len(content),1):.1%})")

    return out_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="技术文档 → 口播文本转换器")
    parser.add_argument("input", help="Markdown 文件或目录")
    parser.add_argument("--model", default="qwen-plus", choices=list(MODEL_PRESETS.keys()),
                        help="LLM 模型预设 (默认 qwen-plus)")
    parser.add_argument("--output", default=None, help="输出目录 (默认 output/oral/)")
    args = parser.parse_args()

    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = Path(args.output)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 收集要处理的文件
    input_path = Path(args.input)
    if input_path.is_dir():
        files = sorted(input_path.glob("*.md"))
        if not files:
            print(f"目录 {input_path} 中没有 .md 文件")
            sys.exit(1)
        print(f"批量模式: 找到 {len(files)} 个 Markdown 文件")
    elif input_path.is_file():
        files = [input_path]
    else:
        print(f"找不到: {input_path}")
        sys.exit(1)

    # 创建 LLM 客户端
    client, model, max_tokens = create_client(args.model)
    print(f"模型: {model}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 逐个处理
    results = []
    for f in files:
        try:
            out = process_file(f, args.model, client, model, max_tokens)
            results.append((f.name, out, "成功"))
        except Exception as e:
            print(f"  错误: {e}")
            results.append((f.name, None, str(e)))

    # 汇总
    print(f"\n{'='*60}")
    print(f"完成! 成功 {sum(1 for _,_,s in results if s=='成功')}/{len(results)}")
    for name, out, status in results:
        mark = "✓" if status == "成功" else "✗"
        print(f"  {mark} {name} → {out.name if out else status}")


if __name__ == "__main__":
    main()
