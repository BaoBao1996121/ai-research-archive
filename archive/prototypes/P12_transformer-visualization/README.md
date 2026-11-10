> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P12 Transformer 可视化学习台

> 面向 Transformer 原理学习的静态交互课件：用 token、热力图、滑块和自测卡解释 Self-Attention、Causal Mask、Multi-Head、Position Encoding 和 Transformer Block。

## 打开方式

直接打开本目录下的 `index.html`，或从万宝楼点击“Transformer 可视化学习台”的“打开演示”。

## 功能

- Self-Attention：用“他”参考“小明”的例子展示当前 token 如何从全句取信息。
- Causal Mask：展示生成模型为什么不能看未来 token。
- Multi-Head：展示不同头可学习不同关注模式。
- Position Encoding：展示词序为什么必须进入模型，以及 RoPE 的旋转直觉。
- Transformer Block：解释 Attention、FFN、残差连接和 LayerNorm 的分工。

## 来源

- 基础报告：`reports/01-理论与架构/R37_Transformer原理从直觉到代码.md`
- 归档日期：2026-06-28
