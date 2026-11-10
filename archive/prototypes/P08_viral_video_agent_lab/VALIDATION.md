---
title: P08 Validation Log
date: 2026-05-19
tags: [validation, p08, eval]
status: draft
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# P08 Validation Log

> 本文件记录 P08 的实际验证结果。每次改动 Agent/Prompt/事件协议后都应更新。

## 验证项

| 项 | 命令/方式 | 期望 |
|---|---|---|
| dry-run demo | `python -m viral_lab.main --provider mock --max-trends 4` | 生成 event_log + run_report |
| 单元测试 | `python -m pytest` | 3 条测试通过 |
| 安全闸门 | 检查 `RiskRejected` | 隐私样例不进入视频生成 |
| 发布闸门 | 检查 `ApprovalRequested` + `PublicationDryRun` | 不出现 `RealPublished` |

## 最近结果

### 2026-06-24 · demo recovery spikes

- ✅ 环境清单：新增 `ENVIRONMENT.md`，确认当前源码目录为空，需要按文档恢复 runnable demo。
- ✅ 假设 1：`scripts/spike_event_log.py` 通过，JSONL 事件日志可写入并回放。
- ✅ 假设 2：`scripts/spike_template_image.py` 通过，Pillow 可生成模板漫画分镜图。
- ✅ 假设 3：`scripts/spike_mp4_encode.py` 在项目 `.venv` 中通过，`imageio + imageio-ffmpeg` 可生成 MP4。
- ⚠️ 初次使用全局 Python 跑 MP4 spike 失败，原因是缺少 `imageio`；已改为项目本地 `.venv` 安装依赖后验证通过。

### 2026-06-24 · recovered runnable demo

- ✅ RED：先新增 `tests/test_pipeline.py`，初次 `pytest` 因 `viral_lab.main` 缺失失败，确认测试有效。
- ✅ GREEN：恢复 `src/viral_lab/` 最小可运行实现，`python -m pytest -q` 结果为 `3 passed`。
- ✅ 一键脚本：`.\scripts\run_template_demo.ps1` 成功，最新 run 为 `output/run_de255d742aad/`。
- ✅ 展示产物：生成 `video_trace_6aefd4e8b8cd.mp4`、`run_report.json`、`event_log.jsonl`、`publish_pkg_60549b950717.json`。
- ✅ 治理证据：`run_report.json` 中 `TrendDetected=2`、`RiskRejected=1`、`PublicationDryRun=1`。
- ✅ 视频元数据：H.264 MP4，720x960，12 fps，6 秒。

### 2026-06-24 · polished real API showcase

- ✅ 展示层升级：模板视频从静态调试卡片升级为 720x1280 竖屏短视频，包含标题页、三幕内容、字幕条、进度条和结尾审核包页。
- ✅ 真实 API：新增 `HackerNewsTrendSource`，通过 Hacker News 官方 Firebase API 拉取 top story 和 item 详情。
- ✅ 启动脚本：新增 `scripts/run_real_api_demo.ps1`，一键测试并生成真实 API 选题视频。
- ✅ 验证结果：`.\scripts\run_real_api_demo.ps1` 成功，run 为 `output/run_3f3ed7477316/`。
- ✅ 真实来源证据：`event_log.jsonl` 中 `TrendDetected` 包含 `source=hacker_news`、`source_url`、`score`、`by`、`comments`。
- ✅ 成品产物：`video_trace_81ea7f6d9d25.mp4`，约 730KB，234 帧，18 fps；同时导出 `caption.txt`、`hashtags.txt`、`publish_checklist.md`。

### 2026-06-24 · local GUI console

- ✅ GUI 服务：新增 `src/viral_lab/gui.py`，使用 Python 标准库 HTTP Server 提供本地 Web 控制台。
- ✅ 启动脚本：新增 `scripts/run_gui.ps1`，启动地址为 `http://127.0.0.1:8787/`。
- ✅ 配置操作：支持真实 API、本地安全演示、manifest 快速模式，以及 trend source、max trends、media provider、video renderer、trend file 配置。
- ✅ 按钮运行：通过 `/api/run` 后台触发真实 `run_pipeline()`，不是前端假数据。
- ✅ 页面验证：浏览器打开 GUI 成功，标题、真实 API 按钮、视频预览区域存在。
- ✅ 运行验证：API 触发 `local_safety` 成功，job 为 `job_0a888bbb78`，run 为 `output/gui/run_fa8024f7b591/`。
- ✅ 产物验证：GUI 运行生成 MP4、run_report、event_log、caption、hashtags、publish_checklist；测试结果 `5 passed`。

### 2026-05-19 · mock dry-run

- ✅ Demo：`python -m viral_lab.main --provider mock --max-trends 4` 成功。
- ✅ 测试：`python -m pytest` 成功。
- ✅ 输出：`output/run_ace199b2a312/run_report.json` 与 `event_log.jsonl` 已生成。
- ✅ 事件：`PublicationDryRun` 出现 3 次，`RiskRejected` 出现 1 次。
- ✅ Trace 修复：artifact 路径已按每条热榜独立 trace 生成，15 个 artifact path 无重复。

### 2026-05-19 · template media + MoviePy MP4

- ✅ 依赖：项目局部 `.venv` 中 `pip install -e ".[media,dev]"` 成功。
- ✅ 测试：`.venv` 内 `python -m pytest` 成功。
- ✅ 命令：`python -m viral_lab.main --provider mock --trend-source file --trend-file config\trends.sample.json --media-provider template --video-renderer moviepy --max-trends 1` 成功。
- ✅ 输出：`output/run_faa3f8ab0799/video_trace_daf97b026cba.mp4` 已生成。
- ✅ 事件：14 个事件闭环，`PublicationDryRun=1`，`ApprovalRequested=1`。
- ✅ 工具：新增 `scripts/run_template_demo.ps1` 一键安装依赖、跑测试并生成模板 MP4。
