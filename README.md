# Skill Center

OpenClaw skill 集合。

## Skills

### video-searcher

影视资源搜索 skill，一句话找到电影/剧集，直接返回可播放链接。

**触发词：** 找片、搜影视、看电影、找剧、免费看

**原理：**
1. TMDB API 搜索影视元数据
2. 获取 IMDB ID
3. 生成 VidSrc 嵌入播放链接
4. 返回可点击链接

**示例：**
```
用户: "找 肖申克的救赎"
返回: https://vidsrc.to/embed/movie/tt0111161
```

### carbonyl

终端里的 Chromium 浏览器 — 把网页渲染成 ANSI 彩色终端界面，无需显示器，支持 WebGL、音视频、60 FPS。

**触发词：** 终端浏览器、carbonyl、终端渲染网页、AI agent 访问网页、无界面浏览器

### cnblogs-post

发布博客文章到博客园 (cnblogs.com)。支持单篇文章发布、设置分类/标签、存草稿。

**触发词：** 发到博客园、发布到cnblogs、博客园发帖

### fredapi

FRED Economic Data — Python 库封装美联储经济数据 API，支持搜索、获取 GDP、CPI、失业率、利率等宏观经济指标。

**触发词：** economic data、FRED、GDP、CPI、inflation、unemployment rate、interest rates、US economy

### keyword-research

Discover high-value SEO keywords with search intent analysis, difficulty scoring, topic clustering, and AI citation potential.

**触发词：** find keywords、keyword research、keyword difficulty score、topic ideas、long-tail keyword

### lightpanda

Self-contained headless browser for AI agents (Zig, no Chrome needed). 9x faster, 16x less memory than Chrome headless. MCP tools for AI automation.

**触发词：** browse website、scrape、extract page content、headless browser、server-side browsing、lightpanda

### marketing-strategy-pmm

Product marketing skill for positioning, GTM strategy, competitive intelligence, and product launches. Covers April Dunford positioning, ICP definition, battlecards, launch playbooks.

**触发词：** product marketing、PMM、positioning、GTM strategy、go-to-market、competitive analysis、battlecard、product launch

### institutional-analysis

机构级个股分析工作流，覆盖 A 股/港股/美股，输出多维度数据、机构建模、评委裁决与完整研究报告。

**触发词：** 专业分析、机构分析

### investor-panel

50 位投资者评审团投票技能。基于个股维度数据生成每位投资者信号、投票分布与一致性结论。

**触发词：** 评审团、大佬怎么看、某某会买吗、做一次大佬投票

### lhb-analyzer

龙虎榜深度分析技能。识别游资席位，判断机构 vs 游资博弈，并做同板块龙虎榜辨识度对比。

**触发词：** 谁在买这只票、最近龙虎榜怎么样、X游资有没有上榜、这是不是X的票

### twitter-post

Post tweets to Twitter/X via the official API v2 (OAuth 1.0a). Supports single tweets, threads, replies, quote tweets with automatic character weight validation.

**触发词：** tweet、post to Twitter、post to X、send a thread、reply to a tweet
