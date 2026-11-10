> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 分支管理stash操作规范

## 触发规则
当需要切换分支但存在未提交更改时，触发stash操作。

## 所需工具
- Git命令行工具或支持stash功能的IDE

## 执行流程
1. 保存当前工作区更改到stash：
   ```bash
   git stash save "切换分支前暂存 2026-06-30"
   ```
2. 切换目标分支：
   ```bash
   git checkout target_branch
   ```
3. 恢复stash内容（可选）：
   ```bash
   git stash apply stash@{0}
   ```
4. 清理stash记录（可选）：
   ```bash
   git stash drop stash@{0}
   ```
5. 查看stash列表：
   ```bash
   git stash list
   ```

## 证据规则
- stash记录：`git stash list`显示的stash条目
- 分支切换日志：`git log`显示的分支切换记录

## 失败模式
- stash丢失：未正确保存stash记录
- 未恢复更改：切换分支后未恢复stash内容
- stash冲突：stash内容与目标分支代码冲突

## 边界
- 未提交更改范围：仅限于当前工作区的更改
- stash生命周期：默认保留至手动清理
