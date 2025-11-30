# 📅 Daily Scheduling Guide - 7 AM Automatic Emails

Complete guide to scheduling your ForexFactory calendar emails to run automatically every day at 7 AM.

---

## 🚀 Quick Setup (Recommended)

### Interactive Setup Script

```bash
cd /home/nmoiseykin/webpage-parser
./setup_daily_schedule.sh
```

This script will:
1. Ask for your email credentials
2. Ask for OpenAI credentials (optional)
3. Create the cron job automatically
4. Verify the setup

**That's it!** Your daily emails will start tomorrow at 7 AM.

---

## 🔧 Manual Setup

### Method 1: Using Cron (Linux/Mac)

**Step 1: Open crontab editor**
```bash
crontab -e
```

**Step 2: Add one of these lines**

**Option A: With AI Analysis**
```bash
0 7 * * * export TO_EMAIL='you@example.com' SMTP_USER='sender@gmail.com' SMTP_PASSWORD='app_pass' OPENAI_API_KEY='sk-...' OPENAI_ASSISTANT_ID='asst_...' && cd /home/nmoiseykin/webpage-parser && ./send_calendar_with_ai.sh >> /tmp/forex_calendar.log 2>&1
```

**Option B: Without AI (Calendar Only)**
```bash
0 7 * * * export TO_EMAIL='you@example.com' SMTP_USER='sender@gmail.com' SMTP_PASSWORD='app_pass' && cd /home/nmoiseykin/webpage-parser && ./send_calendar.sh >> /tmp/forex_calendar.log 2>&1
```

**Step 3: Save and exit**
- Press `Ctrl+X`, then `Y`, then `Enter` (if using nano)
- Or `:wq` and `Enter` (if using vim)

**Step 4: Verify**
```bash
crontab -l
```

You should see your new cron job listed.

---

## 📋 Cron Schedule Examples

```bash
# Every day at 7:00 AM
0 7 * * *

# Every weekday (Mon-Fri) at 7:00 AM
0 7 * * 1-5

# Every day at 7:00 AM and 5:00 PM
0 7,17 * * *

# Every 6 hours (4 times a day)
0 */6 * * *

# Monday, Wednesday, Friday at 7:00 AM
0 7 * * 1,3,5
```

---

## ✅ Verify Setup

### Check Cron Jobs
```bash
crontab -l
```

### View Logs
```bash
# Real-time log viewing
tail -f /tmp/forex_calendar.log

# View last 50 lines
tail -50 /tmp/forex_calendar.log

# View all logs
cat /tmp/forex_calendar.log
```

### Test Run Now (Don't Wait for 7 AM)
```bash
cd /home/nmoiseykin/webpage-parser

# With AI
./send_calendar_with_ai.sh

# Without AI
./send_calendar.sh
```

---

## 🔍 Troubleshooting

### Cron Job Not Running

**1. Check cron service is running**
```bash
systemctl status cron
# or
systemctl status crond
```

**2. Check cron logs**
```bash
# Ubuntu/Debian
grep CRON /var/log/syslog

# RedHat/CentOS
grep CRON /var/log/cron
```

**3. Check your log file**
```bash
tail -50 /tmp/forex_calendar.log
```

### Common Issues

**"Command not found"**
- Use full paths in cron: `/usr/bin/python3` instead of `python3`
- Or ensure PATH is set in crontab

**"Permission denied"**
- Make sure scripts are executable: `chmod +x *.sh`
- Check file permissions

**"Environment variables not set"**
- All variables must be in the cron line
- Or source a config file in the script

**Email not received**
- Check spam folder
- Verify credentials are correct
- Check log file for errors

---

## 📧 Environment Variables

### Required for Email
```bash
TO_EMAIL="recipient@example.com"
SMTP_USER="sender@gmail.com"
SMTP_PASSWORD="gmail_app_password"
```

### Required for AI Analysis
```bash
OPENAI_API_KEY="sk-your-api-key"
OPENAI_ASSISTANT_ID="asst_your-assistant-id"
```

---

## 🛠️ Alternative: Systemd Timer (Linux)

For more control, use systemd timer instead of cron:

### Create Service File

**1. Create service file**
```bash
sudo nano /etc/systemd/system/forex-calendar.service
```

```ini
[Unit]
Description=ForexFactory Calendar Email with AI Analysis

[Service]
Type=oneshot
User=nmoiseykin
Environment="TO_EMAIL=you@example.com"
Environment="SMTP_USER=sender@gmail.com"
Environment="SMTP_PASSWORD=app_password"
Environment="OPENAI_API_KEY=sk-..."
Environment="OPENAI_ASSISTANT_ID=asst_..."
WorkingDirectory=/home/nmoiseykin/webpage-parser
ExecStart=/home/nmoiseykin/webpage-parser/send_calendar_with_ai.sh
StandardOutput=append:/tmp/forex_calendar.log
StandardError=append:/tmp/forex_calendar.log
```

