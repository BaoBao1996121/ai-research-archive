> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# AgentLoop学习计划

## 结论
AgentLoop学习计划的初步实施暴露了若干关键问题，包括Runtime未进入主路径、ToolPipeline未被触发以及AssignmentContract未正确集成。这些问题表明当前AgentLoop的设计和实现需要进一步优化和验证。

## 背景
AgentLoop是整个Crazy项目的核心组件，负责协调模型与工具之间的交互，管理上下文生命周期，并确保任务的可靠执行。AgentLoop的状态机设计和错误恢复机制是其成功的关键。然而，当前的实现中存在一些未解决的问题，这些问题可能会影响整个系统的稳定性和功能性。

## 证据
1. **Runtime未进入主路径**：在测试中发现，Runtime未按预期进入主路径，导致Context生命周期管理出现问题。
2. **ToolPipeline未被触发**：在单次端到端测试中，ToolPipeline未被触发，可能是因为ToolRegistry未正确传入AgentLoop。
3. **AssignmentContract未进入AgentLoop**：模型动作的Schema缺少Assignment接口，导致AssignmentContract未被正确处理。

## 方案取舍
1. **状态机设计**：当前的状态机设计需要进一步验证，以确保其能够正确处理各种异常情况和恢复机制。
2. **事件驱动设计**：另一种可能是采用事件驱动的设计，以提高系统的灵活性和可扩展性。

## 建议路线
1. **验证Runtime触发**：首先需要验证Runtime是否在team路径中被正确触发，确保Context生命周期管理正常。
2. **补充Assignment接口**：在AgentLoop中补充Assignment接口，确保AssignmentContract能够被正确处理。
3. **优化状态机设计**：根据测试结果，进一步优化AgentLoop的状态机设计，确保其能够正确处理各种异常情况和恢复机制。

## 下一步
1. **验证Runtime触发**：通过定向测试验证Runtime在team路径中的触发情况。
2. **补充Assignment接口**：在AgentLoop中补充Assignment接口，并进行相应的测试。
3. **优化状态机设计**：根据测试结果，优化AgentLoop的状态机设计，确保其能够正确处理各种异常情况和恢复机制。

## 风险与成本
1. **风险**：如果AgentLoop的状态机设计未能正确处理异常情况，可能导致系统不稳定或任务失败。
2. **成本**：需要投入额外的时间和资源来验证和优化AgentLoop的设计。

## 待验证
1. **Runtime触发机制**：需要进一步验证Runtime在team路径中的触发机制。
2. **Assignment接口补充**：需要验证补充Assignment接口后，AssignmentContract是否能够被正确处理。
3. **状态机设计优化**：需要验证优化后的状态机设计是否能够正确处理各种异常情况和恢复机制。
