import csv
import os
from itertools import combinations

from models.schemas import ResolvedComposition, InteractionResult, InteractionVerdict
from core.confidence_engine import gate_allows_interaction_check
from core.drug_synonyms import canonical_name
from core.openfda_client import get_interaction_text
from core.gemini_client import summarize_fda_interaction

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "interactions.csv")


def _load_interaction_table() -> dict:
    table = {}
    with open(_DATA_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = tuple(sorted([
                canonical_name(row["drug_a"]),
                canonical_name(row["drug_b"]),
            ]))
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

    fda_result = _check_via_openfda(comp_a, comp_b)
    if fda_result is not None:
        return InteractionResult(drug_a=label_a, drug_b=label_b, **fda_result)

    csv_result = _check_via_csv(comp_a, comp_b)
    if csv_result is not None:
        return InteractionResult(drug_a=label_a, drug_b=label_b, **csv_result)

    return InteractionResult(
        drug_a=label_a, drug_b=label_b, verdict=InteractionVerdict.NO_KNOWN_INTERACTION,
        description="No interaction found in FDA label data or our curated dataset.",
        source="openFDA + curated dataset (not exhaustive)",
    )

def _check_via_openfda(comp_a: ResolvedComposition, comp_b: ResolvedComposition):
    any_data_found = False

    for ing_a in comp_a.active_ingredients:
        text_a = get_interaction_text(ing_a)
        if text_a is None:
            continue

        any_data_found = True

        for ing_b in comp_b.active_ingredients:
            if canonical_name(ing_b) in text_a.lower():
                print("PARAPHRASE CALLED:", ing_a, ing_b)

                raw_excerpt = _excerpt(
                    text_a,
                    canonical_name(ing_b),
                )

                try:
                    summary = summarize_fda_interaction(
                        raw_excerpt,
                        ing_a,
                        ing_b,
                    )
                except Exception as exc:
                    print("Exception in summarize_fda_interaction:", repr(exc))
                    summary = {
                        "plain_description": raw_excerpt,
                        "severity": "unspecified",
                    }

                return {
                    "verdict": InteractionVerdict.KNOWN_INTERACTION,
                    "severity": summary["severity"],
                    "description": summary["plain_description"],
                    "source": "openFDA drug label",
                }

    for ing_b in comp_b.active_ingredients:
        text_b = get_interaction_text(ing_b)
        if text_b is None:
            continue

        any_data_found = True

        for ing_a in comp_a.active_ingredients:
            if canonical_name(ing_a) in text_b.lower():
                print("PARAPHRASE CALLED:", ing_a, ing_b)

                raw_excerpt = _excerpt(
                    text_b,
                    canonical_name(ing_a),
                )

                try:
                    summary = summarize_fda_interaction(
                        raw_excerpt,
                        ing_a,
                        ing_b,
                    )
                except Exception as exc:
                    print("Exception in summarize_fda_interaction:", repr(exc))
                    summary = {
                        "plain_description": raw_excerpt,
                        "severity": "unspecified",
                    }

                return {
                    "verdict": InteractionVerdict.KNOWN_INTERACTION,
                    "severity": summary["severity"],
                    "description": summary["plain_description"],
                    "source": "openFDA drug label",
                }

    if any_data_found:
        return {
            "verdict": InteractionVerdict.NO_KNOWN_INTERACTION,
            "description": "No mention found in available FDA label interaction text.",
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


def _excerpt(text: str, keyword: str, window: int = 150) -> str:
    idx = text.lower().find(keyword)
    if idx == -1:
        return text[:window] + "..."
    start = max(0, idx - window // 2)
    end = min(len(text), idx + window // 2)
    return "..." + text[start:end] + "..."