"""
Parse ForexFactory economic calendar using Selenium to bypass Cloudflare protection.
"""

import sys
import json
import time
from datetime import datetime
import argparse
sys.path.insert(0, '..')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from webpage_parser import WebpageParser


def get_calendar_html_with_selenium(url: str, headless: bool = True) -> str:
    """
    Fetch calendar HTML using Selenium to bypass Cloudflare.
    
    Args:
        url: URL to fetch
        headless: Whether to run browser in headless mode
        
    Returns:
        HTML content as string
    """
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    print("Starting browser...", file=sys.stderr)
    
    try:
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to the page
        print(f"Navigating to {url}...", file=sys.stderr)
        driver.get(url)
        
        # Wait for Cloudflare challenge to complete and calendar to load
        print("Waiting for page to load (this may take 10-15 seconds)...", file=sys.stderr)
        time.sleep(12)  # Give time for Cloudflare challenge
        
        # Try to wait for calendar table to appear
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "calendar__table"))
            )
            print("Calendar table found!", file=sys.stderr)
        except:
            print("Calendar table not found, but continuing...", file=sys.stderr)
        
        # Get the page source
        html = driver.page_source
        
        return html
        
    finally:
        if 'driver' in locals():
            driver.quit()
            print("Browser closed.", file=sys.stderr)


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
    calendar_table = result.soup.find('table', class_='calendar__table')
    
    if not calendar_table:
        print("Warning: Calendar table not found in HTML", file=sys.stderr)
        return events
    
    rows = calendar_table.find_all('tr', class_='calendar__row')
    print(f"Found {len(rows)} calendar rows", file=sys.stderr)
    
    current_date = None
    
    for row in rows:
        # Check if this is a date row
        date_cell = row.find('td', class_='calendar__date')
        if date_cell:
            date_span = date_cell.find('span')
            if date_span and date_span.get_text(strip=True):
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
                else:
                    # Check for other impact indicators
                    for cls in classes:
                        if 'red' in cls.lower():
                            impact_level = 'High'
                        elif 'ora' in cls.lower() or 'orange' in cls.lower():
                            impact_level = 'Medium'
                        elif 'yel' in cls.lower() or 'yellow' in cls.lower():
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
    parser = argparse.ArgumentParser(description='Parse ForexFactory economic calendar using Selenium')
    parser.add_argument('--url', default='https://www.forexfactory.com/calendar', 
                       help='URL to parse (default: ForexFactory calendar)')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--save-html', help='Save fetched HTML to file')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode')
    
    args = parser.parse_args()
    
    try:
        # Fetch HTML using Selenium
        html = get_calendar_html_with_selenium(args.url, headless=not args.no_headless)
        
        # Optionally save HTML
        if args.save_html:
            with open(args.save_html, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML saved to: {args.save_html}", file=sys.stderr)
        
        # Parse the calendar
        print("Parsing calendar...", file=sys.stderr)
        events = parse_calendar_html(html, base_url=args.url)
        
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
            print(f"Found {len(events)} USD events", file=sys.stderr)
        else:
            print(json_output)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

