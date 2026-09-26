import os
import json
import time
import hashlib
from serpapi import GoogleSearch
from urllib.parse import urlparse

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

TRUSTED_DOMAINS = ["1mg.com", "netmeds.com", "pharmeasy.in", "apollopharmacy.in"]

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _cache_key(prefix: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{prefix}_{h}.json")


def _cache_get(prefix: str, payload: str):
    path = _cache_key(prefix, payload)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _cache_set(prefix: str, payload: str, data):
    path = _cache_key(prefix, payload)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _search(params: dict, max_retries: int = 2) -> dict:
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY not set.")
    params = {**params, "api_key": SERPAPI_KEY}
    last_err = None
    for attempt in range(max_retries):
        try:
            return GoogleSearch(params).get_dict()
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"SerpApi failed after {max_retries} attempts: {last_err}")


def search_drug_composition(drug_name: str) -> list[dict]:
    cache_payload = f"composition::{drug_name.strip().lower()}"
    cached = _cache_get("composition", cache_payload)
    if cached is not None:
        return cached

    results = []
    drug_lower = drug_name.strip().lower()
    drug_slug = drug_lower.replace(" ", "-")

    for domain in TRUSTED_DOMAINS:
        query = f"site:{domain} {drug_name} tablet composition"
        data = _search({"q": query, "num": 5, "gl": "in", "hl": "en"})
        organic = data.get("organic_results", [])
        best = None
        for r in organic:
            link = r.get("link", "")
            link_domain = urlparse(link).netloc.replace("www.", "")
            if domain not in link_domain:
                continue

            title = r.get("title", "").lower()
            title_match = drug_lower in title
            url_match = drug_slug in link.lower()

            if title_match or url_match:
                best = r
                break

        if best:
            results.append({
                "source_name": domain,
                "source_url": best.get("link"),
                "title": best.get("title", ""),
                "snippet": best.get("snippet", ""),
            })

    _cache_set("composition", cache_payload, results)
    return results

def search_shopping_equivalents(active_ingredient: str, strength_mg: dict) -> list[dict]:
    cache_payload = f"shopping::{active_ingredient.strip().lower()}::{json.dumps(strength_mg, sort_keys=True)}"
    cached = _cache_get("shopping", cache_payload)
    if cached is not None:
        return cached

    ingredients_list = [i.strip() for i in active_ingredient.split(",") if i.strip()]
    ingredients_str = " ".join(ingredients_list)
    strength_str = " ".join(f"{v:g}mg" for v in strength_mg.values()) if strength_mg else ""
    query = f"{ingredients_str} {strength_str} tablet".strip()

    data = _search({
        "q": query,
        "engine": "google_shopping",
        "google_domain": "google.co.in",
        "gl": "in",
        "hl": "en",
    })
    shopping_results = data.get("shopping_results", [])
    out = []
    for r in shopping_results:
        out.append({
            "brand_name": r.get("title"),
            "price_inr": r.get("extracted_price"),
            "seller": r.get("source"),
            "source_url": r.get("product_link") or r.get("link"),
        })

    cleaned = _clean_equivalents(out)
    _cache_set("shopping", cache_payload, cleaned)
    return cleaned

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