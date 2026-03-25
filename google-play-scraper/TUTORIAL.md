# Google Play Scraper Skill 完整教程

## 📚 目录

1. [快速开始](#快速开始)
2. [核心功能详解](#核心功能详解)
3. [实战案例](#实战案例)
4. [高级用法](#高级用法)
5. [常见问题](#常见问题)
6. [API 参考](#api-参考)

---

## 快速开始

### 1. 安装依赖

```bash
pip install google-play-scraper
```

### 2. 基础使用

```python
from scripts.gplay_scraper import get_app_details

# 获取 WhatsApp 应用信息
app_info = get_app_details("com.whatsapp")
print(f"应用名称: {app_info['title']}")
print(f"评分: {app_info['score']}/5")
print(f"下载量: {app_info['installs']}")
```

**输出示例**:
```json
{
  "title": "WhatsApp Messenger",
  "score": 4.71,
  "installs": "10,000,000,000+",
  "developer": "WhatsApp LLC",
  "genre": "Communication"
}
```

---

## 核心功能详解

### 1. 获取应用详情 `get_app_details`

获取应用的完整信息，包括基本信息、评分、开发者、权限等。

```python
from scripts.gplay_scraper import get_app_details

app_info = get_app_details(
    app_id="com.nianticlabs.pokemongo",  # 应用包名
    lang="zh",                           # 语言: 中文
    country="cn"                         # 国家: 中国
)

# 常用字段
print(f"应用ID: {app_info['app_id']}")
print(f"名称: {app_info['title']}")
print(f"描述: {app_info['description'][:100]}...")
print(f"评分: {app_info['score']}/5 ({app_info['ratings']} 个评分)")
print(f"评论数: {app_info['reviews_count']}")
print(f"下载量: {app_info['installs']} (最少 {app_info['min_installs']})")
print(f"价格: {'免费' if app_info['free'] else app_info['price']}")
print(f"开发者: {app_info['developer']}")
print(f"分类: {app_info['genre']}")
print(f"版本: {app_info['version']}")
print(f"更新日期: {app_info['updated']}")
print(f"图标: {app_info['icon']}")
print(f"截图数: {len(app_info['screenshots'])}")
```

**返回字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 应用名称 |
| `description` | string | 应用描述 |
| `summary` | string | 简短描述 |
| `score` | float | 评分 (0-5) |
| `ratings` | int | 评分数量 |
| `reviews_count` | int | 评论数量 |
| `installs` | string | 下载量文本 |
| `min_installs` | int | 最少下载量 |
| `histogram` | list | 评分分布 [1星, 2星, 3星, 4星, 5星] |
| `developer` | string | 开发者名称 |
| `developerEmail` | string | 开发者邮箱 |
| `developerWebsite` | string | 开发者网站 |
| `genre` | string | 应用分类 |
| `icon` | string | 图标URL |
| `screenshots` | list | 截图URL列表 |
| `video` | string | 视频URL |
| `contentRating` | string | 内容分级 |
| `released` | string | 发布日期 |
| `updated` | int | 更新时间戳 |
| `version` | string | 版本号 |
| `app_id` | string | 应用包名 |
| `url` | string | Google Play 链接 |

---

### 2. 获取应用评论 `get_app_reviews`

获取用户评论，支持分页和筛选。

```python
from scripts.gplay_scraper import get_app_reviews

# 获取最新评论
result = get_app_reviews(
    app_id="com.spotify.music",
    lang="en",
    country="us",
    sort="newest",        # 排序: newest, rating, helpfulness
    count=50,             # 获取数量
    filter_score=5        # 筛选: 只获取5星评论 (可选)
)

reviews = result['reviews']
token = result['continuation_token']  # 用于分页

print(f"获取到 {len(reviews)} 条评论")

for review in reviews[:3]:
    print(f"\n用户: {review['user_name']}")
    print(f"评分: {'★' * review['score']}{'☆' * (5-review['score'])}")
    print(f"内容: {review['content'][:100]}...")
    print(f"点赞: {review['thumbs_up_count']}")
    print(f"时间: {review['at']}")
    if review['reply_content']:
        print(f"开发者回复: {review['reply_content'][:50]}...")
```

**分页获取更多评论**:

```python
# 第一页
result = get_app_reviews("com.spotify.music", count=100)
all_reviews = result['reviews']
token = result['continuation_token']

# 第二页
result = get_app_reviews(
    "com.spotify.music",
    continuation_token=token,
    count=100
)
all_reviews.extend(result['reviews'])

print(f"总共获取 {len(all_reviews)} 条评论")
```

**评论字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `review_id` | string | 评论唯一ID |
| `user_name` | string | 用户名 |
| `user_image` | string | 用户头像URL |
| `content` | string | 评论内容 |
| `score` | int | 评分 (1-5) |
| `thumbs_up_count` | int | 点赞数 |
| `review_created_version` | string | 评论时的应用版本 |
| `at` | string | 评论时间 (ISO格式) |
| `reply_content` | string | 开发者回复内容 |
| `replied_at` | string | 回复时间 |
| `app_version` | string | 应用版本 |

---

### 3. 搜索应用 `search_apps`

在 Google Play 中搜索应用。

```python
from scripts.gplay_scraper import search_apps

# 搜索健身应用
results = search_apps(
    query="fitness tracker",
    lang="en",
    country="us",
    n_hits=10  # 最多30个
)

print(f"找到 {len(results)} 个应用\n")

for i, app in enumerate(results, 1):
    print(f"{i}. {app['title']}")
    print(f"   包名: {app['app_id']}")
    print(f"   评分: {app['score']}/5" if app['score'] else "   评分: 暂无")
    print(f"   分类: {app['genre']}")
    print(f"   价格: {'免费' if app['free'] else f'$ {app[\"price\"]}'}")
    print()
```

**搜索字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `app_id` | string | 应用包名 |
| `title` | string | 应用名称 |
| `icon` | string | 图标URL |
| `screenshots` | list | 截图URL列表 |
| `score` | float | 评分 |
| `genre` | string | 分类 |
| `price` | float | 价格 |
| `free` | bool | 是否免费 |
| `currency` | string | 货币单位 |
| `video` | string | 视频URL |

---

### 4. 获取应用权限 `get_app_permissions`

查看应用需要的权限。

```python
from scripts.gplay_scraper import get_app_permissions

permissions = get_app_permissions("com.facebook.katana")

print("Facebook 应用权限:\n")
for category, perms in permissions.items():
    print(f"【{category}】")
    for perm in perms:
        print(f"  - {perm}")
    print()
```

**输出示例**:
```
【Camera】
  - take pictures and videos

【Contacts】
  - find accounts on the device
  - read your contacts

【Location】
  - approximate location (network-based)
  - precise location (GPS and network-based)

【Storage】
  - read the contents of your USB storage
  - modify or delete the contents of your USB storage
```

---

### 5. 批量获取应用 `batch_get_app_details`

一次性获取多个应用的信息。

```python
from scripts.gplay_scraper import batch_get_app_details

# 定义要查询的应用
apps = [
    "com.whatsapp",           # WhatsApp
    "com.instagram.android",  # Instagram
    "com.twitter.android",    # Twitter/X
    "com.zhiliaoapp.musically" # TikTok
]

# 批量获取 (带1秒延迟避免限流)
results = batch_get_app_details(
    app_ids=apps,
    lang="en",
    country="us",
    delay_seconds=1.0
)

# 打印结果
for app_id, info in results.items():
    if "error" in info:
        print(f"❌ {app_id}: 获取失败 - {info['error']}")
    else:
        print(f"✅ {info['title']}")
        print(f"   评分: {info['score']}/5")
        print(f"   下载: {info['installs']}")
        print()
```

---

### 6. 应用对比 `compare_apps`

对比多个应用的关键指标。

```python
from scripts.gplay_scraper import compare_apps
import json

comparison = compare_apps([
    "com.whatsapp",
    "com.telegram.messenger",
    "com.signalapp.signal"
])

print("=" * 60)
print("即时通讯应用对比")
print("=" * 60)

# 按评分排序
print("\n🏆 按评分排名:")
for i, (app_id, info) in enumerate(comparison['rankings']['by_score'], 1):
    print(f"{i}. {info['title']}: {info['score']}/5 ⭐")

# 按下载量排序
print("\n📥 按下载量排名:")
for i, (app_id, info) in enumerate(comparison['rankings']['by_installs'], 1):
    print(f"{i}. {info['title']}: {info['installs']}")

# 按评分数量排序
print("\n📝 按评分数量排名:")
for i, (app_id, info) in enumerate(comparison['rankings']['by_ratings'], 1):
    print(f"{i}. {info['title']}: {info['ratings']:,} 个评分")

print(f"\n📊 统计: 成功 {comparison['summary']['successful']}/{comparison['summary']['total_apps']}")
```

---

## 实战案例

### 案例 1: 竞品分析报告

分析同类应用的竞争力。

```python
from scripts.gplay_scraper import batch_get_app_details
import pandas as pd
from datetime import datetime

# 音乐流媒体竞品
competitors = [
    "com.spotify.music",      # Spotify
    "com.apple.android.music", # Apple Music
    "com.google.android.apps.youtube.music", # YouTube Music
    "com.amazon.mp3",         # Amazon Music
    "com.deezer.android"      # Deezer
]

# 获取数据
results = batch_get_app_details(competitors, delay_seconds=1)

# 整理数据
analysis = []
for app_id, info in results.items():
    if "error" not in info:
        analysis.append({
            '应用名称': info['title'],
            '包名': app_id,
            '评分': info['score'],
            '评分数量': info['ratings'],
            '下载量': info['installs'],
            '最小下载量': info['min_installs'],
            '开发者': info['developer'],
            '分类': info['genre'],
            '是否免费': '是' if info['free'] else '否',
            '价格': info['price'] if not info['free'] else 0,
            '应用内购买': '是' if info['offers_iap'] else '否',
            '更新日期': datetime.fromtimestamp(info['updated']).strftime('%Y-%m-%d'),
            '版本': info['version']
        })

# 创建 DataFrame
df = pd.DataFrame(analysis)

# 排序并显示
df_sorted = df.sort_values('评分', ascending=False)
print("\n音乐流媒体应用竞品分析:")
print(df_sorted.to_string(index=False))

# 保存到 CSV
df_sorted.to_csv('music_apps_analysis.csv', index=False, encoding='utf-8-sig')
print("\n✅ 已保存到 music_apps_analysis.csv")
```

---

### 案例 2: 评论情感分析

获取并分析用户评论。

```python
from scripts.gplay_scraper import get_app_reviews
from collections import Counter
import re

# 获取大量评论
result = get_app_reviews(
    app_id="com.ubercab",
    count=500,
    sort="newest"
)

reviews = result['reviews']

# 统计评分分布
scores = [r['score'] for r in reviews]
score_dist = Counter(scores)

print("评分分布:")
for score in range(5, 0, -1):
    count = score_dist.get(score, 0)
    bar = "█" * (count // 5)
    print(f"{score}星: {bar} {count} ({count/len(reviews)*100:.1f}%)")

# 分析高频词
print("\n高频词汇 (3星及以下评论):")
negative_reviews = [r['content'] for r in reviews if r['score'] <= 3]
all_text = ' '.join(negative_reviews).lower()

# 简单的关键词提取
keywords = ['bug', 'crash', 'slow', 'error', 'problem', 'issue', 
            'bad', 'terrible', 'worst', 'hate', 'fix', 'update']

for word in keywords:
    count = len(re.findall(r'\b' + word + r'\b', all_text))
    if count > 0:
        print(f"  '{word}': {count} 次")

# 获取最有帮助的评论
helpful_reviews = sorted(reviews, key=lambda x: x['thumbs_up_count'], reverse=True)[:5]
print("\n最有帮助的评论:")
for i, review in enumerate(helpful_reviews, 1):
    print(f"\n{i}. {review['user_name']} ({review['thumbs_up_count']} 👍)")
    print(f"   评分: {'★' * review['score']}")
    print(f"   内容: {review['content'][:150]}...")
```

---

### 案例 3: 应用监控脚本

定期监控应用数据变化。

```python
from scripts.gplay_scraper import get_app_details
import json
from datetime import datetime
import os

APP_ID = "com.yourcompany.yourapp"
METRICS_FILE = "app_metrics.jsonl"

def track_metrics():
    """追踪应用指标"""
    try:
        info = get_app_details(APP_ID)
        
        # 提取关键指标
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "app_id": APP_ID,
            "score": info['score'],
            "ratings": info['ratings'],
            "reviews": info['reviews_count'],
            "installs": info['min_installs'],
            "version": info['version'],
            "updated": info['updated']
        }
        
        # 追加到文件
        with open(METRICS_FILE, "a") as f:
            f.write(json.dumps(metrics) + "\n")
        
        print(f"✅ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 数据已记录")
        print(f"   评分: {metrics['score']}/5")
        print(f"   评分数: {metrics['ratings']:,}")
        print(f"   版本: {metrics['version']}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

# 运行追踪
track_metrics()

# 查看历史趋势 (如果有历史数据)
if os.path.exists(METRICS_FILE):
    print("\n📈 历史数据:")
    with open(METRICS_FILE, "r") as f:
        lines = f.readlines()[-5:]  # 最近5条
        for line in lines:
            data = json.loads(line)
            print(f"  {data['timestamp'][:10]}: {data['score']}/5 ({data['ratings']:,} 评分)")
```

---

### 案例 4: 权限审计报告

检查应用权限合规性。

```python
from scripts.gplay_scraper import get_app_permissions

# 要审计的应用
apps_to_audit = [
    ("com.facebook.katana", "Facebook"),
    ("com.instagram.android", "Instagram"),
    ("com.twitter.android", "Twitter/X"),
    ("com.snapchat.android", "Snapchat"),
    ("com.linkedin.android", "LinkedIn")
]

# 敏感权限列表
sensitive_permissions = [
    "read phone status and identity",
    "read your contacts",
    "precise location",
    "record audio",
    "take pictures and videos",
    "read the contents of your USB storage"
]

print("=" * 70)
print("社交媒体应用权限审计报告")
print("=" * 70)

for app_id, app_name in apps_to_audit:
    try:
        permissions = get_app_permissions(app_id)
        
        print(f"\n📱 {app_name}")
        print("-" * 70)
        
        # 统计权限数量
        total_perms = sum(len(perms) for perms in permissions.values())
        print(f"总权限数: {total_perms}")
        
        # 检查敏感权限
        found_sensitive = []
        all_perms = []
        for category, perms in permissions.items():
            all_perms.extend(perms)
        
        for sensitive in sensitive_permissions:
            for perm in all_perms:
                if sensitive.lower() in perm.lower():
                    found_sensitive.append(perm)
        
        if found_sensitive:
            print(f"⚠️  敏感权限 ({len(found_sensitive)}):")
            for perm in set(found_sensitive):
                print(f"   • {perm}")
        else:
            print("✅ 未发现敏感权限")
            
    except Exception as e:
        print(f"❌ {app_name}: 获取失败 - {e}")

print("\n" + "=" * 70)
print("审计完成")
```

---

### 案例 5: 本地化市场研究

研究不同地区的应用表现。

```python
from scripts.gplay_scraper import search_apps, get_app_details

# 搜索不同地区的健身应用
markets = [
    ("en", "us", "美国"),
    ("zh", "cn", "中国"),
    ("ja", "jp", "日本"),
    ("ko", "kr", "韩国"),
    ("de", "de", "德国")
]

query = "fitness"

print("🌍 健身应用在不同市场的表现\n")

for lang, country, name in markets:
    try:
        # 搜索
        results = search_apps(query, lang=lang, country=country, n_hits=5)
        
        print(f"\n{name} ({lang}-{country}):")
        print("-" * 60)
        
        if results:
            # 获取第一个结果的详情
            top_app = results[0]
            details = get_app_details(top_app['app_id'], lang=lang, country=country)
            
            print(f"热门应用: {details['title']}")
            print(f"评分: {details['score']}/5" if details['score'] else "评分: 暂无")
            print(f"下载: {details['installs']}")
            print(f"分类: {details['genre']}")
            
            # 显示前5个搜索结果
            print("\n搜索结果:")
            for i, app in enumerate(results[:5], 1):
                score_str = f"{app['score']}/5" if app['score'] else "N/A"
                print(f"  {i}. {app['title']} ({score_str})")
        else:
            print("未找到结果")
            
    except Exception as e:
        print(f"错误: {e}")

print("\n" + "=" * 60)
```

---

## 高级用法

### 1. 使用代理

如果需要使用代理访问 Google Play:

```python
import os
# 设置代理环境变量
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
os.environ['HTTPS_PROXY'] = 'http://proxy.example.com:8080'

from scripts.gplay_scraper import get_app_details

app_info = get_app_details("com.whatsapp")
```

### 2. 自定义请求延迟

避免触发限流:

```python
from scripts.gplay_scraper import batch_get_app_details
import time

app_ids = ["com.app1", "com.app2", "com.app3", ...]  # 大量应用

# 使用较长的延迟
results = batch_get_app_details(
    app_ids=app_ids,
    delay_seconds=2.0  # 2秒延迟
)
```

### 3. 错误处理和重试

```python
from scripts.gplay_scraper import get_app_details
import time

def get_app_with_retry(app_id, max_retries=3):
    """带重试的应用详情获取"""
    for attempt in range(max_retries):
        try:
            return get_app_details(app_id)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"尝试 {attempt + 1} 失败，{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"最终失败: {e}")
                return {"error": str(e), "app_id": app_id}

# 使用
info = get_app_with_retry("com.whatsapp")
```

### 4. 数据导出

```python
from scripts.gplay_scraper import get_app_reviews
import json
import csv

# 获取评论
result = get_app_reviews("com.spotify.music", count=200)
reviews = result['reviews']

# 导出为 JSON
with open('reviews.json', 'w', encoding='utf-8') as f:
    json.dump(reviews, f, ensure_ascii=False, indent=2)

# 导出为 CSV
with open('reviews.csv', 'w', encoding='utf-8-sig', newline='') as f:
    if reviews:
        writer = csv.DictWriter(f, fieldnames=reviews[0].keys())
        writer.writeheader()
        writer.writerows(reviews)

print(f"✅ 已导出 {len(reviews)} 条评论")
```

---

## 常见问题

### Q1: 为什么有些应用返回空数据？

**原因**:
- 应用在该地区不可用
- 应用已下架
- Google Play 结构变化

**解决**:
```python
# 尝试不同的地区
for country in ['us', 'gb', 'ca', 'au']:
    try:
        info = get_app_details(app_id, country=country)
        if info.get('title'):
            break
    except:
        continue
```

### Q2: 如何避免被限流？

**建议**:
- 使用 `delay_seconds` 参数添加延迟
- 批量操作时控制并发数量
- 缓存已获取的数据

```python
# 使用缓存
import functools

@functools.lru_cache(maxsize=100)
def get_cached_app_details(app_id, lang="en", country="us"):
    return get_app_details(app_id, lang, country)
```

### Q3: 如何获取特定语言的评论？

```python
# 获取中文评论
reviews_cn = get_app_reviews(
    app_id="com.whatsapp",
    lang="zh",
    country="cn",
    count=100
)

# 获取日文评论
reviews_jp = get_app_reviews(
    app_id="com.whatsapp",
    lang="ja",
    country="jp",
    count=100
)
```

### Q4: 如何处理大量评论？

```python
from scripts.gplay_scraper import get_all_reviews

# 获取所有评论 (注意: 这可能需要很长时间)
all_reviews = get_all_reviews(
    app_id="com.popular.app",
    sleep_milliseconds=100  # 100ms 延迟
)

print(f"总共获取 {len(all_reviews)} 条评论")
```

---

## API 参考

### 函数列表

| 函数 | 用途 | 返回类型 |
|------|------|----------|
| `get_app_details(app_id, lang, country)` | 获取应用详情 | dict |
| `get_app_reviews(app_id, lang, country, sort, count, filter_score)` | 获取评论 | dict |
| `get_all_reviews(app_id, lang, country, sort, filter_score, sleep_milliseconds)` | 获取所有评论 | list |
| `search_apps(query, lang, country, n_hits)` | 搜索应用 | list |
| `get_app_permissions(app_id, lang, country)` | 获取权限 | dict |
| `batch_get_app_details(app_ids, lang, country, delay_seconds)` | 批量获取 | dict |
| `compare_apps(app_ids, lang, country)` | 对比应用 | dict |

### 语言代码参考

常用 ISO 639-1 语言代码:

| 代码 | 语言 |
|------|------|
| `en` | 英语 |
| `zh` | 中文 |
| `ja` | 日语 |
| `ko` | 韩语 |
| `de` | 德语 |
| `fr` | 法语 |
| `es` | 西班牙语 |
| `ru` | 俄语 |
| `pt` | 葡萄牙语 |
| `ar` | 阿拉伯语 |

### 国家代码参考

常用 ISO 3166 国家代码:

| 代码 | 国家 |
|------|------|
| `us` | 美国 |
| `cn` | 中国 |
| `jp` | 日本 |
| `kr` | 韩国 |
| `de` | 德国 |
| `gb` | 英国 |
| `fr` | 法国 |
| `ca` | 加拿大 |
| `au` | 澳大利亚 |
| `br` | 巴西 |

---

## 总结

Google Play Scraper Skill 提供了完整的 Google Play Store 数据抓取能力，适用于:

- 📊 竞品分析
- 📈 市场研究
- 💬 用户反馈分析
- 🔒 权限审计
- 🌍 本地化研究
- 📱 应用监控

**最佳实践**:
1. 始终处理异常情况
2. 使用适当的延迟避免限流
3. 缓存重复请求的数据
4. 尊重 Google Play 的服务条款

**注意事项**:
- 该库通过非官方 API 抓取数据，Google Play 的结构变化可能影响功能
- 大量请求可能导致 IP 被暂时封禁
- 建议用于研究和分析目的

---

**文档版本**: 1.0  
**最后更新**: 2024年3月  
**Skill 版本**: 1.0.0
