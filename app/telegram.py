from __future__ import annotations

from urllib.parse import quote_plus

from app.config import settings
from app.models import Server


def build_payment_deeplink(server: Server) -> str:
    return f"{settings.base_url.rstrip('/')}/servers/{server.id}/pay"


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
