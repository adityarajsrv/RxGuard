from core import serpapi_client, gemini_client
from core.confidence_engine import resolve_confidence
from models.schemas import SourceExtraction, ResolvedComposition


def resolve_drug_composition(drug_name: str) -> ResolvedComposition:
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