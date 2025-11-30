"""
Advanced script to parse forex economic calendar from ForexFactory.
This version can work with saved HTML or attempt direct parsing.
"""

import sys
import json
from datetime import datetime
import argparse
sys.path.insert(0, '..')

from webpage_parser import WebpageParser


def parse_calendar_html(html_content: str, base_url: str = None) -> list:
    """
    Parse calendar HTML content and extract USD events.
    
    Args:
        html_content: HTML string content
        base_url: Base URL for context
        
    Returns:
        List of calendar events
    """
    parser = WebpageParser()
    result = parser.parse_html(html_content, base_url=base_url)
    
    events = []
    
    if not result.soup:
        return events
    
    # ForexFactory specific parsing
    # The calendar table has class "calendar__table"
    calendar_table = result.soup.find('table', class_='calendar__table')
    
    if not calendar_table:
        print("Calendar table not found, trying alternative selectors...", file=sys.stderr)
        # Try finding any table
        calendar_table = result.soup.find('table')
    
    if calendar_table:
        rows = calendar_table.find_all('tr', class_='calendar__row')
        
        current_date = None
        
        for row in rows:
            # Check if this is a date row
            date_cell = row.find('td', class_='calendar__date')
            if date_cell:
                date_span = date_cell.find('span')
                if date_span:
                    current_date = date_span.get_text(strip=True)
            
            # Extract time
            time_cell = row.find('td', class_='calendar__time')
            time_val = time_cell.get_text(strip=True) if time_cell else ''
            
            # Extract currency
            currency_cell = row.find('td', class_='calendar__currency')
            currency = currency_cell.get_text(strip=True) if currency_cell else ''
            
            # Only process USD events
            if currency != 'USD':
                continue
            
            # Extract impact
            impact_cell = row.find('td', class_='calendar__impact')
            impact_level = ''
            if impact_cell:
                impact_span = impact_cell.find('span')
                if impact_span:
                    classes = impact_span.get('class', [])
                    if 'icon--ff-impact-red' in classes:
                        impact_level = 'High'
                    elif 'icon--ff-impact-ora' in classes or 'icon--ff-impact-orange' in classes:
                        impact_level = 'Medium'
                    elif 'icon--ff-impact-yel' in classes or 'icon--ff-impact-yellow' in classes:
                        impact_level = 'Low'
            
            # Extract event name
            event_cell = row.find('td', class_='calendar__event')
            event_name = event_cell.get_text(strip=True) if event_cell else ''
            
            # Extract actual value
            actual_cell = row.find('td', class_='calendar__actual')
            actual = actual_cell.get_text(strip=True) if actual_cell else ''
            
            # Extract forecast value
            forecast_cell = row.find('td', class_='calendar__forecast')
            forecast = forecast_cell.get_text(strip=True) if forecast_cell else ''
            
            # Extract previous value
            previous_cell = row.find('td', class_='calendar__previous')
            previous = previous_cell.get_text(strip=True) if previous_cell else ''
            
            # Only add if we have an event name
            if event_name:
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
    
    return events


def main():
    parser = argparse.ArgumentParser(description='Parse ForexFactory economic calendar')
    parser.add_argument('--html-file', help='Path to saved HTML file to parse')
    parser.add_argument('--url', default='https://www.forexfactory.com/calendar', 
                       help='URL to parse (default: ForexFactory calendar)')
    parser.add_argument('--output', help='Output JSON file path')
    
    args = parser.parse_args()
    
    events = []
    
    try:
        if args.html_file:
            # Parse from saved HTML file
            print(f"Reading HTML from file: {args.html_file}", file=sys.stderr)
            with open(args.html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            events = parse_calendar_html(html_content, base_url=args.url)
        else:
            # Try to fetch from URL
            print(f"Attempting to fetch from: {args.url}", file=sys.stderr)
            print("Note: ForexFactory may block automated requests.", file=sys.stderr)
            print("If this fails, save the page HTML and use --html-file option.", file=sys.stderr)
            
            web_parser = WebpageParser(
                timeout=30,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            web_parser.session.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            result = web_parser.parse(args.url)
            events = parse_calendar_html(result.soup.prettify(), base_url=args.url)
        
        # Create output
        output = {
            'source': args.url,
            'timestamp': datetime.now().isoformat(),
            'currency_filter': 'USD',
            'event_count': len(events),
            'events': events
        }
        
        json_output = json.dumps(output, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"Output saved to: {args.output}", file=sys.stderr)
        else:
            print(json_output)
        
    except FileNotFoundError:
        print(f"Error: HTML file not found: {args.html_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

