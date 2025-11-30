"""
AWS Lambda handler for ForexFactory calendar parser with AI analysis and email delivery.

This function consolidates:
1. Fetching and parsing ForexFactory calendar (USD events only, today only)
2. Getting OpenAI Assistant analysis
3. Generating and sending HTML email

Environment Variables Required:
- TO_EMAIL: Recipient email address
- SMTP_USER: Gmail username
- SMTP_PASSWORD: Gmail App Password
- OPENAI_API_KEY: OpenAI API key
- OPENAI_ASSISTANT_ID: OpenAI Assistant ID
"""

import os
import sys
import json
import time
import smtplib
import socket
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

import requests
import cloudscraper
from bs4 import BeautifulSoup
import httpx
from openai import OpenAI
from market_data import build_market_snapshot, generate_market_table_html


# ============================================================================
# CONFIGURATION
# ============================================================================

FOREXFACTORY_URL = 'https://www.forexfactory.com/calendar'

# AI Questions embedded in code (can be modified here)
AI_QUESTIONS = [
    "Based on today's USD economic calendar events, provide a brief analysis of the potential market impact and trading opportunities. Focus on high-impact events."
]

MARKET_TIMEZONE = os.environ.get('MARKET_TIMEZONE', 'America/New_York')
MARKET_LOOKBACK_HOURS = int(os.environ.get('MARKET_LOOKBACK_HOURS', '48'))
MARKET_SNAPSHOT_ENABLED = os.environ.get('MARKET_SNAPSHOT_ENABLED', 'true').lower() in {'1', 'true', 'yes', 'on'}
OPENAI_CHAT_MODEL = os.environ.get('OPENAI_CHAT_MODEL', 'gpt-4o-mini')
OPENAI_HTTP_DEBUG = os.environ.get('OPENAI_HTTP_DEBUG', 'false').lower() in {'1', 'true', 'yes', 'on'}


# ============================================================================
# NETWORK DIAGNOSTICS
# ============================================================================


def log_network_diagnostics(host: str = "api.openai.com", port: int = 443, test_url: str = "https://api.openai.com/v1/models") -> bool:
    """Log DNS and TCP connectivity diagnostics for the OpenAI endpoint."""
    print("\n[NETWORK] Starting diagnostics for OpenAI connectivity...")
    print(f"[NETWORK] Target host: {host}:{port}")

    # DNS lookup
    try:
        start = time.time()
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        elapsed = time.time() - start
        addresses = sorted({info[4][0] for info in infos})
        print(f"[NETWORK] DNS resolved in {elapsed:.2f}s -> {addresses}")
    except Exception as dns_error:
        print(f"[NETWORK] DNS lookup failed: {dns_error}")
        return False


    # Raw TCP check
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=5) as conn:
            elapsed = time.time() - start
            print(f"[NETWORK] TCP connection established in {elapsed:.2f}s")
    except Exception as tcp_error:
        print(f"[NETWORK] TCP connection failed: {tcp_error}")
        return False

    # Simple HTTPS GET (expecting 401 due to missing auth)
    try:
        start = time.time()
        resp = requests.get(test_url, timeout=5)
        elapsed = time.time() - start
        print(f"[NETWORK] HTTPS GET {test_url} -> status {resp.status_code} in {elapsed:.2f}s")
    except Exception as http_error:
        print(f"[NETWORK] HTTPS GET failed: {http_error}")
        return False

    print("[NETWORK] Diagnostics complete.\n")
    return True


def configure_http_debug():
    if OPENAI_HTTP_DEBUG:
        httpx_logger = logging.getLogger("httpx")
        if not httpx_logger.handlers:
            httpx_logger.addHandler(logging.StreamHandler(sys.stdout))
        httpx_logger.setLevel(logging.DEBUG)
        print("[NETWORK] HTTPX debug logging enabled.")


# ============================================================================
# STEP 1: FETCH AND PARSE CALENDAR
# ============================================================================

def get_today_date_string():
    """Get today's date in ForexFactory format (e.g., 'WedOct 29')."""
    now = datetime.now()
    day_name = now.strftime('%a')  # Mon, Tue, Wed, etc.
    month = now.strftime('%b')     # Jan, Feb, Mar, etc.
    day = now.strftime('%d').lstrip('0')  # Remove leading zero
    return f"{day_name}{month} {day}"


