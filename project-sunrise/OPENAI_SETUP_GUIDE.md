## 🤖 OpenAI Assistant Integration Guide

Complete guide to adding AI-powered market analysis to your ForexFactory calendar emails.

---

## 🎯 What This Does

The system now:
1. ✅ Fetches today's USD economic calendar events
2. ✅ Sends calendar data to OpenAI Assistant
3. ✅ Gets AI-powered market analysis
4. ✅ Combines calendar + AI analysis into beautiful HTML email
5. ✅ Sends everything to your inbox

---

## 📋 Prerequisites

### 1. OpenAI API Key

Get your API key:
- Go to: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy the key (starts with `sk-...`)
- Save it securely

### 2. Create OpenAI Assistant

**Option A: Use Web Interface** (Recommended)
1. Go to: https://platform.openai.com/assistants
2. Click "+ Create"
3. Configure assistant:
   - **Name**: Forex Market Analyst
   - **Model**: gpt-4-turbo-preview (or gpt-4)
   - **Instructions**: 
     ```
     You are an expert forex market analyst. Analyze economic calendar 
     events and provide concise insights about potential market impacts, 
     trading opportunities, and risk factors. Focus on high-impact events 
     and be specific about currency pairs and timeframes.
     ```
   - **Tools**: Enable "Web Browsing" for real-time data
   - **Files**: None needed
4. Click "Save"
5. Copy the Assistant ID (starts with `asst_...`)

**Option B: Use API**
```python
from openai import OpenAI
client = OpenAI(api_key='your-api-key')

assistant = client.beta.assistants.create(
    name="Forex Market Analyst",
    instructions="You are an expert forex market analyst...",
    model="gpt-4-turbo-preview",
    tools=[{"type": "code_interpreter"}]  # or "retrieval" for web search
)

print(assistant.id)  # Copy this ID
```

---

## ⚙️ Configuration

### Set Environment Variables

```bash
# Email configuration (required)
export TO_EMAIL="recipient@example.com"
export SMTP_USER="sender@gmail.com"
export SMTP_PASSWORD="your_gmail_app_password"

# OpenAI configuration (required for AI analysis)
export OPENAI_API_KEY="sk-your-api-key-here"
export OPENAI_ASSISTANT_ID="asst-your-assistant-id-here"
```

### Customize Questions

Edit `examples/questions.txt`:

```txt
# Questions for OpenAI Assistant
# One question per line (lines starting with # are ignored)

Based on today's USD economic calendar events, provide a brief analysis of the potential market impact and trading opportunities. Focus on high-impact events.

What are the key risk factors traders should watch for based on today's economic events?

Provide specific USD currency pair recommendations based on today's calendar.
```

---

## 🚀 Usage

### Complete Workflow (Calendar + AI Analysis + Email)

```bash
# Set environment variables
export TO_EMAIL="you@example.com"
export SMTP_USER="sender@gmail.com"
export SMTP_PASSWORD="gmail_app_password"
export OPENAI_API_KEY="sk-..."
export OPENAI_ASSISTANT_ID="asst_..."

# Run complete workflow
cd /home/nmoiseykin/webpage-parser
./send_calendar_with_ai.sh
```

This will:
1. Fetch today's USD economic events
2. Get AI analysis from OpenAI Assistant
3. Generate beautiful HTML email with both
4. Send to your inbox

### Step-by-Step (Manual)

**Step 1: Fetch Calendar**
```bash
cd /home/nmoiseykin/webpage-parser
source venv/bin/activate

python3 examples/parse_forexfactory_final.py --today-only
```

**Step 2: Get AI Analysis**
```bash
python3 examples/openai_assistant.py \
  --assistant-id "asst_your_id" \
  --api-key "sk_your_key" \
  --questions-file examples/questions.txt \
  --calendar-json examples/forex_calendar_usd.json \
  --output examples/ai_analysis.json
```

**Step 3: Send Email**
```bash
python3 examples/send_calendar_email.py \
  --json-file examples/forex_calendar_usd.json \
  --ai-analysis examples/ai_analysis.json \
  --to-email "you@example.com" \
  --smtp-user "sender@gmail.com" \
  --smtp-password "app_password"
```

### Preview HTML (No Email)

```bash
cd examples
source ../venv/bin/activate

# Get AI analysis first
python3 openai_assistant.py \
  --assistant-id "asst_..." \
  --api-key "sk_..." \
  --questions-file questions.txt \
  --calendar-json forex_calendar_usd.json \
  --output ai_analysis.json

# Generate HTML preview
python3 send_calendar_email.py \
  --json-file forex_calendar_usd.json \
  --ai-analysis ai_analysis.json \
  --save-html preview_with_ai.html \
  --to-email "test" --smtp-user "test" --smtp-password "test"

# Open preview_with_ai.html in browser
```

---

## 📧 Email Format

Your email will now include:

