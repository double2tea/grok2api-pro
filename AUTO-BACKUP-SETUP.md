# Auto-Backup System Setup

## ✅ **已完成配置**

### Git Hooks

| Hook | 功能 | 触发时机 |
|------|------|----------|
| **pre-commit** | 代码质量检查 | 每次提交前 |
| **pre-checkout** | 自动暂存 | 切换分支前 |
| **pre-merge** | 自动暂存 | 合并前 |

### Hookify Hooks

| Hook | 功能 | 触发时机 |
|------|------|----------|
| **auto-backup** | 执行计划前提醒 | 检测到"执行计划"时 |
| **execute-plan** | 子代理自动触发 | 检测到计划执行时 |

## 📝 **Git Hooks详情**

### pre-commit Hook
```bash
# 自动检查：
✅ 合并冲突标记（阻止提交）
✅ 敏感信息泄露（阻止提交）
✅ JavaScript/TypeScript语法
✅ 调试代码（警告）
✅ TODO/FIXME（警告）
✅ 大文件检测（警告）
```

### pre-checkout Hook
```bash
# 自动暂存：
✅ 未提交的工作区更改
✅ 已暂存的更改
# 自动恢复：git stash pop
```

### pre-merge Hook
```bash
# 自动暂存：
✅ 未提交的工作区更改
✅ 已暂存的更改
# 自动恢复：git stash pop
```

## 💡 **使用指南**

### 自动备份触发

**自动（无需操作）：**
- 切换分支前 → 自动暂存
- 合并前 → 自动暂存
- 提交前 → 代码质量检查

**手动触发：**
```bash
# 执行计划前备份
git stash push -m "Plan backup - $(date)"

# 快速备份提交
git add . && git commit -m "Quick backup $(date +'%H:%M')"
```

### 检查命令

```bash
# 查看工作区状态
git status

# 查看暂存列表
git stash list

# 查看最近提交
git log --oneline -5

# 查看所有hooks
ls -la .git/hooks/
```

## 🚀 **自动备份流程**

### 场景1：切换分支
```bash
git checkout feature-branch
# 自动触发 pre-checkout
# 自动暂存未提交更改
```

### 场景2：合并分支
```bash
git merge feature-branch
# 自动触发 pre-merge
# 自动暂存未提交更改
```

### 场景3：执行计划
```
用户：我要开始执行用户认证功能
# 自动触发 Hookify auto-backup
# 提醒用户手动备份
```

### 场景4：提交代码
```bash
git commit -m "Add feature"
# 自动触发 pre-commit
# 自动检查代码质量
```

## ✅ **备份原则**

1. **自动优先** - Git hooks自动处理
2. **手动补充** - 重要操作前手动备份
3. **及时恢复** - 操作完成后及时恢复
4. **定期清理** - 清理过期的暂存记录

## 🔧 **故障排除**

### 暂存冲突
```bash
# 查看冲突
git stash list
git stash show -p stash@{0}

# 手动解决
git stash pop
# 手动合并冲突
git add .
git commit -m "Resolve stash conflict"
```

### 跳过检查
```bash
# 紧急情况跳过pre-commit
git commit --no-verify -m "Emergency commit"
```

### 恢复所有暂存
```bash
# 恢复最新的暂存
git stash pop

# 查看并选择恢复
git stash list
git stash apply stash@{1}
```

## 📊 **总结**

**已设置的自动备份：**
- ✅ pre-commit - 代码质量保护
- ✅ pre-checkout - 分支切换保护
- ✅ pre-merge - 合并操作保护
- ✅ Hookify提醒 - 执行计划前备份

**不再担心：**
- ❌ 忘记备份代码
- ❌ 切换分支丢失更改
- ❌ 合并时冲突
- ❌ 提交低质量代码

**现在可以：**
- ✅ 放心大胆实验
- ✅ 快速回滚
- ✅ 安全分支操作
- ✅ 自动化备份
