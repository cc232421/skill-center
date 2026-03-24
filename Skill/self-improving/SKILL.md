---
name: self-improving
description: Self-reflection + Self-criticism + Self-learning for OpenCode. Learns from user corrections, self-reflects after tasks, and compounds execution quality over time. Triggers: 记住, 错了, 不对, 偏好, 记忆状态, 你学到了什么, 我的习惯.
---

# Self-Improving for OpenCode

自我反思 + 自我批评 + 自我学习。OpenCode 评估自己的工作，捕捉错误，并持续改进。

## Architecture / 架构

```
~/self-improving/
├── memory.md          # HOT: ≤100 lines, always loaded
├── index.md           # Topic index with line counts
├── corrections.md     # Last 50 corrections log
├── projects/          # Per-project learnings
├── domains/           # Domain-specific (code, writing, comms)
└── archive/           # COLD: decayed patterns
```

## Trigger Signals / 触发信号

### 1. Correction Signals / 修正信号

**中文触发词：**
| 触发词 | 示例 |
|--------|------|
| 不对 | "不对，应该是..." |
| 错了 | "错了，应该是这样" |
| 不是这样的 | "不是这样的，应该..." |
| 其实应该是 | "其实应该是 X" |
| 你说错了 | "你说错了，X 才是对的" |
| 我更喜欢 | "我更喜欢 X，不是 Y" |
| 用 X 别用 Y | "用 X，别用 Y" |
| 记住我总是 | "记住我总是这样做的" |
| 我跟你说过了 | "我跟你说过了，要..." |
| 我之前说过了 | "我之前说过了..." |
| 别 | "别这样做" |
| 不要 | "不要用 X" |
| 你怎么老是 | "你怎么老是这样" |
| 为什么你总是 | "为什么你总是..." |
| 停 | "停，这不是我想要的" |

**English equivalents:**
- "No, that's not right..."
- "Actually, it should be..."
- "You're wrong about..."
- "I prefer X, not Y"
- "Remember that I always..."
- "I told you before..."
- "Stop doing X"
- "Why do you keep..."

### 2. Preference Signals / 偏好信号

**中文触发词：**
| 触发词 | 示例 |
|--------|------|
| 我喜欢 | "我喜欢简洁的回答" |
| 总是 | "总是用中文回复" |
| 一定要 | "一定要先检查" |
| 永远不要 | "永远不要用 Tab" |
| 千万别 | "千万别删代码" |
| 我的风格是 | "我的风格是简洁直接" |
| 我习惯 | "我习惯用 YYYY-MM-DD" |
| 这个项目用 | "这个项目用 pnpm" |

**English equivalents:**
- "I like when you..."
- "Always do X for me"
- "Never do Y"
- "My style is..."
- "For [project], use..."

### 3. Memory Queries / 记忆查询

**中文触发词：**
| 触发词 | 动作 |
|--------|------|
| 你知道 X 吗 | 搜索所有层级 |
| 关于 X 你知道什么 | 搜索所有层级 |
| 你学到了什么 | 显示最近 10 条修正 |
| 学到了什么 | 显示最近修正 |
| 记住了什么 | 显示最近修正 |
| 我的习惯 | 显示 HOT 层 memory.md |
| 我的偏好 | 显示 HOT 层 memory.md |
| 我的模式 | 显示 HOT 层 memory.md |
| 记忆状态 | 显示统计信息 |
| 记忆统计 | 显示 tier 统计 |
| 记忆情况 | 显示 tier 统计 |
| 忘掉 X | 从所有层级删除 |
| 删除 X | 从所有层级删除 |
| 忘记 X | 从所有层级删除 |

**English equivalents:**
- "What do you know about X?"
- "What have you learned?"
- "Show my patterns"
- "Memory stats"
- "Forget X"

### 4. Self-Reflection / 自我反思

**After completing significant work, evaluate:**
```
CONTEXT: [任务类型]
REFLECTION: [我注意到什么]
LESSON: [下次要怎样做]
```

**When to reflect:**
- 完成多步骤任务后
- 收到反馈后
- 修复 bug 后
- 发现输出可以更好时

## Core Workflow / 核心流程

### On Correction Detected / 检测到修正

