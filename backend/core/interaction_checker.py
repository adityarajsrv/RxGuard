import csv
import os
from itertools import combinations

from models.schemas import ResolvedComposition, InteractionResult, InteractionVerdict
from core.confidence_engine import gate_allows_interaction_check
from core.drug_synonyms import canonical_name
from core.openfda_client import get_interaction_text
from core.gemini_client import summarize_fda_interaction

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "interactions.csv")
_VALID_SEVERITIES = {"mild", "moderate", "severe"}


def _load_interaction_table() -> dict:
    table = {}
    with open(_DATA_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("drug_a") or not row.get("drug_b") or not row.get("description"):
                continue
            key = tuple(sorted([canonical_name(row["drug_a"]), canonical_name(row["drug_b"])]))
            table[key] = {"severity": row["severity"], "description": row["description"]}
    return table


_INTERACTION_TABLE = _load_interaction_table()


def check_all_pairs(compositions: list[ResolvedComposition]) -> list[InteractionResult]:
    return [_check_pair(a, b) for a, b in combinations(compositions, 2)]


def _check_pair(comp_a: ResolvedComposition, comp_b: ResolvedComposition) -> InteractionResult:
    label_a, label_b = comp_a.drug_name_input, comp_b.drug_name_input

    if not gate_allows_interaction_check(comp_a) or not gate_allows_interaction_check(comp_b):
        return InteractionResult(
            drug_a=label_a, drug_b=label_b, verdict=InteractionVerdict.CANNOT_VERIFY,
            description="One or both drugs did not pass composition verification.",
        )

    shared = {canonical_name(i) for i in comp_a.active_ingredients} & {
        canonical_name(i) for i in comp_b.active_ingredients
    }
    if shared:
        names = ", ".join(sorted({i for i in comp_a.active_ingredients if canonical_name(i) in shared}))
        return InteractionResult(
            drug_a=label_a, drug_b=label_b, verdict=InteractionVerdict.DUPLICATE_INGREDIENT,
            description=(
                f"Both medicines contain {names}. Taking them together adds up the dose of the "
                "same ingredient, which can lead to an overdose. Check the total daily amount "
                "with a pharmacist."
            ),
            source="composition match",
        )

    fda = _check_via_openfda(comp_a, comp_b)
    csv_hit = _check_via_csv(comp_a, comp_b)

    if fda and fda["verdict"] == InteractionVerdict.KNOWN_INTERACTION:
        if fda["severity"] == "unspecified" and csv_hit:
            fda["severity"] = csv_hit["severity"]
        return InteractionResult(drug_a=label_a, drug_b=label_b, **fda)

    if csv_hit:
        return InteractionResult(drug_a=label_a, drug_b=label_b, **csv_hit)

    checked = "openFDA labels and the curated list" if fda is not None else "the curated list only"
    return InteractionResult(
        drug_a=label_a, drug_b=label_b, verdict=InteractionVerdict.NO_KNOWN_INTERACTION,
        description=f"Nothing found in {checked}. This is not proof that no interaction exists. Confirm with a pharmacist.",
        source=checked,
    )


def _fda_known(text: str, ing_x: str, ing_y: str) -> dict:
    raw_excerpt = _excerpt(text, canonical_name(ing_y))
    summary = summarize_fda_interaction(raw_excerpt, ing_x, ing_y)
    severity = str(summary.get("severity", "")).lower()
    return {
        "verdict": InteractionVerdict.KNOWN_INTERACTION,
        "severity": severity if severity in _VALID_SEVERITIES else "unspecified",
        "description": summary.get("plain_description") or raw_excerpt,
        "source": "openFDA drug label",
    }


def _check_via_openfda(comp_a: ResolvedComposition, comp_b: ResolvedComposition):
    any_data = False

    for ing_a in comp_a.active_ingredients:
        text_a = get_interaction_text(ing_a)
        if text_a is None:
            continue
        any_data = True
        for ing_b in comp_b.active_ingredients:
            if canonical_name(ing_b) in text_a.lower():
                return _fda_known(text_a, ing_a, ing_b)

    for ing_b in comp_b.active_ingredients:
        text_b = get_interaction_text(ing_b)
        if text_b is None:
            continue
        any_data = True
        for ing_a in comp_a.active_ingredients:
            if canonical_name(ing_a) in text_b.lower():
                return _fda_known(text_b, ing_b, ing_a)

    if any_data:
        return {
            "verdict": InteractionVerdict.NO_KNOWN_INTERACTION,
            "description": "No mention found in the FDA label interaction text.",
            "source": "openFDA drug label",
        }
    return None


def _check_via_csv(comp_a: ResolvedComposition, comp_b: ResolvedComposition):
    for ing_a in comp_a.active_ingredients:
        for ing_b in comp_b.active_ingredients:
            key = tuple(sorted([canonical_name(ing_a), canonical_name(ing_b)]))
            if key in _INTERACTION_TABLE:
                info = _INTERACTION_TABLE[key]
                return {
                    "verdict": InteractionVerdict.KNOWN_INTERACTION,
                    "severity": info["severity"],
                    "description": info["description"],
                    "source": "curated dataset",
                }
    return None


def _excerpt(text: str, keyword: str, window: int = 300) -> str:
    idx = text.lower().find(keyword)
    if idx == -1:
        return text[:window] + "..."
    start = max(0, idx - window // 2)
    end = min(len(text), idx + window // 2)
    return "..." + text[start:end] + "..."