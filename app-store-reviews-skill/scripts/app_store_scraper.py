#!/usr/bin/env python3
"""
App Store Reviews Scraper - Standalone Implementation
Directly uses Apple's App Store API without relying on Google search.
"""

import requests
import json
import re
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AppStoreScraper:
    """Scrape reviews from Apple App Store."""

    def __init__(
        self,
        country: str = "us",
        app_id: Optional[int] = None,
        app_name: Optional[str] = None,
    ):
        self.country = country.lower()
        self.app_id = app_id
        self.app_name = app_name
        self.reviews = []
        self.reviews_count = 0

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": random.choice(
                    [
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                    ]
                )
            }
        )

    def search_app(self, app_name: str) -> Optional[int]:
        """Search for app by name and return app_id."""
        try:
            search_url = f"https://itunes.apple.com/search"
            params = {
                "term": app_name,
                "country": self.country,
                "entity": "software",
                "limit": 5,
            }

            response = self.session.get(search_url, params=params, timeout=30)
            data = response.json()

            if data["resultCount"] > 0:
                app_id = data["results"][0]["trackId"]
                self.app_name = data["results"][0]["trackName"]
                logger.info(f"Found app: {self.app_name} (ID: {app_id})")
                return app_id
            else:
                logger.warning(f"No app found for: {app_name}")
                return None

        except Exception as e:
            logger.error(f"Error searching for app: {e}")
            return None

    def fetch_reviews(self, how_many: int = 100, sleep: float = 0.5) -> List[Dict]:
        """
        Fetch reviews from App Store.

        Args:
            how_many: Number of reviews to fetch
            sleep: Delay between requests in seconds

        Returns:
            List of review dictionaries
        """
        if not self.app_id and self.app_name:
            self.app_id = self.search_app(self.app_name)

        if not self.app_id:
            raise ValueError(
                "app_id is required. Provide it directly or provide app_name to search."
            )

        self.reviews = []
        offset = 0
        limit = 20

        logger.info(f"Fetching up to {how_many} reviews for app ID {self.app_id}...")

        while len(self.reviews) < how_many:
            try:
                reviews_batch = self._fetch_batch(offset, limit)

                if not reviews_batch:
                    break

                self.reviews.extend(reviews_batch)
                offset += len(reviews_batch)

                logger.info(f"Fetched {len(self.reviews)} reviews so far...")

                if sleep > 0:
                    time.sleep(sleep)

            except Exception as e:
                logger.error(f"Error fetching reviews: {e}")
                break

        self.reviews_count = len(self.reviews)
        logger.info(f"✓ Total reviews fetched: {self.reviews_count}")

        return self.reviews

    def _fetch_batch(self, offset: int, limit: int) -> List[Dict]:
        """Fetch a batch of reviews."""
        url = f"https://itunes.apple.com/{self.country}/rss/customerreviews/id={self.app_id}/sortBy=mostRecent/json"

        try:
            response = self.session.get(url, timeout=30)
            data = response.json()

            if "feed" not in data or "entry" not in data["feed"]:
                return []

            entries = data["feed"]["entry"]

            # Skip the first entry if it's metadata
            if entries and isinstance(entries[0], dict) and "author" not in entries[0]:
                entries = entries[1:]

            reviews = []
            for entry in entries:
                try:
                    review = {
                        "date": self._parse_date(
                            entry.get("updated", {}).get("label", "")
                        ),
                        "rating": int(entry.get("im:rating", {}).get("label", 0)),
                        "title": entry.get("title", {}).get("label", ""),
                        "review": entry.get("content", {}).get("label", ""),
                        "userName": entry.get("author", {})
                        .get("name", {})
                        .get("label", ""),
                        "version": entry.get("im:version", {}).get("label", ""),
                        "isEdited": "updated" in entry,
                    }
                    reviews.append(review)
                except Exception as e:
                    logger.debug(f"Error parsing review entry: {e}")
                    continue

            return reviews

        except Exception as e:
            logger.error(f"Error in batch fetch: {e}")
            return []

    def _parse_date(self, date_str: str) -> datetime:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        except:
            return datetime.now()

    def export_to_json(self, filepath: str):
        """Export reviews to JSON file."""
        output = {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "country": self.country,
            "total_reviews": self.reviews_count,
            "fetched_at": datetime.now().isoformat(),
            "reviews": self.reviews,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"✓ Exported to {filepath}")

    def export_to_csv(self, filepath: str):
        """Export reviews to CSV file."""
        import csv

        if not self.reviews:
            logger.warning("No reviews to export")
            return

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "date",
                    "rating",
                    "title",
                    "review",
                    "userName",
                    "version",
                    "isEdited",
                ],
            )
            writer.writeheader()
            writer.writerows(self.reviews)

        logger.info(f"✓ Exported to {filepath}")


def main():
    """Example usage."""
    scraper = AppStoreScraper(country="us", app_name="instagram")
    scraper.fetch_reviews(how_many=50)

    if scraper.reviews_count > 0:
        scraper.export_to_json("instagram_reviews.json")
        scraper.export_to_csv("instagram_reviews.csv")

        print("\nSample reviews:")
        for review in scraper.reviews[:3]:
            print(f"\n{review['rating']}★ - {review['title']}")
            print(f"  {review['review'][:100]}...")


if __name__ == "__main__":
    main()
