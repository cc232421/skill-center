#!/usr/bin/env python3

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

MIN_ENGAGEMENT = {"likes": 5, "views": 100}

PRIORITY1_PATTERNS = [
    (r"\btool\b", r"\bplugin\b", r"\bapp\b", r"\bextension\b"),
    (r"step.by.step", r"tutorial", r"how.to", r"guide\b", r"\bwalkthrough\b"),
    (r"prompt\b", r"\btemplate\b", r"\bframework\b", r"\bworkflow\b"),
    (r"\bcheatsheet\b", r"checklist", r"\bformula\b", r"\brecipe\b"),
]

PRIORITY2_PATTERNS = [
    (r"productivity", r"\btips?\b", r"\btrick\b", r"\bhack\b", r"efficient"),
    (r"best.practice", r"methodology", r"\bworkflow\b", r"process"),
    (r"content.creation", r"creator", r"writing", r"design"),
    (r"skill\b", r"\bability\b", r"capability", r"\bcompetence\b"),
]

PRIORITY3_PATTERNS = [
    (r"mindset", r"thinking", r"perspective", r"approach"),
    (r"mistake", r"error", r"wrong", r"avoid", r"\bfail\b"),
    (r"expert", r"insight", r"lesson", r"learned", r"realized"),
    (r"\bnote\b", r"remember", r"understand", r"believe"),
]

EXCLUDE_PATTERNS = [
    r"\bGPU\b",
    r"\bTPU\b",
    r"\bH100\b",
    r"\bH200\b",
    r"compute",
    r"infrastructure",
    r"cybersecurity",
    r"hackathon",
    r"bug.bounty",
    r"paper\b",
    r"research\b",
    r"arxiv",
    r"academic",
    r"study\b",
    r"funding",
    r"raised\b",
    r" Series [A-Z]",
    r"revenue",
    r"valuation",
    r"benchmark",
    r"performance.comparison",
    r"vs\.?\s*\w+",
    r"outperform",
    r"\bblood\b",
    r"\bwar\b",
    r"election",
    r"politics",
]


@dataclass(frozen=True)
class FilteredTweet:
    id: str
    text: str
    created_at: str
    username: str
    likes: int
    retweets: int
    replies: int
    views: int
    url: str
    priority: int
    category: str
    reason: str


@dataclass
class FilterResult:
    total_tweets: int
    filtered_count: int
    by_priority: dict[int, int]
    by_category: dict[str, int]
    tweets: list[FilteredTweet]


def normalize_text(text: str) -> str:
    return text.lower()


def matches_any(text: str, pattern_groups: tuple[tuple[str, ...], ...]) -> bool:
    text = normalize_text(text)
    return any(
        any(re.search(p, text, re.IGNORECASE) for p in group)
        for group in pattern_groups
    )


def is_excluded(text: str) -> bool:
    text_lower = normalize_text(text)
    return any(re.search(p, text_lower, re.IGNORECASE) for p in EXCLUDE_PATTERNS)


def get_priority(text: str) -> Optional[int]:
    if matches_any(text, PRIORITY1_PATTERNS):
        return 1
    if matches_any(text, PRIORITY2_PATTERNS):
        return 2
    if matches_any(text, PRIORITY3_PATTERNS):
        return 3
    return None


def get_category(text: str) -> str:
    text_lower = normalize_text(text)
    if re.search(r"\btool\b|\bplugin\b|\bapp\b|\bextension\b|\bsoftware\b", text_lower):
        return "🛠️ 新工具"
    if re.search(r"step.by.step|tutorial|how.to|guide|walkthrough|setup", text_lower):
        return "📝 分步教程"
    if re.search(r"prompt|template|framework|engine|system", text_lower):
        return "💡 提示词技巧"
    if re.search(
        r"workflow|productivity|tips?|trick|hack|efficient|automation", text_lower
    ):
        return "⚡ 效率提升"
    if re.search(r"best.practice|methodology|process|strategy|approach", text_lower):
        return "🎯 方法论"
    if re.search(r"mistake|error|wrong|avoid|fail|warning|trap", text_lower):
        return "⚠️ 避坑指南"
    if re.search(r"mindset|thinking|perspective|insight|lesson|realized", text_lower):
        return "🧠 思维转变"
    if re.search(r"skill|learn|master|expert|knowledge", text_lower):
        return "📚 技能提升"
    return "💎 精选内容"


