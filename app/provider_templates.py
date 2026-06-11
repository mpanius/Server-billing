from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


TEMPLATES_PATH = Path(__file__).with_name("provider_templates.json")
CATALOG_PATH = Path(__file__).with_name("provider_catalog.json")

COUNTRY_LABELS = {
    "RU": {"name": "Россия", "flag": "🇷🇺"},
    "NL": {"name": "Нидерланды", "flag": "🇳🇱"},
    "DE": {"name": "Германия", "flag": "🇩🇪"},
    "FI": {"name": "Финляндия", "flag": "🇫🇮"},
    "FR": {"name": "Франция", "flag": "🇫🇷"},
    "PL": {"name": "Польша", "flag": "🇵🇱"},
    "GB": {"name": "Великобритания", "flag": "🇬🇧"},
    "US": {"name": "США", "flag": "🇺🇸"},
    "CA": {"name": "Канада", "flag": "🇨🇦"},
    "SG": {"name": "Сингапур", "flag": "🇸🇬"},
}

COUNTRIES_BY_DOMAIN = {
    "hetzner.com": ["DE", "FI", "US"],
    "digitalocean.com": ["US", "NL", "DE", "GB", "SG"],
    "vultr.com": ["US", "NL", "DE", "FR", "GB", "SG"],
    "linode.com": ["US", "DE", "GB", "SG"],
    "ovhcloud.com": ["FR", "DE", "PL", "GB", "CA", "US"],
    "scaleway.com": ["FR", "NL", "PL"],
    "contabo.com": ["DE", "US", "SG"],
    "timeweb.cloud": ["RU", "NL", "PL"],
    "selectel.ru": ["RU"],
    "reg.ru": ["RU"],
    "beget.com": ["RU"],
    "firstvds.ru": ["RU", "NL"],
    "vdsina.ru": ["RU"],
    "aeza.net": ["RU", "NL", "DE", "US"],
    "fornex.com": ["NL", "DE", "US"],
    "onlinevds.ru": ["RU"],
    "hostoff.net": ["RU", "NL"],
    "rdp-onedash.ru": ["RU"],
    "ruvds.com": ["RU", "NL"],
    "adminvps.ru": ["RU"],
    "zomro.com": ["NL", "DE", "PL"],
    "serverspace.ru": ["RU"],
    "mchost.ru": ["RU"],
    "sprinthost.ru": ["RU"],
    "eurohoster.org": ["NL", "DE", "PL"],
    "ispserver.com": ["RU", "NL"],
    "ionos.com": ["DE", "US", "GB"],
    "hostinger.com": ["US", "NL", "DE", "GB", "SG"],
    "aws.amazon.com": ["US", "DE", "GB", "SG"],
    "cloud.google.com": ["US", "NL", "DE", "SG"],
    "kamatera.com": ["US", "NL", "DE", "SG"],
    "upcloud.com": ["FI", "DE", "US", "SG"],
    "cherryservers.com": ["NL", "DE", "US"],
    "leaseweb.com": ["NL", "DE", "US", "SG"],
    "4vps.su": ["RU", "NL", "DE", "US", "FI", "FR"],
}

