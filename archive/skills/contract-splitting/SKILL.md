> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Contract拆分规则优化

## 触发规则
当Contract拆分的Slot Recall低于阈值（默认0.8）时，触发规则优化流程。

## 所需工具
- 测试脚本：`tests/test_composite_contract_acceptance_policy.py`
- 质量Oracle脚本：`scripts/kb/run_composite_quality_oracle.py`

## 执行流程
1. **分析现有拆分规则**：
   - 查看当前的Contract拆分逻辑和Acceptance Policy。
   - 识别导致Slot Recall低的具体规则或条件。

2. **优化拆分规则**：
   - 调整或新增拆分规则，以覆盖更多Slot场景。
   - 确保优化后的规则不会显著影响Slot Precision。

3. **补充测试用例**：
   - 针对优化后的规则，新增边界条件和典型场景的测试用例。
   - 确保测试覆盖率提升至90%以上。

4. **运行测试和验证**：
   - 执行测试脚本，验证Slot Recall是否提升至目标值（0.8以上）。
   - 使用质量Oracle脚本，确保优化后的Contract质量符合预期。

5. **记录和提交优化结果**：
   - 记录优化后的规则、测试结果和质量指标。
   - 提交代码变更至版本控制系统。

## 证据规则
- 测试覆盖率：优化后测试用例需覆盖至少90%的拆分场景。
- Slot Recall：优化后需达到0.8以上。
- 质量Oracle通过率：优化后的Contract需通过质量Oracle的Gate指标。

## 失败模式
- **Recall未提升**：优化后的规则未能显著提升Slot Recall。
  - 解决方案：重新分析规则，补充更多边界条件。
- **Precision下降**：优化后的规则导致Slot Precision显著下降。
  - 解决方案：调整规则，平衡Precision和Recall。
- **测试覆盖率不足**：新增测试用例未能覆盖关键场景。
  - 解决方案：补充更多测试用例，确保覆盖率达标。

## 边界
- 仅适用于高置信度Contract场景。
- 优化过程中需确保性能影响在可接受范围内（待验证）。
- 适用于当前的Contract结构和Acceptance Policy框架。
