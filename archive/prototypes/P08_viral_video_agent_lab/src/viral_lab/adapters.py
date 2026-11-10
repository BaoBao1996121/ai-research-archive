from __future__ import annotations

import json
import math
import urllib.request
import wave
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from viral_lab.contracts import new_id
from viral_lab.events import EventLogStore


class TrendSource:
    def fetch(self, max_trends: int) -> list[dict[str, Any]]:
        raise NotImplementedError


class MockTrendSource(TrendSource):
    def fetch(self, max_trends: int) -> list[dict[str, Any]]:
        trends = [
            {
                "id": "trend_ai_office",
                "title": "AI meeting notes went rogue",
                "angle": "Office worker turns a messy meeting into a comedy survival guide.",
                "risk": "low",
            },
            {
                "id": "trend_privacy_leak",
                "title": "A real person's private chat leak",
                "angle": "Sensitive private information should never become content.",
                "risk": "privacy",
            },
            {
                "id": "trend_robot_barista",
                "title": "Robot barista misunderstands latte art",
                "angle": "A robot draws project diagrams on coffee foam.",
                "risk": "low",
            },
            {
                "id": "trend_bug_standup",
                "title": "Daily standup becomes a bug trial",
                "angle": "Every bug gets a lawyer and the PM is the judge.",
                "risk": "low",
            },
        ]
        return trends[:max_trends]


class FileTrendSource(TrendSource):
    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(self, max_trends: int) -> list[dict[str, Any]]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        trends = payload["trends"] if isinstance(payload, dict) else payload
        return list(trends)[:max_trends]


class HackerNewsTrendSource(TrendSource):
    topstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    item_url = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"

    def fetch(self, max_trends: int) -> list[dict[str, Any]]:
        story_ids = _fetch_json(self.topstories_url)
        trends: list[dict[str, Any]] = []
        for story_id in story_ids[: max(10, max_trends * 3)]:
            item = _fetch_json(self.item_url.format(item_id=story_id))
            if not item or item.get("type") != "story" or not item.get("title"):
                continue
            trends.append(
                {
                    "id": f"hn_{item['id']}",
                    "title": item["title"],
                    "angle": _hn_angle(item),
                    "risk": "low",
                    "source": "hacker_news",
                    "source_url": item.get("url") or f"https://news.ycombinator.com/item?id={item['id']}",
                    "score": item.get("score", 0),
                    "by": item.get("by", "unknown"),
                    "comments": item.get("descendants", 0),
                }
            )
            if len(trends) >= max_trends:
                break
        return trends


