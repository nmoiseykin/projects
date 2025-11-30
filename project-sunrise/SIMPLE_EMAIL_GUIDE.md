# 📧 Simple Email Guide - 3 Easy Steps

## What This Does

Takes your ForexFactory USD calendar JSON and:
1. ✨ Converts it to **beautiful mobile-friendly HTML**
2. 📧 Sends it to your email

The email looks professional with:
- Color-coded impact levels (Red/Orange/Green)
- Mobile-responsive design
- All event details (Actual, Forecast, Previous)
- Organized by date

---

## 🚀 3 Steps to Send Email

### Step 1: Get Your Gmail App Password

**Go to:** https://myaccount.google.com/apppasswords

1. Enable 2-Factor Authentication (if not already)
2. Create new app password for "Mail"
3. Copy the 16-character password (like: `abcd efgh ijkl mnop`)

### Step 2: Run This Command

```bash
cd /home/nmoiseykin/webpage-parser/examples
source ../venv/bin/activate

python3 send_calendar_email.py \
  --to-email "YOUR_EMAIL@example.com" \
  --smtp-user "YOUR_GMAIL@gmail.com" \
  --smtp-password "your_16_char_app_password"
```

**Replace:**
- `YOUR_EMAIL@example.com` - Where to send the email
- `YOUR_GMAIL@gmail.com` - Your Gmail address
- `your_16_char_app_password` - The app password from Step 1

### Step 3: Check Your Email! 

Done! Check your inbox for a beautiful calendar email. 📧

---

## 🎯 One-Line Example

```bash
python3 send_calendar_email.py \
  --to-email "trader@example.com" \
  --smtp-user "mybot@gmail.com" \
  --smtp-password "abcdefghijklmnop"
```

---

## 📱 Preview HTML First (Optional)

Want to see how it looks before sending?

```bash
python3 send_calendar_email.py \
  --save-html preview.html \
  --to-email "dummy" \
  --smtp-user "dummy" \
  --smtp-password "dummy"
```

Then open `preview.html` in your browser!

---

## 🤖 Complete Workflow (Fetch + Send)

Want to fetch the latest calendar AND send email in one go?

```bash
# Set your email credentials
export TO_EMAIL="recipient@example.com"
export SMTP_USER="sender@gmail.com"
export SMTP_PASSWORD="your_app_password"

# Run complete workflow
cd /home/nmoiseykin/webpage-parser
./send_calendar.sh
```

This does everything:
1. Fetches latest calendar from ForexFactory
2. Parses USD events
3. Generates HTML
4. Sends email

---

## 🔧 Using Other Email Providers

### Outlook/Office365
```bash
python3 send_calendar_email.py \
  --to-email "recipient@example.com" \
  --smtp-server smtp.office365.com \
  --smtp-user "your_email@outlook.com" \
  --smtp-password "your_password"
```

### Yahoo Mail
```bash
python3 send_calendar_email.py \
  --to-email "recipient@example.com" \
  --smtp-server smtp.mail.yahoo.com \
  --smtp-user "your_email@yahoo.com" \
  --smtp-password "your_app_password"
```

---

## ❓ Common Issues

**"Username and Password not accepted"**
- Use App Password, not your regular Gmail password
- Enable 2-Factor Authentication first

**"Email not received"**
- Check spam/junk folder
- Verify email address is correct

**Want to customize the HTML?**
- Edit `send_calendar_email.py`
- Change colors, fonts, layout in the CSS section

---

## 📂 Files Generated

- `examples/forex_calendar_usd.json` - The calendar data
- `examples/calendar_preview.html` - HTML preview (if --save-html used)
- Email sent to your inbox! 📧

---

## 🎉 That's It!

You now have an automated system to get beautiful USD economic calendar emails!

For more details, see `EMAIL_SETUP_GUIDE.md`