def fetch_calendar_html(url):
    """Fetch ForexFactory calendar HTML using cloudscraper."""
    print(f"Fetching {url} with cloudscraper...")
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        response = scraper.get(url, timeout=30)
        response.raise_for_status()
        
        print(f"Successfully fetched {len(response.text)} bytes")
        return response.text
        
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        # Fallback to regular requests with retry
        import requests
        print("Trying fallback with requests library...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Fallback successful: {len(response.text)} bytes")
        return response.text


def parse_calendar_html(html_content, filter_today=True):
    """Parse calendar HTML and extract USD events."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    events = []
    today_str = get_today_date_string() if filter_today else None
    
    # Find calendar table
    calendar_table = soup.find('table', class_='calendar__table')
    
    if not calendar_table:
        print("Warning: Calendar table not found, trying alternate selector")
        calendar_table = soup.find('table', {'class': lambda x: x and 'calendar' in str(x).lower()})
    
    if not calendar_table:
        print("Error: Could not find calendar table")
        return events
    
    rows = calendar_table.find_all('tr', class_='calendar__row')
    if not rows:
        rows = calendar_table.find_all('tr', {'class': lambda x: x and 'calendar' in str(x).lower()})
    
    print(f"Found {len(rows)} calendar rows")
    
    current_date = None
    
    for row in rows:
        try:
            # Check if this is a date row
            date_cell = row.find('td', class_='calendar__date')
            if date_cell:
                date_span = date_cell.find('span')
                if date_span and date_span.get_text(strip=True):
                    current_date = date_span.get_text(strip=True)
            
            # Extract currency
            currency_cell = row.find('td', class_='calendar__currency')
            currency = currency_cell.get_text(strip=True) if currency_cell else ''
            
            # Only process USD events
            if currency != 'USD':
                continue
            
            # If filtering for today, check if date matches
            if filter_today and today_str and current_date != today_str:
                continue
            
            # Extract time
            time_cell = row.find('td', class_='calendar__time')
            time_val = time_cell.get_text(strip=True) if time_cell else ''
            
            # Extract impact
            impact_cell = row.find('td', class_='calendar__impact')
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
                
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue
    
    return events


def fetch_and_parse_calendar():
    """Fetch and parse ForexFactory calendar (today's USD events only)."""
    print("=" * 60)
    print("STEP 1: Fetching and Parsing Calendar")
    print("=" * 60)
    
    try:
        html = fetch_calendar_html(FOREXFACTORY_URL)
        events = parse_calendar_html(html, filter_today=True)
        
        calendar_data = {
            'source': FOREXFACTORY_URL,
            'timestamp': datetime.now().isoformat(),
            'currency_filter': 'USD',
            'event_count': len(events),
            'events': events
        }
        
        print(f"✅ Parsed {len(events)} USD events for today")
        return calendar_data
        
    except Exception as e:
        print(f"❌ Error fetching calendar: {e}")
        raise


def build_calendar_context(calendar_data):
    events = calendar_data.get('events', [])
    if not events:
        return "There are no USD events scheduled for today."

    lines = ["Today's USD economic calendar:"]
    for event in events:
        time_val = event.get('time') or 'TBA'
        impact = event.get('impact') or 'N/A'
        name = event.get('event') or 'Unknown event'
        actual = event.get('actual') or '—'
        forecast = event.get('forecast') or '—'
        previous = event.get('previous') or '—'
        lines.append(
            f"- {time_val} | Impact: {impact} | {name} | "
            f"Actual: {actual} | Forecast: {forecast} | Previous: {previous}"
        )
    return "\n".join(lines)


def get_ai_analysis(calendar_data, api_key):
    """Get AI analysis using a simple chat completion (single-call)."""
    print("=" * 60)
    print("STEP 2: Getting AI Analysis")
    print("=" * 60)

    if not api_key:
        print("⚠️ OpenAI API key not provided; skipping AI analysis.")
        return None

    timeout_config = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

    try:
        client = OpenAI(api_key=api_key, timeout=timeout_config, max_retries=1)
        calendar_context = build_calendar_context(calendar_data)

        responses = []
        for i, question in enumerate(AI_QUESTIONS, 1):
            print(f"\nQuestion {i}/{len(AI_QUESTIONS)}")
            prompt = (
                f"{calendar_context}\n\n"
                f"Question: {question}\n"
                "Provide a concise, professional answer (3-5 sentences)."
            )

            try:
                print(f"Calling OpenAI chat model {OPENAI_CHAT_MODEL} (question {i})...")
                call_start = time.time()
                result = client.chat.completions.create(
                    model=OPENAI_CHAT_MODEL,
                    temperature=0.3,
                    max_tokens=400,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a professional macro strategist who writes short, actionable "
                                "market summaries for traders."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                elapsed = time.time() - call_start
                answer = result.choices[0].message.content.strip()
                print(f"✅ OpenAI response in {elapsed:.2f}s ({len(answer)} chars)")
            except Exception as chat_error:
                print(f"⚠️ Error getting response from OpenAI: {chat_error}")
                answer = "Error: Failed to get response from OpenAI"

            responses.append({"question": question, "response": answer})

        ai_analysis = {
            'timestamp': datetime.now().isoformat(),
            'model': OPENAI_CHAT_MODEL,
            'question_count': len(AI_QUESTIONS),
            'responses': responses,
        }

        print(f"✅ AI analysis complete: {len(responses)} responses")
        return ai_analysis

    except Exception as e:
        print(f"⚠️ Error setting up OpenAI client: {e}")
        print("Continuing without AI analysis...")
        return None


# ============================================================================
# STEP 3: GENERATE AND SEND EMAIL
# ============================================================================

def generate_html_email(calendar_data, ai_analysis=None, market_html=None):
    """Generate beautiful mobile-friendly HTML table with optional market and AI sections."""
    
    events = calendar_data.get('events', [])
    event_count = calendar_data.get('event_count', 0)
    
    # Get unique date for display
    unique_date = events[0].get('date', 'Today') if events else 'Today'
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USD Economic Calendar - {unique_date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 14px;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .stats {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        
        .stat {{
            text-align: center;
            padding: 5px 10px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #1e3c72;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .content {{
            padding: 20px;
        }}
        
        .date-banner {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .date-banner::before {{
            content: "📅";
            margin-right: 10px;
            font-size: 24px;
        }}
        
        .events-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .events-table thead {{
            background: #2a5298;
            color: white;
        }}
        
        .events-table th {{
            padding: 12px 10px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .events-table tbody tr {{
            border-bottom: 1px solid #e0e0e0;
            transition: background 0.2s ease;
        }}
        
        .events-table tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .events-table tbody tr:last-child {{
            border-bottom: none;
        }}
        
        .events-table td {{
            padding: 15px 10px;
            font-size: 14px;
            vertical-align: middle;
        }}
        
        .time-cell {{
            font-weight: 700;
            color: #667eea;
            white-space: nowrap;
            min-width: 70px;
        }}
        
        .time-cell:empty::after {{
            content: "TBA";
            color: #999;
            font-weight: 400;
        }}
        
        .event-cell {{
            font-weight: 600;
            color: #333;
            min-width: 200px;
        }}
        
        .impact-cell {{
            min-width: 90px;
            text-align: center;
        }}
        
        .impact-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .impact-high {{
            background: #ff4444;
            color: white;
        }}
        
        .impact-medium {{
            background: #ff9800;
            color: white;
        }}
        
        .impact-low {{
            background: #4caf50;
            color: white;
        }}
        
        .data-cell {{
            text-align: center;
            font-weight: 600;
            color: #333;
            min-width: 75px;
        }}
        
        .data-cell:empty::after {{
            content: "—";
            color: #ccc;
        }}
        
        .ai-analysis {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .ai-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            font-size: 20px;
            font-weight: 700;
            color: #1e3c72;
        }}
        
        .ai-header::before {{
            content: "🤖";
            margin-right: 10px;
            font-size: 24px;
        }}
        
        .ai-question {{
            font-weight: 600;
            color: #2a5298;
            margin-bottom: 10px;
            font-size: 15px;
        }}
        
        .ai-response {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            line-height: 1.8;
            color: #333;
            font-size: 14px;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 20px;
        }}

        .market-overview {{
            margin-top: 30px;
            padding: 20px;
            background: #f5f7ff;
            border-radius: 10px;
            border: 1px solid #e0e6ff;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
        }}

        .market-overview-header {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 15px;
        }}

        .market-overview-header h2 {{
            font-size: 20px;
            color: #1e3c72;
            font-weight: 700;
        }}

        .market-overview-subtitle {{
            font-size: 13px;
            color: #667;
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        .market-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .market-table th {{
            background: #e6ebff;
            color: #1e3c72;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            padding: 10px;
            text-align: left;
        }}

        .market-table td {{
            padding: 12px 10px;
            border-bottom: 1px solid #dde3ff;
            font-size: 13px;
        }}

        .symbol-cell {{
            font-weight: 700;
            color: #1e3c72;
        }}

        .symbol-cell .symbol-label {{
            display: block;
            font-size: 11px;
            font-weight: 400;
            color: #666;
        }}

        .comment-cell {{
            font-weight: 600;
            color: #2a5298;
        }}

        .empty-cell {{
            text-align: center;
            padding: 25px;
            color: #999;
            font-style: italic;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
        }}
        
        .footer-text {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .footer-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        
        @media only screen and (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 24px;
            }}
            
            .container {{
                max-width: 100%;
            }}
            
            .events-table {{
                font-size: 12px;
            }}
            
            .events-table th,
            .events-table td {{
                padding: 10px 5px;
            }}
            
            .events-table th {{
                font-size: 10px;
            }}
            
            .event-cell {{
                min-width: 140px;
            }}
            
            .date-banner {{
                font-size: 16px;
                padding: 12px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💵 USD Economic Calendar</h1>
            <div class="subtitle">ForexFactory.com - Today's Events</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{event_count}</div>
                <div class="stat-label">Events Today</div>
            </div>
            <div class="stat">
                <div class="stat-value">USD</div>
                <div class="stat-label">Currency</div>
            </div>
            <div class="stat">
                <div class="stat-value">{unique_date}</div>
                <div class="stat-label">Date</div>
            </div>
        </div>
        
        <div class="content">
            <div class="date-banner">{unique_date} - Today's USD Economic Events</div>
            
            <table class="events-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Event</th>
                        <th>Impact</th>
                        <th>Actual</th>
                        <th>Forecast</th>
                        <th>Previous</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add events as table rows
    if not events:
        html += """
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 30px; color: #999;">
                            No USD events scheduled for today
                        </td>
                    </tr>
"""
    else:
        for event in events:
            event_name = event.get('event', 'Unknown Event')
            time_val = event.get('time', '')
            impact = event.get('impact', '').lower()
            actual = event.get('actual', '')
            forecast = event.get('forecast', '')
            previous = event.get('previous', '')
            
            impact_class = f"impact-{impact}" if impact else "impact-low"
            impact_display = impact.capitalize() if impact else "—"
            
            html += f"""
                    <tr>
                        <td class="time-cell">{time_val}</td>
                        <td class="event-cell">{event_name}</td>
                        <td class="impact-cell">
                            <span class="impact-badge {impact_class}">{impact_display}</span>
                        </td>
                        <td class="data-cell">{actual}</td>
                        <td class="data-cell">{forecast}</td>
                        <td class="data-cell">{previous}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
"""

    # Add market overview if provided
    if market_html:
        html += f"""
        <div class="content">
            {market_html}
        </div>
"""
    
    # Add AI Analysis section if available
    if ai_analysis and ai_analysis.get('responses'):
        html += """
        <div class="content">
            <div class="ai-analysis">
                <div class="ai-header">AI Market Analysis</div>
"""
        
        for response_item in ai_analysis.get('responses', []):
            question = response_item.get('question', '')
            response = response_item.get('response', '')
            
            html += f"""
                <div class="ai-question">Q: {question}</div>
                <div class="ai-response">{response}</div>
"""
        
        html += """
            </div>
        </div>
"""
    
    # Add footer
    html += f"""
        </div>
        
        <div class="footer">
            <div class="footer-text">
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC
            </div>
            <div class="footer-text">
                Source: <a href="https://www.forexfactory.com/calendar" class="footer-link">ForexFactory.com</a>
            </div>
            <div class="footer-text" style="margin-top: 10px; color: #999;">
                📊 Powered by AWS Lambda
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def send_email(to_email, smtp_user, smtp_password, html_content):
    """Send email with HTML content via Gmail SMTP."""
    print("=" * 60)
    print("STEP 3: Sending Email")
    print("=" * 60)
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Today's USD Economic Calendar - {datetime.now().strftime('%b %d, %Y')}"
        msg['From'] = smtp_user
        msg['To'] = to_email
        
        # Attach HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        print(f"Connecting to SMTP server: smtp.gmail.com:587")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        print(f"Logging in as: {smtp_user}")
        server.login(smtp_user, smtp_password)
        
        print(f"Sending email to: {to_email}")
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise


# ============================================================================
# LAMBDA HANDLER
# ============================================================================

def lambda_handler(event, context):
    """
    Main Lambda handler function.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Response dict with statusCode and body
    """
    print("\n" + "=" * 60)
    print("ForexFactory Calendar - AWS Lambda")
    print("=" * 60)
    print(f"Event: {json.dumps(event)}")
    print(f"Execution started: {datetime.now().isoformat()}")
    print("=" * 60 + "\n")
    
    try:
        # Get environment variables
        to_email = os.environ.get('TO_EMAIL')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        # Validate required environment variables
        if not all([to_email, smtp_user, smtp_password]):
            raise ValueError("Missing required environment variables: TO_EMAIL, SMTP_USER, SMTP_PASSWORD")
        
        print(f"Configuration loaded:")
        print(f"  TO_EMAIL: {to_email}")
        print(f"  SMTP_USER: {smtp_user}")
        print(f"  OPENAI enabled: {bool(openai_api_key)}")
        print()
        
        # Enable verbose HTTP logging if requested
        configure_http_debug()

        # Network diagnostics before doing any heavy work
        log_network_diagnostics()

        # Step 1: Fetch and parse calendar
        calendar_data = fetch_and_parse_calendar()

        # Step 2: Collect market overview
        market_html = None
        market_snapshot = None
        if MARKET_SNAPSHOT_ENABLED:
            try:
                tz = ZoneInfo(MARKET_TIMEZONE)
                run_dt = datetime.now(timezone.utc)
                market_snapshot = build_market_snapshot(
                    run_dt=run_dt,
                    tz=tz,
                    lookback_minutes=MARKET_LOOKBACK_HOURS * 60,
                )
                market_html = generate_market_table_html(market_snapshot)
                print(f"✅ Market snapshot generated for {len(market_snapshot.get('symbols', []))} symbols")
            except Exception as e:
                print(f"⚠️  Error generating market snapshot: {e}")
        else:
            print("⏭️  Skipping market snapshot (disabled via MARKET_SNAPSHOT_ENABLED).")
        
        # Step 3: Get AI analysis (if configured)
        ai_analysis = None
        if openai_api_key:
            ai_analysis = get_ai_analysis(calendar_data, openai_api_key)
        else:
            print("\n⏭️  Skipping AI analysis (not configured)")
        
        # Step 4: Generate HTML
        print("\nGenerating HTML email...")
        html_content = generate_html_email(calendar_data, ai_analysis, market_html=market_html)
        print(f"✅ HTML generated ({len(html_content)} bytes)")
        
        # Step 5: Send email
        send_email(to_email, smtp_user, smtp_password, html_content)
        
        # Success response
        result = {
            'timestamp': datetime.now().isoformat(),
            'event_count': calendar_data['event_count'],
            'ai_analysis_included': bool(ai_analysis),
            'market_data_included': bool(market_html),
            'email_sent_to': to_email,
            'status': 'success'
        }
        
        print("\n" + "=" * 60)
        print("✅ COMPLETE! Lambda execution successful")
        print(f"Events parsed: {result['event_count']}")
        print(f"AI analysis: {'Yes' if result['ai_analysis_included'] else 'No'}")
        print(f"Market overview: {'Yes' if result['market_data_included'] else 'No'}")
        print(f"Email sent to: {result['email_sent_to']}")
        print("=" * 60 + "\n")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        error_msg = f"Lambda execution failed: {str(e)}"
        print(f"\n❌ ERROR: {error_msg}")
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }


# For local testing
if __name__ == '__main__':
    print("Running locally (for testing)...")
    print("Make sure to set environment variables!")
    print()
    
    # Mock event and context for local testing
    test_event = {}
    test_context = {}
    
    result = lambda_handler(test_event, test_context)
    print(f"\nResult: {json.dumps(result, indent=2)}")

