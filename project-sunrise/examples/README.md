# Webpage Parser Examples

## ForexFactory Calendar Parser

Parse economic calendar data from ForexFactory.com and extract USD events in JSON format.

### Requirements

```bash
pip install cloudscraper beautifulsoup4 lxml requests
```

### Usage

#### Basic Usage - Fetch and Parse

```bash
python parse_forexfactory_final.py
```

This will:
1. Fetch the ForexFactory calendar (bypassing Cloudflare protection)
2. Parse all calendar events
3. Filter for USD currency only
4. Output JSON to stdout

#### Save Output to File

```bash
python parse_forexfactory_final.py --output forex_calendar.json
```

#### Save HTML for Later Use

```bash
python parse_forexfactory_final.py --save-html calendar.html
```

#### Parse from Saved HTML

```bash
python parse_forexfactory_final.py --html-file calendar.html
```

### Output Format

```json
{
  "source": "https://www.forexfactory.com/calendar",
  "timestamp": "2025-10-28T23:50:26.384877",
  "currency_filter": "USD",
  "event_count": 17,
  "events": [
    {
      "date": "TueOct 28",
      "time": "10:00am",
      "currency": "USD",
      "impact": "Medium",
      "event": "CB Consumer Confidence",
      "actual": "94.6",
      "forecast": "93.4",
      "previous": "95.6"
    },
    ...
  ]
}
```

### Event Fields

- **date**: Date of the event (e.g., "TueOct 28")
- **time**: Time of the event (e.g., "10:00am")
- **currency**: Currency code (always "USD" in this filtered output)
- **impact**: Impact level - "Low", "Medium", or "High"
- **event**: Name of the economic event
- **actual**: Actual released value (if available)
- **forecast**: Forecasted value (if available)
- **previous**: Previous period's value (if available)

### Command-Line Options

```bash
python parse_forexfactory_final.py --help
```

Options:
- `--url URL`: Custom calendar URL (default: ForexFactory calendar)
- `--output FILE`: Save JSON output to file
- `--save-html FILE`: Save fetched HTML to file
- `--html-file FILE`: Parse from saved HTML file

### Example: Full Workflow

```bash
# Fetch and save everything
python parse_forexfactory_final.py \
  --save-html calendar.html \
  --output calendar.json

# Later, parse from saved HTML
python parse_forexfactory_final.py \
  --html-file calendar.html \
  --output updated_calendar.json
```

## How It Works

The parser uses:
1. **cloudscraper** - Bypasses Cloudflare anti-bot protection
2. **BeautifulSoup** - Parses HTML and extracts data
3. **lxml** - Fast HTML parsing backend

The script specifically targets ForexFactory's calendar table structure:
- Identifies calendar rows with class `calendar__row`
- Extracts date, time, currency, impact, event name
- Extracts actual, forecast, and previous values
- Filters for USD currency only
- Outputs in clean JSON format

## Troubleshooting

### "Could not find calendar table"

The page structure may have changed. Save the HTML with `--save-html` and inspect it to verify the calendar structure.

### Connection Errors

ForexFactory has strong anti-bot protection. The cloudscraper should handle this, but if you encounter persistent errors:
- Try again after a short delay
- Check your internet connection
- Verify the URL is correct

### Empty Results

If events are empty but fetching succeeded:
- The calendar may not have USD events for the current week
- Save HTML with `--save-html` to inspect what was fetched
- The page structure may have changed (rare)

