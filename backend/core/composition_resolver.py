from core import serpapi_client, gemini_client, openfda_client
from core.confidence_engine import resolve_confidence
from core.input_parser import split_name_and_strength
from models.schemas import SourceExtraction, ResolvedComposition, ConfidenceTier


def _rx_status(ingredients: list[str]) -> bool | None:
    statuses = [openfda_client.is_prescription_only(i) for i in ingredients]
    if any(s is True for s in statuses):
        return True
    if statuses and all(s is False for s in statuses):
        return False
    return None


def resolve_drug_composition(drug_name: str) -> ResolvedComposition:
    base_name, entered_strength = split_name_and_strength(drug_name)

    if openfda_client.is_recognized_generic(base_name):
        display = base_name.title()
        return ResolvedComposition(
            drug_name_input=base_name,
            confidence=ConfidenceTier.HIGH,
            active_ingredients=[display],
            entered_strength_mg=entered_strength,
            verification_basis="fda_generic_name",
            prescription_only=openfda_client.is_prescription_only(base_name),
            sources_checked=[
                SourceExtraction(
                    source_name="openFDA (recognized generic name)",
                    active_ingredients=[display],
                    raw_text_snippet=f"'{base_name}' matches a single-ingredient drug in FDA labelling records.",
                )
            ],
        )

    raw_sources = serpapi_client.search_drug_composition(drug_name)

    extractions: list[SourceExtraction] = []
    for src in raw_sources:
        extracted = gemini_client.extract_composition_from_snippet(
            source_name=src["source_name"], title=src["title"], snippet=src["snippet"],
        )
        extractions.append(SourceExtraction(
            source_name=src["source_name"],
            source_url=src.get("source_url"),
            active_ingredients=extracted.get("active_ingredients", []),
            strength_mg=extracted.get("strength_mg", {}),
            raw_text_snippet=src.get("snippet"),
        ))

    result = resolve_confidence(drug_name, extractions)
    result.entered_strength_mg = entered_strength
    if result.active_ingredients and result.confidence != ConfidenceTier.UNVERIFIED:
        result.prescription_only = _rx_status(result.active_ingredients)
    return result