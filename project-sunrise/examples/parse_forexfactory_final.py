"""
Parse ForexFactory economic calendar using cloudscraper to bypass Cloudflare.
"""

import sys
import json
from datetime import datetime
import argparse
sys.path.insert(0, '..')

import cloudscraper
from webpage_parser import WebpageParser


def fetch_with_cloudscraper(url: str) -> str:
    """
    Fetch HTML using cloudscraper to bypass Cloudflare.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content as string
    """
    print(f"Fetching {url} with cloudscraper...", file=sys.stderr)
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    response = scraper.get(url)
    response.raise_for_status()
    
    print(f"Successfully fetched {len(response.text)} bytes", file=sys.stderr)
    return response.text


def get_today_date_string():
    """Get today's date in ForexFactory format (e.g., 'TueOct 28')."""
    from datetime import datetime
    now = datetime.now()
    day_name = now.strftime('%a')  # Mon, Tue, Wed, etc.
    month = now.strftime('%b')     # Jan, Feb, Mar, etc.
    day = now.strftime('%d').lstrip('0')  # Remove leading zero
    return f"{day_name}{month} {day}"


def parse_calendar_html(html_content: str, base_url: str = None, filter_today: bool = False) -> list:
    """
    Parse calendar HTML content and extract USD events.
    
    Args:
        html_content: HTML string content
        base_url: Base URL for context
        filter_today: If True, only return today's events
        
    Returns:
        List of calendar events
    """
    parser = WebpageParser()
    result = parser.parse_html(html_content, base_url=base_url)
    
    events = []
    today_str = get_today_date_string() if filter_today else None
    
    if not result.soup:
        return events
    
    # ForexFactory specific parsing
    calendar_table = result.soup.find('table', class_='calendar__table')
    
    if not calendar_table:
        print("Warning: Calendar table not found in HTML", file=sys.stderr)
        # Try alternate selector
        calendar_table = result.soup.find('table', {'class': lambda x: x and 'calendar' in str(x).lower()})
        
    if not calendar_table:
        print("Error: Could not find calendar table", file=sys.stderr)
        return events
    
    rows = calendar_table.find_all('tr', class_='calendar__row')
    if not rows:
        rows = calendar_table.find_all('tr', {'class': lambda x: x and 'calendar' in str(x).lower()})
    
    print(f"Found {len(rows)} calendar rows", file=sys.stderr)
    
    current_date = None
    
    for row in rows:
        try:
            # Check if this is a date row
            date_cell = row.find('td', class_='calendar__date')
            if not date_cell:
                date_cell = row.find('td', {'class': lambda x: x and 'date' in str(x).lower()})
            
            if date_cell:
                date_span = date_cell.find('span')
                if date_span and date_span.get_text(strip=True):
                    current_date = date_span.get_text(strip=True)
            
            # Extract time
            time_cell = row.find('td', class_='calendar__time')
            if not time_cell:
                time_cell = row.find('td', {'class': lambda x: x and 'time' in str(x).lower()})
            time_val = time_cell.get_text(strip=True) if time_cell else ''
            
            # Extract currency
            currency_cell = row.find('td', class_='calendar__currency')
            if not currency_cell:
                currency_cell = row.find('td', {'class': lambda x: x and 'currency' in str(x).lower()})
            currency = currency_cell.get_text(strip=True) if currency_cell else ''
            
            # Only process USD events
            if currency != 'USD':
                continue
            
            # Extract impact
            impact_cell = row.find('td', class_='calendar__impact')
            if not impact_cell:
                impact_cell = row.find('td', {'class': lambda x: x and 'impact' in str(x).lower()})
            
            impact_level = ''
            if impact_cell:
                impact_span = impact_cell.find('span')
                if impact_span:
                    classes = impact_span.get('class', [])
                    classes_str = ' '.join(classes).lower()
                    if 'red' in classes_str or 'high' in classes_str:
                        impact_level = 'High'
                    elif 'ora' in classes_str or 'orange' in classes_str or 'medium' in classes_str:
                        impact_level = 'Medium'
                    elif 'yel' in classes_str or 'yellow' in classes_str or 'low' in classes_str:
                        impact_level = 'Low'
            
            # Extract event name
            event_cell = row.find('td', class_='calendar__event')
            if not event_cell:
                event_cell = row.find('td', {'class': lambda x: x and 'event' in str(x).lower()})
            event_name = event_cell.get_text(strip=True) if event_cell else ''
            
            # Extract actual value
            actual_cell = row.find('td', class_='calendar__actual')
            if not actual_cell:
                actual_cell = row.find('td', {'class': lambda x: x and 'actual' in str(x).lower()})
            actual = actual_cell.get_text(strip=True) if actual_cell else ''
            
            # Extract forecast value
            forecast_cell = row.find('td', class_='calendar__forecast')
            if not forecast_cell:
                forecast_cell = row.find('td', {'class': lambda x: x and 'forecast' in str(x).lower()})
            forecast = forecast_cell.get_text(strip=True) if forecast_cell else ''
            
            # Extract previous value
            previous_cell = row.find('td', class_='calendar__previous')
            if not previous_cell:
                previous_cell = row.find('td', {'class': lambda x: x and 'previous' in str(x).lower()})
            previous = previous_cell.get_text(strip=True) if previous_cell else ''
            
            # Only add if we have an event name
            if event_name:
                # If filtering for today, check if date matches
                if filter_today and today_str:
                    if current_date != today_str:
                        continue
                
                event = {
                    'date': current_date or '',
                    'time': time_val,
                    'currency': currency,
                    'impact': impact_level,
                    'event': event_name,
                    'actual': actual,
                    'forecast': forecast,
                    'previous': previous
                }
                events.append(event)
        except Exception as e:
            print(f"Error parsing row: {e}", file=sys.stderr)
            continue
    
    return events


