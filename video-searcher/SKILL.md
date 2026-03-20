---
name: video-searcher
description: "Search and watch movies/TV shows instantly. Use when user says: 找片, 搜影视, 看电影, 找剧, 免费看, watch movie, find show. Returns direct playable links with one click."
---

# Video Searcher

One-click movie and TV show search with direct playback links.

---

## Core Flow

```
用户输入影视名称
    ↓
搜索 TMDB 获取 IMDB ID
    ↓
生成播放链接
    ↓
返回可点击链接
```

---

## Step 1: Search TMDB

```
GET https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={电影名}
```

**关键字段:**
- `results[].id` → TMDB ID
- `results[].media_type` → movie / tv
- `results[].title` 或 `results[].name` → 影视名称
- `results[].release_date` / `first_air_date` → 年份
- `results[].vote_average` → 评分

---

## Step 2: Get IMDB ID

**Movie:**
```
GET https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_KEY}
```
→ 返回字段 `imdb_id`（如 `tt0111161`）

**TV Show** (⚠️ 必须用 external_ids 端点):
```
GET https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids?api_key={TMDB_KEY}
```
→ 返回字段 `imdb_id`（如 `tt0903747`）

> ⚠️ `/tv/{id}` 端点不返回 imdb_id，必须用 `/tv/{id}/external_ids`

---

## Step 2.5: 处理多个搜索结果

**单一结果** → 直接使用

**多个结果时:**
1. 列出前 3 个，让用户确认
2. 格式：`{序号}. 《{名称}》({年份}) - {类型} ⭐{评分}`

**示例：**
```
找到多个结果，请确认：
1. 《盗梦空间》Inception (2010) - 电影 ⭐8.4
2. Dreams: Cinema of the Subconscious (2010) - 纪录片
3. Inception: The Cobol Job (2010) - 动画短片
```

---

## Step 3: 生成播放链接

**Movie:**
```
Primary:   https://vidsrc.to/embed/movie/{imdb_id}
Backup 1:  https://vidsrc.icu/embed/movie/{imdb_id}
Backup 2:  https://cinemull.cc/movie/{imdb_id}
Backup 3:  https://2embed.cc/embed/{imdb_id}
```

**TV Show:**
```
Primary:   https://vidsrc.to/embed/tv/{imdb_id}/1
Backup 1:  https://vidsrc.icu/embed/tv/{imdb_id}/1
Backup 2:  https://cinemull.cc/tv/{imdb_id}/1
```
- 默认播放第1季第1集
- 指定集数：`/tv/{imdb_id}/S/E`（如 `/tv/tt0903747/1/3` = 第1季第3集）

---

## 输出格式

```
┌─────────────────────────────────────────┐
│ 🎬 《{电影名称}》                         │
│    {年份} · {类型}                        │
│    ⭐ {评分}                             │
├─────────────────────────────────────────┤
│ ▶️ 立即观看                              │
│ {Primary Link}                           │
│                                         │
│ 🔗 备选源                                │
│ • {Backup 1}                           │
│ • {Backup 2}                           │
└─────────────────────────────────────────┘
```

---

## 完整示例

**用户:** "找 肖申克的救赎"

**1. 搜索:**
```
GET https://api.themoviedb.org/3/search/multi?api_key=XXX&query=肖申克的救赎
```
→ 返回 `results[0].id=278, media_type=movie`

**2. 获取 IMDB ID:**
```
GET https://api.themoviedb.org/3/movie/278?api_key=XXX
```
→ 返回 `imdb_id: "tt0111161"`

**3. 输出:**
```
┌─────────────────────────────────────────┐
│ 🎬 《肖申克的救赎》 The Shawshank Redemption│
│    1994 · 剧情 / 犯罪                     │
│    ⭐ 8.7                               │
├─────────────────────────────────────────┤
│ ▶️ 立即观看                              │
│ https://vidsrc.to/embed/movie/tt0111161 │
│                                         │
│ 🔗 备选源                                │
│ • https://vidsrc.icu/embed/movie/tt0111161│
│ • https://cinemull.cc/movie/tt0111161   │
└─────────────────────────────────────────┘
```

---

## 注意事项

- **TMDB API Key**: 优先用环境变量 `TMDB_API_KEY`，或询问用户
- **VidSrc 域名**: vidsrc.to 为主源，被屏蔽时自动切换备选
- **无需爬虫**: VidSrc 已聚合多源视频
- **直接播放**: 点击链接 → 浏览器打开播放器

---

## 错误处理

| 情况 | 处理 |
|------|------|
| TMDB 无结果 | 提示用户确认影视名称是否有错别字 |
| IMDB ID 获取失败 | 用 TMDB ID 代替（部分播放器支持） |
| VidSrc 全部失效 | 告知用户稍后重试，VidSrc 会自动恢复 |
| 多个搜索结果 | 列出选项让用户确认 |