**2. Create timer file**
```bash
sudo nano /etc/systemd/system/forex-calendar.timer
```

```ini
[Unit]
Description=Run ForexFactory Calendar Email Daily at 7 AM

[Timer]
OnCalendar=07:00
Persistent=true
AccuracySec=1min

[Install]
WantedBy=timers.target
```

**3. Enable and start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable forex-calendar.timer
sudo systemctl start forex-calendar.timer
```

**4. Check status**
```bash
systemctl status forex-calendar.timer
systemctl list-timers forex-calendar.timer
```

**5. Test run**
```bash
sudo systemctl start forex-calendar.service
```

---

## 📊 Monitoring

### Create Monitor Script

```bash
nano /home/nmoiseykin/webpage-parser/check_daily_run.sh
```

```bash
#!/bin/bash
# Check if today's email was sent

LOG_FILE="/tmp/forex_calendar.log"
TODAY=$(date +%Y-%m-%d)

if grep -q "$TODAY.*SUCCESS" "$LOG_FILE"; then
    echo "✅ Today's email was sent successfully"
    exit 0
else
    echo "❌ Today's email not sent yet or failed"
    exit 1
fi
```

```bash
chmod +x check_daily_run.sh
```

---

## 🔒 Security Best Practices

### Option 1: Use Environment File

**1. Create secure env file**
```bash
nano ~/.forex_calendar_env
```

```bash
export TO_EMAIL="you@example.com"
export SMTP_USER="sender@gmail.com"
export SMTP_PASSWORD="your_password"
export OPENAI_API_KEY="sk-..."
export OPENAI_ASSISTANT_ID="asst_..."
```

**2. Secure the file**
```bash
chmod 600 ~/.forex_calendar_env
```

**3. Update cron to source it**
```bash
0 7 * * * source ~/.forex_calendar_env && cd /home/nmoiseykin/webpage-parser && ./send_calendar_with_ai.sh >> /tmp/forex_calendar.log 2>&1
```

### Option 2: Use Keyring/Secret Manager

For production, consider:
- **pass** (password store)
- **gnome-keyring**
- **AWS Secrets Manager**
- **HashiCorp Vault**

---

## 📱 Notifications

### Get Notified on Failure

Add notification to cron:

```bash
0 7 * * * (export TO_EMAIL='...' && cd /home/nmoiseykin/webpage-parser && ./send_calendar_with_ai.sh || echo "Forex calendar failed" | mail -s "Cron Failure" you@example.com) >> /tmp/forex_calendar.log 2>&1
```

---

## 🗑️ Remove Schedule

### Remove Cron Job

**1. Edit crontab**
```bash
crontab -e
```

**2. Delete the forex calendar line**

**3. Save and exit**

### Remove Systemd Timer

```bash
sudo systemctl stop forex-calendar.timer
sudo systemctl disable forex-calendar.timer
sudo rm /etc/systemd/system/forex-calendar.service
sudo rm /etc/systemd/system/forex-calendar.timer
sudo systemctl daemon-reload
```

---

## 📈 Log Rotation

Prevent logs from growing too large:

**Create logrotate config**
```bash
sudo nano /etc/logrotate.d/forex-calendar
```

```
/tmp/forex_calendar.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 nmoiseykin nmoiseykin
}
```

---

## ✅ Complete Setup Checklist

- [ ] Email credentials configured
- [ ] OpenAI credentials configured (if using AI)
- [ ] Scripts tested manually
- [ ] Cron job added
- [ ] Cron job verified with `crontab -l`
- [ ] Log file location confirmed
- [ ] Tested with dry run
- [ ] Checked spam folder (first time)
- [ ] Set up log monitoring (optional)
- [ ] Configured log rotation (optional)

---

## 🎉 You're Done!

Your ForexFactory calendar emails will now be sent automatically every day at 7:00 AM!

**Next morning:**
1. Check your email at 7:05 AM
2. Check logs: `tail /tmp/forex_calendar.log`
3. Enjoy your automated market insights! 📊

---

## 📞 Quick Reference

```bash
# View scheduled jobs
crontab -l

# Edit scheduled jobs  
crontab -e

# Remove all cron jobs
crontab -r

# View logs
tail -f /tmp/forex_calendar.log

# Test run manually
cd /home/nmoiseykin/webpage-parser
./send_calendar_with_ai.sh

# Check if cron is running
systemctl status cron
```

