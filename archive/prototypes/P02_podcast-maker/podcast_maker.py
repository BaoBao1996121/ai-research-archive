"""
播客生成器 v2 — 把 Markdown 研究报告转成双人对谈播客音频

v2 改进：
  - 分块生成：长文档按章节拆分，每块独立生成脚本后拼接，信息不丢失
  - 多模型后端：支持 Qwen / OpenAI / Claude / 任意 OpenAI 兼容 API
  - 改进 Prompt：更详细的指令，更高质量的播客脚本
  - 更大输出限制：max_tokens 提升到 8192+

技术栈：LLM API（对话脚本）+ CosyVoice（阿里云语音合成）+ Tkinter GUI
"""

import os
import re
import sys
import threading
import tkinter as tk
import winsound
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path
from datetime import datetime

# ━━━ 项目根目录 & .env 加载 ━━━
_project_root = Path(__file__).resolve().parent.parent.parent

from dotenv import load_dotenv
load_dotenv(_project_root / ".env")

from openai import OpenAI
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

# ━━━ 模型配置预设 ━━━
MODEL_PRESETS = {
    "Qwen-Plus (DashScope)": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "max_tokens": 8192,
    },
    "Qwen-Max (DashScope)": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-max",
        "max_tokens": 8192,
    },
    "Qwen-Long (DashScope)": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-long",
        "max_tokens": 8192,
    },
    "GPT-4o (OpenAI)": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "max_tokens": 16384,
    },
    "自定义 (编辑 .env 中的 CUSTOM_ 前缀)": {
        "api_key_env": "CUSTOM_API_KEY",
        "base_url_env": "CUSTOM_BASE_URL",
        "model_env": "CUSTOM_MODEL",
        "max_tokens": 8192,
    },
}

# CosyVoice 语音合成配置（阿里云 DashScope）
TTS_MODEL = "cosyvoice-v3-flash"  # 性价比最优，1元/万字符
VOICE_HOST = "longanyang"            # 阳光大男孩 - 主持人（标杆音色）
VOICE_GUEST = "longanhuan"           # 欢脱元气女 - 嘉宾（标杆音色）

VOICE_CATALOG = {
    "longanyang": {"name": "龙安洋", "style": "阳光男声"},
    "longcheng_v3": {"name": "龙橙", "style": "智慧青年男"},
    "longtian_v3": {"name": "龙天", "style": "磁性理智男"},
    "longze_v3": {"name": "龙泽", "style": "温暖元气男"},
    "longshuo_v3": {"name": "龙硕", "style": "干练播报男"},
    "longshu_v3": {"name": "龙书", "style": "沉稳青年男"},
    "longsanshu_v3": {"name": "龙三叔", "style": "说书质感男"},
    "longnan_v3": {"name": "龙楠", "style": "睿智青年男"},
    "longanzhi_v3": {"name": "龙安智", "style": "轻熟睿智男"},
    "longanlang_v3": {"name": "龙安朗", "style": "清爽利落男"},
    "longanhuan": {"name": "龙安欢", "style": "元气女声"},
    "longxiaochun_v3": {"name": "龙小淳", "style": "知性积极女"},
    "longanwen_v3": {"name": "龙安温", "style": "优雅知性女"},
    "longanli_v3": {"name": "龙安莉", "style": "利落从容女"},
    "longmiao_v3": {"name": "龙妙", "style": "有声书女声"},
    "longyue_v3": {"name": "龙悦", "style": "温暖磁性女"},
    "longanya_v3": {"name": "龙安雅", "style": "高雅气质女"},
    "longanling_v3": {"name": "龙安灵", "style": "灵动聪慧女"},
    "longwan_v3": {"name": "龙婉", "style": "细腻柔声女"},
}

VOICE_OPTIONS_DUO_HOST = [
    "longanyang",
    "longcheng_v3",
    "longtian_v3",
    "longze_v3",
    "longshuo_v3",
    "longshu_v3",
    "longsanshu_v3",
    "longnan_v3",
    "longanzhi_v3",
    "longanlang_v3",
]

VOICE_OPTIONS_DUO_GUEST = [
    "longanhuan",
    "longxiaochun_v3",
    "longanwen_v3",
    "longanli_v3",
    "longmiao_v3",
    "longyue_v3",
    "longanya_v3",
    "longanling_v3",
    "longwan_v3",
]

VOICE_OPTIONS_ALL = list(dict.fromkeys(VOICE_OPTIONS_DUO_HOST + VOICE_OPTIONS_DUO_GUEST))
VOICE_DISPLAY_TO_ID = {}


