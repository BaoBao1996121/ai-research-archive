> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Crazy Harness子模块实现

## 触发规则
当需要实现`Loop Engineering`和`Capability/Policy/Runtime`子模块时，触发此Skill。

## 所需工具
- 代码审查工具（如GitHub、GitLab）
- 测试框架（如pytest）
- 调试工具（如pdb、print语句）

## 执行流程
1. **检查触发条件**
   - 确认`Runtime`是否进入主路径
   - 确认`ToolPipeline`是否被触发
   - 确认`AssignmentContract`是否进入`AgentLoop`

2. **验证实现**
   - 查看`AgentLoop`的调用路径
   - 检查`ToolRegistry`是否传入`AgentLoop`
   - 确认`Assignment`接口是否补充到`AgentLoop`

3. **修复问题**
   - 如果`Runtime`未进入主路径，验证其在team路径中的触发
   - 如果`ToolPipeline`未被触发，检查`ToolRegistry`的传入
   - 如果`AssignmentContract`未进入`AgentLoop`，补充相应接口

4. **记录结果**
   - 更新代码审查记录
   - 记录测试结果
   - 更新调试日志

## 证据规则
- 代码审查记录
- 测试结果
- 调试日志

## 失败模式
- 触发条件未满足
- 验证失败
- 修复未解决问题

## 边界
- 仅适用于Crazy Harness子模块的实现
- 不处理其他模块的问题
