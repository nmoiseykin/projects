# Quick Start - ForexFactory USD Calendar Parser

## What It Does

Automatically fetches and parses **today's economic calendar** from ForexFactory.com, filtering for **USD events only**, and saves the results as JSON.

## Run It Now

```bash
cd /home/nmoiseykin/webpage-parser
./run_parser.sh
```

That's it! The script will:
1. 🌐 Connect to forexfactory.com (bypassing Cloudflare protection)
2. 📊 Parse the calendar for today's week
3. 💵 Filter for USD currency only
4. 💾 **Save to `examples/forex_calendar_usd.json`**
5. 📄 Display the results

## Output Location

The JSON file is saved to:
```
/home/nmoiseykin/webpage-parser/examples/forex_calendar_usd.json
```

## Sample Output

```json
{
  "source": "https://www.forexfactory.com/calendar",
  "timestamp": "2025-10-28T23:55:12.045402",
  "currency_filter": "USD",
  "event_count": 17,
  "events": [
    {
      "date": "WedOct 29",
      "time": "2:00pm",
      "currency": "USD",
      "impact": "High",
      "event": "Federal Funds Rate",
      "actual": "",
      "forecast": "4.00%",
      "previous": "4.25%"
    },
    ...
  ]
}
```

## Each Event Contains

- **date**: Event date (e.g., "WedOct 29")
- **time**: Event time (e.g., "2:00pm")
- **currency**: Always "USD" (filtered)
- **impact**: "Low", "Medium", or "High"
- **event**: Event name (e.g., "Federal Funds Rate")
- **actual**: Actual value (if released)
- **forecast**: Forecasted value
- **previous**: Previous period's value

## Alternative Run Methods

### Method 1: Direct Python
```bash
cd /home/nmoiseykin/webpage-parser/examples
source ../venv/bin/activate
python3 parse_forexfactory_final.py
```

### Method 2: Custom Output Location
```bash
cd /home/nmoiseykin/webpage-parser/examples
source ../venv/bin/activate
python3 parse_forexfactory_final.py --output /path/to/my_calendar.json
```

### Method 3: Save HTML for Debugging
```bash
python3 parse_forexfactory_final.py --save-html debug.html
```

## Troubleshooting

**Q: Where's the JSON file?**
A: Check `examples/forex_calendar_usd.json`

**Q: How often should I run it?**
A: Run it whenever you need the latest calendar data. The calendar typically shows the current week's events.

**Q: What if it shows 0 events?**
A: There may not be any USD events scheduled for the current timeframe, or the page structure changed.

**Q: Can I change the currency filter?**
A: Yes, edit `parse_forexfactory_final.py` and change the line `if currency != 'USD':` to your desired currency code (e.g., EUR, GBP, JPY).

## Scheduling (Optional)

To run automatically every day:

```bash
# Add to crontab
crontab -e

# Add this line to run daily at 6 AM
0 6 * * * cd /home/nmoiseykin/webpage-parser && ./run_parser.sh >> /tmp/forex_parser.log 2>&1
```

