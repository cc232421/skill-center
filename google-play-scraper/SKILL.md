---
name: google-play-scraper
description: |
  Scrape and analyze Google Play Store app data including app details, reviews, ratings, permissions, and search results.
  
  Use this skill whenever the user needs to:
  - Get information about Android apps from Google Play Store
  - Analyze app reviews and ratings
  - Search for apps on Google Play
  - Check app permissions
  - Perform competitive analysis of mobile apps
  - Extract app metadata (downloads, ratings, developer info, etc.)
  - Monitor app performance metrics
  - Research mobile app market data
  
  This skill provides comprehensive Google Play Store data extraction capabilities without requiring external API keys.
---

# Google Play Scraper Skill

This skill enables you to scrape and analyze data from Google Play Store using the `google-play-scraper` Python library.

## Capabilities

1. **App Details**: Get comprehensive information about any app (title, description, ratings, downloads, developer info, screenshots, etc.)
2. **Reviews**: Fetch and analyze user reviews with filtering options (by rating, date, relevance)
3. **Search**: Search for apps by keywords and get matching results
4. **Permissions**: Retrieve app permission requirements
5. **Batch Operations**: Process multiple apps efficiently

## When to Use

- **Market Research**: Analyze competitor apps, their ratings, and user feedback
- **App Analysis**: Get detailed metadata about specific apps
- **Review Mining**: Extract and analyze user reviews for sentiment or feature requests
- **Permission Auditing**: Check what permissions apps require
- **Trend Monitoring**: Track app performance metrics over time

## Installation

The skill requires Python and the `google-play-scraper` package:

```bash
pip install google-play-scraper
```

## Usage Patterns

### Pattern 1: Get App Details

For getting comprehensive information about a single app:

```python
from scripts.gplay_scraper import get_app_details

# Get details for a specific app
app_info = get_app_details(
    app_id="com.nianticlabs.pokemongo",
    lang="en",
    country="us"
)

# Returns structured data including:
# - title, description, summary
# - ratings, reviews count, score
# - installs, price, developer info
# - screenshots, icon, video
# - permissions, categories
```

### Pattern 2: Fetch Reviews

For extracting and analyzing user reviews:

```python
from scripts.gplay_scraper import get_app_reviews

# Get recent reviews
reviews = get_app_reviews(
    app_id="com.spotify.music",
    lang="en",
    country="us",
    sort="newest",  # or "rating", "helpfulness"
    count=100,
    filter_score=5  # Optional: filter by rating (1-5)
)

# Returns list of reviews with:
# - userName, userImage
# - content, score
# - thumbsUpCount, reviewCreatedVersion
# - at (timestamp), replyContent
```

### Pattern 3: Search Apps

For finding apps by keywords:

```python
from scripts.gplay_scraper import search_apps

# Search for apps
results = search_apps(
    query="fitness tracker",
    lang="en",
    country="us",
    n_hits=30  # Number of results (max 30)
)

# Returns list of apps with:
# - appId, title, icon
# - score, genre, price
# - screenshots, summary
```

### Pattern 4: Get Permissions

For checking app permissions:

```python
from scripts.gplay_scraper import get_app_permissions

# Get permissions
permissions = get_app_permissions(
    app_id="com.facebook.katana",
    lang="en",
    country="us"
)

# Returns dict with permission categories and specific permissions
```

### Pattern 5: Batch Operations

For processing multiple apps:

```python
from scripts.gplay_scraper import batch_get_app_details

# Process multiple apps
app_ids = ["com.whatsapp", "com.instagram.android", "com.twitter.android"]
results = batch_get_app_details(app_ids, lang="en", country="us")

# Returns dict mapping app_id to details
```

## Output Formats

### App Details Output

```json
{
  "title": "App Name",
  "description": "Full description...",
  "summary": "Short summary",
  "installs": "100,000,000+",
  "minInstalls": 100000000,
  "score": 4.5,
  "ratings": 1000000,
  "reviews": 500000,
  "histogram": [100, 200, 300, 400, 500],
  "price": 0,
  "free": true,
  "currency": "USD",
  "developer": "Developer Name",
  "developerEmail": "dev@example.com",
  "developerWebsite": "https://example.com",
  "genre": "Category",
  "genreId": "CATEGORY_ID",
  "icon": "https://...",
  "screenshots": ["https://..."],
  "video": "https://...",
  "contentRating": "Everyone",
  "released": "Jan 1, 2020",
  "updated": 1609459200,
  "version": "1.0.0",
  "appId": "com.example.app",
  "url": "https://play.google.com/store/apps/details?id=com.example.app"
}
```

### Reviews Output

