"""
Queries openFDA's structured drug label data for the official
"Drug Interactions" section text of a given generic ingredient.
Free, no key required at hackathon scale, directly sourced from
FDA-regulated drug labeling — this is the authoritative data source
backing the interaction checker, with the curated CSV as fallback
for ingredients openFDA doesn't cover.

Docs: https://open.fda.gov/apis/drug/label/
"""
import os
import json
import time
import hashlib
import urllib.request
import urllib.parse

from core.drug_synonyms import canonical_name

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

_BASE_URL = "https://api.fda.gov/drug/label.json"


def _cache_key(payload: str) -> str:
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"openfda_{h}.json")


def _cache_get(payload: str):
    path = _cache_key(payload)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _cache_set(payload: str, data):
    with open(_cache_key(payload), "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_interaction_text(generic_ingredient: str, max_retries: int = 2) -> str | None:
    """
    Returns the raw 'drug_interactions' label text for this generic
    ingredient, or None if openFDA has no matching label. None is a
    valid, honest outcome — it means "not found," not "no interactions."
    """
    canonical = canonical_name(generic_ingredient)
    cached = _cache_get(f"interaction_text::{canonical}")
    if cached is not None:
        return cached.get("text")

    query = f'openfda.generic_name:"{canonical}"'
    params = {"search": query, "limit": 1}
    url = f"{_BASE_URL}?{urllib.parse.urlencode(params)}"

    last_err = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            results = data.get("results", [])
            if not results:
                _cache_set(f"interaction_text::{canonical}", {"text": None})
                return None
            interactions = results[0].get("drug_interactions", [])
            text = " ".join(interactions) if interactions else None
            _cache_set(f"interaction_text::{canonical}", {"text": text})
            return text
        except Exception as e:
            last_err = e
            time.sleep(1.0 * (attempt + 1))

    print(f"openFDA lookup failed for {canonical}: {last_err}")
    return None

def check_active_recall(generic_or_brand_name: str) -> dict | None:
    canonical = canonical_name(generic_or_brand_name)
    cached = _cache_get(f"recall::{canonical}")
    if cached is not None:
        return cached

    query = f'openfda.generic_name:"{canonical}"+AND+status:"Ongoing"'
    params = {"search": query, "limit": 3}
    url = f"https://api.fda.gov/drug/enforcement.json?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        if not results:
            out = {"has_active_recall": False}
        else:
            r = results[0]
            out = {
                "has_active_recall": True,
                "reason": r.get("reason_for_recall"),
                "classification": r.get("classification"),
            }
        _cache_set(f"recall::{canonical}", out)
        return out
    except Exception:
        return None    