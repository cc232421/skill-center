#!/usr/bin/env python3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gplay_scraper import get_app_details, get_app_reviews

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GPlayCompetitiveAnalyzer:
    def __init__(self, country: str = "us", lang: str = "en"):
        self.country = country
        self.lang = lang
        self.apps_data = {}

    def fetch_app_data(
        self, app_id: str, display_name: Optional[str] = None, reviews_count: int = 500
    ) -> Dict:
        try:
            logger.info(f"Fetching data for {app_id}...")
            details = get_app_details(app_id, lang=self.lang, country=self.country)
            reviews_result = get_app_reviews(
                app_id,
                lang=self.lang,
                country=self.country,
                count=reviews_count,
                sort="newest",
            )

            return {
                "name": display_name or details.get("title", app_id),
                "app_id": app_id,
                "details": details,
                "reviews": reviews_result.get("reviews", []),
                "total_reviews": reviews_result.get("count", 0),
                "fetched_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to fetch data for {app_id}: {e}")
            return {
                "name": display_name or app_id,
                "app_id": app_id,
                "error": str(e),
                "details": {},
                "reviews": [],
                "total_reviews": 0,
            }

    def compare_apps(self, apps: Dict[str, str], reviews_per_app: int = 500) -> Dict:
        logger.info(f"Starting competitive analysis for {len(apps)} apps...")

        for display_name, app_id in apps.items():
            self.apps_data[display_name] = self.fetch_app_data(
                app_id=app_id, display_name=display_name, reviews_count=reviews_per_app
            )

        return {
            "metadata": {
                "country": self.country,
                "lang": self.lang,
                "apps_analyzed": len(apps),
                "reviews_per_app": reviews_per_app,
                "generated_at": datetime.now().isoformat(),
            },
            "summary": self._generate_summary(),
            "app_details": self._analyze_each_app(),
            "comparisons": self._generate_comparisons(),
            "insights": self._generate_insights(),
        }

    def _generate_summary(self) -> Dict:
        total_reviews = sum(app["total_reviews"] for app in self.apps_data.values())

        ratings = {}
        for name, data in self.apps_data.items():
            if "error" not in data and data["details"]:
                score = data["details"].get("score")
                if score:
                    ratings[name] = score

        return {
            "total_reviews_analyzed": total_reviews,
            "apps_with_data": sum(
                1 for app in self.apps_data.values() if "error" not in app
            ),
            "average_scores": ratings,
            "highest_rated": max(ratings.items(), key=lambda x: x[1])[0]
            if ratings
            else None,
            "lowest_rated": min(ratings.items(), key=lambda x: x[1])[0]
            if ratings
            else None,
            "most_reviewed": max(
                self.apps_data.items(), key=lambda x: x[1]["total_reviews"]
            )[0]
            if self.apps_data
            else None,
        }

    def _analyze_each_app(self) -> Dict:
        details = {}

        for name, data in self.apps_data.items():
            if "error" in data:
                details[name] = {"error": data["error"]}
                continue

            app_details = data.get("details", {})
            reviews = data.get("reviews", [])
            ratings = [r["score"] for r in reviews]
            rating_dist = Counter(ratings)

            details[name] = {
                "app_id": data["app_id"],
                "title": app_details.get("title"),
                "developer": app_details.get("developer"),
                "score": app_details.get("score"),
                "ratings_count": app_details.get("ratings"),
                "installs": app_details.get("installs"),
                "min_installs": app_details.get("min_installs"),
                "genre": app_details.get("genre"),
                "price": app_details.get("price"),
                "free": app_details.get("free"),
                "content_rating": app_details.get("content_rating"),
                "contains_ads": app_details.get("contains_ads"),
                "offers_iap": app_details.get("offers_iap"),
                "reviews_analyzed": data["total_reviews"],
                "review_rating_distribution": {
                    "5_star": rating_dist.get(5, 0),
                    "4_star": rating_dist.get(4, 0),
                    "3_star": rating_dist.get(3, 0),
                    "2_star": rating_dist.get(2, 0),
                    "1_star": rating_dist.get(1, 0),
                },
                "review_rating_percentages": {
                    "5_star": round(rating_dist.get(5, 0) / len(ratings) * 100, 1)
                    if ratings
                    else 0,
                    "4_star": round(rating_dist.get(4, 0) / len(ratings) * 100, 1)
                    if ratings
                    else 0,
                    "3_star": round(rating_dist.get(3, 0) / len(ratings) * 100, 1)
                    if ratings
                    else 0,
                    "2_star": round(rating_dist.get(2, 0) / len(ratings) * 100, 1)
                    if ratings
                    else 0,
                    "1_star": round(rating_dist.get(1, 0) / len(ratings) * 100, 1)
                    if ratings
                    else 0,
                },
            }

        return details

    def _generate_comparisons(self) -> Dict:
        comparisons = {
            "rating_comparison": [],
            "installs_comparison": [],
            "sentiment_comparison": [],
        }

        for name, data in self.apps_data.items():
            if "error" in data:
                continue

            details = data.get("details", {})
            reviews = data.get("reviews", [])
            ratings = [r["score"] for r in reviews]

            if details.get("score"):
                comparisons["rating_comparison"].append(
                    {
                        "app": name,
                        "score": details["score"],
                        "ratings_count": details.get("ratings", 0),
                        "installs": details.get("installs", "N/A"),
                    }
                )

            if details.get("min_installs"):
                comparisons["installs_comparison"].append(
                    {
                        "app": name,
                        "installs": details.get("installs"),
                        "min_installs": details.get("min_installs", 0),
                    }
                )

            if ratings:
                positive = sum(1 for r in ratings if r >= 4)
                neutral = sum(1 for r in ratings if r == 3)
                negative = sum(1 for r in ratings if r <= 2)

                comparisons["sentiment_comparison"].append(
                    {
                        "app": name,
                        "positive": round(positive / len(ratings) * 100, 1),
                        "neutral": round(neutral / len(ratings) * 100, 1),
                        "negative": round(negative / len(ratings) * 100, 1),
                    }
                )

        comparisons["rating_comparison"].sort(key=lambda x: x["score"], reverse=True)
        comparisons["installs_comparison"].sort(
            key=lambda x: x["min_installs"], reverse=True
        )

        return comparisons

    def _generate_insights(self) -> List[str]:
        insights = []

        ratings = {}
        for name, data in self.apps_data.items():
            if "error" not in data and data["details"].get("score"):
                ratings[name] = data["details"]["score"]

        if ratings:
            best = max(ratings.items(), key=lambda x: x[1])
            worst = min(ratings.items(), key=lambda x: x[1])

            insights.append(f"🏆 {best[0]} has the highest rating at {best[1]}★")
            insights.append(f"⚠️  {worst[0]} has the lowest rating at {worst[1]}★")

            installs = {}
            for name, data in self.apps_data.items():
                if "error" not in data and data["details"].get("min_installs"):
                    installs[name] = data["details"]["min_installs"]

            if installs:
                most_popular = max(installs.items(), key=lambda x: x[1])
                insights.append(
                    f"📊 {most_popular[0]} has the most installs ({most_popular[1]:,})"
                )

        return insights

    def export_to_json(self, analysis: Dict, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Exported analysis to {filepath}")

    def export_to_csv(self, analysis: Dict, directory: str = "."):
        os.makedirs(directory, exist_ok=True)

        for name, data in self.apps_data.items():
            if "error" not in data and data["reviews"]:
                df = pd.DataFrame(data["reviews"])
                filepath = os.path.join(
                    directory, f"{name.lower().replace(' ', '_')}_reviews.csv"
                )
                df.to_csv(filepath, index=False, encoding="utf-8")
                logger.info(f"Exported {name} reviews to {filepath}")

    def generate_markdown_report(self, analysis: Dict) -> str:
        report = []

        report.append("# Google Play Store Competitive Analysis Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**Region:** {self.country.upper()}")
        report.append(f"**Apps Analyzed:** {analysis['metadata']['apps_analyzed']}")
        report.append("")

        report.append("## Executive Summary")
        report.append("")
        summary = analysis["summary"]
        report.append(
            f"- **Total Reviews Analyzed:** {summary['total_reviews_analyzed']:,}"
        )
        report.append(f"- **Apps with Data:** {summary['apps_with_data']}")
        if summary["highest_rated"]:
            report.append(
                f"- **Highest Rated:** {summary['highest_rated']} ({summary['average_scores'][summary['highest_rated']]}★)"
            )
        if summary["lowest_rated"]:
            report.append(
                f"- **Lowest Rated:** {summary['lowest_rated']} ({summary['average_scores'][summary['lowest_rated']]}★)"
            )
        report.append("")

        report.append("## Key Insights")
        report.append("")
        for insight in analysis["insights"]:
            report.append(f"- {insight}")
        report.append("")

        report.append("## Rating Comparison")
        report.append("")
        report.append("| App | Store Rating | Total Ratings | Installs |")
        report.append("|-----|-------------|---------------|----------|")
        for item in analysis["comparisons"]["rating_comparison"]:
            report.append(
                f"| {item['app']} | {item['score']}★ | {item['ratings_count']:,} | {item['installs']} |"
            )
        report.append("")

        report.append("## Sentiment Analysis (Sampled Reviews)")
        report.append("")
        report.append("| App | Positive | Neutral | Negative |")
        report.append("|-----|----------|---------|----------|")
        for item in analysis["comparisons"]["sentiment_comparison"]:
            report.append(
                f"| {item['app']} | {item['positive']}% | {item['neutral']}% | {item['negative']}% |"
            )
        report.append("")

        report.append("## Detailed App Analysis")
        report.append("")

        for name, details in analysis["app_details"].items():
            report.append(f"### {name}")
            report.append("")

            if "error" in details:
                report.append(f"⚠️ {details['error']}")
                report.append("")
                continue

            report.append(f"- **App ID:** {details['app_id']}")
            report.append(f"- **Title:** {details['title']}")
            report.append(f"- **Developer:** {details['developer']}")
            report.append(f"- **Store Rating:** {details['score']}★")
            report.append(f"- **Total Ratings:** {details['ratings_count']:,}")
            report.append(f"- **Installs:** {details['installs']}")
            report.append(f"- **Genre:** {details['genre']}")
            report.append(f"- **Content Rating:** {details['content_rating']}")
            report.append(f"- **Free:** {'Yes' if details['free'] else 'No'}")
            report.append(
                f"- **Contains Ads:** {'Yes' if details['contains_ads'] else 'No'}"
            )
            report.append(
                f"- **In-App Purchases:** {'Yes' if details['offers_iap'] else 'No'}"
            )
            report.append("")

            report.append("**Sampled Review Rating Distribution:**")
            report.append("")
            report.append("| Rating | Count | Percentage |")
            report.append("|--------|-------|------------|")
            for star in [5, 4, 3, 2, 1]:
                count = details["review_rating_distribution"][f"{star}_star"]
                pct = details["review_rating_percentages"][f"{star}_star"]
                report.append(f"| {star}★ | {count:,} | {pct}% |")
            report.append("")

        return "\n".join(report)


def main():
    competitors = {
        "Reddit": "com.reddit.frontpage",
        "Twitter": "com.twitter.android",
        "Threads": "com.instagram.threads.app",
    }

    analyzer = GPlayCompetitiveAnalyzer(country="us", lang="en")
    analysis = analyzer.compare_apps(competitors, reviews_per_app=50)
    analyzer.export_to_json(analysis, "gplay_competitor_analysis.json")
    analyzer.export_to_csv(analysis, "gplay_review_data")

    report = analyzer.generate_markdown_report(analysis)
    with open("gplay_competitor_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n✓ Analysis complete!")
    print(f"  - JSON: gplay_competitor_analysis.json")
    print(f"  - CSV: gplay_review_data/")
    print(f"  - Report: gplay_competitor_report.md")


if __name__ == "__main__":
    main()