PRICE_HINT_BY_DOMAIN = {
    "hetzner.com": "от €4.15/мес",
    "digitalocean.com": "от $4/мес",
    "vultr.com": "от $2.50/мес",
    "linode.com": "от $5/мес",
    "ovhcloud.com": "тариф на сайте",
    "scaleway.com": "тариф на сайте",
    "contabo.com": "тариф на сайте",
    "timeweb.cloud": "тариф на сайте",
    "selectel.ru": "тариф на сайте",
    "reg.ru": "тариф на сайте",
    "beget.com": "тариф на сайте",
    "firstvds.ru": "тариф на сайте",
    "vdsina.ru": "тариф на сайте",
    "aeza.net": "тариф на сайте",
    "fornex.com": "тариф на сайте",
    "onlinevds.ru": "от ~500 ₽/мес",
    "hostoff.net": "тариф на сайте",
    "rdp-onedash.ru": "тариф на сайте",
    "ruvds.com": "от ~200 ₽/мес",
    "adminvps.ru": "тариф на сайте",
    "zomro.com": "тариф на сайте",
    "serverspace.ru": "тариф на сайте",
    "mchost.ru": "тариф на сайте",
    "sprinthost.ru": "тариф на сайте",
    "eurohoster.org": "тариф на сайте",
    "ispserver.com": "тариф на сайте",
    "ionos.com": "от €4/мес",
    "hostinger.com": "от $4/мес",
    "aws.amazon.com": "от $3.50/мес",
    "cloud.google.com": "по факту использования",
    "kamatera.com": "от $4/мес",
    "upcloud.com": "от $5/мес",
    "cherryservers.com": "тариф на сайте",
    "leaseweb.com": "тариф на сайте",
    "4vps.su": "от ~90 ₽/мес",
}

API_DOCS_BY_DOMAIN = {
    "hetzner.com": "https://docs.hetzner.cloud/",
    "digitalocean.com": "https://docs.digitalocean.com/reference/api/",
    "vultr.com": "https://www.vultr.com/api/",
    "linode.com": "https://techdocs.akamai.com/linode-api/reference/api",
    "ovhcloud.com": "https://api.ovh.com/",
    "scaleway.com": "https://www.scaleway.com/en/developers/api/",
    "selectel.ru": "https://docs.selectel.ru/api/",
    "timeweb.cloud": "https://timeweb.cloud/api-docs",
    "aws.amazon.com": "https://docs.aws.amazon.com/lightsail/",
    "cloud.google.com": "https://cloud.google.com/compute/docs/reference/rest/v1",
    "4vps.su": "https://4vps.su/page/api",
}

PLANS_BY_DOMAIN: dict[str, list[dict[str, object]]] = {
    "hetzner.com": [
        {"name": "CX22", "price": 4.15, "currency": "EUR", "cpu": 2, "ram_gb": 4, "storage_gb": 40},
        {"name": "CX32", "price": 6.8, "currency": "EUR", "cpu": 4, "ram_gb": 8, "storage_gb": 80},
        {"name": "CX42", "price": 12.8, "currency": "EUR", "cpu": 8, "ram_gb": 16, "storage_gb": 160},
    ],
    "digitalocean.com": [
        {"name": "Basic 1 GB", "price": 4.0, "currency": "USD", "cpu": 1, "ram_gb": 1, "storage_gb": 25},
        {"name": "Basic 2 GB", "price": 6.0, "currency": "USD", "cpu": 1, "ram_gb": 2, "storage_gb": 50},
        {"name": "Basic 4 GB", "price": 12.0, "currency": "USD", "cpu": 2, "ram_gb": 4, "storage_gb": 80},
    ],
    "vultr.com": [
        {"name": "Cloud Compute", "price": 2.5, "currency": "USD", "cpu": 1, "ram_gb": 0.5, "storage_gb": 10},
        {"name": "Cloud Compute", "price": 5.0, "currency": "USD", "cpu": 1, "ram_gb": 1, "storage_gb": 25},
        {"name": "Cloud Compute", "price": 10.0, "currency": "USD", "cpu": 2, "ram_gb": 2, "storage_gb": 55},
    ],
    "aeza.net": [
        {"name": "SWE-PROMO", "price_label": "от €3.6/мес", "cpu": 1, "ram_gb": 2, "storage_gb": 30},
        {"name": "SWE-BASE", "price_label": "от €5/мес", "cpu": 2, "ram_gb": 4, "storage_gb": 60},
    ],
    "timeweb.cloud": [
        {"name": "Cloud-15", "price_label": "от ~450 ₽/мес", "cpu": 1, "ram_gb": 1, "storage_gb": 15},
        {"name": "Cloud-30", "price_label": "от ~700 ₽/мес", "cpu": 2, "ram_gb": 2, "storage_gb": 30},
    ],
    "ruvds.com": [
        {"name": "Start", "price_label": "от ~200 ₽/мес", "cpu": 1, "ram_gb": 0.5, "storage_gb": 10},
        {"name": "Standart", "price_label": "от ~400 ₽/мес", "cpu": 1, "ram_gb": 1, "storage_gb": 20},
    ],
    "4vps.su": [
        {"name": "VPS Start", "price_label": "от ~90 ₽/мес", "cpu": 1, "ram_gb": 1, "storage_gb": 10},
        {"name": "VPS Pro", "price_label": "от ~300 ₽/мес", "cpu": 2, "ram_gb": 2, "storage_gb": 30},
        {"name": "Dedicated", "price_label": "от 1500 ₽/мес", "cpu": 4, "ram_gb": 8, "storage_gb": 120},
    ],
    "onlinevds.ru": [
        {"name": "VDS Start", "price_label": "от ~500 ₽/мес", "cpu": 1, "ram_gb": 1, "storage_gb": 20},
        {"name": "VDS Pro", "price_label": "тариф на сайте", "cpu": 2, "ram_gb": 2, "storage_gb": 40},
    ],
}


