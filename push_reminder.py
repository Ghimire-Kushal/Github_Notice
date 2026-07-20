#!/usr/bin/env python3
"""
GitHub Daily Push Reminder
---------------------------
Checks whether GITHUB_USERNAME has pushed a commit today (in TIMEZONE).
Sends a Telegram update either way: a reminder if there is no push yet,
or a confirmation if today's push is already done.

Run this twice daily (e.g. 8 AM and 8 PM) via cron/launchd (see README instructions).
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta

import requests

# ============================================================
# CONFIG — edit these to customize behavior
# ============================================================
GITHUB_USERNAME = "Ghimire-Kushal"

# Only used for logging/reference — actual run time is controlled by cron/launchd.
BEDTIME_HOUR = 22  # 24-hour format, e.g. 22 = 10 PM

# Nepal Standard Time is UTC+5:45 and has no DST, so a fixed offset is safe.
TIMEZONE = timezone(timedelta(hours=5, minutes=45), name="Asia/Kathmandu")

# For private repos, GitHub's public events API won't show pushes.
# Set a Personal Access Token (repo scope) in env var GITHUB_TOKEN to
# use the authenticated /users/{username}/events endpoint instead, which
# includes private activity you have access to.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # optional

# Telegram credentials — set these as environment variables, never hardcode.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

REMINDER_MESSAGE = "🔴 Aaja push gareko chaina! Ek chotti commit garera streak jogaunu 💻"
PUSHED_MESSAGE = "✅ Aaja push bhaisakyo! Streak safe chha 🔥"

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "push_check.log")

GITHUB_API_TIMEOUT = 10  # seconds
TELEGRAM_API_TIMEOUT = 10  # seconds

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def get_github_events_url(username: str) -> str:
    """Use authenticated endpoint if a token is present (includes private repo
    activity you have access to); otherwise use the public events endpoint."""
    if GITHUB_TOKEN:
        return f"https://api.github.com/users/{username}/events"
    return f"https://api.github.com/users/{username}/events/public"


def fetch_github_events(username: str) -> list:
    """Fetch recent public events for the given GitHub user."""
    url = get_github_events_url(username)
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = requests.get(url, headers=headers, timeout=GITHUB_API_TIMEOUT)

    if response.status_code == 403:
        raise RuntimeError(
            "GitHub API rate limit exceeded or access forbidden. "
            "Consider setting GITHUB_TOKEN to raise your rate limit."
        )
    response.raise_for_status()
    return response.json()


def has_pushed_today(events: list, today_local: datetime.date) -> bool:
    """Return True if any PushEvent's created_at falls on today's local date."""
    for event in events:
        if event.get("type") != "PushEvent":
            continue

        created_at_str = event.get("created_at")
        if not created_at_str:
            continue

        # GitHub timestamps look like "2026-07-13T10:15:30Z" (UTC).
        created_at_utc = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        created_at_local = created_at_utc.astimezone(TIMEZONE)

        if created_at_local.date() == today_local:
            return True

    return False


def send_telegram_message(message: str) -> None:
    """Send a message via the Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID environment variables are not set."
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    response = requests.post(url, data=payload, timeout=TELEGRAM_API_TIMEOUT)
    response.raise_for_status()


def main() -> int:
    logger.info(
        "Starting push check for '%s' (bedtime reference: %02d:00 %s)",
        GITHUB_USERNAME,
        BEDTIME_HOUR,
        TIMEZONE,
    )

    today_local = datetime.now(TIMEZONE).date()

    try:
        events = fetch_github_events(GITHUB_USERNAME)
    except requests.exceptions.ConnectionError:
        logger.error("No internet connection / could not reach GitHub API. Aborting check.")
        return 1
    except requests.exceptions.Timeout:
        logger.error("GitHub API request timed out. Aborting check.")
        return 1
    except (requests.exceptions.RequestException, RuntimeError) as exc:
        logger.error("GitHub API error: %s", exc)
        return 1

    try:
        pushed_today = has_pushed_today(events, today_local)
    except Exception as exc:  # malformed API response, etc.
        logger.error("Error while parsing GitHub events: %s", exc)
        return 1

    if pushed_today:
        logger.info("Push found. Sending confirmation update.")
        message = PUSHED_MESSAGE
    else:
        logger.info("No push found for today. Attempting to send Telegram reminder.")
        message = REMINDER_MESSAGE

    try:
        send_telegram_message(message)
        logger.info("Telegram update sent successfully.")
    except requests.exceptions.ConnectionError:
        logger.error("No internet connection / could not reach Telegram API.")
        return 1
    except requests.exceptions.Timeout:
        logger.error("Telegram API request timed out.")
        return 1
    except (requests.exceptions.RequestException, RuntimeError) as exc:
        logger.error("Telegram API error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
