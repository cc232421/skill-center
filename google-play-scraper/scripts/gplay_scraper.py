#!/usr/bin/env python3
"""
Google Play Scraper wrapper module for Claude Code skill.

This module provides simplified interfaces to the google-play-scraper library
for common use cases like getting app details, reviews, search results, and permissions.
"""

import json
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict

# Try to import google_play_scraper, provide helpful error if not installed
try:
    from google_play_scraper import app, reviews, reviews_all, search, permissions, Sort
except ImportError:
    raise ImportError(
        "google-play-scraper not installed. Run: pip install google-play-scraper"
    )


@dataclass
class AppDetails:
    """Structured app details data."""

    title: str
    description: str
    summary: str
    installs: str
    min_installs: int
    real_installs: int
    score: float
    ratings: int
    reviews_count: int
    histogram: List[int]
    price: float
    free: bool
    currency: str
    sale: bool
    offers_iap: bool
    in_app_product_price: Optional[str]
    developer: str
    developer_id: str
    developer_email: Optional[str]
    developer_website: Optional[str]
    developer_address: Optional[str]
    privacy_policy: Optional[str]
    genre: str
    genre_id: str
    categories: List[Dict[str, Any]]
    icon: str
    header_image: Optional[str]
    screenshots: List[str]
    video: Optional[str]
    video_image: Optional[str]
    content_rating: str
    content_rating_description: Optional[str]
    ad_supported: bool
    contains_ads: bool
    released: Optional[str]
    updated: int
    version: Optional[str]
    comments: List[str]
    app_id: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class Review:
    """Structured review data."""

    review_id: str
    user_name: str
    user_image: Optional[str]
    content: str
    score: int
    thumbs_up_count: int
    review_created_version: Optional[str]
    at: str
    reply_content: Optional[str]
    replied_at: Optional[str]
    app_version: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SearchResult:
    """Structured search result data."""

    app_id: str
    title: str
    icon: str
    screenshots: List[str]
    score: Optional[float]
    genre: str
    price: float
    free: bool
    currency: str
    video: Optional[str]
    video_image: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def get_app_details(
    app_id: str, lang: str = "en", country: str = "us"
) -> Dict[str, Any]:
    """
    Get comprehensive details about an app.

    Args:
        app_id: The app package ID (e.g., "com.whatsapp")
        lang: Language code (ISO 639-1, default: "en")
        country: Country code (ISO 3166, default: "us")

    Returns:
        Dictionary containing app details

    Raises:
        ValueError: If app_id is invalid
        Exception: If app not found or other errors
    """
    if not app_id or not isinstance(app_id, str):
        raise ValueError("app_id must be a non-empty string")

    try:
        result = app(app_id, lang=lang, country=country)

        # Normalize field names for consistency
        normalized = {
            "title": result.get("title"),
            "description": result.get("description"),
            "summary": result.get("summary"),
            "installs": result.get("installs"),
            "min_installs": result.get("minInstalls"),
            "real_installs": result.get("realInstalls"),
            "score": result.get("score"),
            "ratings": result.get("ratings"),
            "reviews_count": result.get("reviews"),
            "histogram": result.get("histogram", []),
            "price": result.get("price", 0),
            "free": result.get("free", True),
            "currency": result.get("currency", "USD"),
            "sale": result.get("sale", False),
            "offers_iap": result.get("offersIAP", False),
            "in_app_product_price": result.get("inAppProductPrice"),
            "developer": result.get("developer"),
            "developer_id": result.get("developerId"),
            "developer_email": result.get("developerEmail"),
            "developer_website": result.get("developerWebsite"),
            "developer_address": result.get("developerAddress"),
            "privacy_policy": result.get("privacyPolicy"),
            "genre": result.get("genre"),
            "genre_id": result.get("genreId"),
            "categories": result.get("categories", []),
            "icon": result.get("icon"),
            "header_image": result.get("headerImage"),
            "screenshots": result.get("screenshots", []),
            "video": result.get("video"),
            "video_image": result.get("videoImage"),
            "content_rating": result.get("contentRating"),
            "content_rating_description": result.get("contentRatingDescription"),
            "ad_supported": result.get("adSupported", False),
            "contains_ads": result.get("containsAds", False),
            "released": result.get("released"),
            "updated": result.get("updated"),
            "version": result.get("version"),
            "comments": result.get("comments", []),
            "app_id": result.get("appId"),
            "url": result.get("url"),
        }

        return normalized

    except Exception as e:
        raise Exception(f"Failed to get app details for {app_id}: {str(e)}")