class MockCreativeProvider:
    def content_plan(self, trend: dict[str, Any]) -> dict[str, Any]:
        return {
            "hook": f"When '{trend['title']}' hits the office group chat...",
            "tone": "playful, safe, original",
            "thesis": trend["angle"],
            "visual_style": "polished vertical comic short, bold subtitles, product-demo finish",
        }

    def storyboard(self, trend: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        panels = [
            {
                "panel": 1,
                "caption": "The trend lands in the team chat.",
                "visual_prompt": f"Open office, laptop alert, headline: {trend['title']}",
            },
            {
                "panel": 2,
                "caption": "The Agent crew turns it into an original skit.",
                "visual_prompt": f"Creative agents remix the idea safely: {plan['thesis']}",
            },
            {
                "panel": 3,
                "caption": "Human review approves the publish package.",
                "visual_prompt": "Checklist, MP4, captions, and dry-run package ready for review.",
            },
        ]
        script = " ".join(
            [
                "A trend comes in.",
                "Risk checks filter unsafe topics.",
                "Small agents create storyboard, art, captions, and voiceover.",
                "The saga waits for every asset before rendering a reviewable MP4.",
            ]
        )
        return {"panels": panels, "voiceover_script": script}

    def caption_package(self, trend: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": "AI Agents Made This Short",
            "caption": (
                f"{plan['hook']} A multi-agent pipeline turned it into an original, "
                "review-ready vertical short."
            ),
            "hashtags": ["#AIAgents", "#MultiAgent", "#ContentAutomation", "#BuildInPublic"],
        }


class MediaFactory:
    def render_panel(self, prompt: str, panel: dict[str, Any], trace_id: str, store: EventLogStore) -> dict[str, Any]:
        raise NotImplementedError

    def render_voiceover(self, script: str, trace_id: str, store: EventLogStore) -> dict[str, Any]:
        raise NotImplementedError


class DryRunMediaFactory(MediaFactory):
    def render_panel(self, prompt: str, panel: dict[str, Any], trace_id: str, store: EventLogStore) -> dict[str, Any]:
        path = store.write_json(f"panel_{panel['panel']}_{trace_id}.json", {"prompt": prompt, "panel": panel})
        return {"type": "prompt", "panel": panel["panel"], "path": str(path), "prompt": prompt}

    def render_voiceover(self, script: str, trace_id: str, store: EventLogStore) -> dict[str, Any]:
        path = store.write_json(f"voiceover_{trace_id}.json", {"script": script})
        return {"type": "voiceover_prompt", "path": str(path), "script": script}


class TemplateMediaFactory(MediaFactory):
    def render_panel(self, prompt: str, panel: dict[str, Any], trace_id: str, store: EventLogStore) -> dict[str, Any]:
        path = store.run_dir / f"panel_{panel['panel']}_{trace_id}.png"
        image = _gradient((720, 1280), "#f7efe3", "#dbeafe")
        draw = ImageDraw.Draw(image)
        panel_no = int(panel["panel"])
        palette = [("#0f766e", "#14b8a6"), ("#7c3aed", "#a855f7"), ("#b45309", "#f59e0b")]
        dark, light = palette[(panel_no - 1) % len(palette)]

        draw.rounded_rectangle((42, 42, 678, 1238), radius=42, fill="#fffaf3", outline="#151515", width=5)
        draw.rounded_rectangle((72, 84, 648, 180), radius=28, fill=dark)
        draw.text((102, 110), f"SCENE 0{panel_no}", fill="white", font=_font(34, bold=True))
        draw.text((445, 116), "P08 AGENT LAB", fill="#ccfbf1", font=_font(20, bold=True))

        _draw_scene_illustration(draw, panel_no, dark, light)

        draw.rounded_rectangle((74, 805, 646, 1040), radius=30, fill="#111827")
        _draw_wrapped_text(draw, (108, 836), panel["caption"], _font(44, bold=True), "#ffffff", 480, 12)
        draw.rounded_rectangle((74, 1068, 646, 1190), radius=24, fill="#f8fafc", outline="#d1d5db", width=2)
        _draw_wrapped_text(draw, (104, 1095), prompt, _font(24), "#334155", 500, 8)
        image.save(path)
        return {
            "type": "image",
            "panel": panel["panel"],
            "path": str(path),
            "prompt": prompt,
            "caption": panel["caption"],
        }

    def render_voiceover(self, script: str, trace_id: str, store: EventLogStore) -> dict[str, Any]:
        path = store.run_dir / f"voiceover_{trace_id}.wav"
        sample_rate = 22050
        seconds = max(6, min(12, math.ceil(len(script) / 24)))
        t = np.linspace(0, seconds, sample_rate * seconds, endpoint=False)
        tone = 0.12 * np.sin(2 * np.pi * 220 * t) + 0.05 * np.sin(2 * np.pi * 330 * t)
        envelope = np.linspace(0.2, 1.0, sample_rate * seconds)
        samples = (tone * envelope * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            handle.writeframes(samples.tobytes())
        return {"type": "audio", "path": str(path), "script": script, "duration_seconds": seconds}


class VideoRenderer:
    def render(self, bundle: dict[str, Any], trace_id: str, store: EventLogStore) -> dict[str, Any]:
        raise NotImplementedError


class ManifestVideoRenderer(VideoRenderer):
    def render(self, bundle: dict[str, Any], trace_id: str, store: EventLogStore) -> dict[str, Any]:
        path = store.write_json(f"video_manifest_{trace_id}.json", bundle)
        return {"type": "manifest", "path": str(path)}


class ImageioVideoRenderer(VideoRenderer):
    def render(self, bundle: dict[str, Any], trace_id: str, store: EventLogStore) -> dict[str, Any]:
        image_assets = [asset for asset in bundle["comic"]["assets"] if asset["type"] == "image"]
        if not image_assets:
            return ManifestVideoRenderer().render(bundle, trace_id, store)

        frames: list[np.ndarray] = []
        fps = 18
        caption = bundle["caption"]
        frames.extend(_scene_frames(_title_card(caption), fps * 2))

        for index, asset in enumerate(image_assets, start=1):
            panel_image = Image.open(asset["path"]).convert("RGB")
            for step in range(fps * 3):
                progress = step / max(1, fps * 3 - 1)
                frame = _compose_video_frame(
                    panel_image,
                    title=caption["title"],
                    subtitle=asset.get("caption", ""),
                    scene_index=index,
                    scene_count=len(image_assets),
                    progress=progress,
                )
                frames.append(np.asarray(frame))

        frames.extend(_scene_frames(_end_card(bundle), fps * 2))

        output = store.run_dir / f"video_{trace_id}.mp4"
        iio.imwrite(output, frames, fps=fps, codec="libx264", macro_block_size=16)
        return {"type": "mp4", "path": str(output), "frames": len(frames), "fps": fps}


class DryRunPublisher:
    def publish(self, video: dict[str, Any], caption: dict[str, Any], checklist: list[str], store: EventLogStore) -> dict[str, Any]:
        package_id = new_id("publish_pkg")
        caption_path = store.run_dir / "caption.txt"
        caption_path.write_text(caption["caption"], encoding="utf-8")
        hashtags_path = store.run_dir / "hashtags.txt"
        hashtags_path.write_text(" ".join(caption["hashtags"]), encoding="utf-8")
        checklist_path = store.run_dir / "publish_checklist.md"
        checklist_path.write_text("\n".join(f"- [ ] {item}" for item in checklist) + "\n", encoding="utf-8")
        path = store.write_json(
            f"{package_id}.json",
            {
                "mode": "dry_run",
                "video": video,
                "caption": caption,
                "checklist": checklist,
                "files": {
                    "caption": str(caption_path),
                    "hashtags": str(hashtags_path),
                    "checklist": str(checklist_path),
                },
                "note": "Real publishing is intentionally disabled. Use this as a manual review package.",
            },
        )
        return {
            "package_id": package_id,
            "path": str(path),
            "mode": "dry_run",
            "files": {
                "caption": str(caption_path),
                "hashtags": str(hashtags_path),
                "checklist": str(checklist_path),
            },
        }


def build_trend_source(name: str, trend_file: Path | None) -> TrendSource:
    if name == "file":
        if trend_file is None:
            raise ValueError("--trend-file is required when --trend-source=file")
        return FileTrendSource(trend_file)
    if name in {"hn", "hackernews"}:
        return HackerNewsTrendSource()
    return MockTrendSource()


def build_media_factory(name: str) -> MediaFactory:
    if name == "template":
        return TemplateMediaFactory()
    return DryRunMediaFactory()


def build_video_renderer(name: str) -> VideoRenderer:
    if name == "moviepy":
        return ImageioVideoRenderer()
    return ManifestVideoRenderer()


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = ["arialbd.ttf", "arial.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text: str, width: int) -> str:
    words = text.split()
    lines: list[str] = []
    line: list[str] = []
    for word in words:
        candidate = " ".join([*line, word])
        if len(candidate) > width and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return "\n".join(lines)


def _gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    width, height = size
    top_rgb = np.array(Image.new("RGB", (1, 1), top).getpixel((0, 0)))
    bottom_rgb = np.array(Image.new("RGB", (1, 1), bottom).getpixel((0, 0)))
    ratio = np.linspace(0, 1, height)[:, None]
    row = (top_rgb * (1 - ratio) + bottom_rgb * ratio).astype(np.uint8)
    arr = np.repeat(row[:, None, :], width, axis=1)
    return Image.fromarray(arr, "RGB")


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    width: int,
    spacing: int,
) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    x, y = xy
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        bbox = draw.textbbox((x, y), line, font=font)
        y += bbox[3] - bbox[1] + spacing


def _draw_scene_illustration(draw: ImageDraw.ImageDraw, panel_no: int, dark: str, light: str) -> None:
    draw.rounded_rectangle((90, 230, 630, 750), radius=36, fill="#e0f2fe", outline="#0f172a", width=4)
    draw.rectangle((112, 622, 608, 654), fill="#0f172a")
    draw.rounded_rectangle((178, 654, 542, 704), radius=18, fill="#334155")
    draw.rounded_rectangle((210, 360, 510, 565), radius=24, fill="#ffffff", outline=dark, width=5)
    draw.ellipse((126, 488, 278, 640), fill=light, outline="#111827", width=4)
    draw.ellipse((442, 488, 594, 640), fill="#fde68a", outline="#111827", width=4)
    draw.ellipse((170, 530, 190, 550), fill="#111827")
    draw.ellipse((218, 530, 238, 550), fill="#111827")
    draw.arc((172, 562, 238, 606), 0, 180, fill="#111827", width=4)
    draw.ellipse((486, 530, 506, 550), fill="#111827")
    draw.ellipse((534, 530, 554, 550), fill="#111827")
    draw.arc((488, 562, 554, 606), 0, 180, fill="#111827", width=4)

    if panel_no == 1:
        draw.rounded_rectangle((170, 282, 550, 340), radius=18, fill="#fef3c7")
        draw.text((196, 300), "TREND ALERT", fill="#92400e", font=_font(24, bold=True))
    elif panel_no == 2:
        for x, label in [(170, "Risk"), (292, "Art"), (414, "Copy")]:
            draw.rounded_rectangle((x, 282, x + 96, 340), radius=18, fill="#ede9fe")
            draw.text((x + 18, 300), label, fill="#5b21b6", font=_font(22, bold=True))
    else:
        draw.rounded_rectangle((164, 278, 556, 346), radius=20, fill="#dcfce7")
        draw.text((196, 300), "REVIEW PACKAGE READY", fill="#166534", font=_font(24, bold=True))


def _title_card(caption: dict[str, Any]) -> Image.Image:
    image = _gradient((720, 1280), "#0f172a", "#155e75")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((58, 76, 662, 1204), radius=44, fill="#f8fafc")
    draw.text((94, 130), "P08 AGENT LAB", fill="#0f766e", font=_font(28, bold=True))
    _draw_wrapped_text(draw, (94, 260), caption["title"], _font(66, bold=True), "#111827", 540, 14)
    _draw_wrapped_text(draw, (94, 520), caption["caption"], _font(32), "#334155", 540, 10)
    draw.rounded_rectangle((94, 940, 626, 1038), radius=28, fill="#111827")
    draw.text((132, 970), "Event-driven multi-agent pipeline", fill="#ffffff", font=_font(27, bold=True))
    draw.text((94, 1090), "Generated locally - review package only", fill="#64748b", font=_font(24))
    return image


def _compose_video_frame(
    panel_image: Image.Image,
    title: str,
    subtitle: str,
    scene_index: int,
    scene_count: int,
    progress: float,
) -> Image.Image:
    frame = _gradient((720, 1280), "#020617", "#1e293b")
    draw = ImageDraw.Draw(frame)
    zoom = 1.0 + progress * 0.04
    panel = _fit_cover(panel_image, (620, 930), zoom)
    frame.paste(panel, (50, 132))
    draw.rounded_rectangle((50, 132, 670, 1062), radius=34, outline="#ffffff", width=3)
    draw.rounded_rectangle((50, 40, 670, 104), radius=22, fill="#ffffff")
    draw.text((78, 58), f"{scene_index}/{scene_count}", fill="#0f766e", font=_font(28, bold=True))
    draw.text((158, 62), title[:38], fill="#111827", font=_font(23, bold=True))
    draw.rounded_rectangle((54, 1090, 666, 1216), radius=28, fill="#ffffff")
    _draw_wrapped_text(draw, (86, 1120), subtitle, _font(34, bold=True), "#111827", 548, 8)
    bar_width = int(612 * ((scene_index - 1 + progress) / scene_count))
    draw.rounded_rectangle((54, 1240, 666, 1258), radius=9, fill="#334155")
    draw.rounded_rectangle((54, 1240, 54 + bar_width, 1258), radius=9, fill="#22c55e")
    return frame


def _end_card(bundle: dict[str, Any]) -> Image.Image:
    image = _gradient((720, 1280), "#ecfeff", "#fef3c7")
    draw = ImageDraw.Draw(image)
    draw.text((76, 110), "Publish Package", fill="#111827", font=_font(58, bold=True))
    draw.text((76, 184), "ready for human review", fill="#475569", font=_font(34))
    items = ["MP4 rendered", "Caption exported", "Hashtags exported", "Checklist included", "Real publish disabled"]
    y = 330
    for item in items:
        draw.rounded_rectangle((82, y, 638, y + 86), radius=24, fill="#ffffff", outline="#cbd5e1", width=2)
        draw.text((116, y + 24), "OK", fill="#15803d", font=_font(28, bold=True))
        draw.text((176, y + 24), item, fill="#111827", font=_font(28, bold=True))
        y += 110
    hashtags = " ".join(bundle["caption"].get("hashtags", []))
    _draw_wrapped_text(draw, (82, 1010), hashtags, _font(28), "#334155", 560, 8)
    draw.text((82, 1168), "P08: observable, replaceable, governable agents", fill="#0f766e", font=_font(24, bold=True))
    return image


def _fit_cover(image: Image.Image, size: tuple[int, int], zoom: float) -> Image.Image:
    width, height = size
    source = image.convert("RGB")
    scale = max(width / source.width, height / source.height) * zoom
    resized = source.resize((int(source.width * scale), int(source.height * scale)))
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _scene_frames(image: Image.Image, count: int) -> list[np.ndarray]:
    return [np.asarray(image.convert("RGB")) for _ in range(count)]


def _fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "P08ViralVideoAgentLab/0.1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _hn_angle(item: dict[str, Any]) -> str:
    score = item.get("score", 0)
    comments = item.get("descendants", 0)
    author = item.get("by", "unknown")
    return (
        f"Hacker News story by {author}, currently around {score} points and "
        f"{comments} comments. Turn it into a safe, original explainer short."
    )
