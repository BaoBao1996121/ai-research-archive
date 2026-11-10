---
title: 小模型微调、LoRA 与量化实战前置学习指南
aliases: [R159, 小模型微调速通, LoRA量化学习指南]
tags: [small-language-model, fine-tuning, sft, lora, qlora, quantization, qwen]
date: 2026-08-07
category: 工程实践
report_id: R159
status: completed
related:
  - "[R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)"
  - "[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)"
  - "[R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)"
  - "[R137](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R137_LLM%E6%8C%87%E4%BB%A4%E9%81%B5%E5%BE%AA%E6%9C%BA%E5%88%B6_%E4%BB%8E%E7%BB%AD%E5%86%99%E5%88%B0%E5%90%AC%E8%AF%9D.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 小模型微调、LoRA 与量化实战前置学习指南

> **一句话结论**：当前最需要补的不是更多算法名词，而是把“样本如何变成 Token 和 Loss、梯度为何只更新 LoRA、量化如何改变存储与计算、评估怎样证明泛化”四条因果链，与已经跑通的 Qwen2.5-0.5B 实验对上。

> **增量价值**：[R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)、[R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)、[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)、[R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)、[R137](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R137_LLM%E6%8C%87%E4%BB%A4%E9%81%B5%E5%BE%AA%E6%9C%BA%E5%88%B6_%E4%BB%8E%E7%BB%AD%E5%86%99%E5%88%B0%E5%90%AC%E8%AF%9D.md) 已分别覆盖训练、Chat Template、量化、预训练和指令遵循；本报告将这些通用知识压缩成一份与本机实测结果绑定的实验前学习地图。

## 1. 已完成实验的准确定位

本机已完成的工作流是：

> `Qwen2.5-0.5B-Instruct` + SFT 训练目标 + FP16 LoRA + NF4 4-bit 推理。

它不是全参数微调，也不是 QLoRA。后者要求在 4-bit 量化基座上训练 LoRA；当前实验是先以 FP16 基座训练 LoRA，再以 NF4 4-bit 方式加载基座做推理。

| 项目 | 已验证结果 |
|---|---:|
| 固定测试集，基座联合准确率 | 8.3% |
| 固定测试集，LoRA 联合准确率 | 100% |
| Challenge 集，基座联合准确率 | 8.3% |
| Challenge 集，LoRA 联合准确率 | 91.7% |
| 可训练参数 | 4,399,104（0.883%） |
| 训练耗时 / 峰值显存 | 约 8 分 35 秒 / 1.305 GB |
| NF4 推理显存变化 | 约 985 MB → 475 MB |
| NF4 推理延迟变化 | 约 2.30 秒 → 3.95 秒 |

这些数字说明 LoRA 已学会一个窄而明确的任务，同时也说明“更省显存”不等于“更快”：0.5B 模型太小，4-bit 解量化与内核调度开销可能超过带宽收益。

## 2. 三条相互独立的坐标轴

不要把 SFT、LoRA、量化当成同一层概念：

1. **训练目标轴**：SFT、DPO、GRPO/RLHF 回答“用什么信号学”。
2. **参数更新轴**：全参数微调、LoRA/PEFT 回答“改哪些参数”。
3. **数值精度轴**：FP32、FP16/BF16、8-bit、4-bit 回答“参数和计算用什么精度表示”。

因此可以有 FP16 LoRA、4-bit QLoRA，也可以有全参数 SFT。当前实验选择的是 SFT + FP16 LoRA；量化只用于推理阶段。

## 3. 必须拉齐的四条因果链

### 3.1 数据到 Loss

`messages → Chat Template → Token IDs → labels → next-token loss`

模型不直接看 JSON。Chat Template 把 system/user/assistant 消息拼成模型训练时熟悉的特殊 Token 序列。训练中把提示部分的 label 设为 `-100`，只让 assistant 答案产生 Loss，避免模型浪费能力学习复述用户输入。

### 3.2 梯度到 LoRA

LoRA 冻结原权重 `W`，只训练低秩增量 `BA`，前向计算可理解为 `W' = W + scale × BA`。秩 `r` 决定增量容量；`alpha/r` 影响增量缩放；target modules 决定在哪些线性层插入 LoRA。Adapter 小是因为只保存 `A/B`，不是复制整个模型。

