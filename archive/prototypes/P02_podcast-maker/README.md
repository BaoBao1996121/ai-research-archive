> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# P02 Podcast Maker

> 技术文档转口播与播客生成工具。本项目依赖 LLM 与 TTS 服务，默认在万宝楼中只展示目录入口，避免在缺少 API key 时误启动失败。

## 启动

```powershell
cd "C:/Users/USER\Documents\Obsidian Vault\prototypes\P02_podcast-maker"
python podcast_maker.py
```

也可以双击本目录下的 `启动播客生成器.bat`。

## 依赖

- Python GUI: Tkinter
- 文档改写: `openai`, `python-dotenv`
- 语音合成: `dashscope`
- API Key: 需要按脚本中的服务配置提供对应 key

## 万宝楼接入策略

- 已修复启动 bat 的旧路径问题。
- 由于它依赖外部 API 和 TTS 账号，万宝楼不默认显示“启动”按钮。
- 环境确认后，可再把 `python podcast_maker.py` 接入为白名单动作。

