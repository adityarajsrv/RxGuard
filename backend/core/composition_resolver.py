from core import serpapi_client, gemini_client, openfda_client
from core.confidence_engine import resolve_confidence
from core.drug_synonyms import canonical_name
from models.schemas import SourceExtraction, ResolvedComposition, ConfidenceTier

def resolve_drug_composition(drug_name: str) -> ResolvedComposition:
    if openfda_client.is_recognized_generic(drug_name):
        canonical = canonical_name(drug_name)
        return ResolvedComposition(
            drug_name_input=drug_name,
            confidence=ConfidenceTier.HIGH,
            active_ingredients=[canonical.capitalize()],
            strength_mg={},
            sources_checked=[
                SourceExtraction(
                    source_name="openFDA (recognized generic name)",
                    source_url=None,
                    active_ingredients=[canonical.capitalize()],
                    strength_mg={},
                    raw_text_snippet=f"'{drug_name}' matches a recognized generic ingredient name in FDA records.",
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

    return resolve_confidence(drug_name, extractions)