### 3.3 数据划分到泛化证据

训练集证明模型能学，验证集帮助选配置，测试集衡量固定分布，Challenge/OOD 集检查换措辞、组合或边界后是否仍会做。固定测试 100% 不能单独证明泛化；本次 Challenge 91.7% 才提供了较强但仍有限的证据，样本量仍小。

### 3.4 精度到资源表现

量化主要减少权重存储和显存带宽，但还会引入 scale、zero-point 或反量化计算。NF4 是面向近似正态权重分布的 4-bit 表示，常用于 QLoRA 或 bitsandbytes 推理；GGUF 更接近 llama.cpp 生态的部署容器/格式；GPTQ、AWQ 是不同的训练后权重量化路线。它们不能只按“都是 4-bit”互换理解。

## 4. 现在先不学什么

第一轮实验前可暂缓 DPO、GRPO、RLHF、QAT、分布式训练、复杂数据混配，以及同时调整多个超参数。先掌握 Token/Template、Loss masking、梯度、LoRA 参数、训练/测试分离和显存/延迟测量，已经足够解释完整闭环。

## 5. 推荐的手动实验阶梯

1. 先跑 0.1 epoch，观察 Loss、速度、显存和输出格式。
2. 只改 epoch：0.5 / 1 / 3，观察欠拟合与记忆化。
3. 只改 rank：4 / 8 / 16，比较参数量、效果和 Adapter 大小。
4. 加入难负样本和边界样本，观察 Challenge 集变化。
5. 再换 1.5B 模型尝试真正的 QLoRA，确认本机资源边界。
6. 最后合并或导出 GGUF，体验训练产物到本地部署的链路。

每轮只改变一个变量，并同时保留配置、数据版本、随机种子、指标与输出样例。

## 6. 边界与待验证项

- 1.5B QLoRA 尚未在本机实跑，资源判断仍是候选方案，不应写成已验证能力。
- 当前数据集和 Challenge 集规模较小，91.7% 不代表开放域能力。
- LoRA 更擅长塑造格式、风格、分类边界和窄任务行为，不应把它当作可靠注入大量新事实的首选方案。
- 小模型量化的收益高度依赖硬件、内核和批量大小，不能从显存下降直接推导延迟下降。

## 7. 项目材料与来源

完整个性化学习稿保存在实验项目的 `outputs/small-model-lab/LEARNING_GUIDE.md`，手动操作入口为同目录 `README.md`，实测证据为 `EXPERIMENT_RESULTS.md`。

外部资料于 2026-08-07 核验：

- [Hugging Face PEFT Quicktour](https://huggingface.co/docs/peft/quicktour)
- [PEFT LoRA reference](https://huggingface.co/docs/peft/main/package_reference/lora)
- [TRL SFTTrainer](https://huggingface.co/docs/trl/en/sft_trainer)
- [bitsandbytes installation and hardware compatibility](https://huggingface.co/docs/bitsandbytes/installation)
- [Qwen2.5-0.5B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)

## 8. Pattern/Skill 锻造判定

本次不新增 Pattern Card 或 Skill。原因是训练、模板、量化和评估方法均已由既有 R 系列报告覆盖；R159 的新增价值是把已有知识和一次真实实验绑定成个性化学习桥梁，尚未形成需要独立自动化的全新稳定流程。

## 9. 家庭电脑复现包

已新增单文件家庭复现手册 `HOME_REPRODUCTION_GUIDE.md`，并生成便携包 `small-model-lora-home-repro-2026-08-07.zip`。归档包含源码、测试、固定数据、参考结果和已验证直接依赖版本；排除 `.venv`、模型缓存、checkpoint、Adapter 与 Python 缓存，要求在目标电脑重新下载基座并亲手训练。

归档验证结果：29 个 ZIP 条目，必需文件缺失 0，禁止项 0；从 ZIP 解压后运行项目测试为 3/3 通过。归档 SHA-256：`DD189A8DEB21CF49F5B7740E4D520A2C6D929A4A590D7F416DFD6962BD57B2BD`。
