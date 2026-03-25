---
name: app-store-reviews
description: Scrape and analyze App Store reviews for iOS apps. Use this skill when the user wants to fetch reviews from Apple App Store, analyze competitor apps, generate competitive analysis reports, or extract user feedback from iOS applications. This skill handles review scraping, data aggregation, sentiment analysis, and generates comprehensive competitive reports. Make sure to use this skill whenever the user mentions App Store reviews, competitor analysis, iOS app feedback, or wants to compare multiple apps.
---

# App Store Reviews Scraper

A comprehensive skill for scraping and analyzing Apple App Store reviews. This skill enables competitive analysis, user sentiment tracking, and automated report generation for iOS applications.

## What This Skill Does

This skill provides:
- **Review Scraping**: Fetch reviews from any iOS app on the App Store
- **Batch Processing**: Scrape multiple apps simultaneously for competitive analysis
- **Data Export**: Save reviews as CSV or JSON for further analysis
- **Competitive Reports**: Generate structured reports comparing multiple apps
- **Sentiment Analysis**: Analyze review ratings and content patterns

## When to Use This Skill

Use this skill when you need to:
- Analyze competitor iOS apps
- Track user sentiment for specific apps
- Generate competitive analysis reports
- Extract user feedback and feature requests
- Monitor app reviews over time
- Compare multiple apps in the same category

## Quick Start

### Basic Usage - Single App

```python
from app_store_scraper import AppStore

# Initialize with app name and country
app = AppStore(country="us", app_name="instagram")

# Fetch 100 reviews
app.review(how_many=100)

# Access reviews data
for review in app.reviews:
    print(f"{review['rating']}★: {review['title']}")
```

### Competitive Analysis - Multiple Apps

```python
from scripts.competitive_analyzer import CompetitiveAnalyzer

# Compare multiple apps
analyzer = CompetitiveAnalyzer(country="us")
apps = ["instagram", "tiktok", "snapchat"]

# Generate competitive report
report = analyzer.compare_apps(apps, reviews_per_app=500)
analyzer.export_report(report, "social_media_competitor_analysis.json")
```

## Installation

### Prerequisites

```bash
pip install app-store-scraper pandas
```

### Skill Setup

The skill automatically handles dependencies. If running standalone scripts:

```bash
# Install required packages
pip install -r requirements.txt
```

## Detailed Usage

### 1. Scraping Reviews

#### Single App Scraping

```python
from app_store_scraper import AppStore

# Method 1: Auto-discover app_id
minecraft = AppStore(country="us", app_name="minecraft")
minecraft.review(how_many=200)

# Method 2: Specify app_id directly
notion = AppStore(country="us", app_name="notion", app_id=1232780281)
notion.review(how_many=100)

# Method 3: Fetch all available reviews
zoom = AppStore(country="us", app_name="zoom")
zoom.review()  # Fetches all reviews (may take time for popular apps)
```

#### Parameters

- `country` (required): Two-letter country code (e.g., "us", "cn", "jp")
- `app_name` (required): App name as shown in App Store
- `app_id` (optional): App Store ID (auto-discovered if not provided)
- `how_many` (optional): Number of reviews to fetch (default: all)
- `after` (optional): datetime object to filter older reviews
- `sleep` (optional): Seconds to sleep between requests (rate limiting)

### 2. Review Data Structure

Each review contains:

```python
{
    "date": datetime.datetime,      # Review date
    "isEdited": bool,               # Was the review edited
    "rating": int,                  # 1-5 star rating
    "review": str,                  # Review content
    "title": str,                   # Review title
    "userName": str                 # Reviewer's username
}
```

### 3. Generating Competitive Reports

#### Using the Competitive Analyzer

```python
from scripts.competitive_analyzer import CompetitiveAnalyzer

analyzer = CompetitiveAnalyzer(country="us")

# Define competitor apps
competitors = {
    "Instagram": "instagram",
    "TikTok": "tiktok",
    "Snapchat": "snapchat",
    "Twitter": "twitter"
}

# Generate comprehensive report
report = analyzer.generate_competitor_report(
    competitors=competitors,
    reviews_per_app=1000,
    output_format="markdown"  # or "json", "html"
)

# Save report
with open("competitor_report.md", "w") as f:
    f.write(report)
```

#### Report Contents

The competitive report includes:

1. **Executive Summary**
   - Total reviews analyzed
   - Average ratings comparison
   - Key insights

2. **App-by-App Analysis**
   - Rating distribution
   - Review volume trends
   - Common themes

3. **Comparative Metrics**
   - Side-by-side rating comparison
   - Review sentiment analysis
   - Feature mention frequency

4. **Recommendations**
   - Competitive positioning
   - Improvement opportunities
   - Market gaps

### 4. Data Export

#### Export to CSV

```python
import pandas as pd
from app_store_scraper import AppStore

app = AppStore(country="us", app_name="notion")
app.review(how_many=500)

# Convert to DataFrame
df = pd.DataFrame(app.reviews)

# Export to CSV
df.to_csv("notion_reviews.csv", index=False)
```

#### Export to JSON

```python
import json

# Export reviews
with open("reviews.json", "w") as f:
    json.dump(app.reviews, f, indent=2, default=str)
```

## Advanced Features

### 1. Time-Based Filtering