```
1. 解析修正类型 (preference, pattern, override)
2. 检查是否重复 (corrections.md)
3. 如果是新修正:
   - 添加到 ~/self-improving/corrections.md 带时间戳
   - 计数 +1
4. 如果是重复:
   - 计数 +1，更新时间戳
   - 如果计数 >= 3: 询问是否确认为规则
5. 写入对应文件:
   - 全局 → ~/self-improving/memory.md
   - 领域 → ~/self-improving/domains/{domain}.md
   - 项目 → ~/self-improving/projects/{project}.md
6. 更新 ~/self-improving/index.md
```

### On Memory Query / 记忆查询

**"你知道 X 吗" / "What do you know about X?"**
→ 搜索所有层级，返回匹配结果和来源

**"你学到了什么" / "What have you learned?"**
→ 显示 corrections.md 最近 10 条

**"我的习惯" / "Show my patterns"**
→ 显示 memory.md (HOT 层)

**"记忆状态" / "Memory stats"**
```
📊 自我改进记忆

🔥 HOT (始终加载):
  memory.md: X 条目

🌡️ WARM (按需加载):
  projects/: X 文件
  domains/: X 文件

❄️ COLD (归档):
  archive/: X 文件

最近 7 天:
  记录修正: X
  确认规则: X
  模式: 被动
```

**"忘掉 X" / "Forget X"**
→ 从所有层级删除 (需确认)

## Tiered Storage / 分层存储

| Tier | Location | Limit | Behavior |
|------|----------|-------|----------|
| HOT | memory.md | ≤100 行 | 始终可访问 |
| WARM | projects/, domains/ | ≤200 行 | 上下文匹配时加载 |
| COLD | archive/ | 无限 | 显式查询时加载 |

## Promotion Rules / 升级规则

- **7 天内使用 3 次** → 升级到 HOT (memory.md)
- **30 天未使用** → 降级到 WARM
- **90 天未使用** → 归档到 COLD
- **绝不未经询问删除**

## Conflict Resolution / 冲突解决

模式冲突时:
1. 最具体的胜出 (project > domain > global)
2. 最新的胜出 (同一层级)
3. 不明确时询问用户

## Complete Trigger Reference / 完整触发词对照表

### 修正类 / Corrections

| English | 中文 |
|---------|------|
| "No, that's not right..." | "不对", "错了", "不是这样的" |
| "Actually, it should be..." | "其实应该是...", "应该是..." |
| "You're wrong about..." | "你说错了", "你搞错了" |
| "I prefer X, not Y" | "我更喜欢 X", "用 X 别用 Y" |
| "Remember that I always..." | "记住我总是...", "我一直..." |
| "I told you before..." | "我跟你说过了", "我之前说过了" |
| "Stop doing X" | "别做", "不要", "停" |
| "Why do you keep..." | "你怎么老是", "为什么你总是" |

### 偏好类 / Preferences

| English | 中文 |
|---------|------|
| "I like when you..." | "我喜欢", "我喜欢你..." |
| "Always do X for me" | "总是", "一定要", "永远" |
| "Never do Y" | "永远不要", "千万别", "不要" |
| "My style is..." | "我的风格是", "我习惯..." |
| "For [project], use..." | "这个项目用...", "这个项目..." |

### 查询类 / Queries

| English | 中文 |
|---------|------|
| "What do you know about X?" | "你知道 X 吗", "关于 X 你知道什么" |
| "What have you learned?" | "你学到了什么", "学到了什么" |
| "Show my patterns" | "我的习惯", "我的偏好", "我的模式" |
| "Memory stats" | "记忆状态", "记忆统计", "记忆情况" |
| "Forget X" | "忘掉 X", "删除 X", "忘记 X" |

## Transparency / 透明性

- 每次使用记忆 → 引用来源: "Using X (from memory.md:12)"
- 绝不从沉默中推断偏好

## Security Boundaries / 安全边界

本技能绝不:
- 存储凭证、健康数据、第三方密钥
- 发出网络请求
- 读取 ~/self-improving/ 以外的文件
- 从沉默或观察中推断偏好
- 修改自身的 SKILL.md

## Quick Reference / 快速参考

| Command | 命令 | Action |
|---------|------|--------|
| Log correction | 记录修正 | 追加到 corrections.md |
| Confirm pattern | 确认规则 | 3次后移到 memory.md |
| Self-reflect | 自我反思 | 使用 CONTEXT/REFLECTION/LESSON 格式 |
| Query memory | 查询记忆 | 搜索 ~/self-improving/ |
| Memory stats | 记忆状态 | 显示 tier 统计 |
| Forget pattern | 忘记规则 | 确认后从所有层级删除 |
