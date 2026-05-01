#!/usr/bin/env python3
"""
Camera/Photo App Pain Point Analysis
Scrape App Store reviews for camera-related apps and extract user pain points.
"""
import json
import re
import sys
import os
from datetime import datetime, timedelta
from collections import Counter

# Use the venv python
PYTHON = "/Users/eric/dreame/code/skill-center/.claude/skills/ai-weekly-digest/.venv/bin/python3"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app_store_scraper import AppStoreScraper  # local script
except ImportError:
    from app_store_scraper import AppStoreScraper  # pip package

# Camera/Photo apps to analyze
CAMERA_APPS = {
    "Camera+ 2": "camera-plus-2",
    "VSCO": "vsco-photo-video-editor",
    "Halide": "halide",
    "ProCam X": "procam",
    "Lightroom": "adobe-photoshop-lightroom",
    "Snapseed": "snapseed",
    "Afterlight": "afterlight",
    "PicsArt": "picsart-photo-video-collage",
    "Facetune": "facetune",
    "YouCam Perfect": "youcam-perfect",
    "Camera360": "camera360",
    "Moment": "moment-camera",
    "Obscura": "obscura-camera",
    "Darkroom": "darkroom-photo-editor",
    "PhotoMatix": "photomix",
}


# Pain point keywords and categories
PAIN_POINT_PATTERNS = {
    "性能/崩溃": [
        r"crash(es)?", r"freez(e|es|ing|ed)", r"lag(s|ged|ging)?",
        r"slow", r"not responsive", r"hang(s|ing)?", r"卡", r"闪退",
        r"freeze", r"死机", r"崩溃",
    ],
    "画质/拍照效果": [
        r"qualit(y|ies)", r"blur(ry|r)?", r"sharp", r"focus",
        r"expos(ure|ed)", r"grain", r"noise", r"bright", r"dark",
        r"picture", r"photo", r"image", r"resolution", r"像素",
        r"模糊", r"清晰", r"对焦", r"曝光", r"噪点", r"画质",
    ],
    "订阅/付费": [
        r"subscription", r"pay", r"paid", r"money", r"price",
        r"expensive", r"cheap", r"free", r"trial", r"upgrade",
        r"付费", r"订阅", r"收费", r"贵", r"免费",
        r"credit", r"points", r"coins", r"premium", r"pro",
    ],
    "保存/导出": [
        r"save(d)?", r"export", r"exporting", r"cannot save",
        r"lost", r"disappear", r"vanish", r"missing",
        r"保存", r"导出", r"丢失", r"消失", r"无法保存",
        r"jpeg", r"jpg", r"png", r"heic", r"raw", r"format",
    ],
    "UI/UX": [
        r"confusing", r"complicated", r"complicated", r"intuit",
        r"ui", r"design", r"layout", r"icon", r"button",
        r"menu", r"setting", r"hard to find", r"buried",
        r"界面", r"操作", r"复杂", r"找不到", r"难用",
    ],
    "功能缺失": [
        r"wish", r"want", r"need", r"feature", r"miss",
        r"hope", r"please add", r"should have", r"lack",
        r"功能", r"缺少", r"需要", r"建议", r"希望",
        r"no(thing)? option", r"cannot", r"no way to",
    ],
    "滤镜/效果": [
        r"filter(s)?", r"preset(s)?", r"effect(s)?",
        r"edit", r"editing", r"color", r"tone", r"lut",
        r"滤镜", r"预设", r"特效", r"调色",
    ],
}


def scrape_app(app_name: str, app_id: str, country: str = "us", count: int = 300):
    """Scrape reviews for a single app."""
    try:
        scraper = AppStoreScraper(country=country, app_name=app_id)
        scraper.fetch_reviews(how_many=count, sleep=0.5)
        return {
            "name": app_name,
            "app_name": app_id,
            "total": scraper.reviews_count,
            "reviews": scraper.reviews,
        }
    except Exception as e:
        return {"name": app_name, "app_name": app_id, "total": 0, "reviews": [], "error": str(e)}


def detect_pain_points(reviews: list) -> dict:
    """Detect pain points from review text."""
    categories = {cat: [] for cat in PAIN_POINT_PATTERNS}

    for review in reviews:
        text = (review.get("title", "") + " " + review.get("review", "")).lower()
        text_chinese = review.get("review", "")

        for category, patterns in PAIN_POINT_PATTERNS.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, text) or re.search(pattern, text_chinese):
                        categories[category].append({
                            "rating": review.get("rating"),
                            "title": review.get("title", ""),
                            "review": review.get("review", ""),
                        })
                        break  # One match per category per review
                except re.error:
                    continue

    return categories