```json
[
  {
    "reviewId": "uuid",
    "userName": "User Name",
    "userImage": "https://...",
    "content": "Review text...",
    "score": 5,
    "thumbsUpCount": 10,
    "reviewCreatedVersion": "1.0.0",
    "at": "2024-01-01T00:00:00",
    "replyContent": "Developer reply...",
    "repliedAt": "2024-01-02T00:00:00",
    "appVersion": "1.0.0"
  }
]
```

## Best Practices

1. **Rate Limiting**: Be respectful to Google Play servers. Use reasonable delays between requests (built into the scripts).

2. **Error Handling**: Always handle potential errors:
   - App not found
   - Network issues
   - Rate limiting

3. **Language/Country**: Specify appropriate `lang` and `country` parameters for localized results:
   - `lang`: ISO 639-1 language code (e.g., "en", "zh", "ja")
   - `country`: ISO 3166 country code (e.g., "us", "cn", "jp")

4. **Review Pagination**: When fetching many reviews, use continuation tokens for pagination rather than fetching all at once.

5. **Data Validation**: Validate app IDs format (typically `com.company.appname`).

## Common App IDs

Here are some popular app IDs for reference:
- WhatsApp: `com.whatsapp`
- Instagram: `com.instagram.android`
- Facebook: `com.facebook.katana`
- TikTok: `com.zhiliaoapp.musically`
- Spotify: `com.spotify.music`
- Twitter/X: `com.twitter.android`
- Pokemon GO: `com.nianticlabs.pokemongo`

## Limitations

- Google Play Store structure changes may affect scraping
- Some apps may have restricted access
- Review counts are limited by Google's pagination (max ~200 per request)
- Rate limits apply (handled automatically with delays)

## Example Workflows

### Workflow 1: Competitive Analysis

```python
# 1. Get details for competitor apps
competitors = ["com.whatsapp", "com.telegram.messenger", "com.signalapp.signal"]
details = batch_get_app_details(competitors)

# 2. Compare ratings and downloads
for app_id, info in details.items():
    print(f"{info['title']}: {info['score']}/5 ({info['installs']} installs)")

# 3. Get recent reviews for sentiment analysis
for app_id in competitors:
    reviews = get_app_reviews(app_id, count=100)
    # Analyze reviews...
```

### Workflow 2: App Monitoring

```python
# Track app metrics over time
import json
from datetime import datetime

app_id = "com.yourcompany.yourapp"
app_info = get_app_details(app_id)

# Save metrics with timestamp
metrics = {
    "timestamp": datetime.now().isoformat(),
    "score": app_info["score"],
    "ratings": app_info["ratings"],
    "reviews": app_info["reviews"],
    "installs": app_info["minInstalls"]
}

# Append to tracking file
with open("app_metrics.jsonl", "a") as f:
    f.write(json.dumps(metrics) + "\n")
```

### Workflow 3: Review Analysis

```python
# Get all reviews for analysis
reviews = get_app_reviews(
    app_id="com.example.app",
    count=1000,
    sort="newest"
)

# Filter by rating
positive = [r for r in reviews if r["score"] >= 4]
negative = [r for r in reviews if r["score"] <= 2]

# Export for further analysis
import pandas as pd
df = pd.DataFrame(reviews)
df.to_csv("reviews.csv", index=False)
```

## Troubleshooting

**Issue**: "App not found" error
- Verify the app ID is correct
- Check if the app is available in the specified country

**Issue**: Empty or incomplete data
- Some apps may restrict certain information
- Try different language/country combinations

**Issue**: Rate limiting
- The scripts include automatic delays
- For large batches, increase delays between requests

### Workflow 4: Competitive Analysis Report

For generating comprehensive competitive analysis reports:

```python
from scripts.competitive_analyzer import GPlayCompetitiveAnalyzer

analyzer = GPlayCompetitiveAnalyzer(country="us", lang="en")

competitors = {
    "App A": "com.example.appA",
    "App B": "com.example.appB",
    "App C": "com.example.appC"
}

analysis = analyzer.compare_apps(competitors, reviews_per_app=500)

# Export results
analyzer.export_to_json(analysis, "competitor_analysis.json")
analyzer.export_to_csv(analysis, "review_data")

# Generate markdown report
report = analyzer.generate_markdown_report(analysis)
with open("competitor_report.md", "w") as f:
    f.write(report)
```

The report includes:
- Executive summary with key metrics
- Rating comparison across apps
- Sentiment analysis (positive/neutral/negative)
- Detailed app information
- Review rating distribution

## File Structure

```
google-play-scraper/
├── SKILL.md
├── requirements.txt
├── scripts/
│   ├── gplay_scraper.py          # Core scraping functions
│   └── competitive_analyzer.py   # Competitive analysis tools
└── evals/
    └── evals.json
```

## References

- Original library: https://github.com/JoMingyu/google-play-scraper
- PyPI: https://pypi.org/project/google-play-scraper/
- ISO 639-1 language codes: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
- ISO 3166 country codes: https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
