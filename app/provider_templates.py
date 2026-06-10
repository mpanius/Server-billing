from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


TEMPLATES_PATH = Path(__file__).with_name("provider_templates.json")


@lru_cache(maxsize=1)
def list_provider_templates() -> list[dict[str, object]]:
    with TEMPLATES_PATH.open(encoding="utf-8-sig") as file:
        providers = json.load(file)
    return sorted(providers, key=lambda item: str(item["name"]).lower())
