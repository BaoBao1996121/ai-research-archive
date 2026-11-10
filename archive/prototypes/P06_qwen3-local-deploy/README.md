> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P06 · Qwen3.6 在 RTX 3060 Ti 8GB 上的本地部署 + 极限优化

> **配套报告**：`reports/06-工具与生态/R75_Qwen3.6本地部署RTX3060Ti实战.md`（[R75](../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R75_Obsidian%2BClaudeCode%E8%B6%8A%E7%94%A8%E8%B6%8A%E8%81%AA%E6%98%8E%E6%A8%A1%E5%BC%8F%E6%8B%86%E8%A7%A3.md)）
> **目标**：让 8GB 显卡 + 64GB RAM + i5-12600KF 这套消费级配置跑起 **Qwen3.6**（2026-04 最新一代国产开源大模型），并把性能调到极限。

## 5 分钟跑通

```powershell
cd prototypes\P06_qwen3-local-deploy

# 1. 装依赖
pip install -r requirements.txt

# 2. 看本地有哪些模型 + 推荐
python model_check.py

# 3. 一键应用 6 项性能优化（设环境变量 + 创建调优模型）
python tune.py --all

# 4. 重启 Ollama 让环境变量生效（很重要！）
Get-Process ollama* | Stop-Process -Force
# 然后重新启动 Ollama 桌面应用

# 5. 验证可用性
python verify.py --model qwen3.6:35b

# 6. 性能 benchmark（对比 35B-A3B vs 8B）
python benchmark.py

# 7. 交互式 chat
python chat_cli.py --model qwen3.6:35b
# 或开启 thinking
python chat_cli.py --model qwen3.6:35b --think
```

## 文件清单

| 文件 | 用途 |
|------|------|
| `model_check.py` | 列出本地 Qwen 模型，按 8GB 显卡价值排序给出推荐 |
| `tune.py`        | **一键应用 6 项性能优化**：设 5 个关键环境变量 + 创建 `qwen3.6-tuned` 调优模型 |
| `verify.py`      | 端到端验证 (Ollama 可达 + 模型已拉 + 推理成功)，自动适配 Qwen3.6 / Qwen3 |
| `benchmark.py`   | 多模型对比 benchmark (TTFT + TPS + 端到端延迟)，默认对比 `qwen3.6:35b` vs `qwen3:8b` |
| `chat_cli.py`    | 交互式 chat，支持 `/think` 切换、自动适配 Qwen3.6 的 `enable_thinking` API |
| `agent_demo.py`  | LangChain ReAct Agent + 简单工具 demo |
| `requirements.txt` | openai>=1.54.0, requests>=2.31.0 |

## tune.py 应用了哪些优化？

**5 个环境变量**（全部由 tune.py 自动 setx，永久生效）：

| 变量 | 值 | 作用 |
|------|----|------|
| `OLLAMA_KV_CACHE_TYPE` | `q8_0` | KV Cache 8-bit 量化，省 50% 显存，质量损失 <1% |
| `OLLAMA_FLASH_ATTENTION` | `1` | Flash Attention，长上下文性能提升 30%+ |
| `OLLAMA_KEEP_ALIVE` | `24h` | 模型常驻 RAM，避免冷启动 30-60 秒延迟 |
| `OLLAMA_NUM_PARALLEL` | `1` | 8GB 显卡老老实实串行 |
| `OLLAMA_NUM_GPU` | `32` | Qwen3.6-35B-A3B 推荐 GPU 层数（共 40 层）|

**调优后的 Modelfile**（命名 `qwen3.6-tuned`）：

```
FROM qwen3.6:35b
PARAMETER num_gpu 32
PARAMETER num_ctx 16384
PARAMETER num_predict 4096
PARAMETER temperature 0.7
PARAMETER top_p 0.8
PARAMETER top_k 20
PARAMETER min_p 0.0
```

跑这个调优后的模型：
```powershell
ollama run qwen3.6-tuned --verbose
```

## 8GB 显卡能跑哪些 Qwen？速查表

| 模型 | 大小 | 速度 | 多模态 | 用什么场景 |
|------|------|------|--------|---------|
| **`qwen3.6:35b`** (MoE) | 24GB (CPU offload) | 8-15 t/s | ✅ | **甜点**，多模态+Agent+长对话 |
| `qwen3.6:27b` (稠密) | 17GB (重 offload) | 2-5 t/s | ✅ | 能力上限，跑 coding 任务批处理 |
| `qwen3:8b` | 5GB (全 GPU) | 35-45 t/s | ❌ | 保底基线，交互对话 |
| `qwen3:4b-2507` | 2.5GB | 60+ t/s | ❌ | 长文档极速处理 |

**关键洞察**：MoE 36B/3B 激活的 `qwen3.6:35b` 在 8GB 显卡上**反而比 17GB 的稠密 27B 更快**——稀疏激活让 CPU↔GPU IO 降到 1/9。这就是 MoE 在消费级硬件上的反直觉优势。

## Qwen3.6 与 Qwen3 的关键差异（破坏性变更）

| 项 | Qwen3 | Qwen3.6 |
|----|-------|---------|
| `/think` `/nothink` 软切换 | ✅ | ❌ **不支持** |
| 关闭思考的方式 | system prompt 加 `/nothink` | API 参数 `enable_thinking=False` |
| Thinking Preservation | ❌ | ✅ Agent 多轮可保留历史推理 |
| 多模态 | ❌（VL 单独发） | ✅ 原生视觉 |
| 上下文 | 32K-256K | 262K（YaRN 可到 1M）|

→ 这就是为什么 `chat_cli.py` 和 `verify.py` 必须根据模型名自动切换机制。

## 进阶：如果 Ollama 还嫌慢

**KTransformers**（清华开源，专为"小 GPU + 大 RAM 跑 MoE"优化）可达 Ollama 的 1.5-2 倍速度：

```bash
# WSL2 / Linux
git clone https://github.com/kvcache-ai/ktransformers && cd ktransformers
pip install -e .
python -m ktransformers.local_chat \
  --model_path Qwen/Qwen3.6-35B-A3B \
  --gguf_path /path/to/Qwen3.6-35B-A3B-Q4_K_M.gguf \
  --cpu_infer 12
```

详见 R75 §阶段 3·优化 6。

## 排错速查

| 现象 | 速查 |
|------|------|
| `ollama run` 直接 OOM | tune.py --create-modelfile，把 num_gpu 从 32 降到 28 |
| t/s 仅 2-4 | `nvidia-smi` 看是否被浏览器/视频软件占了 GPU |
| 输出仍带 `<think>` | API 参数 `chat_template_kwargs.enable_thinking=False`；本 CLI 已自动处理 |
| 第一句要 30 秒 | 设 `OLLAMA_KEEP_ALIVE=24h`（tune.py 已设）|
| C 盘塞爆 | tune.py --apply-all 会设 `OLLAMA_MODELS=F:\ollama_models` |

完整避坑表：见 R75 §避坑指南（16 项）。

---

**当前状态**：脚手架完整。`qwen3:8b` 已就绪，`qwen3.6:35b` 24GB 后台拉取中。下载完成后跑 `python verify.py` 拿到真实数据。
