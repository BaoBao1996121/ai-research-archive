---
title: P08 自媒体创作生产指南
date: 2026-05-19
tags: [prototype, production, creator-workflow, openai, video]
status: in-progress
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P08 自媒体创作生产指南

> 一句话概括：把 P08 从学习原型升级为真实自媒体生产工具时，先做“导出发布包 + 手动发布”，再考虑官方 API 自动发布。

## 你需要提供什么

### 必需

1. **OpenAI API Key**：用于文案、图像、配音。填到环境变量 `OPENAI_API_KEY`，不要发给我。
2. **账号定位**：你要做什么号，例如“搞笑漫画热榜解读 / AI 科普短剧 / 职场讽刺”。
3. **选题来源**：第一阶段建议你人工整理到 `config/trends.local.json`，或接官方/授权数据源。
4. **发布平台**：抖音/小红书/B站/视频号。当前默认只导出视频和文案，你手动上传。
5. **审核规则**：哪些题材绝对不碰，例如隐私、真实人物、未授权搬运、医疗金融建议等。

### 可选

- 平台开放 API 资质 / OAuth 应用信息：只有做全自动发布才需要。
- 固定角色形象 / Logo / 片头片尾素材。
- 配音风格和禁用词表。

## 推荐阶段路线

| 阶段 | 目标 | 自动化程度 | 风险 |
|---|---|---:|---:|
| V1 | 输入选题 → 生成视频文件 + 文案 | 70% | 低 |
| V2 | 加选题池、成本统计、失败重试 | 80% | 中 |
| V3 | 接平台官方发布 API | 90% | 高 |
| V4 | 多账号矩阵 + A/B 测试 | 95% | 很高 |

**建议现在做 V1。** 不要一上来全自动发平台，误发一次可能比省下的 10 分钟更贵。

## 本地真实生成命令

### 1. 安装媒体依赖

```powershell
cd prototypes\P08_viral_video_agent_lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[media,live,dev]"
```

### 2. 准备选题文件

复制：

```powershell
Copy-Item config\trends.sample.json config\trends.local.json
```

然后编辑 `config/trends.local.json`。

### 3. 设置 OpenAI Key

```powershell
$env:OPENAI_API_KEY = "你的 key"
```

### 4. 生成真实图像 + 配音 + MP4

```powershell
python -m viral_lab.main --provider openai --trend-source file --trend-file config\trends.local.json --media-provider openai --video-renderer moviepy --max-trends 1
```

输出位置：`output/run_xxx/`

你会得到：

- `panel_*.png`：漫画图
- `voiceover_*.mp3`：配音
- `video_*.mp4`：短视频
- `run_report.json`：本次生产报告
- `event_log.jsonl`：全链路事件日志

## 无 API Key 的真实渲染练习

如果没有 OpenAI Key，也可以先用模板图 + 静音音频生成 MP4：

```powershell
python -m viral_lab.main --provider mock --trend-source file --trend-file config\trends.sample.json --media-provider template --video-renderer moviepy --max-trends 1
```

这会生成真实 MP4，只是画面是模板漫画卡片，配音是静音占位。

也可以直接运行一键脚本：

```powershell
.\scripts\run_template_demo.ps1
```

已验证结果：2026-05-19 在本机生成 `output/run_faa3f8ab0799/video_trace_daf97b026cba.mp4`。

## 发布策略

当前建议：

1. 系统生成 `video_*.mp4` 和文案。
2. 你人工查看视频、文案、风险提示。
3. 你手动上传到抖音/小红书/B站。
4. 把播放数据回填，后续做选题优化。

全自动发布需要平台官方能力，不建议用浏览器自动化绕平台规则。

## 成本估算

以每天 1 条、每条 3 张图 + 1 段 TTS 估算：

- 文案：低成本，通常不是大头。
- 图像：主要成本项，3 张/条。
- TTS：中低成本。
- 人审：时间成本最大，但早期必须保留。

先每天 1 条跑 7 天，比一开始搭 100% 自动发布更有价值。

## 每天工作流

1. 上午：填 3-5 个候选选题到 `trends.local.json`。
2. 运行系统生成 1 条视频。
3. 看 `run_report.json` 和成片。
4. 手动发布。
5. 晚上记录播放量、完播率、评论关键词。
6. 每周把高表现题材总结进账号策略。

## 不做的事

- 不抓取未授权内容。
- 不绕验证码。
- 不自动搬运真实视频。
- 不在无人审核时真实发布。
- 不用真实个人隐私做梗。