def get_reason(text: str, priority: int) -> str:
    text_lower = normalize_text(text)
    if priority == 1:
        if re.search(r"step.by.step|tutorial|how.to|guide", text_lower):
            return "实用的分步教程"
        if re.search(r"prompt|template", text_lower):
            return "可直接使用的提示词模板"
        if re.search(r"tool|plugin|app|extension", text_lower):
            return "有价值的新工具"
        if re.search(r"workflow|automation", text_lower):
            return "可复用的工作流"
        return "立刻能用的实用内容"
    if priority == 2:
        if re.search(r"productivity|tips?|trick|hack", text_lower):
            return "提升效率的实用技巧"
        if re.search(r"best.practice|methodology", text_lower):
            return "经过验证的方法论"
        return "可复用的方法技巧"
    if priority == 3:
        if re.search(r"mistake|error|avoid|fail", text_lower):
            return "专家总结的避坑经验"
        if re.search(r"insight|lesson|realized", text_lower):
            return "专家的深刻洞察"
        return "思维方式的转变"
    return "高价值内容"


def meets_engagement_threshold(tweet: dict) -> bool:
    try:
        likes = int(tweet.get("likes") or 0)
        views = int(tweet.get("views") or 0)
        return likes >= MIN_ENGAGEMENT["likes"] or views >= MIN_ENGAGEMENT["views"]
    except (ValueError, TypeError):
        return False


def filter_tweet(tweet: dict, min_priority: int = 1) -> Optional[FilteredTweet]:
    if tweet.get("is_retweet"):
        return None
    if tweet.get("is_reply"):
        return None
    text = tweet.get("text", "")
    if len(text) < 20:
        return None
    if is_excluded(text):
        return None
    priority = get_priority(text)
    if priority is None or priority > min_priority:
        return None
    if not meets_engagement_threshold(tweet):
        return None
    return FilteredTweet(
        id=str(tweet["id"]),
        text=tweet["text"],
        created_at=tweet["created_at"],
        username=tweet["username"],
        likes=int(tweet.get("likes") or 0),
        retweets=int(tweet.get("retweets") or 0),
        replies=int(tweet.get("replies") or 0),
        views=int(tweet.get("views") or 0),
        url=tweet["url"],
        priority=priority,
        category=get_category(text),
        reason=get_reason(text, priority),
    )


def filter_tweets(data: dict, min_priority: int = 1) -> FilterResult:
    all_tweets: list[dict] = []
    for account_data in data.get("accounts", {}).values():
        username = account_data.get("username", "unknown")
        for tweet in account_data.get("tweets", []):
            tweet["username"] = username
            all_tweets.append(tweet)

    filtered: list[FilteredTweet] = []
    for tweet in all_tweets:
        result = filter_tweet(tweet, min_priority)
        if result:
            filtered.append(result)

    filtered.sort(
        key=lambda t: (t.priority, -(t.likes + t.retweets * 2)),
    )

    by_priority: dict[int, int] = {}
    by_category: dict[str, int] = {}
    for t in filtered:
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        by_category[t.category] = by_category.get(t.category, 0) + 1

    return FilterResult(
        total_tweets=len(all_tweets),
        filtered_count=len(filtered),
        by_priority=by_priority,
        by_category=by_category,
        tweets=filtered,
    )


def save_filtered(result: FilterResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "filtered_at": datetime.now().isoformat(),
                "total_tweets": result.total_tweets,
                "filtered_count": result.filtered_count,
                "by_priority": result.by_priority,
                "by_category": result.by_category,
                "tweets": [
                    {
                        **t.__dict__,
                        "likes": t.likes,
                        "retweets": t.retweets,
                        "replies": t.replies,
                        "views": t.views,
                    }
                    for t in result.tweets
                ],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"💾 Filtered results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Weekly Digest - Filter tweets by priority"
    )
    parser.add_argument("--input", default="data/tweets.json", help="Input file")
    parser.add_argument("--output", default="data/filtered.json", help="Output file")
    parser.add_argument(
        "--min-priority", type=int, default=1, help="Min priority (1-3)"
    )

    args = parser.parse_args()
    input_path = Path(__file__).parent.parent / args.input
    output_path = Path(__file__).parent.parent / args.output

    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        print(f"   请先运行 fetch_all.py 获取推文数据")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  AI Weekly Digest - 内容筛选器")
    print(f"{'=' * 60}")
    print(f"  输入文件: {input_path}")
    print(f"  最低优先级: {args.min_priority}")
    print(f"{'=' * 60}\n")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = filter_tweets(data, min_priority=args.min_priority)

    print(f"\n📊 筛选结果:")
    print(f"   总推文数: {result.total_tweets}")
    print(f"   筛选后数量: {result.filtered_count}")
    print(f"   按优先级: {result.by_priority}")
    print(f"   按分类: {result.by_category}")

    if result.filtered_count == 0:
        print("\n⚠️  没有筛选到符合条件的内容")
        print("   可能原因:")
        print("   - 推文不包含Priority 1-3的关键字")
        print("   - 需要检查auth_token是否有效")
        print("   - 可以尝试降低最低优先级")
        sys.exit(0)

    save_filtered(result, output_path)

    print(f"\n{'=' * 60}")
    print(f"  ✅ 筛选完成! 共 {result.filtered_count} 条精选内容")
    print(f"   下一步: python3 scripts/generate_report.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
