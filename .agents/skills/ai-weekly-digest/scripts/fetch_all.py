#!/usr/bin/env python3
import argparse
import json
import sys
import time
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

TREND_CRAWLER_PATH = (
    Path.home() / "Documents" / "trend-crawler-master" / "trend-crawler"
)
if TREND_CRAWLER_PATH.exists():
    sys.path.insert(0, str(TREND_CRAWLER_PATH))

HOMEBREW_TWEETY_PATH = Path("/opt/homebrew/lib/python3.14/site-packages")
if HOMEBREW_TWEETY_PATH.exists():
    sys.path.insert(0, str(HOMEBREW_TWEETY_PATH))

try:
    from tweety import Twitter
    import yaml
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Install missing packages:")
    print(
        "   /opt/homebrew/bin/python3 -m pip install tweety-ns pyyaml --break-system-packages"
    )
    sys.exit(1)

DEFAULT_MIN_INTERVAL = 5.0
_last_request_time = 0.0


def rate_limit_wait(min_interval: float = DEFAULT_MIN_INTERVAL) -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < min_interval:
        wait_time = min_interval - elapsed
        jitter = random.uniform(0.5, 2.0)
        total_wait = wait_time + jitter
        print(f"  ⏳ Rate limit wait {total_wait:.1f}s...")
        time.sleep(total_wait)
    _last_request_time = time.time()


@dataclass(frozen=True)
class Tweet:
    id: str
    text: str
    created_at: str
    username: str
    likes: int
    retweets: int
    replies: int
    views: int
    url: str
    is_retweet: bool
    is_reply: bool


@dataclass
class FetchResult:
    username: str
    success: bool
    tweets: list[Tweet]
    error: Optional[str] = None


class BatchTwitterFetcher:
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token or self._load_auth_token()
        self.app = Twitter("session")
        if self.auth_token:
            self.app.load_auth_token(self.auth_token)
            print("✅ auth_token loaded")
        else:
            print("⚠️  No auth_token, using guest mode (limited)")

    def _load_auth_token(self) -> Optional[str]:
        config_paths = [
            TREND_CRAWLER_PATH / "config.yaml",
            Path.home() / ".config" / "twitter-crawler" / "config.yaml",
            Path.home() / ".twitter_auth.yaml",
        ]
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)
                        if "twitter_accounts" in config:
                            return config["twitter_accounts"].get("auth_token")
                        if "auth_token" in config:
                            return config["auth_token"]
                except Exception:
                    continue
        return None

    def get_tweets(self, username: str, days: int = 7, limit: int = 20) -> FetchResult:
        rate_limit_wait()
        cutoff_date = datetime.now() - timedelta(days=days)
        try:
            tweets: list[Tweet] = []
            all_tweets = self.app.get_tweets(username, pages=1)
            for tweet in all_tweets:
                if not hasattr(tweet, "text"):
                    continue
                try:
                    tweet_date = tweet.created_on
                    if isinstance(tweet_date, str):
                        tweet_date = datetime.fromisoformat(
                            tweet_date.replace("Z", "+00:00")
                        )
                    if tweet_date < cutoff_date:
                        continue
                except Exception:
                    pass
                if len(tweets) >= limit:
                    break
                replies = getattr(tweet, "reply_counts", 0) or 0
                views = getattr(tweet, "views", 0)
                if views == "Unavailable":
                    views = 0
                views = int(views) if views else 0
                tweets.append(
                    Tweet(
                        id=str(tweet.id),
                        text=tweet.text,
                        created_at=str(tweet.created_on),
                        username=username,
                        likes=tweet.likes,
                        retweets=tweet.retweet_counts,
                        replies=replies,
                        views=views,
                        url=f"https://twitter.com/{username}/status/{tweet.id}",
                        is_retweet=getattr(tweet, "is_retweet", False) or False,
                        is_reply=getattr(tweet, "is_reply", False) or False,
                    )
                )
            return FetchResult(username=username, success=True, tweets=tweets)
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                error_msg = "rate_limit"
            elif "auth" in error_msg.lower():
                error_msg = "auth_failed"
            return FetchResult(
                username=username, success=False, tweets=[], error=error_msg
            )

    def batch_fetch(
        self, usernames: list[str], days: int = 7, limit: int = 20, parallel: int = 5
    ) -> dict[str, FetchResult]:
        results: dict[str, FetchResult] = {}
        total = len(usernames)
        print(f"\n📋 Fetching tweets from {total} accounts...")
        print(f"   Days: {days}, Limit per account: {limit}\n")
        for i, username in enumerate(usernames, 1):
            username = username.lstrip("@")
            print(f"[{i}/{total}] @{username}...", end=" ", flush=True)
            result = self.get_tweets(username, days=days, limit=limit)
            results[username] = result
            if result.success:
                print(f"✅ {len(result.tweets)} tweets")
            else:
                print(f"❌ {result.error}")
            if i < total:
                time.sleep(random.uniform(1, 3))
        return results