def get_app_reviews(
    app_id: str,
    lang: str = "en",
    country: str = "us",
    sort: str = "newest",
    count: int = 100,
    filter_score: Optional[int] = None,
    continuation_token: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Get reviews for an app.

    Args:
        app_id: The app package ID
        lang: Language code (ISO 639-1, default: "en")
        country: Country code (ISO 3166, default: "us")
        sort: Sort order - "newest", "rating", or "helpfulness"
        count: Number of reviews to fetch (default: 100)
        filter_score: Filter by rating (1-5), None for all
        continuation_token: Token for pagination from previous call

    Returns:
        Dictionary with "reviews" list and "continuation_token"
    """
    if not app_id or not isinstance(app_id, str):
        raise ValueError("app_id must be a non-empty string")

    # Map sort strings to Sort enum
    sort_map = {
        "newest": Sort.NEWEST,
        "rating": Sort.RATING,
        "helpfulness": Sort.MOST_RELEVANT,
        "most_relevant": Sort.MOST_RELEVANT,
    }
    sort_enum = sort_map.get(sort.lower(), Sort.NEWEST)

    try:
        result, token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=sort_enum,
            count=count,
            filter_score_with=filter_score,
            continuation_token=continuation_token,
        )

        # Normalize review data
        normalized_reviews = []
        for r in result:
            review = {
                "review_id": r.get("reviewId"),
                "user_name": r.get("userName"),
                "user_image": r.get("userImage"),
                "content": r.get("content"),
                "score": r.get("score"),
                "thumbs_up_count": r.get("thumbsUpCount", 0),
                "review_created_version": r.get("reviewCreatedVersion"),
                "at": r.get("at").isoformat() if r.get("at") else None,
                "reply_content": r.get("replyContent"),
                "replied_at": r.get("repliedAt").isoformat()
                if r.get("repliedAt")
                else None,
                "app_version": r.get("appVersion"),
            }
            normalized_reviews.append(review)

        return {
            "reviews": normalized_reviews,
            "continuation_token": token,
            "count": len(normalized_reviews),
        }

    except Exception as e:
        raise Exception(f"Failed to get reviews for {app_id}: {str(e)}")


def get_all_reviews(
    app_id: str,
    lang: str = "en",
    country: str = "us",
    sort: str = "newest",
    filter_score: Optional[int] = None,
    sleep_milliseconds: int = 0,
) -> List[Dict[str, Any]]:
    """
    Get ALL reviews for an app (may make many requests).

    WARNING: This can make thousands of HTTP requests for popular apps.
    Use with caution and consider rate limits.

    Args:
        app_id: The app package ID
        lang: Language code
        country: Country code
        sort: Sort order
        filter_score: Filter by rating (1-5)
        sleep_milliseconds: Delay between requests

    Returns:
        List of all reviews
    """
    if not app_id or not isinstance(app_id, str):
        raise ValueError("app_id must be a non-empty string")

    sort_map = {
        "newest": Sort.NEWEST,
        "rating": Sort.RATING,
        "helpfulness": Sort.HELPFULNESS,
    }
    sort_enum = sort_map.get(sort.lower(), Sort.NEWEST)

    try:
        result = reviews_all(
            app_id,
            lang=lang,
            country=country,
            sort=sort_enum,
            filter_score_with=filter_score,
            sleep_milliseconds=sleep_milliseconds,
        )

        # Normalize
        normalized_reviews = []
        for r in result:
            review = {
                "review_id": r.get("reviewId"),
                "user_name": r.get("userName"),
                "user_image": r.get("userImage"),
                "content": r.get("content"),
                "score": r.get("score"),
                "thumbs_up_count": r.get("thumbsUpCount", 0),
                "review_created_version": r.get("reviewCreatedVersion"),
                "at": r.get("at").isoformat() if r.get("at") else None,
                "reply_content": r.get("replyContent"),
                "replied_at": r.get("repliedAt").isoformat()
                if r.get("repliedAt")
                else None,
                "app_version": r.get("appVersion"),
            }
            normalized_reviews.append(review)

        return normalized_reviews

    except Exception as e:
        raise Exception(f"Failed to get all reviews for {app_id}: {str(e)}")


def search_apps(
    query: str, lang: str = "en", country: str = "us", n_hits: int = 30
) -> List[Dict[str, Any]]:
    """
    Search for apps on Google Play.

    Args:
        query: Search query string
        lang: Language code
        country: Country code
        n_hits: Number of results (max 30)

    Returns:
        List of search results
    """
    if not query or not isinstance(query, str):
        raise ValueError("query must be a non-empty string")

    try:
        results = search(query, lang=lang, country=country, n_hits=n_hits)

        # Normalize
        normalized = []
        for r in results:
            item = {
                "app_id": r.get("appId"),
                "title": r.get("title"),
                "icon": r.get("icon"),
                "screenshots": r.get("screenshots", []),
                "score": r.get("score"),
                "genre": r.get("genre"),
                "price": r.get("price", 0),
                "free": r.get("free", True),
                "currency": r.get("currency", "USD"),
                "video": r.get("video"),
                "video_image": r.get("videoImage"),
            }
            normalized.append(item)

        return normalized

    except Exception as e:
        raise Exception(f"Failed to search for '{query}': {str(e)}")


def get_app_permissions(
    app_id: str, lang: str = "en", country: str = "us"
) -> Dict[str, List[str]]:
    """
    Get permissions required by an app.

    Args:
        app_id: The app package ID
        lang: Language code
        country: Country code

    Returns:
        Dictionary mapping permission categories to lists of permissions
    """
    if not app_id or not isinstance(app_id, str):
        raise ValueError("app_id must be a non-empty string")

    try:
        result = permissions(app_id, lang=lang, country=country)
        return result
    except Exception as e:
        raise Exception(f"Failed to get permissions for {app_id}: {str(e)}")


def batch_get_app_details(
    app_ids: List[str],
    lang: str = "en",
    country: str = "us",
    delay_seconds: float = 1.0,
) -> Dict[str, Dict[str, Any]]:
    """
    Get details for multiple apps with rate limiting.

    Args:
        app_ids: List of app package IDs
        lang: Language code
        country: Country code
        delay_seconds: Delay between requests to avoid rate limiting

    Returns:
        Dictionary mapping app_id to details (or error message)
    """
    results = {}

    for i, app_id in enumerate(app_ids):
        try:
            details = get_app_details(app_id, lang=lang, country=country)
            results[app_id] = details
        except Exception as e:
            results[app_id] = {"error": str(e)}

        # Add delay between requests (except for the last one)
        if i < len(app_ids) - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)

    return results


def compare_apps(
    app_ids: List[str], lang: str = "en", country: str = "us"
) -> Dict[str, Any]:
    """
    Compare multiple apps and return a comparison summary.

    Args:
        app_ids: List of app package IDs
        lang: Language code
        country: Country code

    Returns:
        Comparison data including rankings by score, installs, etc.
    """
    details = batch_get_app_details(app_ids, lang=lang, country=country)

    # Filter out errors
    valid_apps = {k: v for k, v in details.items() if "error" not in v}

    if not valid_apps:
        return {"error": "No valid apps found", "details": details}

    # Create comparison summary
    comparison = {
        "apps": valid_apps,
        "rankings": {
            "by_score": sorted(
                valid_apps.items(),
                key=lambda x: x[1].get("score", 0) or 0,
                reverse=True,
            ),
            "by_installs": sorted(
                valid_apps.items(),
                key=lambda x: x[1].get("min_installs", 0) or 0,
                reverse=True,
            ),
            "by_ratings": sorted(
                valid_apps.items(),
                key=lambda x: x[1].get("ratings", 0) or 0,
                reverse=True,
            ),
        },
        "summary": {
            "total_apps": len(app_ids),
            "successful": len(valid_apps),
            "failed": len(app_ids) - len(valid_apps),
        },
    }

    return comparison


# CLI interface for direct script execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Google Play Scraper CLI")
    parser.add_argument(
        "command", choices=["details", "reviews", "search", "permissions"]
    )
    parser.add_argument("--app-id", help="App package ID")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--lang", default="en", help="Language code")
    parser.add_argument("--country", default="us", help="Country code")
    parser.add_argument("--count", type=int, default=100, help="Number of reviews")
    parser.add_argument("--output", help="Output JSON file")

    args = parser.parse_args()

    try:
        if args.command == "details":
            if not args.app_id:
                print("Error: --app-id required for details command")
                exit(1)
            result = get_app_details(args.app_id, args.lang, args.country)

        elif args.command == "reviews":
            if not args.app_id:
                print("Error: --app-id required for reviews command")
                exit(1)
            result = get_app_reviews(
                args.app_id, args.lang, args.country, count=args.count
            )

        elif args.command == "search":
            if not args.query:
                print("Error: --query required for search command")
                exit(1)
            result = search_apps(args.query, args.lang, args.country)

        elif args.command == "permissions":
            if not args.app_id:
                print("Error: --app-id required for permissions command")
                exit(1)
            result = get_app_permissions(args.app_id, args.lang, args.country)

        # Output result
        output = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Output saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
