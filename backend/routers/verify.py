from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.schemas import (
    VerifyResponse, DrugCardResult, EquivalentDrug,
    ResolvedComposition, ConfidenceTier,
)
from core.composition_resolver import resolve_drug_composition
from core.confidence_engine import gate_allows_equivalents_lookup, gate_allows_interaction_check
from core.interaction_checker import check_all_pairs
from core.serpapi_client import search_shopping_equivalents
from core.openfda_client import get_indications_text, get_interaction_text, get_warnings_text
from core.gemini_client import (
    summarize_usage_context,
    generate_plain_summary,
    extract_drug_names_from_image,
)
from core.rag_engine import build_label_chunks, answer_from_chunks

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _run_pipeline(clean_names: list[str]) -> VerifyResponse:
    drug_cards: list[DrugCardResult] = []

    for name in clean_names:
        try:
            composition = resolve_drug_composition(name)
        except Exception as e:
            print(f"Composition resolution failed for '{name}': {e}")
            composition = ResolvedComposition(
                drug_name_input=name,
                confidence=ConfidenceTier.UNVERIFIED,
                disagreement_reason="Verification service temporarily unavailable for this drug.",
            )

        if gate_allows_interaction_check(composition):
            for ing in composition.active_ingredients:
                raw = get_indications_text(ing)
                if raw:
                    composition.usage_context = summarize_usage_context(raw, ing)
                    break
            if composition.usage_context is None:
                composition.usage_context = "No official usage information found for this medicine."
        else:
            composition.usage_context = "Not shown — composition could not be verified."

        composition.plain_summary = generate_plain_summary(
            composition.drug_name_input,
            composition.active_ingredients,
            composition.usage_context,
            composition.confidence.value,
        )

        equivalents = []
        if gate_allows_equivalents_lookup(composition):
            try:
                raw = search_shopping_equivalents(
                    active_ingredient=", ".join(composition.active_ingredients),
                    strength_mg=composition.strength_mg,
                )
                equivalents = [EquivalentDrug(**item) for item in raw if item.get("brand_name")]
            except Exception as e:
                print(f"Equivalents lookup failed for '{name}': {e}")

        drug_cards.append(DrugCardResult(composition=composition, equivalents=equivalents))

    interactions = check_all_pairs([card.composition for card in drug_cards])
    return VerifyResponse(drugs=drug_cards, interactions=interactions)


@router.post("/verify", response_model=VerifyResponse)
@limiter.limit("10/minute")
def verify_drugs(request: Request, body: dict):
    drug_names = body.get("drug_names", [])
    clean_names = [n.strip()[:80] for n in drug_names if n.strip()]
    if not clean_names:
        raise HTTPException(status_code=400, detail="No valid drug names provided.")
    return _run_pipeline(clean_names)


@router.post("/verify-image", response_model=VerifyResponse)
@limiter.limit("5/minute")
async def verify_from_image(request: Request, file: UploadFile = File(...)):
    image_bytes = await file.read()
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB).")

    drug_names = extract_drug_names_from_image(image_bytes, file.content_type)
    clean_names = [n.strip()[:80] for n in drug_names if n.strip()][:10]
    if not clean_names:
        raise HTTPException(status_code=422, detail="Could not identify any medicine names in the image.")

    return _run_pipeline(clean_names)

@router.post("/ask")
@limiter.limit("15/minute")
def ask_about_drug(request: Request, body: dict):
    drug_name = body.get("drug_name", "").strip()[:80]
    question = body.get("question", "").strip()[:300]
    confidence = body.get("confidence", "").strip()

    if not drug_name or not question:
        raise HTTPException(status_code=400, detail="drug_name and question are required.")

    if confidence == "unverified":
        return {
            "answer": f"I couldn't verify what's actually in {drug_name}, so I can't safely answer questions about it. Please confirm the name and check with a pharmacist.",
            "grounded": False,
        }

    indications = get_indications_text(drug_name)
    interactions = get_interaction_text(drug_name)
    warnings = get_warnings_text(drug_name)
    chunks = build_label_chunks(drug_name, {
        "indications": indications,
        "interactions": interactions,
        "warnings": warnings,
    })
    result = answer_from_chunks(question, chunks, drug_name)
    return result