def _voice_display(voice_id: str) -> str:
    voice_id = voice_id.strip()
    meta = VOICE_CATALOG.get(voice_id, {"name": voice_id, "style": "默认风格"})
    name = meta["name"].strip()
    style = meta["style"].strip()
    display = f"{name}（{voice_id}） - {style}"
    VOICE_DISPLAY_TO_ID[display] = voice_id
    return display


def _voice_display_list(voice_ids: list[str]) -> list[str]:
    return [_voice_display(voice_id) for voice_id in voice_ids]


def _voice_id_from_value(value: str) -> str:
    return VOICE_DISPLAY_TO_ID.get(value, value)

VOICE_PREVIEW_TEXT = {
    "主持人": "大家好，欢迎收听今天的技术播客。接下来我会用尽量自然、好懂的方式，把复杂问题讲清楚。",
    "嘉宾": "这个话题很有意思。我们不只讲结论，也讲清楚背后的原因、取舍，还有真正落地时会踩的坑。",
}

# 输出目录
OUTPUT_DIR = _project_root / "output" / "podcasts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ━━━ Prompt ━━━

SYSTEM_PROMPT_OPENING = """你是一位顶级播客脚本改编专家。你的任务是把技术文档改编成引人入胜的双人播客对谈脚本。

## 角色设定
- 【主持人】：好奇心强，善于提出好问题，帮听众梳理脉络。会追问"为什么""具体怎么做""有没有例子"。
- 【嘉宾】：深入浅出的技术专家，擅长用类比和例子解释复杂概念。

## 风格要求
- 口语化、自然，像两个老朋友在聊技术，不是在念稿
- 有真实感的互动："对对对""你这个比喻太形象了""等等，我打断一下""说到这个我想到一个有意思的事"
- 嘉宾的回答要有深度和细节，不要蜻蜓点水。一个重要概念要花 3-5 句话讲透
- 主持人适时帮听众总结："所以简单来说就是……"
- 遇到专业术语要解释："这里说的 RAG，全称是 Retrieval-Augmented Generation，通俗理解就是……"
- 不要跳过文档中的关键数据、对比表、代码示例 —— 用口语化方式转述它们

## 输出格式（严格遵守）
每行一段对话，格式如下：
【主持人】对话内容
【嘉宾】对话内容

不要输出任何标题、分隔线、注释或说明文字。只输出【主持人】和【嘉宾】的对话。"""

# ━━━ 单口讲解模式 Prompt ━━━

SYSTEM_PROMPT_SOLO = """你是一位顶级技术播客主播，擅长用口语化风格把复杂的技术文档讲清楚。

## 风格要求
- 像在录一期独白类播客，语气自然、有节奏感，不是在念稿
- 遇到专业术语要解释："这里说的 RAG，全称是 Retrieval-Augmented Generation，通俗理解就是……"
- 用类比和例子帮听众理解抽象概念
- 不要跳过文档中的关键数据、对比表、代码示例 —— 用口语化方式转述
- 适当加入过渡语："好，接下来聊一个更有意思的点……""说到这里你可能会想……""这里划重点……"

## 忠实性铁律（最重要）
- 严禁编造原文中不存在的数据、数字、代码行数、人物、案例
- 如果原文没有具体数字，说"文档中提到"而非编造数字
- 原文有对比表时，逐行讲清楚，不要跳过或模糊概括
- 可以用自己的话重新组织，但信息必须来自原文

## 输出格式（严格遵守）
直接输出讲解正文。不要输出任何标题、分隔线、章节号。
不要用【主持人】【嘉宾】等角色标记。就像你在对着麦克风讲话。"""

SOLO_FIRST_CHUNK = """这是一篇技术文档的【第一部分】。请先用一段精彩的开场白引出今天的话题，然后深入讲解这部分内容。

重要：尽可能详细地覆盖文档中的关键信息、数据、对比、观点。每个核心观点要花几句话讲透，不要蜻蜓点水。
严禁编造原文中没有的具体数据和案例。

文档内容：

{content}"""

SOLO_MIDDLE_CHUNK = """这是同一篇文档的【后续部分】。请延续之前的讲解，继续讲解以下新内容。

要求：
- 用自然的过渡衔接（"好，接下来……""说完这个，我们来看……"）
- 不要重新开场，不要重复之前已经讲过的内容
- 尽可能详细覆盖这部分的关键信息
- 严禁编造原文中没有的数据和案例

文档内容：

{content}"""

