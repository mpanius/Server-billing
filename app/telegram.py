from __future__ import annotations

import json
import urllib.parse
import urllib.request
from urllib.parse import quote_plus

from app.config import settings
from app.models import Server
from app.repository import get_effective_setting


def build_payment_deeplink(server: Server) -> str:
    base_url = get_effective_setting("base_url", settings.base_url).rstrip("/")
    return f"{base_url}/servers/{server.id}/pay"


def build_reminder_text(server: Server) -> str:
    amount = f"{server.amount:g} {server.currency}"
    due = server.next_payment_date.strftime("%d.%m.%Y")
    return (
        "Скоро оплата сервера\n\n"
        f"{server.name}\n"
        f"Провайдер: {server.provider}\n"
        f"IP: {server.ip_address or 'не указан'}\n"
        f"Сумма: {amount}\n"
        f"Оплатить до: {due}\n"
        f"Осталось дней: {server.days_left}\n\n"
        f"Открыть оплату: {build_payment_deeplink(server)}"
    )


def build_telegram_share_url(server: Server) -> str:
    text = quote_plus(build_reminder_text(server))
    return f"https://t.me/share/url?url={quote_plus(build_payment_deeplink(server))}&text={text}"


def telegram_api(token: str, method: str, params: dict[str, object] | None = None) -> dict[str, object]:
    base = f"https://api.telegram.org/bot{token}/{method}"
    url = base
    if params:
        url = f"{base}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok"):
        raise RuntimeError(str(payload))
    return payload


def telegram_get(token: str, method: str) -> dict[str, object]:
    return telegram_api(token, method)


def telegram_bot_username(token: str) -> str:
    payload = telegram_get(token, "getMe")
    result = payload.get("result") or {}
    username = result.get("username") if isinstance(result, dict) else ""
    return f"@{username}" if username else "подключен"


def telegram_bot_link(username: str) -> str:
    handle = (username or "").strip().lstrip("@")
    if not handle:
        return ""
    return f"https://t.me/{handle}?start=panel"


def ensure_telegram_polling(token: str) -> bool:
    """Remove webhook so getUpdates can read incoming messages."""
    payload = telegram_api(token, "deleteWebhook", {"drop_pending_updates": "false"})
    return bool(payload.get("ok"))


def _chat_type_label(chat_type: str) -> str:
    labels = {
        "private": "личный чат",
        "group": "группа",
        "supergroup": "супергруппа",
        "channel": "канал",
    }
    return labels.get(chat_type, chat_type or "чат")


def _chat_title(chat: dict[str, object]) -> str:
    if chat.get("title"):
        return str(chat["title"])
    username = chat.get("username")
    if username:
        return f"@{username}"
    parts = [str(part) for part in (chat.get("first_name"), chat.get("last_name")) if part]
    return " ".join(parts) or "Личный чат"


def _chat_from_update(item: dict[str, object]) -> dict[str, object] | None:
    for key in ("message", "edited_message", "channel_post", "my_chat_member"):
        block = item.get(key)
        if not isinstance(block, dict):
            continue
        chat = block.get("chat")
        if isinstance(chat, dict) and chat.get("id") is not None:
            return chat
    return None


def detect_telegram_chats(token: str) -> list[dict[str, str]]:
    ensure_telegram_polling(token)
    payload = telegram_api(
        token,
        "getUpdates",
        {
            "limit": 100,
            "timeout": 0,
            "allowed_updates": json.dumps(
                ["message", "edited_message", "channel_post", "my_chat_member"],
            ),
        },
    )
    updates = payload.get("result") or []
    chats: dict[str, dict[str, str]] = {}
    for item in updates:
        if not isinstance(item, dict):
            continue
        chat = _chat_from_update(item)
        if not chat:
            continue
        chat_id = str(chat["id"])
        chat_type = str(chat.get("type") or "chat")
        chats[chat_id] = {
            "id": chat_id,
            "title": _chat_title(chat),
            "type": chat_type,
            "type_label": _chat_type_label(chat_type),
        }
    return list(chats.values())
