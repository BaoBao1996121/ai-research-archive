> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../../ARCHIVE_POLICY.md)阅读。

# RAG优化流程

## 结论
RAG链路优化流程包括基准固定参照机制、runtime差距分析方法和Negative/Boundary归因框架，旨在提升RAG链路的准确性和性能。

## 背景
在RAG链路优化过程中，发现runtime与terminal之间的差距较大，主要由route和guard引起。为了系统性地解决这一问题，需要建立一套完整的优化流程，包括基准固定参照机制、runtime差距分析方法和Negative/Boundary归因框架。

## 证据
1. **Hit@5数据**：runtime Hit@5为0.5357，表明当前RAG链路的准确性有待提升。
2. **Negative/Boundary分析**：Negative/Boundary需要区分guard和prompt问题，进一步分析FAIL和WARN。
3. **工具调用**：通过会话和工具调用，提取了trace耗时数据，发现当前trace阶段耗时定义无法直接相加。

## 方案取舍
1. **系统性优化**：选择建立基准固定参照机制、runtime差距分析方法和Negative/Boundary归因框架，进行全面优化。
2. **避免局部优化**：不单独优化某一部分，而是从整体出发，确保优化效果的全面性和可持续性。

## 建议路线
1. **分析Negative/Boundary的FAIL和WARN**：深入分析Negative/Boundary的FAIL和WARN，区分guard和prompt问题，优化RAG链路的准确性和性能。
2. **优化route和guard**：针对route和guard进行优化，减少runtime与terminal之间的差距。
3. **验证耗时定义**：检查diagnostics.py中的耗时定义，确保trace阶段耗时数据的准确性。
4. **集成benchmark**：选择langchain或evaluate作为第三方框架，集成到当前benchmark中，提升benchmark的质量和全面性。

通过以上步骤，可以系统性地优化RAG链路，提升其准确性和性能，为后续的优化工作奠定坚实的基础。