```
╔══════════════════════════════════════════════════════════╗
║          💵 USD Economic Calendar                        ║
║       ForexFactory.com - Today's Events                  ║
╠══════════════════════════════════════════════════════════╣
║  Events Today: 5  |  Currency: USD  |  Date: WedOct 29 ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  📅 WedOct 29 - Today's USD Economic Events             ║
║                                                          ║
║  ┌────────────────────────────────────────────────────┐ ║
║  │ Time │ Event          │ Impact │ Act │ Fcst │ Prev │ ║
║  ├────────────────────────────────────────────────────┤ ║
║  │ 2pm  │ Federal Funds..│  HIGH  │  —  │ 4.00%│4.25% │ ║
║  │ ...  │ ...            │  ...   │ ... │ ...  │ ... │ ║
║  └────────────────────────────────────────────────────┘ ║
║                                                          ║
║  🤖 AI Market Analysis                                  ║
║  ┌────────────────────────────────────────────────────┐ ║
║  │ Q: Based on today's USD economic calendar events... │ ║
║  │                                                      │ ║
║  │ Today's USD economic calendar features several      │ ║
║  │ high-impact events, particularly the FOMC meeting   │ ║
║  │ and Federal Funds Rate decision at 2:00 PM EST...   │ ║
║  │                                                      │ ║
║  │ Key Trading Opportunities:                          │ ║
║  │ - Watch for volatility spikes during FOMC...        │ ║
║  │ - Consider tightening stops before 2 PM...          │ ║
║  └────────────────────────────────────────────────────┘ ║
╚══════════════════════════════════════════════════════════╝
```

---

## 💰 Cost Estimates

OpenAI API pricing (as of 2024):

**GPT-4 Turbo:**
- Input: $0.01 per 1K tokens
- Output: $0.03 per 1K tokens
- Estimated cost per analysis: $0.01 - $0.05

**GPT-4:**
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens
- Estimated cost per analysis: $0.03 - $0.10

**Daily cost:** ~$0.05 - $0.10 (one email per day)
**Monthly cost:** ~$1.50 - $3.00 (30 emails)

Check current pricing: https://openai.com/pricing

---

## 🔧 Troubleshooting

### "Error: Assistant response timed out"
- Your assistant may be taking too long
- Increase timeout in `openai_assistant.py` line 49: `max_wait = 120`
- Or simplify your questions

### "Error: Rate limit exceeded"
- You've hit OpenAI API rate limits
- Wait a few minutes and try again
- Upgrade your OpenAI plan for higher limits

### "Error: Invalid assistant ID"
- Double-check your Assistant ID starts with `asst_`
- Verify the assistant exists in your OpenAI dashboard

### "No AI analysis in email"
- Check that `ai_analysis.json` was created
- Verify environment variables are set correctly
- Check console output for errors

### "Assistant gives generic responses"
- Improve the assistant instructions
- Add more context in `questions.txt`
- Use GPT-4 instead of GPT-3.5

---

## 🎨 Customization

### Change AI Analysis Style

Edit assistant instructions in OpenAI dashboard:

```
You are a concise forex analyst. Provide:
1. 2-3 sentence summary of market impact
2. Specific trading setups (entry, stop, target)
3. Risk level (Low/Medium/High)
Keep responses under 200 words.
```

### Add More Questions

Edit `examples/questions.txt`:

```txt
What specific USD currency pairs should traders focus on today?

Provide exact entry and exit levels for one high-probability trade setup.

What time (EST) should traders be most cautious?
```

### Change Email Subject

```bash
python3 send_calendar_email.py \
  --subject "📊 Daily Forex Calendar + AI Analysis" \
  ...
```

---

## 🤖 Automation

### Daily at 7 AM with AI Analysis

```bash
crontab -e

# Add this line:
0 7 * * * export TO_EMAIL="you@example.com" SMTP_USER="bot@gmail.com" SMTP_PASSWORD="pass" OPENAI_API_KEY="sk-..." OPENAI_ASSISTANT_ID="asst_..." && cd /home/nmoiseykin/webpage-parser && ./send_calendar_with_ai.sh >> /tmp/forex_ai.log 2>&1
```

---

## 📝 Files

- `examples/openai_assistant.py` - AI assistant integration
- `examples/questions.txt` - Questions to ask the assistant
- `examples/ai_analysis.json` - AI responses (generated)
- `send_calendar_with_ai.sh` - Complete workflow script
- `send_calendar_email.py` - Email generator (updated with AI section)

---

## ✅ Quick Start Checklist

- [ ] Get OpenAI API key
- [ ] Create OpenAI Assistant (with web browsing enabled)
- [ ] Copy Assistant ID
- [ ] Set environment variables
- [ ] Customize questions in `questions.txt`
- [ ] Test with `./send_calendar_with_ai.sh`
- [ ] Check your email!
- [ ] Set up daily automation (optional)

---

## 🎉 You're Ready!

Your ForexFactory calendar emails now include AI-powered market analysis!

**Next steps:**
1. Test the system
2. Refine your questions
3. Adjust assistant instructions for better insights
4. Set up daily automation

Questions? Check the main documentation files or test each step manually.

