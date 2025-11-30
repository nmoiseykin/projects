"""
Example script to parse forex economic calendar and extract USD events.
"""

import sys
import json
from datetime import datetime
sys.path.insert(0, '..')

from webpage_parser import WebpageParser


def parse_forex_calendar(url: str) -> list:
    """
    Parse forex economic calendar and extract USD events.
    
    Args:
        url: URL of the forex calendar page
        
    Returns:
        List of calendar events in dictionary format
    """
    # Use more realistic browser headers
    parser = WebpageParser(
        timeout=30,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Add additional headers to look more like a real browser
    parser.session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    })
    
    try:
        print(f"Fetching calendar from: {url}")
        result = parser.parse(url)
        
        # Extract calendar events
        events = []
        
        # Look for table rows in the calendar
        if result.soup:
            # Try different selectors for calendar tables
            calendar_rows = result.soup.find_all('tr', class_=lambda x: x and 'calendar' in x.lower()) or \
                           result.soup.find_all('tr', class_=lambda x: x and 'event' in x.lower()) or \
                           result.soup.select('table.calendar tr') or \
                           result.soup.select('tbody tr')
            
            current_date = None
            
            for row in calendar_rows:
                # Try to extract date
                date_cell = row.find('td', class_=lambda x: x and 'date' in str(x).lower())
                if date_cell and date_cell.get_text(strip=True):
                    current_date = date_cell.get_text(strip=True)
                
                # Extract currency
                currency_cell = row.find('td', class_=lambda x: x and 'currency' in str(x).lower())
                if not currency_cell:
                    currency_cell = row.find('span', class_=lambda x: x and 'currency' in str(x).lower())
                
                currency = currency_cell.get_text(strip=True) if currency_cell else None
                
                # Only process USD events
                if currency != 'USD':
                    continue
                
                # Extract time
                time_cell = row.find('td', class_=lambda x: x and 'time' in str(x).lower())
                time_val = time_cell.get_text(strip=True) if time_cell else ''
                
                # Extract impact
                impact_cell = row.find('td', class_=lambda x: x and 'impact' in str(x).lower())
                impact = impact_cell.get('title', '') if impact_cell else ''
                if not impact and impact_cell:
                    # Check for impact indicators (icons/spans)
                    impact_span = impact_cell.find('span')
                    if impact_span:
                        impact = impact_span.get('title', impact_span.get('class', [''])[0])
                
                # Extract event name/detail
                event_cell = row.find('td', class_=lambda x: x and ('event' in str(x).lower() or 'detail' in str(x).lower()))
                if not event_cell:
                    event_cell = row.find('span', class_=lambda x: x and 'event' in str(x).lower())
                event_name = event_cell.get_text(strip=True) if event_cell else ''
                
                # Extract actual value
                actual_cell = row.find('td', class_=lambda x: x and 'actual' in str(x).lower())
                actual = actual_cell.get_text(strip=True) if actual_cell else ''
                
                # Extract forecast value
                forecast_cell = row.find('td', class_=lambda x: x and 'forecast' in str(x).lower())
                forecast = forecast_cell.get_text(strip=True) if forecast_cell else ''
                
                # Extract previous value
                previous_cell = row.find('td', class_=lambda x: x and 'previous' in str(x).lower())
                previous = previous_cell.get_text(strip=True) if previous_cell else ''
                
                # Only add if we have an event name
                if event_name and currency == 'USD':
                    event = {
                        'date': current_date or '',
                        'time': time_val,
                        'currency': currency,
                        'impact': impact,
                        'event': event_name,
                        'actual': actual,
                        'forecast': forecast,
                        'previous': previous
                    }
                    events.append(event)
        
        return events
        
    except Exception as e:
        print(f"Error parsing calendar: {str(e)}", file=sys.stderr)
        raise


def main():
    # URL of the forex calendar
    url = "https://www.forexfactory.com/calendar"
    
    try:
        events = parse_forex_calendar(url)
        
        # Output as JSON
        output = {
            'source': url,
            'timestamp': datetime.now().isoformat(),
            'currency_filter': 'USD',
            'event_count': len(events),
            'events': events
        }
        
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Failed to parse calendar: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