```python
from datetime import datetime, timedelta
from app_store_scraper import AppStore

# Get reviews from last 30 days
app = AppStore(country="us", app_name="uber")
month_ago = datetime.now() - timedelta(days=30)

app.review(how_many=1000, after=month_ago)
```

### 2. Rate Limiting

```python
# Add delay between requests to avoid rate limiting
app = AppStore(country="us", app_name="spotify")
app.review(how_many=1000, sleep=2)  # 2 second delay between requests
```

### 3. Podcast Reviews

```python
from app_store_scraper import Podcast

# Scrape podcast reviews
podcast = Podcast(country="us", app_name="stuff you should know")
podcast.review(how_many=100)
```

## Best Practices

### 1. Respect Rate Limits

- Use `sleep` parameter for large scraping jobs
- Start with smaller `how_many` values to test
- Avoid aggressive parallel scraping

### 2. Data Validation

```python
# Always check if reviews were fetched
if app.reviews_count > 0:
    print(f"Successfully fetched {app.reviews_count} reviews")
else:
    print("No reviews found - check app name and country")
```

### 3. Error Handling

```python
from app_store_scraper import AppStore
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

try:
    app = AppStore(country="us", app_name="example-app")
    app.review(how_many=100)
except Exception as e:
    print(f"Error: {e}")
```

## Common Use Cases

### Use Case 1: Competitor Monitoring

```python
from scripts.competitive_analyzer import CompetitiveAnalyzer
import schedule
import time

def weekly_competitor_report():
    analyzer = CompetitiveAnalyzer(country="us")
    
    competitors = {
        "Your App": "your-app-name",
        "Competitor A": "competitor-a",
        "Competitor B": "competitor-b"
    }
    
    report = analyzer.generate_competitor_report(
        competitors=competitors,
        reviews_per_app=500
    )
    
    # Save with timestamp
    from datetime import datetime
    filename = f"competitor_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, "w") as f:
        f.write(report)

# Schedule weekly report
schedule.every().monday.at("09:00").do(weekly_competitor_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Use Case 2: Sentiment Analysis

```python
from app_store_scraper import AppStore
import pandas as pd

app = AppStore(country="us", app_name="your-app")
app.review(how_many=1000)

# Analyze rating distribution
ratings = [r['rating'] for r in app.reviews]
avg_rating = sum(ratings) / len(ratings)

print(f"Average Rating: {avg_rating:.2f}")
print(f"5★: {ratings.count(5)} ({ratings.count(5)/len(ratings)*100:.1f}%)")
print(f"4★: {ratings.count(4)} ({ratings.count(4)/len(ratings)*100:.1f}%)")
print(f"3★: {ratings.count(3)} ({ratings.count(3)/len(ratings)*100:.1f}%)")
print(f"2★: {ratings.count(2)} ({ratings.count(2)/len(ratings)*100:.1f}%)")
print(f"1★: {ratings.count(1)} ({ratings.count(1)/len(ratings)*100:.1f}%)")
```

### Use Case 3: Feature Request Extraction

```python
from app_store_scraper import AppStore
import re

app = AppStore(country="us", app_name="your-app")
app.review(how_many=500)

# Extract feature requests
feature_keywords = ['feature', 'add', 'wish', 'please', 'would be nice', 'need']
feature_requests = []

for review in app.reviews:
    text = review['review'].lower()
    if any(keyword in text for keyword in feature_keywords):
        feature_requests.append({
            'rating': review['rating'],
            'title': review['title'],
            'review': review['review']
        })

# Sort by rating (prioritize low ratings with feature requests)
feature_requests.sort(key=lambda x: x['rating'])

for req in feature_requests[:10]:
    print(f"[{req['rating']}★] {req['title']}")
    print(f"    {req['review'][:100]}...")
    print()
```

## Troubleshooting

### Issue: "App not found"

**Solution**: Verify the app name is correct. Try searching in the App Store first.

```python
# Try variations of the name
app = AppStore(country="us", app_name="tik-tok")  # Try with hyphens
app = AppStore(country="us", app_name="tiktok")   # Try without spaces
```

### Issue: "No reviews fetched"

**Solution**: Check the country code. Some apps have reviews only in specific regions.

```python
# Try different countries
for country in ["us", "gb", "ca", "au"]:
    app = AppStore(country=country, app_name="app-name")
    app.review(how_many=20)
    if app.reviews_count > 0:
        print(f"Found reviews in {country}")
        break
```

### Issue: Rate limiting

**Solution**: Add delays between requests and reduce batch size.

```python
app.review(how_many=100, sleep=3)  # 3 second delay
```

## Limitations

1. **Maximum 20 reviews per API call** - This is an App Store limitation
2. **Public reviews only** - Cannot access reviews from users who opted out
3. **No historical data beyond available reviews** - Can only fetch existing reviews
4. **Country-specific** - Reviews are tied to specific App Store regions

## Related Resources

- [app-store-scraper PyPI](https://pypi.org/project/app-store-scraper/)
- [App Store Connect API](https://developer.apple.com/app-store-connect/api/)
- [ISO 3166-1 Country Codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)

## Contributing

When improving this skill:
1. Test with multiple app categories
2. Verify competitive report accuracy
3. Ensure rate limiting is respected
4. Validate data export formats
