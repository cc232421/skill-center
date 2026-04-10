---
name: fredapi
description: |
  fredapi — Python library for FRED (Federal Reserve Economic Data). Use this when the user needs economic data, financial indicators, macroeconomic analysis, GDP, CPI, unemployment, interest rates, stock indices, or any Federal Reserve economic data. Triggers on: "economic data", "FRED", "GDP", "CPI", "inflation", "unemployment rate", "interest rates", "federal reserve", "macro economic", " macroeconomic", "stock market data", "S&P 500", "treasury yield", "bond yields", "real GDP", "consumer price index", "PPI", "industrial production", "fredapi", "federal reserve data", "St. Louis Fed", "US economy", "economic indicators". Helps search, fetch, and analyze thousands of US and international economic indicators from FRED.
allowed-tools: Bash, Read
compatibility: "Claude Code ≥1.0, OpenClaw, OpenCode"
---

# fredapi — FRED Economic Data for AI Agents

Python library wrapping the FRED (Federal Reserve Economic Data) API from the St. Louis Fed. Returns data as pandas Series or DataFrames.

**What you can do with this skill:**
- Search for economic indicators by keyword
- Fetch time series data (GDP, CPI, unemployment, interest rates, etc.)
- Analyze data revisions (ALFRED archival data)
- Get series metadata (units, frequency, notes)

## Installation

```bash
pip install fredapi
# or
uv pip install fredapi
```

Requires: Python 3, pandas

## API Key Setup

**You MUST have a FRED API key.** Get one free at: https://fred.stlouisfed.org/docs/api/api_key.html

Three ways to provide the key (in order of priority):

```python
# 1. Environment variable (recommended for AI agents)
import os
os.environ['FRED_API_KEY'] = 'your-32-char-key-here'

from fredapi import Fred
fred = Fred()  # reads from env automatically

# 2. Direct string
from fredapi import Fred
fred = Fred(api_key='your-32-char-key-here')

# 3. File path
from fredapi import Fred
fred = Fred(api_key_file='/path/to/fred_key.txt')
```

If no key is found, `Fred()` raises a clear error pointing to the signup page.

## Quick Start

```python
from fredapi import Fred

fred = Fred(api_key=os.environ['FRED_API_KEY'])

# Search for a series
results = fred.search('gross domestic product')
print(results[['title', 'frequency', 'units']].head())

# Fetch a time series
gdp = fred.get_series('GDP')
print(gdp.tail(10))

# Get series info
info = fred.get_series_info('GDP')
print(info['title'], info['units'])
```

## All Methods

### Search Methods

#### `fred.search(text, limit=1000, order_by=None, sort_order=None, filter=None)`

Full-text search for series. Returns a DataFrame.

```python
# Basic search
df = fred.search('unemployment rate')
print(df[['title', 'id', 'units']].head(10))

# Filter by frequency
df = fred.search('CPI', filter=('frequency', 'Monthly'))

# Filter by units (e.g., Percent)
df = fred.search('interest rate', filter=('units', 'Percent'))

# Order by popularity (most downloaded)
df = fred.search('gdp', order_by='popularity', sort_order='desc')

# Limit results
df = fred.search('real gdp', limit=5)
```

#### `fred.search_by_release(release_id, limit=0, ...)`

Search series by FRED release ID (e.g., 151 = "Gross Domestic Product").

```python
# GDP release
df = fred.search_by_release(151)
```

#### `fred.search_by_category(category_id, limit=0, ...)`

Search series within a FRED category.

```python
# Category 32145 = "Production & Business Activity"
df = fred.search_by_category(32145)
```

---

### Data Fetch Methods

#### `fred.get_series(series_id, observation_start=None, observation_end=None, **kwargs)`

Get latest data (alias: `get_series_latest_release`). Returns a pandas Series.

```python
# Full series
data = fred.get_series('SP500')
print(data.tail(5))

# Date range
data = fred.get_series('GDP', observation_start='2020-01-01', observation_end='2024-12-31')

# Specific FRED API kwargs
data = fred.get_series('CPIAUCSL', units='pc1')  # percent change
```

#### `fred.get_series_info(series_id)`

Get metadata about a series (title, frequency, units, notes, etc.). Returns a pandas Series.

```python
info = fred.get_series_info('CPIAUCSL')
print(info['title'])    # "Consumer Price Index for All Urban Consumers"
print(info['units'])    # "Index 1982-84=100"
print(info['frequency'])# "Monthly"
print(info['notes'])    # Description notes
```

#### `fred.get_series_first_release(series_id)`

Get **first-release data only**, ignoring all subsequent revisions. Essential for backtesting.

```python
# GDP first release vs later revisions
gdp_first = fred.get_series_first_release('GDP')
gdp_latest = fred.get_series_latest_release('GDP')

# Compare: first release is usually different from revised values
print("Latest:", gdp_latest.iloc[-1])
print("First: ", gdp_first.iloc[-1])
```

#### `fred.get_series_as_of_date(series_id, as_of_date)`

Get data **as it was known on a specific historical date** (revisions after that date are excluded).

```python
# What did analysts think GDP was on Jan 30, 2014?
data = fred.get_series_as_of_date('GDP', '1/30/2014')
```

