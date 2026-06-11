from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import settings


APP_DIR = Path(__file__).resolve().parent
COUNTRIES_PATH = APP_DIR / "provider_countries.json"
CACHE_DIR = Path(settings.database_path).resolve().parent / "catalog_cache"
BUNDLE_CACHE = CACHE_DIR / "provider_bundle.json"


def _bundle_payload() -> dict[str, object] | None:
    if not BUNDLE_CACHE.exists():
        return None
    with BUNDLE_CACHE.open(encoding="utf-8-sig") as file:
        payload = json.load(file)
    return payload if isinstance(payload, dict) else None


@lru_cache(maxsize=1)
def country_catalog() -> dict[str, str]:
    bundle = _bundle_payload()
    if bundle and isinstance(bundle.get("countries"), dict):
        return {str(code): str(name) for code, name in bundle["countries"].items()}
    with COUNTRIES_PATH.open(encoding="utf-8-sig") as file:
        payload = json.load(file)
    raw = payload.get("countries") if isinstance(payload, dict) else {}
    return {str(code): str(name) for code, name in raw.items()} if isinstance(raw, dict) else {}


def country_flag_url(code: str) -> str:
    return f"/static/flags/{code.strip().lower()}.svg"


def country_label(code: str) -> dict[str, str] | None:
    catalog = country_catalog()
    name = catalog.get(code)
    if not name:
        return None
    return {"code": code, "name": name, "flag_url": country_flag_url(code)}


def country_labels(codes: list[str]) -> list[dict[str, str]]:
    labels = []
    for code in codes:
        item = country_label(code)
        if item:
            labels.append(item)
    return labels


def all_country_options() -> list[dict[str, str]]:
    catalog = country_catalog()
    return [
        {"code": code, "name": name, "flag_url": country_flag_url(code)}
        for code, name in sorted(catalog.items(), key=lambda item: item[1].lower())
    ]


def clear_country_catalog_cache() -> None:
    country_catalog.cache_clear()
