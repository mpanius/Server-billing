from __future__ import annotations

import ipaddress

from fastapi import Request, WebSocket

from app.config import settings
from app.repository import get_app_setting

ALLOWLIST_KEY = "panel_ip_allowlist"

LOCALHOST_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
)


def panel_ip_allowlist_text() -> str:
    return get_app_setting(ALLOWLIST_KEY, settings.panel_ip_allowlist or "").strip()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    if request.client and request.client.host:
        return request.client.host
    return ""


def client_ip_from_websocket(websocket: WebSocket) -> str:
    forwarded = websocket.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = websocket.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    if websocket.client and websocket.client.host:
        return websocket.client.host
    return ""


def parse_allowlist(text: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network | ipaddress.IPv4Address | ipaddress.IPv6Address]:
    entries: list[
        ipaddress.IPv4Network | ipaddress.IPv6Network | ipaddress.IPv4Address | ipaddress.IPv6Address
    ] = []
    for raw in text.replace(",", "\n").split("\n"):
        item = raw.strip()
        if not item or item.startswith("#"):
            continue
        if "/" in item:
            entries.append(ipaddress.ip_network(item, strict=False))
        else:
            entries.append(ipaddress.ip_address(item))
    return entries


def normalize_allowlist(text: str) -> tuple[str, list[str]]:
    errors: list[str] = []
    lines: list[str] = []
    for raw in text.replace(",", "\n").split("\n"):
        item = raw.strip()
        if not item or item.startswith("#"):
            continue
        try:
            if "/" in item:
                ipaddress.ip_network(item, strict=False)
            else:
                ipaddress.ip_address(item)
        except ValueError:
            errors.append(item)
            continue
        lines.append(item)
    return "\n".join(lines), errors


def is_localhost(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(addr in network for network in LOCALHOST_NETWORKS)


def is_address_allowed(addr_text: str, allowlist_text: str | None = None) -> bool:
    text = panel_ip_allowlist_text() if allowlist_text is None else allowlist_text.strip()
    if not text:
        return True
    if not addr_text:
        return False
    try:
        addr = ipaddress.ip_address(addr_text)
    except ValueError:
        return False
    if is_localhost(addr):
        return True
    for entry in parse_allowlist(text):
        if isinstance(entry, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            if addr in entry:
                return True
        elif addr == entry:
            return True
    return False


def is_ip_allowed(request: Request) -> bool:
    return is_address_allowed(client_ip(request))


def is_websocket_ip_allowed(websocket: WebSocket) -> bool:
    return is_address_allowed(client_ip_from_websocket(websocket))
