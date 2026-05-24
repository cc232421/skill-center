---
name: ai-weekly-digest
description: AI 干货周报生成器 - 扫描 65 个顶级 AI Twitter 账号，筛选高价值内容，生成结构化周报
allowed-tools: Bash, Read, Write, Edit
---

# AI 干货周报生成器

## 概述

自动扫描 65 个顶级 AI Twitter 账号的最近推文（过去 7 天），根据实用价值筛选高优先级内容，生成结构化 Markdown 周报。

## 工作流程

```
1. fetch_all.py     → 批量获取 65 个账号的推文
2. filter_content.py → 根据 Priority 1-3 标准筛选
3. generate_report.py → 生成 Markdown 周报
```

## 使用方法

### 完整流程

```bash
cd ~/.Codex/skills/ai-weekly-digest
python3 scripts/run_weekly_digest.py
```

### 单独运行

```bash
# 第一步：获取所有推文
python3 scripts/fetch_all.py --days 7 --limit 20

# 第二步：筛选高价值内容
python3 scripts/filter_content.py --input data/tweets.json --output data/filtered.json

# 第三步：生成周报
python3 scripts/generate_report.py --input data/filtered.json --output weekly-digest.md
```

### 参数选项

**fetch_all.py:**
- `--days N` - 回溯天数（默认 7）
- `--limit N` - 每个账号获取推文数（默认 20）
- `--parallel N` - 并行数量（默认 5）
- `--output PATH` - 输出路径（默认 data/tweets.json）

**filter_content.py:**
- `--input PATH` - 输入文件（tweets.json）
- `--output PATH` - 输出文件（filtered.json）
- `--min-priority N` - 最低优先级（1-3，默认 1）

**generate_report.py:**
- `--input PATH` - 筛选后的 JSON 文件
- `--output PATH` - 输出 Markdown 文件
- `--title TITLE` - 周报标题

## 65 个目标账号

### 🏢 机构账号（17个）

@OpenAI, @GoogleDeepMind, @nvidia, @NVIDIAAI, @AnthropicAI, @MetaAI, @deepseek_ai, @Alibaba_Qwen, @midjourney, @Kimi_Moonshot, @MiniMax_AI, @BytedanceTalk, @DeepMind, @GoogleAI, @GroqInc, @Hailuo_AI, @MIT_CSAIL

### 👤 个人账号（48个）

@elonmusk, @sama, @zuck, @demishassabis, @DarioAmodei, @karpathy, @ylecun, @geoffreyhinton, @ilyasut, @AndrewYNg, @jeffdean, @drfeifei, @Thom_Wolf, @danielaamodei, @gdb, @GaryMarcus, @JustinLin610, @steipete, @ESYudkowsky, @erikbryn, @alliekmiller, @tunguz, @Ronald_vanLoon, @DeepLearn007, @nigewillson, @petitegeek, @YuHelenYu, @TamaraMcCleary, @swyx, @joshwoodward, @kevinweil, @petergyang, @thenanyu, @realmadhuguru, @_catwu, @trq212, @amasad, @rauchg, @alexalbert__, @levie, @ryolu_, @mattturck, @zarazhangrui, @nikunj, @danshipper, @adityaag

## 筛选标准

### ✅ Priority 1: 立刻能用（Immediately Usable）

- 工具、插件或应用，能解决实际问题
- 分步教程或指南
- Prompt 模板或框架
- 工作流优化技巧

### ✅ Priority 2: 可复用方法论（Reusable Methodologies）

- 内容创作工作流
- AI 使用最佳实践
- 生产力技巧
- Skill 构建框架

### ✅ Priority 3: 思维转变（Mindset Shifts）

- 如何以不同方式思考 AI
- 常见错误及避免方法
- 专家对 AI 使用模式的洞察

### ❌ 排除规则

- 技术基础设施（GPU、TPU、算力）
- 网络安全专业内容
- 没有实际应用的学术论文
- 企业/B2B 公告（除非对个人直接有用）
- 融资/营收新闻
- 模型基准测试和技术对比

## 输出格式

### 周报模板

```markdown
# AI 干货周报 - 内容创作者必看

**扫描时间:** [当前日期]
**数据源:** 65个顶级 AI Builder 账号
**筛选标准:** ✅ 立刻能用 | ✅ 工作流改进 | ✅ 可复用方法论

---

## 🔥 本周最实用的内容

### 1. **[标题]**

**账号:** @handle
**类型:** [🛠️ 可复用方法 | 💡 工作流优化 | 📝 提示词技巧 | 🚀 新工具]

**核心方法/技巧:**
- [要点 1]
- [要点 2]

**为什么有用:**
[1-2句话说明实际价值]

**链接:** [推文链接]

---

## 📊 筛选统计

- **扫描账号数:** 65 个
- **时间范围:** 过去7天
- **筛选出的实用内容:** X 条
```

## 依赖

- tweety-ns（从 twitter-crawler 的 venv 加载）
- python-dateutil
- pyyaml

## 注意事项

1. 需要有效的 auth_token 才能获取推文
2. Twitter 有频率限制，脚本会自动处理
3. 建议每周运行一次生成周报
4. 可通过 `--parallel` 调整并行数量加快获取速度