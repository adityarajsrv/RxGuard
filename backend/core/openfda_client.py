import os
import json
import time
import hashlib
import urllib.error
import urllib.parse
import urllib.request

from core.drug_synonyms import canonical_name

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

_BASE_URL = "https://api.fda.gov/drug/label.json"

_FIELD_LIMITS = {
    "indications_and_usage": 12000,
    "drug_interactions": 40000,
    "warnings_and_cautions": 12000,
    "warnings": 12000,
    "boxed_warning": 12000,
}

_SALT_TOKENS = {
    "sodium", "potassium", "calcium", "magnesium", "hydrochloride", "hcl",
    "sulfate", "sulphate", "maleate", "tartrate", "succinate", "besylate",
    "mesylate", "acetate", "phosphate", "citrate", "trihydrate", "dihydrate",
    "monohydrate", "hydrobromide", "disodium",
}


def _cache_path(key: str) -> str:
    return os.path.join(_CACHE_DIR, f"openfda_{hashlib.sha256(key.encode()).hexdigest()[:16]}.json")


def _cache_get(key: str):
    path = _cache_path(key)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _cache_set(key: str, data):
    with open(_cache_path(key), "w", encoding="utf-8") as f:
        json.dump(data, f)


def _trim(label: dict) -> dict:
    openfda = label.get("openfda", {})
    out = {
        "generic_names": [g.lower() for g in openfda.get("generic_name", [])],
        "product_types": openfda.get("product_type", []),
    }
    for field, limit in _FIELD_LIMITS.items():
        value = label.get(field)
        if value:
            out[field] = " ".join(value)[:limit]
    return out


def _request(query: str, limit: int = 8, retries: int = 2):
    """Returns a list of trimmed labels, [] for no match, None for a network failure."""
    url = f"{_BASE_URL}?{urllib.parse.urlencode({'search': query, 'limit': limit})}"
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            return [_trim(l) for l in data.get("results", [])]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []
            last_err = e
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(1.0 * (attempt + 1))
    print(f"openFDA request failed: {last_err}")
    return None


def _labels_for(canonical: str):
    key = f"labels_v2::{canonical}"
    cached = _cache_get(key)
    if cached is not None:
        return cached["labels"]

    labels = []
    for query in (
        f'openfda.generic_name.exact:"{canonical.upper()}"',
        f'openfda.generic_name:"{canonical}"',
    ):
        result = _request(query)
        if result is None:
            return None
        if result:
            labels = result
            break

    _cache_set(key, {"labels": labels})
    return labels


def _base_name(generic_name: str) -> str:
    tokens = generic_name.lower().replace(",", " ").split()
    while len(tokens) > 1 and tokens[-1] in _SALT_TOKENS:
        tokens.pop()
    return " ".join(tokens)


def _is_single_ingredient(label: dict, canonical: str) -> bool:
    names = label.get("generic_names", [])
    return bool(names) and all(_base_name(n) == canonical for n in names)


def _single_ingredient_labels(canonical: str):
    labels = _labels_for(canonical)
    if not labels:
        return []
    return [l for l in labels if _is_single_ingredient(l, canonical)]


def _section(ingredient: str, field: str) -> str | None:
    canonical = canonical_name(ingredient)
    pool = [l for l in _single_ingredient_labels(canonical) if l.get(field)]
    if not pool:
        return None
    return max(pool, key=lambda l: len(l[field]))[field]


def is_recognized_generic(name: str) -> bool:
    canonical = canonical_name(name)
    if len(canonical) < 3 or canonical in _SALT_TOKENS:
        return False
    return len(_single_ingredient_labels(canonical)) > 0


def is_prescription_only(ingredient: str) -> bool | None:
    """Proxy based on FDA labelling: True only if every sampled single-ingredient
    label is prescription. None when unknown."""
    canonical = canonical_name(ingredient)
    types = []
    for label in _single_ingredient_labels(canonical):
        types.extend(t.upper() for t in label.get("product_types", []))
    if not types:
        return None
    has_rx = any("PRESCRIPTION" in t for t in types)
    has_otc = any("OTC" in t for t in types)
    return has_rx and not has_otc


def get_indications_text(ingredient: str) -> str | None:
    return _section(ingredient, "indications_and_usage")


def get_interaction_text(ingredient: str) -> str | None:
    return _section(ingredient, "drug_interactions")


def get_warnings_text(ingredient: str) -> str | None:
    return _section(ingredient, "warnings_and_cautions") or _section(ingredient, "warnings")


def get_boxed_warning_text(ingredient: str) -> str | None:
    return _section(ingredient, "boxed_warning")