> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Claim Shadow验证方案

## 问题
如何验证Claim Shadow对source-backed slot的召回率提升效果？

## 判断
Claim Shadow对source-backed slot有明显收益。

## 规则
1. **实验设计**：
   - 采用小样本因果消融实验
   - 对比Claim Shadow开启与关闭两种状态
   - 选择覆盖Claim anchor槽位的样本

2. **数据收集**：
   - 收集运行时日志（runtime_evidence）
   - 关注slot_count、claim_anchor_slot_count等指标
   - 记录latency_delta_ms等性能数据

3. **结果分析**：
   - 槽位匹配率提升：claim_added_slot_count增加
   - 知识库缺口减少：kb_gap_risk_count降低
   - 平均延迟优化：latency_delta_ms为负值

## 例外
- 当全量验证未完成时，结论仅适用于小样本
- 若性能瓶颈未解决，可能影响整体效果

## 检查清单
- [ ] 是否制定了小样本因果消融实验方案
- [ ] 是否收集了runtime_evidence日志
- [ ] 是否对比了claim_anchor_slot_count变化
- [ ] 是否分析了latency_delta_ms指标
- [ ] 是否评估了kb_gap_risk_count风险

## 待验证
- 全量验证的覆盖范围待进一步确认
- 性能优化的具体瓶颈待进一步分析
