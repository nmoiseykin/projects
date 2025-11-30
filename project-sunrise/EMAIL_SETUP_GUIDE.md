# Email Setup Guide

## Overview

This guide will help you send the ForexFactory USD calendar as a beautiful mobile-friendly HTML email.

## 📧 What You Get

The email includes:
- **Beautiful gradient design** with professional styling
- **Mobile-responsive layout** (looks great on phones and tablets)
- **Color-coded impact levels** (Red=High, Orange=Medium, Green=Low)
- **All event details**: Actual, Forecast, Previous values
- **Grouped by date** for easy reading
- **Summary statistics** at the top

## 🚀 Quick Start

### Option 1: Using Gmail (Recommended)

1. **Enable 2-Factor Authentication** on your Google Account
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Create an App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password (remove spaces)

3. **Run the command:**
```bash
cd /home/nmoiseykin/webpage-parser/examples
source ../venv/bin/activate

python3 send_calendar_email.py \
  --json-file forex_calendar_usd.json \
  --to-email "recipient@example.com" \
  --smtp-user "your_email@gmail.com" \
  --smtp-password "your_16_char_app_password"
```

### Option 2: Complete Workflow (Fetch + Send)

Set environment variables and run:

```bash
export TO_EMAIL="recipient@example.com"
export SMTP_USER="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"

cd /home/nmoiseykin/webpage-parser
./send_calendar.sh
```

This will:
1. ✅ Fetch latest calendar from ForexFactory
2. ✅ Parse and filter for USD events
3. ✅ Generate beautiful HTML
4. ✅ Send email

## 📧 Email Configuration Examples

### Gmail
```bash
--smtp-server smtp.gmail.com \
--smtp-port 587 \
--smtp-user your_email@gmail.com \
--smtp-password your_app_password
```

### Outlook / Office 365
```bash
--smtp-server smtp.office365.com \
--smtp-port 587 \
--smtp-user your_email@outlook.com \
--smtp-password your_password
```

### Yahoo Mail
```bash
--smtp-server smtp.mail.yahoo.com \
--smtp-port 587 \
--smtp-user your_email@yahoo.com \
--smtp-password your_app_password
```

### Custom SMTP Server
```bash
--smtp-server your.smtp.server \
--smtp-port 587 \
--smtp-user your_username \
--smtp-password your_password
```

## 🔧 Command-Line Options

### Basic Options
- `--json-file`: JSON file to read (default: forex_calendar_usd.json)
- `--to-email`: Recipient email (REQUIRED)
- `--subject`: Email subject line
- `--save-html`: Save HTML to file (for preview)

### SMTP Options
- `--smtp-server`: SMTP server address (default: smtp.gmail.com)
- `--smtp-port`: SMTP port (default: 587)
- `--smtp-user`: SMTP username/email (REQUIRED)
- `--smtp-password`: SMTP password (REQUIRED)
- `--from-email`: From address (default: same as smtp-user)
- `--use-ssl`: Use SSL port 465 instead of TLS port 587

## 📱 Preview HTML Before Sending

Generate HTML without sending:

```bash
python3 send_calendar_email.py \
  --json-file forex_calendar_usd.json \
  --save-html preview.html \
  --to-email dummy@example.com \
  --smtp-user dummy \
  --smtp-password dummy
```

Then open `preview.html` in your browser to see how it looks!

## 🤖 Automate Daily Emails

### Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to send daily at 7 AM
0 7 * * * export TO_EMAIL="you@example.com" SMTP_USER="sender@gmail.com" SMTP_PASSWORD="app_password" && cd /home/nmoiseykin/webpage-parser && ./send_calendar.sh >> /tmp/forex_email.log 2>&1
```

### Using systemd timer (Linux)

Create `/etc/systemd/system/forex-calendar.service`:
```ini
[Unit]
Description=Send ForexFactory Calendar Email

[Service]
Type=oneshot
Environment="TO_EMAIL=you@example.com"
Environment="SMTP_USER=sender@gmail.com"
Environment="SMTP_PASSWORD=app_password"
WorkingDirectory=/home/nmoiseykin/webpage-parser
ExecStart=/home/nmoiseykin/webpage-parser/send_calendar.sh
```

Create `/etc/systemd/system/forex-calendar.timer`:
```ini
[Unit]
Description=Send ForexFactory Calendar Daily

[Timer]
OnCalendar=daily
OnCalendar=07:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable forex-calendar.timer
sudo systemctl start forex-calendar.timer
```

## 🎨 Customization

The HTML template is in `send_calendar_email.py`. You can customize:

- **Colors**: Change gradient colors in the CSS
- **Fonts**: Modify font-family in the style section
- **Layout**: Adjust grid layouts and spacing
- **Impact badges**: Change colors for high/medium/low impact
- **Header/Footer**: Customize branding and text

## 🐛 Troubleshooting

### "Username and Password not accepted" (Gmail)
- You must use an App Password, not your regular Gmail password
- Enable 2-Factor Authentication first
- Generate a new App Password at https://myaccount.google.com/apppasswords

### "Connection refused"
- Check SMTP server and port
- Try --use-ssl flag for port 465
- Check firewall settings

### Email not received
- Check spam/junk folder
- Verify recipient email is correct
- Check SMTP server logs

### HTML looks broken
- Some email clients strip CSS
- Gmail, Outlook, Apple Mail should work fine
- Preview in browser first with --save-html

## 📝 Example Complete Command

```bash
cd /home/nmoiseykin/webpage-parser/examples
source ../venv/bin/activate

python3 send_calendar_email.py \
  --json-file forex_calendar_usd.json \
  --to-email "trader@example.com" \
  --subject "📊 Daily USD Economic Calendar" \
  --smtp-server smtp.gmail.com \
  --smtp-port 587 \
  --smtp-user "mybot@gmail.com" \
  --smtp-password "abcd efgh ijkl mnop" \
  --save-html daily_calendar.html
```

## 🔒 Security Tips

1. **Never commit passwords to git**
2. Use environment variables for credentials
3. Use app passwords instead of real passwords
4. Restrict app password to "Mail" only
5. Rotate passwords regularly
6. Use a dedicated email account for sending

## ✨ Features of the HTML Email

- **Responsive Design**: Looks great on all devices
- **Color-Coded Impact**: Quick visual identification
- **Professional Layout**: Clean, modern appearance
- **Event Cards**: Each event in its own card
- **Time Badges**: Prominent time display
- **Data Grid**: Actual/Forecast/Previous in organized layout
- **Date Grouping**: Events organized by day
- **Summary Stats**: Event count at the top
- **Footer Info**: Source and timestamp

