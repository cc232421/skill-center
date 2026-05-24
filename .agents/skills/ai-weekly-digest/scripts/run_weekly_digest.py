#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

PYTHON_WITH_TWEETY = "/opt/homebrew/bin/python3"


def run_script(script_name: str, args: list[str]) -> int:
    script_path = Path(__file__).parent / script_name
    cmd = [PYTHON_WITH_TWEETY, str(script_path)] + args
    print(f"\n{'=' * 60}")
    print(f"  Running: {script_name} {' '.join(args)}")
    print(f"{'=' * 60}\n")
    result = subprocess.run(cmd)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Weekly Digest workflow")
    parser.add_argument(
        "--days", type=int, default=7, help="Days to look back (default: 7)"
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Tweets per account (default: 20)"
    )
    parser.add_argument(
        "--parallel", type=int, default=5, help="Parallel fetches (default: 5)"
    )
    parser.add_argument(
        "--min-priority", type=int, default=1, help="Minimum priority (default: 1)"
    )
    parser.add_argument("--title", default="AI Weekly Digest", help="Report title")
    parser.add_argument("--output", default="weekly-digest.md", help="Output filename")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  AI Weekly Digest")
    print(f"{'=' * 60}")
    print(f"  Days: {args.days}")
    print(f"  Tweets/account: {args.limit}")
    print(f"  Min priority: {args.min_priority}")
    print(f"  Output: {args.output}")
    print(f"{'=' * 60}")

    fetch_args = [
        "--days",
        str(args.days),
        "--limit",
        str(args.limit),
        "--parallel",
        str(args.parallel),
        "--output",
        "data/tweets.json",
    ]
    ret = run_script("fetch_all.py", fetch_args)
    if ret != 0:
        print("\nFailed: fetch_all.py")
        sys.exit(ret)

    filter_args = [
        "--input",
        "data/tweets.json",
        "--output",
        "data/filtered.json",
        "--min-priority",
        str(args.min_priority),
    ]
    ret = run_script("filter_content.py", filter_args)
    if ret != 0:
        print("\nFailed: filter_content.py")
        sys.exit(ret)

    report_args = [
        "--input",
        "data/filtered.json",
        "--output",
        args.output,
        "--title",
        args.title,
        "--days",
        str(args.days),
        "--min-priority",
        str(args.min_priority),
    ]
    ret = run_script("generate_report.py", report_args)
    if ret != 0:
        print("\nFailed: generate_report.py")
        sys.exit(ret)

    print(f"\n{'=' * 60}")
    print(f"  Done! Report: {args.output}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