def _normalize_plans(provider: dict[str, object]) -> list[dict[str, object]]:
    domain = str(provider.get("domain", ""))
    plans = provider.get("plans") or PLANS_BY_DOMAIN.get(domain) or []
    if plans:
        return list(plans)
    hint = str(provider.get("price_hint") or PRICE_HINT_BY_DOMAIN.get(domain, "тариф на сайте"))
    return [{"name": "Старт", "price_label": hint}]


def _enrich_provider(provider: dict[str, object]) -> dict[str, object]:
    domain = str(provider.get("domain", ""))
    countries = COUNTRIES_BY_DOMAIN.get(domain, [])
    provider["countries"] = countries
    provider["country_labels"] = [COUNTRY_LABELS[code] for code in countries if code in COUNTRY_LABELS]
    provider["price_hint"] = PRICE_HINT_BY_DOMAIN.get(domain, "тариф на сайте")
    provider["visit_url"] = str(provider.get("referral_url") or provider.get("website_url") or "")
    provider["plans"] = _normalize_plans(provider)
    provider["api_docs_url"] = str(provider.get("api_docs_url") or API_DOCS_BY_DOMAIN.get(domain, ""))
    provider["integration_type"] = str(provider.get("integration_type") or "manual")
    provider["promo_text"] = str(provider.get("promo_text") or "")
    provider["sponsored"] = bool(provider.get("sponsored"))
    provider["featured"] = bool(provider.get("featured"))
    return provider


@lru_cache(maxsize=1)
def list_provider_templates() -> list[dict[str, object]]:
    with TEMPLATES_PATH.open(encoding="utf-8-sig") as file:
        providers = json.load(file)
    enriched = [_enrich_provider(dict(provider)) for provider in providers]
    return sorted(enriched, key=lambda item: str(item["name"]).lower())


def provider_countries(providers: list[dict[str, object]] | None = None) -> list[dict[str, str]]:
    providers = providers or list_provider_templates()
    codes = sorted({code for provider in providers for code in provider.get("countries", [])})
    return [
        {"code": code, "name": COUNTRY_LABELS[code]["name"], "flag": COUNTRY_LABELS[code]["flag"]}
        for code in codes
        if code in COUNTRY_LABELS
    ]


@lru_cache(maxsize=1)
def provider_catalog_meta() -> dict[str, object]:
    if not CATALOG_PATH.exists():
        return {"notice": "", "promos": []}
    with CATALOG_PATH.open(encoding="utf-8-sig") as file:
        payload = json.load(file)
    return {
        "notice": str(payload.get("notice", "")),
        "promos": list(payload.get("promos") or []),
    }


def provider_template_by_domain(domain: str) -> dict[str, object] | None:
    normalized = domain.strip().lower()
    for provider in list_provider_templates():
        if str(provider.get("domain", "")).lower() == normalized:
            return provider
    return None
