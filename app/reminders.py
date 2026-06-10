from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from datetime import date

from app.config import settings
from app.db import connect
from app.models import Server
from app.repository import list_servers
from app.telegram import build_payment_deeplink

logger = logging.getLogger(__name__)


def reminder_days() -> set[int]:
    raw = getattr(settings, "reminder_days", "7,3,1,0")
    days: set[int] = set()
    for value in raw.split(","):
        value = value.strip()
        if value:
            days.add(int(value))
    return days


def ensure_notification_log() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                reminder_key TEXT NOT NULL,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(server_id, channel, reminder_key)
            )
            """
        )


def was_sent(server: Server, reminder_key: str) -> bool:
    ensure_notification_log()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id FROM notification_log
            WHERE server_id = ? AND channel = 'telegram' AND reminder_key = ?
            """,
            (server.id, reminder_key),
        ).fetchone()
    return row is not None


def mark_sent(server: Server, reminder_key: str) -> None:
    ensure_notification_log()
    with connect() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO notification_log (server_id, channel, reminder_key)
            VALUES (?, 'telegram', ?)
            """,
            (server.id, reminder_key),
        )


def reminder_key(server: Server) -> str:
    return f"{server.next_payment_date.isoformat()}:{server.days_left}"


def build_message(server: Server) -> str:
    amount = f"{server.amount:g} {server.currency}"
    due = server.next_payment_date.strftime("%d.%m.%Y")
    if server.days_left < 0:
        state = f"просрочено на {-server.days_left} дн."
    elif server.days_left == 0:
        state = "оплата сегодня"
    else:
        state = f"осталось {server.days_left} дн."

    return (
        "Скоро оплата сервера\n\n"
        f"{server.name}\n"
        f"Провайдер: {server.provider}\n"
        f"Аккаунт: {server.account_name or 'не привязан'}\n"
        f"IP: {server.ip_address or 'не указан'}\n"
        f"Сумма: {amount}\n"
        f"Оплатить до: {due} ({state})\n\n"
        f"Открыть оплату: {build_payment_deeplink(server)}"
    )


def send_telegram(text: str) -> bool:
    token = settings.telegram_bot_token.strip()
    chat_id = settings.telegram_chat_id.strip()
    if not token or not chat_id:
        logger.info("Telegram token or chat id is empty; reminders are disabled.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode()
    request = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        parsed = json.loads(body)
        if not parsed.get("ok"):
            raise RuntimeError(body)
    return True


def send_due_reminders() -> int:
    due_days = reminder_days()
    sent = 0
    for server in list_servers():
        if server.days_left not in due_days and server.days_left >= 0:
            continue
        if server.days_left < 0 and -1 not in due_days:
            continue

        key = reminder_key(server)
        if was_sent(server, key):
            continue

        if send_telegram(build_message(server)):
            mark_sent(server, key)
            sent += 1
    return sent


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("Reminder worker started.")
    interval = int(getattr(settings, "check_interval_seconds", 86400))
    while True:
        try:
            sent = send_due_reminders()
            logger.info("Reminder check finished. Sent: %s. Date: %s", sent, date.today())
        except Exception:
            logger.exception("Reminder check failed.")
        time.sleep(interval)


if __name__ == "__main__":
    main()