SOLO_LAST_CHUNK = """这是文档的【最后一部分】。请讲完这部分内容后，做一个收尾总结。

收尾要求：
- 先正常讲解这部分内容
- 讲完后做一个 3-5 句话的核心要点回顾
- 用一句话收尾，给听众一个思考方向
- 严禁编造原文中没有的数据和案例

文档内容：

{content}"""

SOLO_SINGLE = """请把以下完整文档改编为播客独白讲解。

要求：
- 精彩的开场白引出话题
- 深入讲解文档的核心内容，每个重要概念要花几句话讲透
- 不要跳过关键数据、对比表、具体数字
- 充分覆盖文档内容
- 收尾总结核心要点
- 严禁编造原文中没有的具体数据和案例

文档内容：

{content}"""

PROMPT_FIRST_CHUNK = """这是一篇技术文档的【第一部分】。请先写一个精彩的开场白（主持人介绍今天的话题和嘉宾），然后深入讨论这部分内容。

重要：尽可能详细地覆盖文档中的关键信息、数据、对比、观点。不要只讲大概，要把有价值的细节讲出来。每个核心观点至少花 3-5 轮对话讲透。

文档内容：

{content}"""

PROMPT_MIDDLE_CHUNK = """这是同一篇文档的【后续部分】。请延续之前的对话，继续讨论以下新内容。

要求：
- 用自然的过渡衔接（如"接下来我们聊聊……""那说到这个……""还有一个很关键的点"）
- 不要重新开场，不要重复之前已经讲过的内容
- 尽可能详细覆盖这部分的关键信息，不要跳过数据和具体例子
- 保持相同的口语化对话风格

文档内容：

{content}"""

PROMPT_LAST_CHUNK = """这是文档的【最后一部分】。请讨论完这部分内容后，做一个精彩的收尾。

收尾要求：
- 先正常讨论这部分的内容（不要急着结束）
- 讨论完后，嘉宾做一个 3-5 句话的核心要点总结
- 主持人做简短的 wrap-up 和结束语

文档内容：

{content}"""

PROMPT_SINGLE = """请把以下完整文档改编为播客对话脚本。

要求：
- 精彩的开场白（主持人引出话题）
- 深入讨论文档的核心内容，每个重要概念花 3-5 轮对话讲透
- 不要跳过关键数据、对比表、具体数字 —— 用口语化方式讲出来
- 至少 30 轮对话，充分覆盖文档内容
- 精彩的结尾总结

文档内容：

{content}"""


# ━━━ 核心逻辑 ━━━

def read_markdown(filepath: str) -> str:
    """读取 Markdown 文件内容"""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def split_by_sections(text: str, max_chunk_chars: int = 8000) -> list[str]:
    """按 Markdown 标题拆分文档为多块，每块不超过 max_chunk_chars"""
    # 按一级/二级标题拆分
    sections = re.split(r'\n(?=##?\s)', text)

    chunks = []
    current_chunk = ""

    for section in sections:
        if len(current_chunk) + len(section) <= max_chunk_chars:
            current_chunk += section
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            # 单个 section 超限时按段落再拆
            if len(section) > max_chunk_chars:
                paragraphs = section.split("\n\n")
                sub_chunk = ""
                for para in paragraphs:
                    if len(sub_chunk) + len(para) <= max_chunk_chars:
                        sub_chunk += para + "\n\n"
                    else:
                        if sub_chunk.strip():
                            chunks.append(sub_chunk.strip())
                        sub_chunk = para + "\n\n"
                if sub_chunk.strip():
                    chunks.append(sub_chunk.strip())
                current_chunk = ""
            else:
                current_chunk = section

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def create_llm_client(preset_name: str) -> tuple:
    """根据预设创建 LLM 客户端，返回 (client, model_name, max_tokens)"""
    cfg = MODEL_PRESETS.get(preset_name, MODEL_PRESETS["Qwen-Plus (DashScope)"])

    # 支持从 env 读 base_url 和 model（自定义模式）
    api_key = os.getenv(cfg.get("api_key_env", ""), "")
    base_url = os.getenv(cfg.get("base_url_env", ""), cfg.get("base_url", ""))
    model = os.getenv(cfg.get("model_env", ""), cfg.get("model", ""))

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model, cfg.get("max_tokens", 8192)


# ━━━ Prompt 路由表 ━━━
_PROMPT_ROUTES = {
    "duo": {
        "system": SYSTEM_PROMPT_OPENING,
        "single": PROMPT_SINGLE,
        "first": PROMPT_FIRST_CHUNK,
        "middle": PROMPT_MIDDLE_CHUNK,
        "last": PROMPT_LAST_CHUNK,
    },
    "solo": {
        "system": SYSTEM_PROMPT_SOLO,
        "single": SOLO_SINGLE,
        "first": SOLO_FIRST_CHUNK,
        "middle": SOLO_MIDDLE_CHUNK,
        "last": SOLO_LAST_CHUNK,
    },
}


