from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.schemas import (
    VerifyRequest, VerifyResponse, DrugCardResult, EquivalentDrug,
    ResolvedComposition, ConfidenceTier,
)
from core.composition_resolver import resolve_drug_composition
from core.confidence_engine import gate_allows_equivalents_lookup
from core.interaction_checker import check_all_pairs
from core.serpapi_client import search_shopping_equivalents

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/verify", response_model=VerifyResponse)
@limiter.limit("10/minute")
def verify_drugs(request: Request, body: VerifyRequest):
    clean_names = [n.strip()[:80] for n in body.drug_names if n.strip()]
    if not clean_names:
        raise HTTPException(status_code=400, detail="No valid drug names provided.")

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