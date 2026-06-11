#!/usr/bin/env python3
"""Add default traffic_tb to all plans in provider_plans.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANS_PATH = ROOT / "app" / "provider_plans.json"

DEFAULTS = [1, 2, 5]


def main() -> None:
    with PLANS_PATH.open(encoding="utf-8-sig") as file:
        payload = json.load(file)
    plans_by_domain = payload.get("plans_by_domain", {})
    for domain, plans in plans_by_domain.items():
        for index, plan in enumerate(plans):
            if plan.get("traffic_unlimited"):
                continue
            if plan.get("traffic_tb") is None:
                plan["traffic_tb"] = DEFAULTS[min(index, len(DEFAULTS) - 1)]
    payload["prices_as_of"] = payload.get("prices_as_of") or "2026-06-11"
    with PLANS_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"Updated {len(plans_by_domain)} providers")


if __name__ == "__main__":
    main()