#### `fred.get_series_all_releases(series_id, realtime_start=None, realtime_end=None)`

Get **full revision history** from ALFRED. Returns a DataFrame with columns: `date`, `realtime_start`, `value`.

```python
# Every revision of GDP across all time
df = fred.get_series_all_releases('GDP')
print(df.head(10))
#     realtime_start   date       value
# 0   2014-01-30     2013-10-01  17102.5  (first release)
# 1   2014-02-28     2013-10-01  17080.7  (first revision)
# 2   2014-03-27     2013-10-01  17089.6  (second revision)
```

#### `fred.get_series_vintage_dates(series_id)`

List all dates when a series was revised or had new data released.

```python
dates = fred.get_series_vintage_dates('GDP')
print(dates[-5:])  # Last 5 vintage dates
```

---

## Common Use Cases

### 1. Get current economic indicators

```python
indicators = {
    'SP500':    fred.get_series('SP500'),
    'GDP':      fred.get_series('GDP'),
    'CPI':      fred.get_series('CPIAUCSL'),
    'UNEMP':    fred.get_series('UNRATE'),
    'INTEREST': fred.get_series('DFF'),  # Fed Funds Rate
}

for name, data in indicators.items():
    print(f"{name}: {data.iloc[-1]:.2f} ({data.index[-1].strftime('%Y-%m')})")
```

### 2. Compare first release vs final data (revision analysis)

```python
series_id = 'GDPPOT'  # Real Potential GDP

first = fred.get_series_first_release(series_id)
latest = fred.get_series_latest_release(series_id)

# How much does initial estimate differ from final?
diff = (latest - first).dropna()
print(f"Average revision: {diff.mean():.1f}")
print(f"Max revision:      {diff.max():.1f}")
```

### 3. Historical data for a specific period

```python
# US Recession analysis
gdp = fred.get_series('GDPC1', observation_start='2000-01-01')
unemp = fred.get_series('UNRATE', observation_start='2000-01-01')

# Find recession periods
recessions = fred.get_series('JHDUSRGDPBR', observation_start='2000-01-01')
```

### 4. Search for related series

```python
# Find all interest rate series
rates = fred.search('federal funds rate')
print(rates['title'].head(10))

# Find real GDP series
rgdp = fred.search('real gross domestic product')
print(rgdp[['title', 'id']].head())
```

### 5. Get data for chart

```python
# Simple line chart data
data = fred.get_series('SP500', observation_start='2020-01-01')
# data.index = dates, data.values = prices
# Ready for matplotlib or any charting library
```

---

## Popular Series IDs

| Series ID | Description |
|-----------|-------------|
| `GDP` | Gross Domestic Product (Quarterly, Billions) |
| `GDPC1` | Real GDP (Quarterly, Chained 2017$) |
| `CPIAUCSL` | Consumer Price Index (Monthly) |
| `UNRATE` | Unemployment Rate (Monthly, %) |
| `FEDFUNDS` | Federal Funds Rate (Monthly, %) |
| `DFF` | Effective Federal Funds Rate (Daily, %) |
| `SP500` | S&P 500 (Daily) |
| `MORTGAGE30US` | 30-Year Fixed Rate Mortgage (Weekly, %) |
| `PCECTPI` | PCE Price Index (Monthly) |
| `GDPPOT` | Real Potential GDP (Quarterly) |
| `INDPRO` | Industrial Production (Monthly, Index) |
| `PAYEMS` | Total Nonfarm Payrolls (Monthly, Thousands) |
| `ICSA` | Initial Claims for Unemployment (Weekly) |
| `DEXCHUS` | China/US Exchange Rate (Daily) |
| `DEXUSEU` | US/Euro Exchange Rate (Daily) |

---

## Data Revision: Why It Matters

FRED contains two databases:
- **FRED**: latest revised data
- **ALFRED**: archival data showing what was known at each point in history

```python
# Economic data is revised multiple times
# GDP for Q4 2023 was first reported: ~2.0% growth
# Revised a month later: ~3.2% growth
# Final: ~3.3% growth

# For backtesting or historical accuracy, use:
first_release = fred.get_series_first_release('GDP')  # Ignore revisions
all_releases  = fred.get_series_all_releases('GDP')  # See all revisions
as_of_date    = fred.get_series_as_of_date('GDP', '3/1/2024')  # What was known then
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ValueError: You need to set a valid API key` | Set `FRED_API_KEY` env var or pass `api_key=` parameter |
| `ValueError: No data exists for series id` | Check series ID at https://fred.stlouisfed.org/series/{id} |
| Slow responses | Use `observation_start`/`observation_end` to limit date range |
| Rate limit | FRED allows ~120 requests/sec. Add delays in loops |
| Proxy/network issues | Pass `proxies={'http': ..., 'https': ...}` to `Fred()` |

## Reference

- FRED API docs: https://fred.stlouisfed.org/docs/api/fred/
- fredapi GitHub: https://github.com/mortada/fredapi
- FRED website: https://fred.stlouisfed.org/
- Free API key signup: https://fred.stlouisfed.org/docs/api/api_key.html
