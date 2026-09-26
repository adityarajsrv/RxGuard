import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.confidence_engine import resolve_confidence, gate_allows_equivalents_lookup, gate_allows_interaction_check
from models.schemas import SourceExtraction, ConfidenceTier


def test_two_agreeing_sources_is_high():
    sources = [
        SourceExtraction(source_name="1mg.com", active_ingredients=["Paracetamol", "Chlorzoxazone"], strength_mg={"Paracetamol": 650, "Chlorzoxazone": 250}),
        SourceExtraction(source_name="netmeds.com", active_ingredients=["Paracetamol", "Chlorzoxazone"], strength_mg={"Paracetamol": 650, "Chlorzoxazone": 250}),
    ]
    result = resolve_confidence("Chlorzox-P", sources)
    assert result.confidence == ConfidenceTier.HIGH
    assert gate_allows_equivalents_lookup(result) is True
    assert gate_allows_interaction_check(result) is True
    print("PASS: two agreeing sources -> HIGH")


def test_single_source_is_medium():
    sources = [SourceExtraction(source_name="1mg.com", active_ingredients=["Metformin"], strength_mg={"Metformin": 500})]
    result = resolve_confidence("Glyciphage", sources)
    assert result.confidence == ConfidenceTier.MEDIUM
    assert gate_allows_equivalents_lookup(result) is False
    assert gate_allows_interaction_check(result) is True
    print("PASS: single source -> MEDIUM")


def test_conflicting_ingredients_is_unverified():
    sources = [
        SourceExtraction(source_name="siteA.com", active_ingredients=["Paracetamol"], strength_mg={"Paracetamol": 500}),
        SourceExtraction(source_name="siteB.com", active_ingredients=["Ibuprofen"], strength_mg={"Ibuprofen": 400}),
    ]
    result = resolve_confidence("Confusatab", sources)
    assert result.confidence == ConfidenceTier.UNVERIFIED
    assert result.disagreement_reason is not None
    print("PASS: conflicting sources -> UNVERIFIED")


def test_no_sources_is_unverified():
    result = resolve_confidence("UnknownDrugXYZ", [])
    assert result.confidence == ConfidenceTier.UNVERIFIED
    print("PASS: zero sources -> UNVERIFIED")


def test_agreeing_ingredients_but_strength_mismatch_is_medium():
    sources = [
        SourceExtraction(source_name="siteA.com", active_ingredients=["Amoxicillin"], strength_mg={"Amoxicillin": 500}),
        SourceExtraction(source_name="siteB.com", active_ingredients=["Amoxicillin"], strength_mg={"Amoxicillin": 250}),
    ]
    result = resolve_confidence("Amoxil", sources)
    assert result.confidence == ConfidenceTier.MEDIUM
    print("PASS: strength mismatch -> MEDIUM")


if __name__ == "__main__":
    test_two_agreeing_sources_is_high()
    test_single_source_is_medium()
    test_conflicting_ingredients_is_unverified()
    test_no_sources_is_unverified()
    test_agreeing_ingredients_but_strength_mismatch_is_medium()
    print("\nAll tests passed.")