def build_pain_report(results: list) -> str:
    """Build a comprehensive pain point report."""
    report = []
    report.append("# 📸 拍照类应用用户痛点分析报告")
    report.append("")
    report.append(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**分析应用数:** {len(results)}")
    total_reviews = sum(r["total"] for r in results)
    report.append(f"**总评论数:** {total_reviews}")
    report.append("")

    # Section 1: Pain point overview
    report.append("## 一、痛点概览")
    report.append("")

    all_pain_counts = Counter()
    for r in results:
        if r.get("error"):
            continue
        categories = detect_pain_points(r["reviews"])
        for cat, items in categories.items():
            all_pain_counts[cat] += len(items)

    report.append("| 痛点类别 | 提及次数 | 占比 |")
    report.append("|----------|---------|------|")
    for cat, count in all_pain_counts.most_common():
        pct = round(count / max(total_reviews, 1) * 100, 1)
        report.append(f"| {cat} | {count} | {pct}% |")
    report.append("")

    # Section 2: Low rating reviews analysis
    report.append("## 二、低分评论分析（1-2星）")
    report.append("")

    for r in results:
        if r.get("error") or r["total"] == 0:
            continue
        low_reviews = [rv for rv in r["reviews"] if rv.get("rating", 5) <= 2]
        if not low_reviews:
            continue
        report.append(f"### {r['name']} ({len(low_reviews)}条低分评论)")
        report.append("")

        for rv in low_reviews[:5]:  # Top 5 per app
            stars = "⭐" * rv.get("rating", 0)
            report.append(f"**{stars}** {rv.get('title', '')}")
            text = rv.get("review", "")[:200]
            report.append(f"> {text}...")
            report.append("")

    # Section 3: Per-app pain points
    report.append("## 三、各应用痛点详情")
    report.append("")

    for r in results:
        if r.get("error"):
            report.append(f"### ❌ {r['name']} - 获取失败: {r['error']}")
            report.append("")
            continue

        categories = detect_pain_points(r["reviews"])
        total_pain = sum(len(v) for v in categories.values())
        if total_pain == 0:
            continue

        avg_rating = sum(rv["rating"] for rv in r["reviews"]) / max(len(r["reviews"]), 1)

        report.append(f"### {r['name']}")
        report.append(f"- 平均评分: {avg_rating:.2f} ⭐")
        report.append(f"- 总评论: {r['total']} 条")
        report.append(f"- 痛点评数: {total_pain} 条")
        report.append("")

        for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
            if not items:
                continue
            report.append(f"**{cat}** ({len(items)} 条)")
            for item in items[:2]:  # Top 2 examples
                stars = "⭐" * item["rating"]
                title = item["title"][:80] if item["title"] else "(无标题)"
                review_snippet = item["review"][:100] if item["review"] else ""
                report.append(f"- [{stars}] {title}")
                if review_snippet:
                    report.append(f"  > {review_snippet[:100]}")
            report.append("")

    # Section 4: Top recurring complaints
    report.append("## 四、高频痛点关键词")
    report.append("")

    keyword_counter = Counter()
    for r in results:
        if r.get("error"):
            continue
        for rv in r["reviews"]:
            text = (rv.get("title", "") + " " + rv.get("review", "")).lower()
            # Extract meaningful 2-3 word phrases
            words = re.findall(r'\b[a-z]{4,}\b', text)
            keyword_counter.update(words)

    # Filter for meaningful complaint words
    stop_words = {"that", "this", "with", "have", "will", "would", "could", "should",
                  "from", "they", "been", "were", "what", "when", "your", "more",
                  "like", "just", "very", "even", "only", "also", "than", "some",
                  "after", "their", "there", "which", "about", "other", "into",
                  "make", "using", "used", "need", "want", "have", "really"}

    significant = [(w, c) for w, c in keyword_counter.most_common(50) if w not in stop_words]
    report.append("| 关键词 | 出现次数 |")
    report.append("|--------|---------|")
    for word, count in significant[:20]:
        report.append(f"| {word} | {count} |")
    report.append("")

    # Section 5: Summary & Recommendations
    report.append("## 五、总结与机会")
    report.append("")

    top_cats = [cat for cat, _ in all_pain_counts.most_common(3)]
    report.append("### 主要痛点")
    for i, cat in enumerate(top_cats, 1):
        count = all_pain_counts[cat]
        report.append(f"{i}. **{cat}** - 占比 {count} 条评论")
    report.append("")

    report.append("### 市场机会")
    # Generate insights based on pain points
    if "性能/崩溃" in top_cats:
        report.append("- 🚀 用户普遍反馈性能问题，**快速稳定**的相机应用有机会脱颖而出")
    if "订阅/付费" in top_cats:
        report.append("- 💰 订阅模式引发抵触，**一次性买断**或透明定价策略有吸引力")
    if "保存/导出" in top_cats:
        report.append("- 💾 导出丢失是高频雷区，**可靠的保存和格式支持**是基础要求")
    if "功能缺失" in top_cats:
        report.append("- ✨ 用户渴望新功能，**AI增强拍摄**和**智能场景识别**是热点方向")
    if "滤镜/效果" in top_cats:
        report.append("- 🎨 滤镜需求旺盛，**丰富的预设和AI调色**可提升付费转化")

    report.append("")
    report.append("---\n*由 App Store Reviews Scraper 自动生成*")

    return "\n".join(report)


def main():
    print("📸 开始爬取拍照类应用评论...")
    print()

    results = []
    for display_name, app_id in CAMERA_APPS.items():
        print(f"  → 正在获取: {display_name} ({app_id})...", end=" ", flush=True)
        r = scrape_app(display_name, app_id, count=300)
        if r.get("error"):
            print(f"❌ {r['error']}")
        else:
            print(f"✅ {r['total']} 条评论")
        results.append(r)

    print()
    print("✅ 数据抓取完成，开始分析...")
    print()

    # Generate report
    report = build_pain_report(results)

    # Save report
    output_path = "/Users/eric/dreame/code/skill-center/camera_pain_points_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ 报告已生成: {output_path}")
    print()

    # Also save raw data
    raw_path = "/Users/eric/dreame/code/skill-center/camera_reviews_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, default=str)
    print(f"✅ 原始数据已保存: {raw_path}")

    # Print summary
    print()
    print("=== 摘要 ===")
    total = sum(r["total"] for r in results)
    failed = sum(1 for r in results if r.get("error"))
    print(f"  分析应用: {len(results)} 个")
    print(f"  成功: {len(results) - failed} 个, 失败: {failed} 个")
    print(f"  总评论数: {total} 条")


if __name__ == "__main__":
    main()