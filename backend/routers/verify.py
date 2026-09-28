from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.schemas import (
    VerifyRequest, AskRequest, VerifyResponse, DrugCardResult, EquivalentDrug,
    ResolvedComposition, ConfidenceTier, SourceExtraction
)
from core.composition_resolver import resolve_drug_composition
from core.confidence_engine import gate_allows_equivalents_lookup, gate_allows_interaction_check
from core.interaction_checker import check_all_pairs
from core.serpapi_client import search_shopping_equivalents
from core.openfda_client import get_indications_text, get_interaction_text, get_warnings_text
from core.gemini_client import (
    summarize_usage_context,
    generate_plain_summary,
    extract_composition_from_image
)
from core.rag_engine import build_label_chunks, answer_from_chunks

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _clean_names(names: list[str]) -> list[str]:
    seen, out = set(), []
    for n in names:
        n = " ".join(n.strip().split())[:80]
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out[:10]


def _equivalents_for(composition: ResolvedComposition) -> tuple[list[EquivalentDrug], str | None]:
    if not gate_allows_equivalents_lookup(composition):
        return [], "Equivalents are only shown when the composition is verified with high confidence."
    if composition.prescription_only:
        return [], (
            "Prescription medicine: any substitution should be decided by your doctor or "
            "pharmacist, so price alternatives are not shown."
        )

    strength = dict(composition.strength_mg)
    if not strength:
        if composition.entered_strength_mg and len(composition.active_ingredients) == 1:
            strength = {composition.active_ingredients[0]: composition.entered_strength_mg}
        else:
            return [], 'Add a strength to compare equivalents, for example "Aspirin 75".'

    try:
        raw = search_shopping_equivalents(", ".join(composition.active_ingredients), strength)
    except Exception as e:  # noqa: BLE001
        print(f"Equivalents lookup failed for '{composition.drug_name_input}': {e}")
        return [], "Equivalents lookup is temporarily unavailable."

    items = [EquivalentDrug(**i) for i in raw if i.get("brand_name")]
    if not items:
        return [], "No listings matched this ingredient and strength."
    return items, None


def _run_pipeline(clean_names: list[str]) -> VerifyResponse:
    drug_cards: list[DrugCardResult] = []

    for name in clean_names:
        try:
            composition = resolve_drug_composition(name)
        except Exception as e:  # noqa: BLE001
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

        equivalents, note = _equivalents_for(composition)
        composition.equivalents_note = note
        drug_cards.append(DrugCardResult(composition=composition, equivalents=equivalents))

    interactions = check_all_pairs([card.composition for card in drug_cards])
    return VerifyResponse(drugs=drug_cards, interactions=interactions)


@router.post("/verify", response_model=VerifyResponse)
@limiter.limit("10/minute")
def verify_drugs(request: Request, body: VerifyRequest):
    clean_names = _clean_names(body.drug_names)
    if not clean_names:
        raise HTTPException(status_code=400, detail="No valid drug names provided.")
    return _run_pipeline(clean_names)


@router.post("/verify-image", response_model=VerifyResponse)
@limiter.limit("5/minute")
async def verify_from_image(request: Request, file: UploadFile = File(...)):
    image_bytes = await file.read()
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB).")

    extracted = extract_composition_from_image(image_bytes, file.content_type)
    medicines = extracted.get("medicines", [])
    if not medicines:
        raise HTTPException(status_code=422, detail="Could not identify any medicine names in the image.")

    drug_cards: list[DrugCardResult] = []
    for med in medicines[:10]:
        name = " ".join(med.get("drug_name", "").split())[:80]
        if not name:
            continue

        packaging_source = SourceExtraction(
            source_name="printed packaging",
            active_ingredients=med.get("active_ingredients", []),
            strength_mg={k: v for k, v in med.get("strength_mg", {}).items() if isinstance(v, (int, float))},
            raw_text_snippet="Extracted directly from the uploaded photo.",
        )

        try:
            composition = resolve_drug_composition(name)
        except Exception as e:
            print(f"Composition resolution failed for '{name}': {e}")
            composition = ResolvedComposition(drug_name_input=name, confidence=ConfidenceTier.UNVERIFIED)

        if packaging_source.active_ingredients:
            composition.sources_checked.append(packaging_source)
            composition = _reconfirm_with_packaging(composition, packaging_source)

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
            composition.drug_name_input, composition.active_ingredients,
            composition.usage_context, composition.confidence.value,
        )

        equivalents, note = _equivalents_for(composition)
        composition.equivalents_note = note
        drug_cards.append(DrugCardResult(composition=composition, equivalents=equivalents))

    interactions = check_all_pairs([c.composition for c in drug_cards])
    return VerifyResponse(drugs=drug_cards, interactions=interactions)


def _reconfirm_with_packaging(composition: ResolvedComposition, packaging: SourceExtraction) -> ResolvedComposition:
    """If the packaging's ingredients match what the web already confirmed, and
    strength was previously missing, adopt the packaging's strength — the photo
    is direct evidence, not a guess, so this raises confidence rather than
    lowering it, but only on agreement, never on conflict."""
    from core.drug_synonyms import canonical_name

    web_set = {canonical_name(i) for i in composition.active_ingredients}
    pkg_set = {canonical_name(i) for i in packaging.active_ingredients}

    if not web_set:
        return composition
    if web_set != pkg_set:
        composition.disagreement_reason = (
            (composition.disagreement_reason + " " if composition.disagreement_reason else "")
            + "The printed packaging lists different ingredients than web sources found — treat with caution."
        )
        composition.confidence = ConfidenceTier.MEDIUM if composition.confidence == ConfidenceTier.HIGH else composition.confidence
        return composition

    if not composition.strength_mg and packaging.strength_mg:
        composition.strength_mg = packaging.strength_mg
    return composition


@router.post("/ask")
@limiter.limit("15/minute")
def ask_about_drug(request: Request, body: AskRequest):
    drug_name = " ".join(body.drug_name.split())
    question = " ".join(body.question.split())

    if body.confidence == "unverified":
        return {
            "answer": f"I couldn't verify what's actually in {drug_name}, so I can't safely answer questions about it. Please confirm the name and check with a pharmacist.",
            "grounded": False,
            "verified": None,
        }

    chunks = build_label_chunks(drug_name, {
        "indications": get_indications_text(drug_name),
        "interactions": get_interaction_text(drug_name),
        "warnings": get_warnings_text(drug_name),
    })
    return answer_from_chunks(question, chunks, drug_name)