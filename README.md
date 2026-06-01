# AI Agents

Python workspace for practicing AI agent patterns.

## Setup

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy environment variables:

```bash
cp .env.example .env
```

Add your Supabase anon key to `.env`:

```bash
SUPABASE_URL=https://zhvzzsscjdwxtylshgji.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

Run the starter agent:

```bash
python agents/starter_agent.py
```

Check Supabase client setup:

```bash
python agents/supabase_smoke_test.py
```

Create the first test table in Supabase:

```bash
# Paste database/agent_logs.sql into the Supabase SQL editor and run it.
```

Insert a test log row:

```bash
python agents/write_agent_log.py "First log from Python"
```

## WhatsApp YouTube Email Agent

This agent receives a WhatsApp message through Twilio, searches YouTube, and emails the best result through Gmail SMTP.

Add these values to `.env`:

```bash
YOUTUBE_API_KEY=your-youtube-data-api-key
GMAIL_ADDRESS=your-gmail-address@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
EMAIL_TO=where-to-send-results@example.com
WHATSAPP_ALLOWED_FROM=whatsapp:+353...
```

Run the webhook locally:

```bash
python agents/whatsapp_youtube_email_agent.py
```

Expose it with a tunnel such as ngrok, then set your Twilio WhatsApp sandbox webhook to:

```text
https://your-public-url.ngrok-free.app/whatsapp
```

Example WhatsApp message:

```text
find me best video on learning python on youtube
```

## Telegram YouTube Email Bot

This bot receives a Telegram message, searches YouTube, and emails the result. It can run locally without Twilio or WhatsApp.

Create a bot in Telegram:

```text
Open Telegram -> message @BotFather -> /newbot
```

Add the bot token to `.env`:

```bash
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_ALLOWED_CHAT_ID=
```

Run the bot:

```bash
python agents/telegram_youtube_email_bot.py
```

Then message your bot:

```text
find me best video on learning python on youtube send to person@example.com
```

You can send to multiple addresses in the same Telegram message:

```text
find me best video on AI agents on youtube send to person@example.com and teammate@example.com
```

## Vercel Telegram Webhook

Vercel can host the Telegram bot as a webhook at:

```text
https://your-vercel-app.vercel.app/api/telegram
```

Add these environment variables in Vercel:

```bash
YOUTUBE_API_KEY=
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
EMAIL_TO=
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_CHAT_ID=
```

`EMAIL_TO` is the fallback recipient if the Telegram message does not include an email address. You can set it to one address or multiple comma-separated addresses.

After deployment, register the Telegram webhook:

```bash
python agents/set_telegram_webhook.py https://your-vercel-app.vercel.app/api/telegram
```

You can check the deployed endpoint in a browser:

```text
https://your-vercel-app.vercel.app/api/telegram
```

## Structure

- `agents/` - individual practice agents.
- `api/` - Vercel serverless webhook functions.
- `database/` - SQL setup scripts for Supabase tables and policies.
- `shared/` - reusable helpers as your agents become more advanced.
- `.env.example` - template for secrets and config.
- `requirements.txt` - Python dependencies.
