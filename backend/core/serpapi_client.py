import os
import re
import json
import time
import hashlib
from urllib.parse import urlparse
from serpapi import GoogleSearch

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

TRUSTED_DOMAINS = ["1mg.com", "netmeds.com", "pharmeasy.in", "apollopharmacy.in"]

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

_PACK_RE = re.compile(r"(\d{1,3})\s*(?:'s\b|s\b|tablets?\b|tabs?\b|capsules?\b|caps?\b)", re.IGNORECASE)


def _cache_path(prefix: str, payload: str) -> str:
    return os.path.join(_CACHE_DIR, f"{prefix}_{hashlib.sha256(payload.encode()).hexdigest()[:16]}.json")


def _cache_get(prefix: str, payload: str):
    path = _cache_path(prefix, payload)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _cache_set(prefix: str, payload: str, data):
    with open(_cache_path(prefix, payload), "w", encoding="utf-8") as f:
        json.dump(data, f)


def _search(params: dict, max_retries: int = 2) -> dict:
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY not set.")
    params = {**params, "api_key": SERPAPI_KEY}
    last_err = None
    for attempt in range(max_retries):
        try:
            return GoogleSearch(params).get_dict()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"SerpApi failed after {max_retries} attempts: {last_err}")


def search_drug_composition(drug_name: str) -> list[dict]:
    payload = f"composition_v6::{drug_name.strip().lower()}"
    cached = _cache_get("composition", payload)
    if cached is not None:
        return cached

    drug_lower = drug_name.strip().lower()
    drug_slug = drug_lower.replace(" ", "-")
    results = []

    for domain in TRUSTED_DOMAINS:
        best = None
        for query in (f"site:{domain} {drug_name} tablet composition", f"site:{domain} {drug_name}"):
            data = _search({"q": query, "num": 5, "gl": "in", "hl": "en"})
            for r in data.get("organic_results", []):
                link = r.get("link", "")
                if domain not in urlparse(link).netloc.replace("www.", ""):
                    continue
                title = r.get("title", "").lower()
                snippet_text = r.get("snippet", "").lower()
                if (drug_lower in title or drug_slug in link.lower()) and drug_lower in (title + " " + snippet_text):
                    best = r
                    break
            if best:
                break
        if best:
            results.append({
                "source_name": domain,
                "source_url": best.get("link"),
                "title": best.get("title", ""),
                "snippet": best.get("snippet", ""),
            })

    _cache_set("composition", payload, results)
    return results

def _pack_size(title: str) -> int | None:
    match = _PACK_RE.search(title)
    if not match:
        return None
    size = int(match.group(1))
    return size if size > 0 else None


def _has_number(title: str, value: float) -> bool:
    return re.search(rf"(?<!\d){re.escape(f'{value:g}')}(?!\d)", title) is not None


def _clean_equivalents(raw: list[dict]) -> list[dict]:
    seen = {}
    for item in raw:
        name = (item.get("brand_name") or "").strip().lower()
        price = item.get("price_inr")
        if not name or price is None or price <= 0:
            continue
        if name not in seen or price < seen[name]["price_inr"]:
            seen[name] = item

    items = list(seen.values())
    if not items:
        return []

    prices = sorted(i["price_inr"] for i in items)
    median = prices[len(prices) // 2]
    items = [i for i in items if i["price_inr"] <= median * 3]
    return sorted(items, key=lambda i: i["price_inr"])[:6]


def search_shopping_equivalents(active_ingredient: str, strength_mg: dict) -> list[dict]:
    payload = f"{active_ingredient.strip().lower()}::{json.dumps(strength_mg, sort_keys=True)}"
    cached = _cache_get("shopping_v2", payload)
    if cached is not None:
        return cached

    ingredients = [i.strip() for i in active_ingredient.split(",") if i.strip()]
    strength_str = " ".join(f"{v:g}mg" for v in strength_mg.values())
    query = " ".join(f"{' '.join(ingredients)} {strength_str} tablet".split())

    data = _search({
        "q": query,
        "engine": "google_shopping",
        "google_domain": "google.co.in",
        "gl": "in",
        "hl": "en",
    })

    out = []
    for r in data.get("shopping_results", []):
        title = r.get("title") or ""
        low = title.lower()
        if not all(i.lower() in low for i in ingredients):
            continue
        if strength_mg and not all(_has_number(title, v) for v in strength_mg.values()):
            continue
        price = r.get("extracted_price")
        pack = _pack_size(title)
        out.append({
            "brand_name": title,
            "price_inr": price,
            "seller": r.get("source"),
            "source_url": r.get("product_link") or r.get("link"),
            "pack_size": pack,
            "price_per_unit": round(price / pack, 2) if price and pack else None,
        })

    cleaned = _clean_equivalents(out)
    _cache_set("shopping_v2", payload, cleaned)
    return cleaned