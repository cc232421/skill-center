#!/usr/bin/env python3

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class DigestConfig:
    title: str
    subtitle: str
    scan_time: str
    total_accounts: int
    total_tweets: int
    filtered_count: int
    days: int
    min_priority: int


def format_date(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str


def format_number(n: int) -> str:
    if n >= 1000000:
        return f"{n / 1000000:.1f}M"
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def format_tweet_text(text: str, max_length: int = 280) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def generate_header(config: DigestConfig) -> str:
    return f"""# {config.title}

{config.subtitle}

**📅 扫描时间:** {config.scan_time}
**📊 数据源:** {config.total_accounts} 个顶级 AI Builder 账号
**⏱️ 时间范围:** 过去 {config.days} 天
**🎯 筛选标准:** Priority 1-{config.min_priority} | 排除基础设施/学术/融资/技术对比

---

## 📈 筛选统计

| 指标 | 数值 |
|------|------|
| 扫描账号 | {config.total_accounts} 个 |
| 原始推文 | {config.total_tweets} 条 |
| 精选内容 | {config.filtered_count} 条 |
| 精选率 | {config.filtered_count / config.total_tweets * 100:.1f}% |

---

## 🔥 本周最实用的内容

"""


def generate_tweet_entry(index: int, tweet: dict, config: DigestConfig) -> str:
    priority_label = {1: "🔥 Priority 1", 2: "⭐ Priority 2", 3: "💡 Priority 3"}.get(
        tweet["priority"], "⚪ Other"
    )

    engagement = f"❤️ {format_number(tweet['likes'])} | 🔁 {format_number(tweet['retweets'])} | 💬 {format_number(tweet['replies'])}"

    text_lines = []
    words = tweet["text"].split()
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= 60:
            current_line += (" " if current_line else "") + word
        else:
            if current_line:
                text_lines.append(current_line)
            current_line = word
    if current_line:
        text_lines.append(current_line)

    formatted_text = "\n".join(f"> {line}" for line in text_lines)

    return f"""### {index}. {tweet["category"]} {priority_label}

**账号:** [@{tweet["username"]}](https://twitter.com/{tweet["username"]})
**理由:** {tweet["reason"]}
**时间:** {format_date(tweet["created_at"])}
**互动:** {engagement}

{formatted_text}

**🔗 [查看原推]({tweet["url"]})**

---

"""


def generate_footer(config: DigestConfig) -> str:
    return f"""## 📌 备注

- ✅ **Priority 1 (🔥):** 立刻能用的工具、教程、提示词模板
- ⭐ **Priority 2 (⭐):** 可复用的方法论、最佳实践
- 💡 **Priority 3 (💡):** 思维转变、避坑指南

### 排除内容

- ❌ 技术基础设施（GPU、TPU、算力）
- ❌ 网络安全专业内容
- ❌ 学术论文（无实际应用）
- ❌ 企业/B2B公告
- ❌ 融资/营收新闻
- ❌ 模型基准测试对比

---

*🤖 由 AI 干货周报生成器自动生成*
*📅 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""


def generate_report(
    data: dict,
    title: str = "AI 干货周报 - Builder 必看",
    subtitle: str = "每周精选 · 拒绝噪音 · 直接实用",
    days: int = 7,
    min_priority: int = 1,
) -> str:
    config = DigestConfig(
        title=title,
        subtitle=subtitle,
        scan_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_accounts=data.get("total_accounts", 65),
        total_tweets=data.get("total_tweets", 0),
        filtered_count=data.get("filtered_count", 0),
        days=days,
        min_priority=min_priority,
    )

    tweets = data.get("tweets", [])
    priority1 = [t for t in tweets if t.get("priority") == 1]
    priority2 = [t for t in tweets if t.get("priority") == 2]
    priority3 = [t for t in tweets if t.get("priority") == 3]
    others = [t for t in tweets if t.get("priority", 0) > 3]

    sections = [generate_header(config)]

    if priority1:
        sections.append("\n### 🔥 Priority 1 - 立刻能用\n")
        for i, tweet in enumerate(priority1[:10], 1):
            sections.append(generate_tweet_entry(i, tweet, config))

    if priority2:
        idx = len(priority1) + 1
        sections.append("\n### ⭐ Priority 2 - 方法论\n")
        for tweet in priority2[:10]:
            sections.append(generate_tweet_entry(idx, tweet, config))
            idx += 1

    if priority3:
        idx = len(priority1) + len(priority2) + 1
        sections.append("\n### 💡 Priority 3 - 思维转变\n")
        for tweet in priority3[:10]:
            sections.append(generate_tweet_entry(idx, tweet, config))
            idx += 1

    if others:
        idx = len(priority1) + len(priority2) + len(priority3) + 1
        sections.append("\n### ⚪ 其他精选\n")
        for tweet in others[:5]:
            sections.append(generate_tweet_entry(idx, tweet, config))
            idx += 1

    sections.append(generate_footer(config))

    return "".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description="AI Weekly Digest - Generate Markdown report"
    )
    parser.add_argument("--input", default="data/filtered.json", help="Input file")
    parser.add_argument(
        "--output", default="weekly-digest.md", help="Output Markdown file"
    )
    parser.add_argument("--title", default="AI Weekly Digest", help="Report title")
    parser.add_argument(
        "--subtitle", default="Weekly curation for AI builders", help="Report subtitle"
    )
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--min-priority", type=int, default=1, help="Min priority")

    args = parser.parse_args()
    input_path = Path(__file__).parent.parent / args.input
    output_path = Path(__file__).parent.parent / args.output

    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        print(f"   请先运行 filter_content.py 筛选推文")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  AI Weekly Digest - Markdown 周报生成器")
    print(f"{'=' * 60}")
    print(f"  输入文件: {input_path}")
    print(f"  输出文件: {output_path}")
    print(f"  周报标题: {args.title}")
    print(f"{'=' * 60}\n")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = generate_report(
        data,
        title=args.title,
        subtitle=args.subtitle,
        days=args.days,
        min_priority=args.min_priority,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'=' * 60}")
    print(f"  ✅ 周报生成完成!")
    print(f"  📄 文件: {output_path}")
    print(f"  📊 精选内容: {data.get('filtered_count', 0)} 条")
    print(f"{'=' * 60}")
    print(f"\n💡 提示:")
    print(f"   - 可以用 cat 查看: cat {output_path}")
    print(f"   - 或用 markdown 编辑器打开")


if __name__ == "__main__":
    main()
