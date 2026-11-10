> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# ASR文本清洗与意图识别方案

## 结论
推荐使用豆包ASR结合WeTextProcessing进行文本清洗，以及豆包LLM Function Calling进行意图识别，形成完整的语音处理方案。

## 背景
在语音交互系统中，ASR（自动语音识别）输出的文本可能存在噪声、语法错误或不准确的转录结果。同时，意图识别需要准确理解用户的语音指令，以提供合适的响应。因此，需要一套高效的文本清洗和意图识别方案。

## 证据
1. **ASR文本清洗**：
   - 调研了FunASR、WeTextProcessing和pycorrector等工具。
   - 分块摘要详细分析了工具优劣，豆包ASR结合WeTextProcessing表现最佳。
   - 证据强度：强。

2. **意图识别**：
   - 对比了豆包LLM Function Calling、Semantic Router和HF Zero-shot Classification等方案。
   - 分块摘要详细分析了方案优劣，豆包LLM Function Calling表现最佳。
   - 证据强度：强。

## 方案取舍
1. **ASR文本清洗**：
   - **FunASR**：功能全面，但配置复杂，不适合快速部署。
   - **WeTextProcessing**：轻量级，易于集成，适合实时处理。
   - **pycorrector**：专注于语法纠错，但对语音转录噪声处理能力有限。
   - **最终选择**：豆包ASR结合WeTextProcessing，兼顾准确性和易用性。

2. **意图识别**：
   - **Semantic Router**：适合复杂意图，但需要大量训练数据。
   - **HF Zero-shot Classification**：无需训练数据，但准确率有限。
   - **豆包LLM Function Calling**：支持零样本学习，准确率高，适合快速部署。
   - **最终选择**：豆包LLM Function Calling，支持零样本学习，准确率高。

## 建议路线
1. **ASR文本清洗**：
   - 配置热词表和替换词表，优化语音转录结果。
   - 集成WeTextProcessing进行文本清洗，提升文本质量。

2. **意图识别**：
   - 定义标准化的意图识别Schema。
   - 集成豆包LLM Function Calling，完成意图识别测试。

## 待验证
- 生产环境热词表配置尚未验证，可能导致产品名误识别。
- 意图识别Schema定义尚未完成，需进一步测试。

## 下次使用方式
- 验证热词表配置，确保语音转录准确性。
- 完成意图识别Schema定义，确保意图识别准确率。
- 集成完整方案，进行生产环境测试。
