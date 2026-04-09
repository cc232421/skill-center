#!/usr/bin/env python3
"""
cnblogs-post: Post blog articles to cnblogs via MetaWeblog XML-RPC API

Usage:
  python3 post.py --title "标题" --content "<p>HTML内容</p>" [--category "分类"] [--tags "a,b,c"] [--draft]

Environment variables (recommended):
  CNBLOGS_USERNAME   - cnblogs username
  CNBLOGS_PASSWORD   - cnblogs password
  CNBLOGS_BLOGAPP    - blog alias (e.g. "myblog" from www.cnblogs.com/myblog/)

Output JSON: {ok, post_id, url, title} or {ok:false, error}
"""

import sys
import os
import json
import argparse
import xmlrpc.client
from pathlib import Path


def die(msg):
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    sys.exit(1)


def get_config_path():
    return Path.home() / ".cnblogs-post" / "credentials"


def load_stored_credentials():
    """Load credentials from ~/.cnblogs-post/credentials (username\npassword\nblogapp\n)"""
    path = get_config_path()
    if not path.exists():
        return None
    lines = path.read_text().strip().split("\n")
    if len(lines) < 2:
        return None
    return {
        "username": lines[0].strip(),
        "password": lines[1].strip(),
        "blogapp": lines[2].strip() if len(lines) > 2 else "",
    }


def save_credentials(username, password, blogapp):
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{username}\n{password}\n{blogapp}\n")
    os.chmod(path, 0o600)


def load_credentials(args):
    """Priority: args > env > stored file > interactive prompt"""
    username = (args.get("username") or os.environ.get("CNBLOGS_USERNAME") or "").strip()
    password = (args.get("password") or os.environ.get("CNBLOGS_PASSWORD") or "").strip()
    blogapp = (args.get("blogapp") or os.environ.get("CNBLOGS_BLOGAPP") or "").strip()

    # Validate
    missing = []
    if not username:
        missing.append("username")
    if not password:
        missing.append("password")
    if not blogapp:
        missing.append("blogapp")

    if missing:
        # Try stored
        stored = load_stored_credentials()
        if stored:
            username = username or stored.get("username", "")
            password = password or stored.get("password", "")
            blogapp = blogapp or stored.get("blogapp", "")

        still_missing = [m for m in ["username", "password", "blogapp"]
                        if not (username if m == "username" else password if m == "password" else blogapp)]

        if still_missing:
            print(f"Missing credentials: {', '.join(still_missing)}", file=sys.stderr)
            print(f"Please set environment variables or run: python3 {sys.argv[0]} --setup", file=sys.stderr)
            die(f"Missing credential(s): {', '.join(still_missing)}")

    return username, password, blogapp


def post_cnblogs(title, content, username, password, blogapp, category=None, tags=None, draft=False):
    """
    Post to cnblogs via MetaWeblog XML-RPC API.
    Endpoint: https://www.cnblogs.com/services/metaweblog.aspx
    """
    endpoint = "https://www.cnblogs.com/services/metaweblog.aspx"

    try:
        server = xmlrpc.client.ServerProxy(endpoint, verbose=False)
    except Exception as e:
        die(f"Failed to connect to cnblogs API: {e}")

    struct = {
        "title": title,
        "description": content,
    }

    if category:
        struct["categories"] = [category]

    # mt_keywords = tags
    if tags:
        struct["mt_keywords"] = tags

    try:
        post_id = server.metaWeblog.newPost(
            blogapp,        # blogid
            username,       # username
            password,       # password
            struct,         # post content struct
            not draft       # publish (True) or draft (False)
        )
    except xmlrpc.client.Fault as e:
        die(f"API error {e.faultCode}: {e.faultString}")
    except Exception as e:
        die(f"Request failed: {e}")

    # Construct post URL
    # cnblogs URL format: https://www.cnblogs.com/{blogapp}/p/{post_id}.html
    url = f"https://www.cnblogs.com/{blogapp}/p/{post_id}.html"

    return post_id, url


def interactive_setup():
    """Prompt user for credentials and save them."""
    print("=== cnblogs-post setup ===")
    username = input("cnblogs username (邮箱/用户名): ").strip()
    password = input("cnblogs password: ").strip()
    blogapp = input("blog alias (博客地址如 www.cnblogs.com/这里/): ").strip()
    blogapp = blogapp.strip("/").split("/")[-1]  # extract from URL

    if not username or not password or not blogapp:
        die("All fields are required.")

    save_credentials(username, password, blogapp)
    print(f"Credentials saved to {get_config_path()}")
    print("You can now use post.py without entering credentials.")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Post to cnblogs via MetaWeblog API")
    parser.add_argument("title", nargs="?", help="Post title")
    parser.add_argument("content", nargs="?", help="Post content (HTML)")
    parser.add_argument("--title", dest="title2", help="Post title (alternative)")
    parser.add_argument("--content", dest="content2", help="Post content HTML (alternative)")
    parser.add_argument("--category", dest="category", default="", help="Category name")
    parser.add_argument("--tags", dest="tags", default="", help="Tags, comma-separated")
    parser.add_argument("--draft", dest="draft", action="store_true", help="Save as draft")
    parser.add_argument("--blogapp", dest="blogapp", default="", help="Blog alias")
    parser.add_argument("--username", dest="username", default="", help="cnblogs username")
    parser.add_argument("--password", dest="password", default="", help="cnblogs password")
    parser.add_argument("--setup", dest="setup", action="store_true", help="Interactive credential setup")

    args = parser.parse_args()

    if args.setup:
        interactive_setup()

    title = (args.title or args.title2 or "").strip()
    content = (args.content or args.content2 or "").strip()

    # If no args, print help
    if not title and not content and not (title == "" and sys.stdin.isatty()):
        parser.print_help()
        sys.exit(0)

    if not title:
        die("Title is required. Use --title or pass as first argument.")
    if not content:
        # Try reading from stdin
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()
        if not content:
            die("Content is required. Use --content, pass as second argument, or pipe HTML via stdin.")

    username, password, blogapp = load_credentials({
        "username": args.username,
        "password": args.password,
        "blogapp": args.blogapp,
    })

    category = args.category.strip() or None
    tags = args.tags.strip() or None
    draft = args.draft

    post_id, url = post_cnblogs(
        title=title,
        content=content,
        username=username,
        password=password,
        blogapp=blogapp,
        category=category,
        tags=tags,
        draft=draft,
    )

    print(json.dumps({
        "ok": True,
        "post_id": str(post_id),
        "url": url,
        "title": title,
        "draft": draft,
    }))


if __name__ == "__main__":
    main()
