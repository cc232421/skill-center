---
name: claude_first_10k
display_name: Claude首10K用户增长
description: |
  负责Claude Pro/Team订阅用户从0增长到首10K的完整增长策略。
  触发场景：
  - 用户问"如何获取首批用户"、"冷启动怎么做"
  - 用户问"增长黑客方法"、"裂变增长策略"
  - 用户问"增长策略"、"用户获取策略"
  - 用户提到"早期用户"、"种子用户"、"MVP推广"
  - 用户要求制定"增长计划"、"用户增长方案"
  - 用户问"增长指标"、"如何衡量增长"
  - 制定用户增长方案时使用此技能
trigger:
  - 首10K*
  - 用户增长
  - 增长策略
  - 增长黑客
  - 冷启动
  - 种子用户
  - 裂变*
  - 增长计划
  - 用户获取
  - MVP*推广
  - 如何获取首批用户
---

# Claude首10K用户增长 Skill

## 核心职责

接收一个增长诊断上下文，返回完整的增长策略报告，涵盖：痛点分析、资源过滤、用户画像、定价策略、增长计划和内容复用建议。

## 输入格式

技能接受以下参数（全部可选，skill 根据对话上下文填充）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_type | string | 否 | 产品类型：saas/consumer/marketplace等 |
| target_geography | string | 否 | 目标市场：CN/US/EU/东南亚等 |
| current_stage | string | 否 | 当前阶段：idea/mvp/launched/post_money |
| budget_range | string | 否 | 预算范围：shoestring/tight/modest/comfortable |
| current_users | int | 否 | 当前用户数 |
| main_problem | string | 否 | 用户反馈中最突出的1-2个痛点（原文） |
| revenue_model | string | 否 | 营收模式：subscription/freemium/transaction/ads |
| competitors | string | 否 | 主要竞品（逗号分隔） |

## FSM 状态机

技能内部维护以下状态（存储在 Skill 内存中，不同时跨会话）：

```
IDLE → DIAGNOSIS → PLANNING → VALIDATION → EXECUTION → REVIEW
```

| 状态 | 说明 |
|------|------|
| IDLE | 无输入，等待触发 |
| DIAGNOSIS | 分析产品类型、目标市场、预算，识别核心痛点 |
| PLANNING | 制定增长战略、路径、优先级 |
| VALIDATION | 检查资源充足性，评估方案可行性 |
| EXECUTION | 输出完整策略报告 |
| REVIEW | 检查报告完整性，补充遗漏模块 |

## 7大增长模块（Pipeline）

### 模块A — Stage Router（阶段路由）

根据 `current_stage` 和 `budget_range` 判断增长阶段：

| Stage | 增长策略 |
|-------|---------|
| idea | 100次访谈+精益测试 |
| mvp | 用户画像+定价测试 |
| launched | 渠道优先级排序 |
| post_money | 规模化增长 |

### 模块B — Pain Analyzer（痛点分析）

对用户反馈进行结构化分析：
- 提取核心痛点（高频词/句）
- 区分"功能型痛点"（需要功能）和"情绪型痛点"（需要安全感）
- 关联痛点 → 增长杠杆（内容素材/定价锚点/用户故事）
- 输出：痛点评级（p0/p1/p2）、可复用素材片段

### 模块C — Resource Filter（资源过滤器）

根据 `budget_range` 过滤可选增长手段：

| 预算 | 可用手段 |
|------|---------|
| shoestring | 内容营销、社区运营、口碑裂变 |
| tight | +SEO/ASO、基础付费渠道 |
| modest | +中小KOL合作、付费广告测试 |
| comfortable | +全渠道铺开、补贴获客 |

### 模块D — Buyer Parser（用户画像）

构建目标用户画像：
- 基础属性：角色/公司规模/行业/使用场景
- 决策链：EB(经济决策者)/TB(技术决策者)/UO(用户)
- 痛点映射：痛点 → 情绪 → 购买动机
- 渠道偏好：ABM/内容触达/活动/demo

### 模块E — Pricing Advisor（定价策略）

根据营收模型和产品类型给出定价建议：
- Freemium：免费层设计逻辑、免费→付费转化点
- Subscription：锚定定价、心理定价、版本分层
- Transaction：抽佣比例、GMV激励
- Ads：Fill Rate预估、CPM区间

### 模块F — Plan Builder（增长计划）

综合以上模块，输出结构化增长计划：

1. **北极星指标**（单一定量指标）
2. **增长路径图**（Phase 1-3，每阶段目标+策略）
3. **优先级矩阵**（Impact × Ease 2×2）
4. **关键里程碑**（OKR格式）
5. **预算分配建议**

### 模块G — Content Repurposer（内容复用）

将增长计划转化为可执行的内容资产：
- 增长故事文案（用于传播）
- 用户案例模板（用于social proof）
- FAQ清单（用于客服+SEO）
- 传播素材建议（用于裂变/口碑）

## 错误代码

| 代码 | 含义 | 处理方式 |
|------|------|---------|
| E001 | 缺少产品类型 | 询问用户或使用默认值 "saas" |
| E002 | 缺少目标市场 | 询问用户或使用默认值 "CN" |
| E003 | 缺少预算范围 | 询问用户或使用默认值 "tight" |
| E004 | 缺少核心痛点 | 询问用户或生成推测性痛点列表 |
| E005 | 缺少营收模式 | 询问用户或使用默认值 "subscription" |
| E006 | 阶段识别失败 | 回退到 "launched" 默认阶段 |
| E007 | 资源评估失败 | 降低增长策略野心，保守估算 |
| E008 | 增长计划不完整 | 自动补充缺失模块 |
| E009 | 内容素材不足 | 输出"待填充"占位符，标注需要运营补全 |
| E010 | 预算超出范围 | 使用最接近的可用预算档 |
| E011 | 竞品数据缺失 | 跳过竞品对比模块 |
| E012 | 用户画像不清晰 | 生成假设性画像并标注"需验证" |
| E013 | 定价策略冲突 | 提供3种定价方案供选择 |
| E014 | 增长路径歧义 | 输出多条路径并标注各自适用条件 |
| E015 | 里程碑不SMART | 自动改写为SMART格式 |
| E016 | 渠道优先级排序失败 | 按通用转化率排序并说明假设 |

