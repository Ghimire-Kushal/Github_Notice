# GitHub Daily Push Reminder — Setup Guide

## 1. Create a Telegram bot (via BotFather)

1. Open Telegram, search for **@BotFather**, and start a chat.
2. Send `/newbot` and follow the prompts (choose a name and a username ending in `bot`).
3. BotFather replies with a **bot token** like `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`.
   This is your `TELEGRAM_BOT_TOKEN`.
4. Send at least one message to your new bot (e.g. "hi") from your personal Telegram account —
   this is required so the bot can message you back.
5. Get your **chat_id**:
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in a browser
     (replace `<YOUR_BOT_TOKEN>` with your real token).
   - Look for `"chat":{"id":123456789,...}` in the JSON response — that number is your
     `TELEGRAM_CHAT_ID`.
   - If the response is empty, make sure you sent a message to the bot first, then refresh.

## 2. Set environment variables securely

Never hardcode secrets in the script. Add them to your shell profile
(`~/.zshrc` for macOS default shell) or a dedicated env file loaded by cron/launchd.

```bash
# ~/.zshrc (or ~/.bash_profile)
export TELEGRAM_BOT_TOKEN="your-bot-token-here![alt text](image.png)"
export TELEGRAM_CHAT_ID="your-chat-id-here"
# Optional, only needed if you want private-repo push detection:
# export GITHUB_TOKEN="your-personal-access-token"
```

Then reload: `source ~/.zshrc`

launchd does NOT read your shell profile, so for scheduled runs you must
supply the env vars directly in the `.plist` file (see below) — put the
plist in a private location (not committed to any public repo) since it
will contain your secrets in plain text.

## 3. Install dependencies

```bash
pip3 install requests
```

## 4. Run manually to test

```bash
python3 /Users/Project/GithubNotice/push_reminder.py
```

Check `push_check.log` in the same folder for output.

## 5. Schedule with launchd (macOS) — runs daily at 10:30 PM Nepal time

Nepal time is UTC+5:45 with no DST. Convert 22:30 Asia/Kathmandu to your
Mac's local time zone before filling in `Hour`/`Minute` below — launchd
schedules in the machine's local time zone, not Nepal time. For example,
if your Mac is set to US Eastern (UTC-4 during DST), 22:30 NPT is 12:45
the same day US Eastern. Adjust the numbers to match your actual system
clock (run `date` to check your Mac's current local time zone).

Create `~/Library/LaunchAgents/com.kushal.pushreminder.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kushal.pushreminder</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/Project/GithubNotice/push_reminder.py</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>TELEGRAM_BOT_TOKEN</key>
        <string>your-bot-token-here</string>
        <key>TELEGRAM_CHAT_ID</key>
        <string>your-chat-id-here</string>
    </dict>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>22</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/Project/GithubNotice/launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Project/GithubNotice/launchd_stderr.log</string>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.kushal.pushreminder.plist
```

To unload (disable):

```bash
launchctl unload ~/Library/LaunchAgents/com.kushal.pushreminder.plist
```

To test immediately without waiting for the schedule:

```bash
launchctl start com.kushal.pushreminder
```

## 5b. Alternative: crontab (Linux, or macOS if you prefer cron)

Nepal time UTC+5:45 has no clean cron equivalent unless your system's
`TZ` is set to Asia/Kathmandu. The safest approach is to set `TZ` inline
in the crontab line:

```
# Edit with: crontab -e
30 22 * * * TZ="Asia/Kathmandu" TELEGRAM_BOT_TOKEN="your-bot-token-here" TELEGRAM_CHAT_ID="your-chat-id-here" /usr/bin/python3 /Users/Project/GithubNotice/push_reminder.py >> /Users/Project/GithubNotice/cron_stdout.log 2>&1
```

If your cron daemon doesn't honor a per-line `TZ=`, set it at the top of
the crontab instead:

```
TZ=Asia/Kathmandu
30 22 * * * TELEGRAM_BOT_TOKEN="your-bot-token-here" TELEGRAM_CHAT_ID="your-chat-id-here" /usr/bin/python3 /Users/Project/GithubNotice/push_reminder.py >> /Users/Project/GithubNotice/cron_stdout.log 2>&1
```

## 6. Customizing later

- **Change bedtime**: edit `BEDTIME_HOUR` in `push_reminder.py` (for reference/logging only)
  and update the `Hour`/`Minute` in the plist or crontab entry to match.
- **Check private repos**: set the `GITHUB_TOKEN` environment variable to a
  Personal Access Token with `repo` scope (create one at
  https://github.com/settings/tokens). The script automatically switches
  to the authenticated `/users/{username}/events` endpoint when this is set,
  which includes private activity you have access to.
- **Multiple repos / orgs**: the events API already aggregates all push
  activity for the user across repos they have access to, so no per-repo
  change is needed — just make sure `GITHUB_TOKEN` has access if they're private.
