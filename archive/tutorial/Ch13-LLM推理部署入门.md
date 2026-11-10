---
title: "Ch13: LLM 推理部署入门 — 从调 API 到起自己的服务"
aliases: ["Ch13-LLM推理部署入门", "LLM推理部署入门"]
tags: [教程, 推理部署, vLLM, Ollama, 量化, serving, llm-ops]
date: 2026-04-25
status: completed
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../ARCHIVE_POLICY.md)。

# Chapter 13: LLM 推理部署入门 — 从调 API 到起自己的服务

> 📍 前置：完成 Chapter 11（已经知道"部署"是啥、为啥要 Docker）
> 🎯 完成本章后你能：说清"开源模型怎么跑在自己机器上"的全链路；选对量化格式和推理引擎；5 分钟跑通一个 7B 模型；知道生产化要补什么
> ⏱️ 预计时间：25 分钟阅读 + 45 分钟动手
> 📚 深度报告：[R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 量化与推理引擎 · [R59](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 推理优化技术 · [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 服务化 SLA 与监控

---

## 为什么要自己部署 LLM？（WHY）

到现在你一直在"调 API"——OpenAI、Anthropic、Azure、DeepSeek。它们很好用，但有三种场景你绕不开自部署：

1. **数据不能出企业网**（医疗、金融、政务、内部代码）
2. **单次调用不贵但量大**（日均百万次调用时，API 费能买一张 H100）
3. **需要定制能力**（微调过的模型、特殊推理模式、agent 框架深度集成）

这三种情况一出现，你就要面对一套完全不同的技术栈：**GPU / 量化 / 推理引擎 / 批处理 / SLA / 监控**。

本章的作用是**把这套栈从"听着很可怕"变成"你知道每一块在干嘛"**，然后带你跑通第一个自部署的 7B 模型。

---

## 核心概念（WHAT）

### 部署 LLM 的四层"洋葱"

```
           ┌─────────────────────────────────────┐
           │  L4 · 服务化（API 网关 / SLA / 监控） │  ← R63
           ├─────────────────────────────────────┤
           │  L3 · 推理引擎（vLLM / llama.cpp 等）│  ← R58 / R59
           ├─────────────────────────────────────┤
           │  L2 · 量化（FP16 → INT4 / GGUF 等）  │  ← R58
           ├─────────────────────────────────────┤
           │  L1 · 模型权重（HuggingFace / GGUF） │
           └─────────────────────────────────────┘
                          ↓
                    GPU / CPU 硬件
```

每一层都在回答一个问题：

| 层 | 回答的问题 | 新手易混点 |
|----|----------|-----------|
| **L1 权重** | 模型参数从哪来？ | `.safetensors` / `.bin` / `.gguf` 不是一个东西 |
| **L2 量化** | 怎么让 70GB 的模型塞进 8GB 显存？ | 量化不是"压缩"，是"降精度" |
| **L3 引擎** | 怎么让它跑得又快又稳？ | vLLM 和 Ollama 定位完全不同 |
| **L4 服务化** | 怎么让几千人用而不崩？ | QPS 在 LLM 里不是好指标，改看 TPS |

### 三个最容易踩的坑（先看避坑单）

| 坑 | 现象 | 原因 | 解法 |
|----|------|------|------|
| 显存爆掉 | `CUDA out of memory` | 没量化 / KV Cache 吃满 | 用 Q4_K_M 量化 + 限 `--max-model-len` |
| 中文切得很碎 | 100 中文 ≈ 200+ token | 模型用了英文优化 tokenizer | 选 Qwen/GLM 等中文优化模型（详见 [R56](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)） |
| 本地快 · 上线慢 | 单用户 80 t/s · 10 人并发降到 5 t/s | 没用带 PagedAttention 的引擎 | 生产必上 vLLM / TGI，别用 transformers 裸跑 |

> ☝️ 这三个坑几乎每个第一次部署 LLM 的人都会踩一次，提前看一眼能省 2-3 天。

---

## Hello World：5 分钟跑起一个 7B 模型

### 方案 A：Ollama（最友好，推荐首次）

**适用场景**：本地 Mac / 有一张消费级显卡（3090/4090/M2 Pro+）想快速把玩。

```bash
# 1. 装 Ollama（Mac / Linux / Windows 都有）
# 官网 https://ollama.com 下载安装

# 2. 拉一个中文友好的 7B 量化模型（~4.4GB）
ollama pull qwen2.5:7b

# 3. 命令行聊起来
ollama run qwen2.5:7b

# 4. 它同时起了一个 OpenAI 兼容的 API 在 :11434
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role":"user","content":"用一句话解释 LLM 量化"}]
  }'
# Expected output: 返回 JSON，choices[0].message.content 是一段中文解释
```

✅ **你就已经"自部署"了 LLM**。Ollama 背后用的是 llama.cpp + GGUF 量化。

### 方案 B：vLLM（生产级性能，需要 CUDA GPU）

**适用场景**：有 NVIDIA GPU（至少 16GB 显存）+ 要做多用户并发 + 要上生产环境。

```bash
# 1. 装 vLLM
pip install vllm==0.6.3

# 2. 起一个 OpenAI 兼容的服务（自动从 HF 下载权重）
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct-AWQ \
  --quantization awq \
  --max-model-len 8192 \
  --port 8000

# 3. 调它（跟 OpenAI SDK 完全兼容）
pip install openai==1.54.0
python - <<'EOF'
from openai import OpenAI
c = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
r = c.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    messages=[{"role":"user","content":"用 3 句话解释 PagedAttention"}]
)
print(r.choices[0].message.content)
EOF
# Expected output: 一段关于 PagedAttention 的中文解释
```

> **Ollama vs vLLM 怎么选？** 一句话：**Mac / 单人把玩用 Ollama，Linux GPU / 多人并发用 vLLM**。详细选型矩阵见 [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 的第 4 章。

### 🛑 停下来想一想

在跑完 Ollama 后，试着观察：

1. `ollama run qwen2.5:7b` 启动时要花几秒？这几秒它在做什么？（提示：权重从磁盘加载到显存）
2. 当你连续问它 3 个问题时，第 2、3 个问题的 **首字延迟**（TTFT）为什么更短？（提示：KV Cache）
3. 如果你开另一个终端同时问 5 个问题，会发生什么？（试一下）

这三个现象分别对应 [R59](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 里讲的三个核心优化点：**权重加载 / KV Cache / 批处理调度**。

---

## 量化：让 70GB 塞进 8GB 的魔法（简版）

### 核心直觉（费曼式类比）

想象你有一本高清彩色图鉴（FP16 权重 70GB）。量化做的事情，相当于：

- **INT8** = 把每张图压成 JPEG 75%，体积减半，肉眼几乎看不出区别
- **INT4** = 进一步压缩到 JPEG 30%，体积 1/4，近看有点糊但整体还认得出
- **INT2** = 极限压缩，很多细节丢了，模型会开始"说傻话"

> 📌 **关键洞察**：量化不是"压缩"，是**用更少的 bit 表示每个参数**。换来的是显存减半（或更多），代价是精度损失（通常 < 3%）。

### 四种格式速查

| 格式 | 谁用 | 典型精度 | 显存节省 | 适用场景 |
|------|------|--------|---------|---------|
| **GGUF** (Q4_K_M) | llama.cpp / Ollama | ~2-3% 损失 | 4x | CPU + 消费级 GPU |
| **AWQ** | vLLM / TGI | ~1-2% 损失 | 4x | 生产级 NVIDIA GPU |
| **GPTQ** | AutoGPTQ / vLLM | ~2-3% 损失 | 4x | 老项目兼容 |
| **FP8** | H100 / vLLM 新版 | < 1% 损失 | 2x | 最高端 GPU |

**新手建议**：本地玩用 GGUF Q4_K_M；生产用 AWQ。深入细节看 [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)。

---

## 推理引擎：为什么不能用 transformers 裸跑

写 agent 时你可能用过这种代码：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
out = model.generate(tok("你好", return_tensors="pt").input_ids, max_new_tokens=50)
```

✅ 能跑。❌ 但**单机 10 个并发请求就崩了**，而且每秒生成 token 数比 vLLM 低一个数量级。

### 为什么？三件事没做：

1. **连续批处理（Continuous Batching）**：transformers 等一个请求跑完才处理下一个；vLLM 能把多个请求的 token 生成混在一起
2. **PagedAttention**：transformers 给每个请求分配连续的 KV Cache 显存（浪费）；vLLM 像操作系统一样分页管理
3. **算子融合**：transformers 走的是标准 PyTorch 算子；vLLM/TGI 用了 FlashAttention 等融合算子（GPU 利用率提升 2-3x）

### 五大引擎怎么选？

| 引擎 | 硬件 | 定位 | 适合场景 |
|------|------|------|---------|
| **vLLM** | NVIDIA GPU | 高吞吐通用 | 企业级 7B-70B 服务 |
| **TGI** | NVIDIA GPU | HuggingFace 官方 | 企业级生产 |
| **TensorRT-LLM** | NVIDIA GPU | 极致性能 | 延迟敏感 / 大模型 |
| **llama.cpp** | CPU + 消费 GPU | 轻量通用 | 边缘 / 单机 / Mac |
| **Ollama** | 封装 llama.cpp | 开发者友好 | 个人 / 小团队 |

> 深入对比、benchmark 数据、选型决策树见 [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 第 3-4 章。

---

## 从跑通到生产：还缺什么？（L4 服务化）

你在 8000 端口跑起 vLLM 的那一刻，离"生产"还差很远。真正上线需要：

### 生产 Checklist

| 维度 | 要补的东西 | 参考报告 |
|------|----------|---------|
| **监控** | TTFT / ITL / TPS / 错误率 / GPU 利用率 | [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 第 4 章 |
| **SLA** | P50 / P99 延迟目标、可用性承诺 | [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 第 3 章 |
| **成本** | Token 计量、Prompt Caching、分层定价 | [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 第 5 章 |
| **扩容** | 按 TPS 而非 QPS 做 Autoscaling | [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 第 6 章 |
| **限流** | 按 input_tokens/s + output_tokens/s 双限流 | [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 第 7 章 |
| **降级** | 主模型挂了走哪个备用？ | [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 第 8 章 |
| **安全** | Prompt Injection / 越狱检测 | [R57](../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) 红队基线 |

### 🛑 费曼式自检

如果有人问你："我们公司要给 1000 人部署一个内部代码助手，硬件预算 20 万，技术栈怎么选？"

你应该能 5 分钟内给出架构草图，覆盖：

- 模型选什么（7B? 14B? 32B? 为什么）
- 量化用什么格式（AWQ? GGUF?）
- 引擎用什么（vLLM / TGI / llama.cpp?）
- 几张 GPU、什么型号
- 监控用什么（Langfuse? Phoenix?）
- SLA 目标（TTFT < ? ITL < ? 可用性 ?）

**答不出 4 个以上 → 回头读 [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)[R59](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)[R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 三联报告**。

---

## 本章阶段性验收

学完本章你应该能做到：

- [ ] 用 Ollama 在本地跑起 Qwen2.5-7B，并用 curl 调通 API
- [ ] 说出 GGUF / AWQ / GPTQ / FP8 各自的适用场景
- [ ] 解释为什么不能用 `transformers.generate` 做生产部署
- [ ] 说出 TTFT 和 ITL 的区别、以及各自受什么影响
- [ ] 画出"模型权重 → 量化 → 推理引擎 → 服务化"的四层图

全部 ✅ → 进入 [Ch09](Ch09-%E5%AE%89%E5%85%A8%E4%B8%8E%E5%8F%AF%E9%9D%A0%E6%80%A7.md) 或直接深耕 [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)[R59](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)[R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 三联报告。
有 ❌ → 回头把对应的章节再跑一遍。

---

## 延伸阅读

- [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) — LLM 推理部署工程指南（量化 + 推理引擎完整版）
- [R59](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) — 推理优化技术：KV Cache / FlashAttention / 投机解码
- [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) — LLM 服务化生产部署：成本 / 延迟 / 监控 / SLA
- [R56](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) — Tokenization 深度解析（部署前务必看）
- [R57](../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) — Agent 安全与红队（服务上线前的安全基线）
- [tutorial/Ch11-部署上线](Ch11-%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF.md) — 应用层的部署 9 级光谱

---

## 📌 来源

- 本工作区 [R58](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) / [R59](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) / [R63](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 三联报告（本章为其教学层入口）
- Ollama 官方文档（2026-04）
- vLLM v0.6.x 文档

**本章为教学层重组**：不引入新事实，所有技术判断均对应上述三篇深度报告。
