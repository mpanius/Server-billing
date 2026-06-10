from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


def parse_rates(raw: str) -> dict[str, float]:
    rates = {"RUB": 1.0}
    root = ET.fromstring(raw)
    for item in root.findall("Valute"):
        code = item.findtext("CharCode", "").strip().upper()
        nominal = float(item.findtext("Nominal", "1").replace(",", "."))
        value = float(item.findtext("Value", "0").replace(",", "."))
        if code and nominal:
            rates[code] = value / nominal
    return rates


def fetch_cbr_rates() -> dict[str, float]:
    with urllib.request.urlopen(CBR_DAILY_URL, timeout=20) as response:
        raw = response.read().decode("windows-1251")
    return parse_rates(raw)


def rates_to_string(rates: dict[str, float]) -> str:
    return ",".join(f"{code}:{value:.8f}" for code, value in sorted(rates.items()))


def rates_from_string(value: str) -> dict[str, float]:
    rates = {"RUB": 1.0}
    for part in value.split(","):
        if ":" not in part:
            continue
        code, rate = part.split(":", 1)
        try:
            rates[code.strip().upper()] = float(rate)
        except ValueError:
            continue
    return rates


def today_label() -> str:
    return date.today().isoformat()
