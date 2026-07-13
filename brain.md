Build a GitHub daily push reminder system with these specs:

GOAL: Check if I (GitHub username: Ghimire-Kushal) have pushed any commits today. 
If no push detected by my bedtime, send me a Telegram notification reminder. 
If I already pushed, stay silent.

REQUIREMENTS:
1. Language: Python (use `requests` library)
2. Use GitHub REST API endpoint: GET https://api.github.com/users/Ghimire-Kushal/events/public
   - Filter events where type == "PushEvent"
   - Check if created_at date matches today's date (local timezone: Asia/Kathmandu, UTC+5:45)
3. If a PushEvent exists for today → exit silently (log "Push found, no reminder needed")
4. If no PushEvent found → send a Telegram message via Telegram Bot API:
   - Use bot token and chat_id from environment variables (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
   - Message text: "🔴 Aaja push gareko chaina! Ek chotti commit garera streak jogaunu 💻"
5. Add proper error handling (API failure, rate limit, no internet)
6. Add logging to a local file (push_check.log) with timestamp of each check and result
7. Make it runnable via cron/launchd — structure it as a single standalone script (push_reminder.py)
8. Include a config section at top of file for: GITHUB_USERNAME, BEDTIME_HOUR (for reference/logging only, actual scheduling done externally via cron), TIMEZONE

ALSO PROVIDE:
- Step-by-step instructions to create a free Telegram bot (via BotFather) and get chat_id
- The exact launchd .plist file (macOS) OR crontab entry (Linux) to run this script daily at 10:30 PM Nepal time
- Instructions to set environment variables securely (not hardcoded in script)

Keep code clean, commented, and beginner-friendly to modify later (e.g. changing bedtime or adding multiple repos check for private repos with a personal access token).