def save_results(results: dict[str, FetchResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "fetched_at": datetime.now().isoformat(),
        "total_accounts": len(results),
        "successful": sum(1 for r in results.values() if r.success),
        "failed": sum(1 for r in results.values() if not r.success),
        "accounts": {},
    }
    for username, result in results.items():
        data["accounts"][username] = {
            "success": result.success,
            "error": result.error,
            "tweet_count": len(result.tweets),
            "tweets": [asdict(t) for t in result.tweets],
        }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="AI Weekly Digest batch tweet fetcher")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--parallel", type=int, default=5)
    parser.add_argument("--output", type=str, default="data/tweets.json")
    parser.add_argument("--accounts", type=str)
    parser.add_argument("--auth-token", type=str)

    args = parser.parse_args()

    output_path = Path(__file__).parent.parent / args.output

    if args.accounts:
        accounts_path = Path(args.accounts)
        if accounts_path.exists():
            with open(accounts_path, "r", encoding="utf-8") as f:
                accounts = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
        else:
            print(f"❌ accounts file not found: {accounts_path}")
            sys.exit(1)
    else:
        accounts = [
            "OpenAI",
            "GoogleDeepMind",
            "nvidia",
            "NVIDIAAI",
            "AnthropicAI",
            "MetaAI",
            "deepseek_ai",
            "Alibaba_Qwen",
            "midjourney",
            "Kimi_Moonshot",
            "MiniMax_AI",
            "BytedanceTalk",
            "DeepMind",
            "GoogleAI",
            "GroqInc",
            "Hailuo_AI",
            "MIT_CSAIL",
            "elonmusk",
            "sama",
            "zuck",
            "demishassabis",
            "DarioAmodei",
            "karpathy",
            "ylecun",
            "geoffreyhinton",
            "ilyasut",
            "AndrewYNg",
            "jeffdean",
            "drfeifei",
            "Thom_Wolf",
            "danielaamodei",
            "gdb",
            "GaryMarcus",
            "JustinLin610",
            "steipete",
            "ESYudkowsky",
            "erikbryn",
            "alliekmiller",
            "tunguz",
            "Ronald_vanLoon",
            "DeepLearn007",
            "nigewillson",
            "petite_geek",
            "YuHelenYu",
            "TamaraMcCleary",
            "swyx",
            "joshwoodward",
            "kevinweil",
            "petergyang",
            "thenanyu",
            "realmadhuguru",
            "_catwu",
            "trq212",
            "amasad",
            "rauchg",
            "alexalbert__",
            "levie",
            "ryolu_",
            "mattturck",
            "zarazhangrui",
            "nikunj",
            "danshipper",
            "adityaag",
        ]

    print(f"\n{'=' * 60}")
    print(f"  AI Weekly Digest - 推文批量获取器")
    print(f"{'=' * 60}")
    print(f"  账号数量: {len(accounts)}")
    print(f"  回溯天数: {args.days}")
    print(f"  每账号上限: {args.limit}")
    print(f"  output: {output_path}")
    print(f"{'=' * 60}\n")

    fetcher = BatchTwitterFetcher(auth_token=args.auth_token)

    results = fetcher.batch_fetch(
        usernames=accounts,
        days=args.days,
        limit=args.limit,
        parallel=args.parallel,
    )

    success_count = sum(1 for r in results.values() if r.success)
    total_tweets = sum(len(r.tweets) for r in results.values())

    print(f"\n{'=' * 60}")
    print(
        f"  fetch complete! success: {success_count}/{len(accounts)}, tweets: {total_tweets}"
    )
    print(f"{'=' * 60}")

    save_results(results, output_path)


if __name__ == "__main__":
    main()
