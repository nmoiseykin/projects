# How to Add OpenAI Environment Variables to AWS Lambda

## Quick Fix: Add OpenAI Environment Variables

The Lambda function works but is skipping AI analysis because these environment variables are missing:

- `OPENAI_API_KEY`
- `OPENAI_ASSISTANT_ID`

## Steps in AWS Console

1. **Go to AWS Lambda Console**
   - Navigate to your Lambda function (e.g., `forex-calendar-daily`)

2. **Open Configuration Tab**
   - Click on **"Configuration"** tab
   - Click on **"Environment variables"** in the left sidebar

3. **Add Environment Variables**
   - Click **"Edit"** button
   - Click **"Add environment variable"** for each one:

   **First Variable:**
   - Key: `OPENAI_API_KEY`
   - Value: `sk-your-openai-api-key`

   **Second Variable:**
   - Key: `OPENAI_ASSISTANT_ID`
   - Value: `asst_your_openai_assistant_id`

4. **Save**
   - Click **"Save"** button at the bottom

## Verification

After saving, test the function again:
1. Go to **"Test"** tab
2. Click **"Test"** button
3. Check CloudWatch Logs - you should see:
   - `OPENAI enabled: True`
   - `STEP 2: Getting AI Analysis`
   - Instead of `⏭️ Skipping AI analysis (not configured)`

## Current Environment Variables (Complete List)

Your Lambda function should have these environment variables:

```
TO_EMAIL=you@example.com
SMTP_USER=your_gmail_account@gmail.com
SMTP_PASSWORD=your_app_specific_password
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_ASSISTANT_ID=asst_your_openai_assistant_id
```

## Security Note

These environment variables are encrypted at rest in AWS Lambda. However, for production, consider using:
- **AWS Secrets Manager** for sensitive values like API keys
- **AWS Systems Manager Parameter Store** as an alternative

For now, environment variables work fine and are simpler to manage.

## After Adding Variables

Once you add the OpenAI variables, test the function again. The email should now include an "AI Market Analysis" section with insights about today's USD economic events!

