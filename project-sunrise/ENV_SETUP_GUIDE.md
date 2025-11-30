# 🔐 Environment Configuration Guide

Complete guide for using `.env` file to manage your configuration securely.

---

## 🎯 Why Use .env File?

**Benefits:**
- ✅ **Secure** - Credentials stored in one file (not in cron)
- ✅ **Simple** - Easy to update without editing cron
- ✅ **Clean** - No long environment variable exports
- ✅ **Safe** - Automatically excluded from git
- ✅ **Portable** - Easy to backup and restore

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Create .env File

**Option A: Interactive (Easiest)**
```bash
cd /home/nmoiseykin/webpage-parser
./setup_env.sh
```

**Option B: Manual**
```bash
cp .env.example .env
nano .env
# Fill in your credentials
```

### Step 2: Verify Configuration

```bash
# Check .env file exists
ls -la .env

# View contents (be careful - contains passwords!)
cat .env
```

### Step 3: Set Up Daily Schedule

```bash
./setup_cron_with_env.sh
```

**That's it!** The cron job will automatically read from `.env` file.

---

## 📝 .env File Format

```bash
# Email Configuration (REQUIRED)
TO_EMAIL=recipient@example.com
SMTP_USER=sender@gmail.com
SMTP_PASSWORD=your_gmail_app_password

# OpenAI Configuration (OPTIONAL)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_ASSISTANT_ID=asst_your-assistant-id-here

# Advanced Settings (OPTIONAL)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
LOG_FILE=/tmp/forex_calendar.log
```

---

## 🔒 Security

### File Permissions

The `.env` file is automatically secured:
```bash
chmod 600 .env  # Owner read/write only
```

Verify permissions:
```bash
ls -la .env
# Should show: -rw------- (600)
```

### Git Protection

`.env` is automatically excluded from git via `.gitignore`:
```
.env
.env.local
.env.*.local
```

**Never commit .env to git!**

---

## 🔧 Usage

### All Scripts Auto-Load .env

All workflow scripts now automatically load `.env`:
- `send_calendar_with_ai.sh`
- `send_calendar.sh`
- `run_parser.sh`

Just run them normally:
```bash
./send_calendar_with_ai.sh
```

No need to export variables manually!

### Cron Job

Simple cron line (no env vars needed):
```bash
0 7 * * * cd /home/nmoiseykin/webpage-parser && ./send_calendar_with_ai.sh >> /tmp/forex_calendar.log 2>&1
```

The script loads `.env` automatically.

---

## ✏️ Updating Configuration

### Change Email or Password

```bash
nano .env
# Update values
# Save and exit
```

Changes take effect immediately - no need to update cron!

### Add OpenAI Configuration

```bash
nano .env
# Add or update:
OPENAI_API_KEY=sk-your-new-key
OPENAI_ASSISTANT_ID=asst_your-new-id
# Save and exit
```

### Test Changes

```bash
./send_calendar_with_ai.sh
```

---

## 🔄 Migration from Old Setup

If you previously used environment variables in cron:

### Step 1: Create .env File
```bash
./setup_env.sh
```

### Step 2: Remove Old Cron Job
```bash
crontab -e
# Delete the old line with all the "export" statements
```

### Step 3: Add New Cron Job
```bash
./setup_cron_with_env.sh
```

Or manually:
```bash
crontab -e
# Add this simple line:
0 7 * * * cd /home/nmoiseykin/webpage-parser && ./send_calendar_with_ai.sh >> /tmp/forex_calendar.log 2>&1
```

---

## 📋 Multiple Environments

### Production .env
```bash
# Main configuration
.env
```

### Development .env
```bash
# Create separate config for testing
cp .env .env.development

# Edit as needed
nano .env.development

# Use it
source .env.development
./send_calendar_with_ai.sh
```

### Backup .env
```bash
# Backup before changes
cp .env .env.backup.$(date +%Y%m%d)

# Restore from backup
cp .env.backup.20241029 .env
```

---

## 🧪 Testing

### Test .env Loading
```bash
# Check if .env is loaded correctly
cd /home/nmoiseykin/webpage-parser
source .env
echo "To: $TO_EMAIL"
echo "From: $SMTP_USER"
echo "AI: $OPENAI_ASSISTANT_ID"
```

### Test Script with .env
```bash
./send_calendar_with_ai.sh
```

Should show:
```
📝 Loading configuration from .env file...
```

---

## ❗ Troubleshooting

### "⚠️ Warning: .env file not found!"

**Solution:**
```bash
./setup_env.sh
```

### ".env exists but credentials not loading"

**Check file format:**
```bash
cat .env
```

Make sure:
- No spaces around `=`
- No quotes needed (unless value has spaces)
- No comments on same line as values

**Good:**
```bash
TO_EMAIL=test@example.com
```

**Bad:**
```bash
TO_EMAIL = test@example.com  # Wrong - spaces around =
TO_EMAIL="test@example.com"  # Wrong - quotes not needed
```

### "Permission denied"

**Fix permissions:**
```bash
chmod 600 .env
```

### Scripts still ask for credentials

**Make sure .env is in the correct location:**
```bash
ls -la /home/nmoiseykin/webpage-parser/.env
```

Should be in the project root directory.

---

## 🔐 Best Practices

1. **Never commit .env to git**
   - Already protected by `.gitignore`
   - Double-check: `git status` should not show `.env`

2. **Use .env.example for documentation**
   - Commit `.env.example` (without real credentials)
   - Use it as a template

3. **Backup .env securely**
   ```bash
   cp .env ~/secure_backup/.env.backup
   chmod 600 ~/secure_backup/.env.backup
   ```

4. **Rotate passwords regularly**
   - Update `.env` with new credentials
   - No need to update cron

5. **Use app passwords**
   - Gmail: Use App Passwords (not your real password)
   - OpenAI: Use separate API key per project

6. **Restrict file access**
   ```bash
   chmod 600 .env  # Owner only
   ```

---

## 📂 File Structure

```
webpage-parser/
├── .env                    # Your actual credentials (git-ignored)
├── .env.example            # Template (safe to commit)
├── .gitignore              # Excludes .env from git
├── setup_env.sh            # Interactive setup script
├── setup_cron_with_env.sh  # Cron setup using .env
├── send_calendar_with_ai.sh # Auto-loads .env
├── send_calendar.sh        # Auto-loads .env
└── ENV_SETUP_GUIDE.md      # This file
```

---

## 🎯 Quick Reference

```bash
# Create .env
./setup_env.sh

# Edit .env
nano .env

# View .env (careful - shows passwords!)
cat .env

# Check permissions
ls -la .env

# Setup cron with .env
./setup_cron_with_env.sh

# Test script (uses .env)
./send_calendar_with_ai.sh

# Backup .env
cp .env .env.backup

# Verify .env not in git
git status
```

---

## ✅ Checklist

- [ ] Created .env file (`./setup_env.sh`)
- [ ] Verified .env permissions (600)
- [ ] Confirmed .env not in git (`git status`)
- [ ] Tested script manually
- [ ] Set up cron job (`./setup_cron_with_env.sh`)
- [ ] Verified cron job (`crontab -l`)
- [ ] Backed up .env securely
- [ ] Documented password in password manager

---

## 🎉 You're Done!

Your configuration is now:
- ✅ Secure (file permissions)
- ✅ Protected (git-ignored)
- ✅ Simple (one file to edit)
- ✅ Permanent (survives reboots)
- ✅ Easy to update (just edit .env)

**Next time you need to update credentials, just edit `.env` - no need to touch cron!**

