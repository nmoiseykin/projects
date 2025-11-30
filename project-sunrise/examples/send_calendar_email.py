"""
Convert ForexFactory calendar JSON to beautiful HTML table and send via email.
"""

import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import argparse


def load_calendar_json(json_file):
    """Load calendar data from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_ai_analysis(json_file):
    """Load AI analysis from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def generate_html_email(calendar_data, ai_analysis=None, market_html=None):
    """Generate beautiful mobile-friendly HTML email with optional market and AI sections."""
    
    events = calendar_data.get('events', [])
    timestamp = calendar_data.get('timestamp', '')
    event_count = calendar_data.get('event_count', 0)
    
    # Get unique date for display (assuming today's events)
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
            time = event.get('time', '')
            impact = event.get('impact', '').lower()
            actual = event.get('actual', '')
            forecast = event.get('forecast', '')
            previous = event.get('previous', '')
            
            impact_class = f"impact-{impact}" if impact else "impact-low"
            impact_display = impact.capitalize() if impact else "—"
            
            html += f"""
                    <tr>
                        <td class="time-cell">{time}</td>
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
        <div class="footer">
            <div class="footer-text">
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
            <div class="footer-text">
                Source: <a href="https://www.forexfactory.com/calendar" class="footer-link">ForexFactory.com</a>
            </div>
            <div class="footer-text" style="margin-top: 10px; color: #999;">
                📊 Automated by WebPage Parser
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def send_email(to_email, subject, html_content, smtp_config):
    """Send email with HTML content."""
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_config['from_email']
    msg['To'] = to_email
    
    # Attach HTML
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Send email
    print(f"Connecting to SMTP server: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}", file=sys.stderr)
    
    if smtp_config['use_tls']:
        server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
        server.starttls()
    else:
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], smtp_config['smtp_port'])
    
    if smtp_config['smtp_user'] and smtp_config['smtp_password']:
        print(f"Logging in as: {smtp_config['smtp_user']}", file=sys.stderr)
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
    
    print(f"Sending email to: {to_email}", file=sys.stderr)
    server.sendmail(smtp_config['from_email'], to_email, msg.as_string())
    server.quit()
    
    print("✅ Email sent successfully!", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Send ForexFactory calendar as beautiful HTML table email')
    parser.add_argument('--json-file', default='forex_calendar_usd.json',
                       help='JSON file to read (default: forex_calendar_usd.json)')
    parser.add_argument('--ai-analysis', 
                       help='AI analysis JSON file (optional)')
    parser.add_argument('--to-email', required=True,
                       help='Recipient email address')
    parser.add_argument('--subject', default='📊 Today\'s USD Economic Calendar',
                       help='Email subject')
    parser.add_argument('--save-html', help='Save HTML to file (optional)')
    
    # SMTP configuration
    parser.add_argument('--smtp-server', default='smtp.gmail.com',
                       help='SMTP server (default: smtp.gmail.com)')
    parser.add_argument('--smtp-port', type=int, default=587,
                       help='SMTP port (default: 587)')
    parser.add_argument('--smtp-user', required=True,
                       help='SMTP username/email')
    parser.add_argument('--smtp-password', required=True,
                       help='SMTP password or app password')
    parser.add_argument('--from-email', 
                       help='From email address (default: same as smtp-user)')
    parser.add_argument('--use-ssl', action='store_true',
                       help='Use SSL instead of TLS (default: TLS)')
    
    args = parser.parse_args()
    
    # Set from_email if not provided
    if not args.from_email:
        args.from_email = args.smtp_user
    
    try:
        # Load JSON data
        print(f"Loading calendar from: {args.json_file}", file=sys.stderr)
        calendar_data = load_calendar_json(args.json_file)
        
        # Load AI analysis if provided
        ai_analysis = None
        if args.ai_analysis:
            print(f"Loading AI analysis from: {args.ai_analysis}", file=sys.stderr)
            ai_analysis = load_ai_analysis(args.ai_analysis)
            if ai_analysis:
                print(f"✓ AI analysis loaded with {len(ai_analysis.get('responses', []))} responses", file=sys.stderr)
        
        # Generate HTML
        if ai_analysis:
            print("Generating beautiful HTML table with AI analysis...", file=sys.stderr)
        else:
            print("Generating beautiful HTML table...", file=sys.stderr)
        html_content = generate_html_email(calendar_data, ai_analysis=ai_analysis)
        
        # Optionally save HTML
        if args.save_html:
            with open(args.save_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML saved to: {args.save_html}", file=sys.stderr)
        
        # Configure SMTP
        smtp_config = {
            'smtp_server': args.smtp_server,
            'smtp_port': args.smtp_port if not args.use_ssl else 465,
            'smtp_user': args.smtp_user,
            'smtp_password': args.smtp_password,
            'from_email': args.from_email,
            'use_tls': not args.use_ssl,
        }
        
        # Send email
        send_email(args.to_email, args.subject, html_content, smtp_config)
        
        print(f"\n✅ SUCCESS! Email sent to {args.to_email}", file=sys.stderr)
        
    except FileNotFoundError:
        print(f"Error: JSON file not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
