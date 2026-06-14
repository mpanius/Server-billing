from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.config import settings
from app.connectors import ConnectorError
from app.url_safety import assert_update_service_url


def start_system_update() -> tuple[bool, str]:
    if not settings.app_update_url or not settings.app_update_token:
        return False, "Update service is not configured."
    if len(settings.app_update_token.strip()) < 32:
        return False, "APP_UPDATE_TOKEN слишком короткий (минимум 32 символа)."

    try:
        assert_update_service_url(settings.app_update_url, context="APP_UPDATE_URL")
    except ConnectorError as error:
        return False, str(error)

    request = urllib.request.Request(
        settings.app_update_url,
        data=b"{}",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Update-Token": settings.app_update_token,
            "User-Agent": "server-billing-manager/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read()[:200].decode("utf-8", errors="ignore").strip()
        if error.code == 403:
            return False, "Updater отклонил токен (403). Проверьте APP_UPDATE_TOKEN в .env."
        return False, f"Updater HTTP {error.code}: {detail or error.reason}"
    except urllib.error.URLError as error:
        return False, f"Не удалось связаться с updater: {error.reason}"
    return bool(payload.get("ok")), str(payload.get("message", ""))
