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
from app_store_scraper import AppStoreScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CompetitiveAnalyzer:
    def __init__(self, country: str = "us"):
        self.country = country
        self.apps_data = {}
        
    def fetch_app_reviews(self, app_name: str, app_id: Optional[int] = None, 
                         how_many: int = 500) -> Dict:
        try:
            logger.info(f"Fetching reviews for {app_name}...")
            scraper = AppStoreScraper(country=self.country, app_name=app_name, app_id=app_id)
            scraper.fetch_reviews(how_many=how_many, sleep=0.5)
            
            return {
                'name': app_name,
                'app_id': scraper.app_id,
                'total_reviews': scraper.reviews_count,
                'reviews': scraper.reviews,
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch reviews for {app_name}: {e}")
            return {
                'name': app_name,
                'error': str(e),
                'total_reviews': 0,
                'reviews': []
            }
    
    def compare_apps(self, apps: Dict[str, str], reviews_per_app: int = 500) -> Dict:
        logger.info(f"Starting competitive analysis for {len(apps)} apps...")
        
        for display_name, app_name in apps.items():
            self.apps_data[display_name] = self.fetch_app_reviews(
                app_name=app_name,
                how_many=reviews_per_app
            )
        
        return {
            'metadata': {
                'country': self.country,
                'apps_analyzed': len(apps),
                'reviews_per_app': reviews_per_app,
                'generated_at': datetime.now().isoformat()
            },
            'summary': self._generate_summary(),
            'app_details': self._analyze_each_app(),
            'comparisons': self._generate_comparisons(),
            'insights': self._generate_insights()
        }
    
    def _generate_summary(self) -> Dict:
        total_reviews = sum(app['total_reviews'] for app in self.apps_data.values())
        
        ratings = {}
        for name, data in self.apps_data.items():
            if data['total_reviews'] > 0:
                avg_rating = sum(r['rating'] for r in data['reviews']) / data['total_reviews']
                ratings[name] = round(avg_rating, 2)
        
        return {
            'total_reviews_analyzed': total_reviews,
            'apps_with_data': sum(1 for app in self.apps_data.values() if app['total_reviews'] > 0),
            'average_ratings': ratings,
            'best_rated': max(ratings.items(), key=lambda x: x[1])[0] if ratings else None,
            'most_reviewed': max(self.apps_data.items(), 
                               key=lambda x: x[1]['total_reviews'])[0] if self.apps_data else None
        }
    
    def _analyze_each_app(self) -> Dict:
        details = {}
        
        for name, data in self.apps_data.items():
            if data['total_reviews'] == 0:
                details[name] = {'error': 'No reviews fetched'}
                continue
            
            reviews = data['reviews']
            ratings = [r['rating'] for r in reviews]
            rating_dist = Counter(ratings)
            
            month_ago = datetime.now() - timedelta(days=30)
            recent_reviews = [r for r in reviews if r['date'] > month_ago]
            
            details[name] = {
                'app_id': data.get('app_id'),
                'total_reviews': data['total_reviews'],
                'average_rating': round(sum(ratings) / len(ratings), 2),
                'rating_distribution': {
                    '5_star': rating_dist.get(5, 0),
                    '4_star': rating_dist.get(4, 0),
                    '3_star': rating_dist.get(3, 0),
                    '2_star': rating_dist.get(2, 0),
                    '1_star': rating_dist.get(1, 0)
                },
                'rating_percentages': {
                    '5_star': round(rating_dist.get(5, 0) / len(ratings) * 100, 1),
                    '4_star': round(rating_dist.get(4, 0) / len(ratings) * 100, 1),
                    '3_star': round(rating_dist.get(3, 0) / len(ratings) * 100, 1),
                    '2_star': round(rating_dist.get(2, 0) / len(ratings) * 100, 1),
                    '1_star': round(rating_dist.get(1, 0) / len(ratings) * 100, 1)
                },
                'recent_reviews_count': len(recent_reviews),
                'recent_average_rating': round(
                    sum(r['rating'] for r in recent_reviews) / len(recent_reviews), 2
                ) if recent_reviews else None
            }
        
        return details
    
    def _generate_comparisons(self) -> Dict:
        comparisons = {
            'rating_comparison': [],
            'volume_comparison': [],
            'sentiment_comparison': []
        }
        
        for name, data in self.apps_data.items():
            if data['total_reviews'] == 0:
                continue
            
            reviews = data['reviews']
            ratings = [r['rating'] for r in reviews]
            
            comparisons['rating_comparison'].append({
                'app': name,
                'average_rating': round(sum(ratings) / len(ratings), 2),
                'total_reviews': data['total_reviews']
            })
            
            comparisons['volume_comparison'].append({
                'app': name,
                'total_reviews': data['total_reviews']
            })
            
            positive = sum(1 for r in ratings if r >= 4)
            neutral = sum(1 for r in ratings if r == 3)
            negative = sum(1 for r in ratings if r <= 2)
            
            comparisons['sentiment_comparison'].append({
                'app': name,
                'positive': round(positive / len(ratings) * 100, 1),
                'neutral': round(neutral / len(ratings) * 100, 1),
                'negative': round(negative / len(ratings) * 100, 1)
            })
        
        comparisons['rating_comparison'].sort(key=lambda x: x['average_rating'], reverse=True)
        comparisons['volume_comparison'].sort(key=lambda x: x['total_reviews'], reverse=True)
        
        return comparisons
    
    def _generate_insights(self) -> List[str]:
        insights = []
        
        ratings = {}
        for name, data in self.apps_data.items():
            if data['total_reviews'] > 0:
                avg = sum(r['rating'] for r in data['reviews']) / data['total_reviews']
                ratings[name] = avg
        
        if ratings:
            best = max(ratings.items(), key=lambda x: x[1])
            worst = min(ratings.items(), key=lambda x: x[1])
            
            insights.append(f"🏆 {best[0]} has the highest average rating at {best[1]:.2f}★")
            insights.append(f"⚠️  {worst[0]} has the lowest average rating at {worst[1]:.2f}★")
            
            volumes = {name: data['total_reviews'] 
                      for name, data in self.apps_data.items()}
            most_active = max(volumes.items(), key=lambda x: x[1])
            insights.append(
                f"📊 {most_active[0]} has the most user engagement with "
                f"{most_active[1]} reviews analyzed"
            )
        
        return insights
    
    def export_to_json(self, analysis: Dict, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Exported analysis to {filepath}")
    
    def export_to_csv(self, analysis: Dict, directory: str = "."):
        os.makedirs(directory, exist_ok=True)
        
        for name, data in self.apps_data.items():
            if data['total_reviews'] > 0:
                df = pd.DataFrame(data['reviews'])
                filepath = os.path.join(directory, f"{name.lower().replace(' ', '_')}_reviews.csv")
                df.to_csv(filepath, index=False, encoding='utf-8')
                logger.info(f"Exported {name} reviews to {filepath}")
    
    def generate_markdown_report(self, analysis: Dict) -> str:
        report = []
        
        report.append("# App Store Competitive Analysis Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**Region:** {self.country.upper()}")
        report.append(f"**Apps Analyzed:** {analysis['metadata']['apps_analyzed']}")
        report.append("")
        
        report.append("## Executive Summary")
        report.append("")
        summary = analysis['summary']
        report.append(f"- **Total Reviews Analyzed:** {summary['total_reviews_analyzed']:,}")
        report.append(f"- **Apps with Data:** {summary['apps_with_data']}")
        if summary['best_rated']:
            report.append(f"- **Best Rated:** {summary['best_rated']} ({summary['average_ratings'][summary['best_rated']]}★)")
        if summary['most_reviewed']:
            report.append(f"- **Most Reviewed:** {summary['most_reviewed']}")
        report.append("")
        
        report.append("## Key Insights")
        report.append("")
        for insight in analysis['insights']:
            report.append(f"- {insight}")
        report.append("")
        
        report.append("## Rating Comparison")
        report.append("")
        report.append("| App | Average Rating | Total Reviews |")
        report.append("|-----|---------------|---------------|")
        for item in analysis['comparisons']['rating_comparison']:
            report.append(f"| {item['app']} | {item['average_rating']}★ | {item['total_reviews']:,} |")
        report.append("")
        
        report.append("## Sentiment Analysis")
        report.append("")
        report.append("| App | Positive | Neutral | Negative |")
        report.append("|-----|----------|---------|----------|")
        for item in analysis['comparisons']['sentiment_comparison']:
            report.append(
                f"| {item['app']} | {item['positive']}% | {item['neutral']}% | {item['negative']}% |"
            )
        report.append("")
        
        report.append("## Detailed App Analysis")
        report.append("")
        
        for name, details in analysis['app_details'].items():
            report.append(f"### {name}")
            report.append("")
            
            if 'error' in details:
                report.append(f"⚠️ {details['error']}")
                report.append("")
                continue
            
            report.append(f"- **App ID:** {details['app_id']}")
            report.append(f"- **Average Rating:** {details['average_rating']}★")
            report.append(f"- **Total Reviews:** {details['total_reviews']:,}")
            report.append("")
            
            report.append("**Rating Distribution:**")
            report.append("")
            report.append("| Rating | Count | Percentage |")
            report.append("|--------|-------|------------|")
            for star in [5, 4, 3, 2, 1]:
                count = details['rating_distribution'][f'{star}_star']
                pct = details['rating_percentages'][f'{star}_star']
                report.append(f"| {star}★ | {count:,} | {pct}% |")
            report.append("")
            
            if details['recent_average_rating']:
                report.append(f"**Recent Activity (30 days):** {details['recent_reviews_count']} reviews, "
                            f"{details['recent_average_rating']}★ average")
                report.append("")
        
        return "\n".join(report)


def main():
    competitors = {
        "Instagram": "instagram",
        "TikTok": "tiktok",
        "Snapchat": "snapchat",
    }
    
    analyzer = CompetitiveAnalyzer(country="us")
    analysis = analyzer.compare_apps(competitors, reviews_per_app=50)
    analyzer.export_to_json(analysis, "competitor_analysis.json")
    analyzer.export_to_csv(analysis, "review_data")
    
    report = analyzer.generate_markdown_report(analysis)
    with open("competitor_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n✓ Analysis complete!")
    print(f"  - JSON: competitor_analysis.json")
    print(f"  - CSV: review_data/")
    print(f"  - Report: competitor_report.md")


if __name__ == "__main__":
    main()