def generate_script_chunked(
    content: str,
    client: OpenAI,
    model_name: str,
    max_tokens: int = 8192,
    progress_callback=None,
    mode: str = "duo",
) -> str:
    """分块生成播客脚本——长文档按章节分块，逐块生成后拼接"""
    chunks = split_by_sections(content)
    total_chunks = len(chunks)
    prompts = _PROMPT_ROUTES.get(mode, _PROMPT_ROUTES["duo"])

    if progress_callback:
        mode_label = "双人对谈" if mode == "duo" else "单口讲解"
        progress_callback(f"  文档拆分为 {total_chunks} 个分块（{mode_label}模式）")

    all_scripts = []
    total_input_tokens = 0
    total_output_tokens = 0

    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(f"  生成脚本 [{i+1}/{total_chunks}]（{len(chunk)} 字符）...")

        # 根据位置选择不同的 prompt
        if total_chunks == 1:
            user_prompt = prompts["single"].format(content=chunk)
        elif i == 0:
            user_prompt = prompts["first"].format(content=chunk)
        elif i == total_chunks - 1:
            user_prompt = prompts["last"].format(content=chunk)
        else:
            user_prompt = prompts["middle"].format(content=chunk)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )

        script_part = response.choices[0].message.content
        all_scripts.append(script_part)

        if response.usage:
            total_input_tokens += response.usage.prompt_tokens
            total_output_tokens += response.usage.completion_tokens

    if progress_callback:
        progress_callback(
            f"  脚本生成完成！Token：输入 {total_input_tokens} + 输出 {total_output_tokens} = {total_input_tokens + total_output_tokens}"
        )

    return "\n".join(all_scripts)


def parse_script(script: str, mode: str = "duo") -> list[dict]:
    """解析脚本为 [{role, text}, ...] 列表"""
    if mode == "solo":
        return _parse_solo_script(script)
    return _parse_duo_script(script)


def _parse_duo_script(script: str) -> list[dict]:
    """解析双人对谈脚本"""
    lines = []
    pattern = re.compile(r"【(主持人|嘉宾)】(.+)")

    current_role = None
    current_text = ""

    for line in script.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            if current_role and current_text:
                lines.append({"role": current_role, "text": current_text.strip()})
            current_role = m.group(1)
            current_text = m.group(2).strip()
        elif current_role:
            current_text += " " + line

    if current_role and current_text:
        lines.append({"role": current_role, "text": current_text.strip()})

    return lines


def _parse_solo_script(script: str) -> list[dict]:
    """解析单口讲解脚本——按段落拆分，全部标记为主持人"""
    paragraphs = re.split(r'\n{2,}', script.strip())
    lines = []
    for p in paragraphs:
        text = p.strip()
        # 跳过纯标题行或空行
        if not text or re.match(r'^#{1,3}\s', text):
            continue
        # 去掉可能残留的角色标记
        text = re.sub(r'^【[^】]+】', '', text).strip()
        if text:
            lines.append({"role": "主持人", "text": text})
    return lines


def _clean_tts_text(text: str) -> str:
    """清理文本中不适合 TTS 合成的字符"""
    # 去掉 markdown 格式符号
    text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text)  # **bold** / *italic*
    text = re.sub(r'`{1,3}(.+?)`{1,3}', r'\1', text)    # `code`
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)      # [link](url)
    # 去掉 XML/HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 连续空白合并
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _split_tts_text(text: str, max_chars: int = 5000) -> list[str]:
    """把长文本按句子边界拆分为 TTS 友好的小段（CosyVoice 支持 20000 字符/次）"""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    # 按中文句号、感叹号、问号、分号、省略号拆分
    sentences = re.split(r'(?<=[。！？；…\.\!\?])', text)
    current = ""
    for s in sentences:
        if not s.strip():
            continue
        if len(current) + len(s) <= max_chars:
            current += s
        else:
            if current.strip():
                chunks.append(current.strip())
            current = s
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_chars]]


