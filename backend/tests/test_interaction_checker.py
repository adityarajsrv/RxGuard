import sys, os
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.interaction_checker import check_all_pairs
from models.schemas import ResolvedComposition, ConfidenceTier, InteractionVerdict


@patch("core.interaction_checker.summarize_fda_interaction")
@patch("core.interaction_checker.get_interaction_text")
def test_known_interaction_detected(mock_get_text, mock_summarize):
    mock_get_text.side_effect = lambda ing: (
        "aspirin, cilostazol, clopidogrel increase bleeding risk" if ing.lower() == "warfarin" else None
    )
    mock_summarize.return_value = {
        "plain_description": "Increases risk of serious bleeding.",
        "severity": "severe",
    }

    comps = [
        ResolvedComposition(drug_name_input="Warfarin 5mg", confidence=ConfidenceTier.HIGH, active_ingredients=["Warfarin"]),
        ResolvedComposition(drug_name_input="Disprin", confidence=ConfidenceTier.HIGH, active_ingredients=["Aspirin"]),
    ]
    results = check_all_pairs(comps)
    assert results[0].verdict == InteractionVerdict.KNOWN_INTERACTION
    assert results[0].severity == "severe"
    assert results[0].source == "openFDA drug label"
    print("PASS: known interaction (mocked openFDA) detected as severe")


def test_unverified_drug_blocks_check():
    comps = [
        ResolvedComposition(drug_name_input="Warfarin 5mg", confidence=ConfidenceTier.HIGH, active_ingredients=["Warfarin"]),
        ResolvedComposition(drug_name_input="MysteryPill", confidence=ConfidenceTier.UNVERIFIED, active_ingredients=[]),
    ]
    results = check_all_pairs(comps)
    assert results[0].verdict == InteractionVerdict.CANNOT_VERIFY
    print("PASS: unverified drug blocks check (no API call needed — gate closes first)")


@patch("core.interaction_checker.get_interaction_text")
def test_no_known_interaction_is_distinct(mock_get_text):
    mock_get_text.return_value = None  # simulate openFDA having no data at all

    comps = [
        ResolvedComposition(drug_name_input="Metformin 500mg", confidence=ConfidenceTier.HIGH, active_ingredients=["Metformin"]),
        ResolvedComposition(drug_name_input="Paracetamol 500mg", confidence=ConfidenceTier.HIGH, active_ingredients=["Paracetamol"]),
    ]
    results = check_all_pairs(comps)
    assert results[0].verdict == InteractionVerdict.NO_KNOWN_INTERACTION
    print("PASS: no-interaction distinct from cannot-verify (mocked empty openFDA + empty CSV match)")


if __name__ == "__main__":
    test_known_interaction_detected()
    test_unverified_drug_blocks_check()
    test_no_known_interaction_is_distinct()
    print("\nAll tests passed.")