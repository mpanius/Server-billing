#!/usr/bin/env python3
"""Download flat SVG flags into app/static/flags/."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_PATH = ROOT / "app" / "provider_countries.json"
FLAGS_DIR = ROOT / "app" / "static" / "flags"
SOURCE = "https://flagcdn.com/{code}.svg"


def main() -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    with COUNTRIES_PATH.open(encoding="utf-8-sig") as file:
        payload = json.load(file)
    codes = list(payload.get("countries", {}).keys())
    for code in codes:
        target = FLAGS_DIR / f"{code.lower()}.svg"
        if target.exists() and target.stat().st_size > 100:
            continue
        url = SOURCE.format(code=code.lower())
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                target.write_bytes(response.read())
            print(f"OK {code}")
        except Exception as error:
            print(f"FAIL {code}: {error}")


if __name__ == "__main__":
    main()