def synthesize_audio(dialogues: list[dict], output_path: str,
                     host_voice: str, guest_voice: str,
                     progress_callback=None):
    """用 CosyVoice 把对话列表合成为音频文件"""
    temp_dir = Path(output_path).parent / "_temp_segments"
    temp_dir.mkdir(exist_ok=True)

    segment_files = []
    total = len(dialogues)
    seg_idx = 0

    for i, d in enumerate(dialogues):
        text = _clean_tts_text(d["text"])
        if not text:
            continue

        voice = host_voice if d["role"] == "主持人" else guest_voice
        sub_texts = _split_tts_text(text)

        if progress_callback:
            suffix = f"（拆为 {len(sub_texts)} 段）" if len(sub_texts) > 1 else ""
            progress_callback(f"  合成语音 [{i+1}/{total}]：{d['role']} - {text[:30]}...{suffix}")

        for sub in sub_texts:
            seg_path = str(temp_dir / f"seg_{seg_idx:04d}.mp3")
            try:
                # CosyVoice 非流式调用：每次必须新建 SpeechSynthesizer 实例
                synthesizer = SpeechSynthesizer(
                    model=TTS_MODEL,
                    voice=voice,
                )
                audio_data = synthesizer.call(sub)
                if audio_data and len(audio_data) > 0:
                    with open(seg_path, "wb") as f:
                        f.write(audio_data)
                    segment_files.append(seg_path)
                else:
                    if progress_callback:
                        progress_callback(f"    ⚠️ 片段合成返回空数据（跳过）")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"    ⚠️ 片段合成失败（跳过）：{str(e)[:80]}")
            seg_idx += 1

    if progress_callback:
        progress_callback("  正在拼接音频片段...")

    with open(output_path, "wb") as outfile:
        for seg in segment_files:
            with open(seg, "rb") as infile:
                outfile.write(infile.read())

    for seg in segment_files:
        os.remove(seg)
    try:
        temp_dir.rmdir()
    except OSError:
        pass

    if progress_callback:
        progress_callback(f"  🎧 音频已保存：{Path(output_path).name}")


# ━━━ GUI ━━━

class PodcastMakerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("📻 播客生成器 v2 — 分块生成 + 多模型后端")
        self.root.geometry("950x750")
        self.root.configure(bg="#f5f5f5")

        self.selected_files: list[str] = []
        self._stop_requested = False
        self._preview_file_path: Path | None = None
        self._preview_is_playing = False
        self._preview_is_generating = False
        self._preview_active_role: str | None = None
        self._preview_active_value: str | None = None
        self._build_ui()

    def _build_ui(self):
        # ━━━ 顶部：文件选择区 ━━━
        top_frame = ttk.LabelFrame(self.root, text="📂 选择要转换的文档", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="添加文件...", command=self._add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="添加 reports/ 全部", command=self._add_reports_dir).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="移除选中", command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空列表", command=self._clear_files).pack(side=tk.LEFT, padx=(0, 5))

        list_frame = ttk.Frame(top_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.file_listbox = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED, height=6,
            font=("Consolas", 10), bg="white"
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ━━━ 中间：设置区 ━━━
        mid_frame = ttk.LabelFrame(self.root, text="⚙️ 转换设置", padding=10)
        mid_frame.pack(fill=tk.X, padx=10, pady=5)

        settings_grid = ttk.Frame(mid_frame)
        settings_grid.pack(fill=tk.X)

        # Row 0: 模型选择
        ttk.Label(settings_grid, text="LLM 模型：").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.model_preset_var = tk.StringVar(value="Qwen-Plus (DashScope)")
        model_combo = ttk.Combobox(
            settings_grid, textvariable=self.model_preset_var, width=35,
            values=list(MODEL_PRESETS.keys()), state="readonly"
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        model_combo.bind("<<ComboboxSelected>>", self._on_model_changed)

        self.api_status_label = ttk.Label(settings_grid, text="", foreground="green")
        self.api_status_label.grid(row=0, column=2, columnspan=2, sticky=tk.W)
        self._update_api_status()

        # Row 1: 播客模式
        ttk.Label(settings_grid, text="播客模式：").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.podcast_mode_var = tk.StringVar(value="duo")
        mode_combo = ttk.Combobox(
            settings_grid, textvariable=self.podcast_mode_var, width=35,
            values=["duo", "solo"], state="readonly"
        )
        mode_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))

        self.mode_desc_label = ttk.Label(settings_grid, text="双人对谈（主持人+嘉宾）", foreground="#555")
        self.mode_desc_label.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
        mode_combo.bind("<<ComboboxSelected>>", self._on_mode_changed)

        # Row 2: 声音
        ttk.Label(settings_grid, text="主持人声音：").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.host_voice_var = tk.StringVar(value=VOICE_HOST)
        self.host_voice_combo = ttk.Combobox(
            settings_grid,
            textvariable=self.host_voice_var,
            width=35,
            values=_voice_display_list(VOICE_OPTIONS_DUO_HOST),
            state="readonly",
        )
        self.host_voice_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.host_preview_btn = ttk.Button(
            settings_grid,
            text="试听主持人",
            command=lambda: self._start_voice_preview("主持人"),
        )
        self.host_preview_btn.grid(row=3, column=1, sticky=tk.W, pady=(4, 0))

        ttk.Label(settings_grid, text="嘉宾声音：").grid(row=2, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.guest_voice_var = tk.StringVar(value=VOICE_GUEST)
        self.guest_voice_combo = ttk.Combobox(
            settings_grid,
            textvariable=self.guest_voice_var,
            width=25,
            values=_voice_display_list(VOICE_OPTIONS_DUO_GUEST),
            state="readonly",
        )
        self.guest_voice_combo.grid(row=2, column=3, sticky=tk.W, pady=(5, 0))
        self.guest_preview_btn = ttk.Button(
            settings_grid,
            text="试听嘉宾",
            command=lambda: self._start_voice_preview("嘉宾"),
        )
        self.guest_preview_btn.grid(row=3, column=3, sticky=tk.W, pady=(4, 0))
        self.preview_status_label = ttk.Label(settings_grid, text="未试听", foreground="#666")
        self.preview_status_label.grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=(4, 0))

        self.host_voice_var.set(_voice_display(VOICE_HOST))
        self.guest_voice_var.set(_voice_display(VOICE_GUEST))

        # Row 2: 选项
        opt_frame = ttk.Frame(mid_frame)
        opt_frame.pack(fill=tk.X, pady=(8, 0))

        self.script_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="仅生成脚本（不合成音频）",
                        variable=self.script_only_var).pack(side=tk.LEFT, padx=(0, 20))

        self.longform_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="长文分块生成（推荐，保留更多内容）",
                        variable=self.longform_var).pack(side=tk.LEFT)

        # ━━━ 按钮区 ━━━
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.convert_btn = ttk.Button(action_frame, text="🎙️ 开始转换", command=self._start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(action_frame, text="⏹️ 停止", command=self._request_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(action_frame, text="📁 打开输出目录", command=self._open_output_dir).pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(action_frame, variable=self.progress_var,
                        maximum=100, length=300).pack(side=tk.RIGHT, padx=(10, 0))

        # ━━━ 底部：日志区 ━━━
        log_frame = ttk.LabelFrame(self.root, text="📋 转换日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=14, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self._on_mode_changed()

    # ━━━ 文件操作 ━━━

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="选择 Markdown 文件",
            initialdir=str(_project_root / "reports"),
            filetypes=[("Markdown 文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                self.file_listbox.insert(tk.END, Path(f).name)

    def _add_reports_dir(self):
        reports_dir = _project_root / "reports"
        if not reports_dir.exists():
            self._log("⚠️ reports/ 目录不存在")
            return
        count = 0
        for f in sorted(reports_dir.glob("*.md")):
            fp = str(f)
            if fp not in self.selected_files:
                self.selected_files.append(fp)
                self.file_listbox.insert(tk.END, f.name)
                count += 1
        self._log(f"已添加 {count} 个报告文件")

    def _remove_selected(self):
        for i in reversed(list(self.file_listbox.curselection())):
            self.file_listbox.delete(i)
            self.selected_files.pop(i)

    def _clear_files(self):
        self.selected_files.clear()
        self.file_listbox.delete(0, tk.END)

    def _open_output_dir(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(OUTPUT_DIR))

    def _set_combobox_values(self, combo: ttk.Combobox, values: list[str], current_var: tk.StringVar, default_value: str):
        display_values = _voice_display_list(values)
        combo["values"] = display_values
        current_voice_id = _voice_id_from_value(current_var.get())
        target_value = current_var.get() if current_var.get() in display_values else _voice_display(default_value)
        if current_voice_id in values:
            target_value = _voice_display(current_voice_id)
        current_var.set(target_value)

    def _set_preview_buttons_state(self, enabled: bool):
        if not enabled or self._preview_is_generating:
            self.host_preview_btn.configure(state=tk.DISABLED)
            self.guest_preview_btn.configure(state=tk.DISABLED)
            return

        self.host_preview_btn.configure(state=tk.NORMAL)
        if self.podcast_mode_var.get() == "solo":
            self.guest_preview_btn.configure(state=tk.DISABLED)
        else:
            self.guest_preview_btn.configure(state=tk.NORMAL)

        host_value = self.host_voice_var.get()
        guest_value = self.guest_voice_var.get()
        self.host_preview_btn.configure(
            text="停止主持人试听" if self._preview_is_playing and self._preview_active_role == "主持人" and self._preview_active_value == host_value else "试听主持人"
        )
        self.guest_preview_btn.configure(
            text="停止嘉宾试听" if self._preview_is_playing and self._preview_active_role == "嘉宾" and self._preview_active_value == guest_value else "试听嘉宾"
        )

    def _start_voice_preview(self, role: str):
        preset_name = self.model_preset_var.get()
        cfg = MODEL_PRESETS.get(preset_name, {})
        env_key = cfg.get("api_key_env", "")

        if env_key:
            api_key = os.getenv(env_key, "")
            if not api_key or api_key.startswith("sk-你的"):
                self._log(f"⚠️ 请先在 .env 中配置 {env_key}，再试听音色")
                return

        current_value = self.host_voice_var.get() if role == "主持人" else self.guest_voice_var.get()
        if self._preview_is_playing and self._preview_active_role == role and self._preview_active_value == current_value:
            self._stop_voice_preview()
            return

        if self._preview_is_playing:
            self._stop_voice_preview(log_message=False)

        self._preview_is_generating = True
        self._set_preview_buttons_state(False)
        threading.Thread(target=self._preview_voice, args=(role,), daemon=True).start()

    def _preview_voice(self, role: str):
        try:
            voice_value = self.host_voice_var.get() if role == "主持人" else self.guest_voice_var.get()
            voice = _voice_id_from_value(voice_value)
            preview_text = VOICE_PREVIEW_TEXT.get(role, VOICE_PREVIEW_TEXT["主持人"])
            preview_dir = OUTPUT_DIR / "_previews"
            preview_dir.mkdir(parents=True, exist_ok=True)
            preview_path = preview_dir / f"{voice}_{role}_试听.wav"

            self._log(f"🔊 正在生成{role}音色试听：{voice}")
            self.root.after(0, lambda: self.preview_status_label.configure(text=f"正在生成试听：{voice_value}", foreground="#1d4ed8"))
            synthesizer = SpeechSynthesizer(
                model=TTS_MODEL,
                voice=voice,
                format=AudioFormat.WAV_22050HZ_MONO_16BIT,
            )
            audio_data = synthesizer.call(preview_text)
            if not audio_data:
                raise RuntimeError("试听音频为空")

            with open(preview_path, "wb") as f:
                f.write(audio_data)

            self._preview_file_path = preview_path
            winsound.PlaySound(str(preview_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            self._preview_is_playing = True
            self._preview_active_role = role
            self._preview_active_value = voice_value
            self.root.after(0, lambda: self.preview_status_label.configure(text=f"正在试听：{voice_value}", foreground="#15803d"))
            self._log(f"🎵 已在 GUI 内开始试听：{preview_path.name}")
        except Exception as e:
            self._preview_is_playing = False
            self._preview_active_role = None
            self._preview_active_value = None
            self._log(f"❌ 音色试听失败：{e}")
            self.root.after(0, lambda: self.preview_status_label.configure(text=f"试听失败：{e}", foreground="#b91c1c"))
        finally:
            self._preview_is_generating = False
            self.root.after(0, lambda: self._set_preview_buttons_state(True))

    def _stop_voice_preview(self, log_message: bool = True):
        winsound.PlaySound(None, 0)
        self._preview_is_playing = False
        self._preview_active_role = None
        self._preview_active_value = None
        self.preview_status_label.configure(text="试听已停止", foreground="#666")
        self._set_preview_buttons_state(True)
        if log_message:
            self._log("⏹️ 已停止音色试听")

    # ━━━ 模型 ━━━

    def _on_mode_changed(self, event=None):
        mode = self.podcast_mode_var.get()
        if mode == "solo":
            self.mode_desc_label.configure(text="单口讲解（开放全部音色，男女都可选）")
            self._set_combobox_values(self.host_voice_combo, VOICE_OPTIONS_ALL, self.host_voice_var, VOICE_HOST)
            self.guest_voice_combo.configure(state=tk.DISABLED)
            self.guest_preview_btn.configure(state=tk.DISABLED)
        else:
            self.mode_desc_label.configure(text="双人对谈（主持人+嘉宾）")
            self._set_combobox_values(self.host_voice_combo, VOICE_OPTIONS_DUO_HOST, self.host_voice_var, VOICE_HOST)
            self._set_combobox_values(self.guest_voice_combo, VOICE_OPTIONS_DUO_GUEST, self.guest_voice_var, VOICE_GUEST)
            self.guest_voice_combo.configure(state="readonly")
            self.guest_preview_btn.configure(state=tk.NORMAL)

        self._set_preview_buttons_state(True)

    def _on_model_changed(self, event=None):
        self._update_api_status()

    def _update_api_status(self):
        preset_name = self.model_preset_var.get()
        cfg = MODEL_PRESETS.get(preset_name, {})
        env_key = cfg.get("api_key_env", "")
        if not env_key:
            self.api_status_label.configure(text="⚠️ 请手动配置", foreground="orange")
            return
        api_key = os.getenv(env_key, "")
        if api_key and not api_key.startswith("sk-你的"):
            self.api_status_label.configure(
                text=f"✅ {env_key} 已配置（{api_key[:8]}...）", foreground="green")
        else:
            self.api_status_label.configure(
                text=f"❌ 请在 .env 中设置 {env_key}", foreground="red")

    # ━━━ 转换 ━━━

    def _start_conversion(self):
        selected_indices = self.file_listbox.curselection()
        files = [self.selected_files[i] for i in selected_indices] if selected_indices else list(self.selected_files)

        if not files:
            self._log("⚠️ 请先添加要转换的文件！")
            return

        preset_name = self.model_preset_var.get()
        cfg = MODEL_PRESETS.get(preset_name, {})
        env_key = cfg.get("api_key_env", "")
        if env_key:
            api_key = os.getenv(env_key, "")
            if not api_key or api_key.startswith("sk-你的"):
                self._log(f"⚠️ 请先在 .env 中配置 {env_key}")
                return

        self.convert_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self._stop_requested = False
        self.progress_var.set(0)

        threading.Thread(target=self._convert_files, args=(files,), daemon=True).start()

    def _request_stop(self):
        self._stop_requested = True
        self._log("⏹️ 正在停止...（当前块完成后停止）")

    def _convert_files(self, files: list[str]):
        total = len(files)
        preset_name = self.model_preset_var.get()
        self._log(f"━━━ 开始转换 {total} 个文件 | 模型：{preset_name} ━━━")

        try:
            llm_client, model_name, max_tokens = create_llm_client(preset_name)
        except Exception as e:
            self._log(f"❌ 创建 LLM 客户端失败：{e}")
            self._finish_conversion()
            return

        for idx, filepath in enumerate(files):
            if self._stop_requested:
                self._log("⏹️ 已停止")
                break

            filename = Path(filepath).stem
            self._log(f"\n{'='*50}")
            self._log(f"[{idx+1}/{total}] {filename}")

            try:
                content = read_markdown(filepath)
                self._log(f"  文档长度：{len(content)} 字符")

                podcast_mode = self.podcast_mode_var.get()
                script = generate_script_chunked(
                    content, llm_client, model_name,
                    max_tokens=max_tokens,
                    progress_callback=self._log,
                    mode=podcast_mode,
                )

                mode_suffix = "单口" if podcast_mode == "solo" else "对谈"
                script_path = OUTPUT_DIR / f"{filename}_脚本_{mode_suffix}.txt"
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script)
                self._log(f"  📝 脚本已保存：{script_path.name}")

                dialogues = parse_script(script, mode=podcast_mode)
                self._log(f"  解析出 {len(dialogues)} 段对话")

                if not dialogues:
                    self._log("  ⚠️ 脚本解析失败，跳过音频")
                    continue

                if not self.script_only_var.get():
                    audio_path = str(OUTPUT_DIR / f"{filename}_播客_{mode_suffix}.mp3")
                    synthesize_audio(
                        dialogues, audio_path,
                        host_voice=_voice_id_from_value(self.host_voice_var.get()),
                        guest_voice=_voice_id_from_value(self.guest_voice_var.get()),
                        progress_callback=self._log,
                    )
                else:
                    self._log("  ⏭️ 跳过音频合成（仅脚本模式）")

            except Exception as e:
                self._log(f"  ❌ 出错：{e}")
                import traceback
                self._log(f"  {traceback.format_exc()}")

            progress = (idx + 1) / total * 100
            self.root.after(0, self.progress_var.set, progress)

        self._log(f"\n━━━ 全部完成！输出目录：{OUTPUT_DIR} ━━━")
        self._finish_conversion()

    def _finish_conversion(self):
        self.root.after(0, lambda: self.convert_btn.configure(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_btn.configure(state=tk.DISABLED))

    # ━━━ 日志 ━━━

    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        def _append():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(0, _append)


# ━━━ 入口 ━━━

def main():
    root = tk.Tk()
    PodcastMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