def main():
    parser = argparse.ArgumentParser(description='Parse ForexFactory economic calendar')
    parser.add_argument('--url', default='https://www.forexfactory.com/calendar', 
                       help='URL to parse (default: ForexFactory calendar)')
    parser.add_argument('--output', default='forex_calendar_usd.json',
                       help='Output JSON file path (default: forex_calendar_usd.json)')
    parser.add_argument('--save-html', help='Save fetched HTML to file')
    parser.add_argument('--html-file', help='Parse from saved HTML file instead of fetching')
    parser.add_argument('--today-only', action='store_true',
                       help='Filter events for today only')
    
    args = parser.parse_args()
    
    try:
        if args.html_file:
            # Load from file
            print(f"Reading HTML from {args.html_file}...", file=sys.stderr)
            with open(args.html_file, 'r', encoding='utf-8') as f:
                html = f.read()
        else:
            # Fetch with cloudscraper
            html = fetch_with_cloudscraper(args.url)
            
            # Optionally save HTML
            if args.save_html:
                with open(args.save_html, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"HTML saved to: {args.save_html}", file=sys.stderr)
        
        # Parse the calendar
        if args.today_only:
            print("Parsing calendar (filtering for TODAY only)...", file=sys.stderr)
        else:
            print("Parsing calendar...", file=sys.stderr)
        events = parse_calendar_html(html, base_url=args.url, filter_today=args.today_only)
        
        # Create output
        output = {
            'source': args.url,
            'timestamp': datetime.now().isoformat(),
            'currency_filter': 'USD',
            'event_count': len(events),
            'events': events
        }
        
        json_output = json.dumps(output, indent=2, ensure_ascii=False)
        
        # Always save to file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        print(f"\n✅ SUCCESS!", file=sys.stderr)
        print(f"📄 Output saved to: {args.output}", file=sys.stderr)
        print(f"📊 Found {len(events)} USD events for today's calendar", file=sys.stderr)
        print(f"🕐 Timestamp: {output['timestamp']}", file=sys.stderr)
        
        # Also print to stdout for convenience
        print("\n" + json_output)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