## 中国市场本地化

当 `target_geography` 为 `CN` 时，额外执行：

1. **平台映射**
   - App Store → 应用宝/华为应用市场
   - Google Ads → 巨量引擎/腾讯广告
   - Facebook → 微信生态/抖音
   - SEO → 小红书/知乎/百度

2. **合规要求**
   - ICP备案/文网文证建议提醒
   - 数据本地化存储建议
   - 广告审核规避建议

3. **KOL渠道**
   - 优先级：KOC种草 > 腰部KOL > 头部KOL
   - 平台选择：小红书（种草）/ 抖音（品牌）/ B站（深度）/ 知乎（信任）

4. **裂变合规**
   - 微信分享限制 → 替代：海报+私信/公众号
   - 诱导分享风险 → 使用"邀请得XXX"替代"分享得XXX"

## OpenClaw集成

技能内部调用以下OpenClaw框架模块（可选，取决于 `SEL_DATA_DIR` 环境变量）：

```python
# 记录决策快照
from decision_snapshot import save_snapshot

snapshot = save_snapshot(
    symbol="claude_first_10k",
    action="growth_plan",
    price=0.0,
    regime="planning",
    regime_confidence=0.8,
    strategy="first_10k",
    reason="growth_strategy_generated",
    market=market,
    period="once",
)

# 记录增长教训
from self_review_and_extract import extract_lesson
lesson = extract_lesson(snapshot_ids=[snapshot["snapshot_id"]])
```

## 输出格式

技能返回以下结构：

```python
{
  "skill_version": "2.0",
  "stage": "EXECUTION",
  "inputs_received": {...},        # 原始输入参数
  "pain_analysis": {
    "primary_pains": [{"pain": str, "rating": "p0"|"p1"|"p2", "leverage": str}],
    "secondary_pains": [...],
    "emotional_pains": [...],
    "content_fragments": [str],
  },
  "buyer_personas": [
    {
      "name": str,
      "role": str,
      "company": str,
      "decision_chain": "EB"|"TB"|"UO",
      "key_motivation": str,
      "channel_preference": str,
    }
  ],
  "pricing_advice": {
    "model": str,
    "recommended_tiers": [{"name": str, "price": float, "features": [str]}],
    "anchoring_strategy": str,
  },
  "growth_plan": {
    "north_star_metric": str,
    "phases": [
      {
        "phase": "Phase 1",
        "duration": str,
        "goal": str,
        "strategies": [str],
        "metrics": [{"metric": str, "target": str}],
        "budget_hint": str,
      }
    ],
    "priority_matrix": [[str, str, str, str]],  # 2x2
    "okrs": [{"objective": str, "key_results": [str]}],
  },
  "china_localization": {...} | None,   # 仅当 target_geography=CN 时
  "content_assets": {
    "growth_story": str,
    "user_case_template": str,
    "faq_list": [{"q": str, "a": str}],
    "viral_suggestion": str,
  },
  "errors": [{"code": str, "message": str}],   # 本次处理中遇到的错误
}
```

## 工作流程

### Step 1: DIAGNOSIS

接收输入参数 → 识别缺失字段 → 填充默认值或询问用户 → 调用 Stage Router

### Step 2: PLANNING

- 调用 Pain Analyzer 提取痛点
- 调用 Resource Filter 过滤手段
- 调用 Buyer Parser 构建画像
- 调用 Pricing Advisor 给出定价建议

### Step 3: VALIDATION

- 检查资源充足性
- 评估方案可行性
- 如有冲突，触发 E013/E014 并提供备选方案

### Step 4: EXECUTION

- 调用 Plan Builder 生成增长计划
- 调用 Content Repurposer 生成内容资产
- 中国市场时调用本地化模块

### Step 5: REVIEW

- 检查报告完整性
- 补充缺失模块
- 可选：调用 OpenClaw 框架记录快照

## 示例对话

**用户**: 我做了一个AI写作工具，面向中国市场的年轻创作者，预算很紧（<1万），目前MVP阶段，有什么增长建议？
**Skill 行为**:
1. 识别 `product_type=saas`, `target_geography=CN`, `budget_range=shoestring`, `current_stage=mvp`
2. Stage Router → MVP阶段策略
3. Pain Analyzer → AI写作痛点提取
4. Resource Filter → 预算紧张手段：内容营销+社区运营+口碑裂变
5. Buyer Parser → 创作者画像（UO为主）
6. Pricing Advisor → 免费+付费订阅
7. China Localization → 小红书种草/知乎信任/抖音品牌
8. Plan Builder → Phase 1-3增长路径
9. Content Repurposer → 增长故事+FAQ

**用户**: 帮我看看增长计划里的指标合理吗
**Skill 行为**: 调用 REVIEW 状态 → 检查指标 SMART 格式 → 如不满足自动改写（E015）

## 错误处理

- E001-E005：缺失必填信息 → 使用默认值填充并标注"推测"
- E006-E007：识别/评估失败 → 降级到保守策略
- E008-E009：完整性问题 → 自动补充或输出占位符
- E010-E016：边界情况 → 提供备选方案并说明原因

所有错误合并到 `errors` 字段，不阻断主流程。