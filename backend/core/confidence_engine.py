from models.schemas import SourceExtraction, ResolvedComposition, ConfidenceTier

STRENGTH_TOLERANCE_PCT = 0.05


def _normalize_ingredient(name: str) -> str:
    return name.strip().lower().replace("  ", " ")


def _ingredient_sets_match(a: SourceExtraction, b: SourceExtraction) -> bool:
    set_a = {_normalize_ingredient(i) for i in a.active_ingredients}
    set_b = {_normalize_ingredient(i) for i in b.active_ingredients}
    return set_a == set_b and len(set_a) > 0


def _strengths_match(a: SourceExtraction, b: SourceExtraction) -> bool:
    norm_a = {_normalize_ingredient(k): v for k, v in a.strength_mg.items()}
    norm_b = {_normalize_ingredient(k): v for k, v in b.strength_mg.items()}
    shared_keys = set(norm_a) & set(norm_b)
    if not shared_keys:
        return True
    for key in shared_keys:
        va, vb = norm_a[key], norm_b[key]
        if va == 0 or vb == 0:
            continue
        if abs(va - vb) / max(va, vb) > STRENGTH_TOLERANCE_PCT:
            return False
    return True


def resolve_confidence(drug_name_input: str, sources: list[SourceExtraction]) -> ResolvedComposition:
    usable_sources = [s for s in sources if s.active_ingredients]

    if len(usable_sources) == 0:
        return ResolvedComposition(
            drug_name_input=drug_name_input,
            confidence=ConfidenceTier.UNVERIFIED,
            sources_checked=sources,
            disagreement_reason="No source returned a usable composition extraction.",
        )

    if len(usable_sources) == 1:
        src = usable_sources[0]
        return ResolvedComposition(
            drug_name_input=drug_name_input,
            confidence=ConfidenceTier.MEDIUM,
            active_ingredients=src.active_ingredients,
            strength_mg=src.strength_mg,
            sources_checked=sources,
        )

    reference = usable_sources[0]
    all_ingredients_agree = all(_ingredient_sets_match(reference, s) for s in usable_sources[1:])

    if not all_ingredients_agree:
        return ResolvedComposition(
            drug_name_input=drug_name_input,
            confidence=ConfidenceTier.UNVERIFIED,
            sources_checked=sources,
            disagreement_reason=f"Sources disagree on active ingredients across {len(usable_sources)} extractions.",
        )

    all_strengths_agree = all(_strengths_match(reference, s) for s in usable_sources[1:])

    if all_strengths_agree:
        return ResolvedComposition(
            drug_name_input=drug_name_input,
            confidence=ConfidenceTier.HIGH,
            active_ingredients=reference.active_ingredients,
            strength_mg=reference.strength_mg,
            sources_checked=sources,
        )

    return ResolvedComposition(
        drug_name_input=drug_name_input,
        confidence=ConfidenceTier.MEDIUM,
        active_ingredients=reference.active_ingredients,
        strength_mg=reference.strength_mg,
        sources_checked=sources,
        disagreement_reason=f"Ingredients agree, strength differs beyond {STRENGTH_TOLERANCE_PCT*100:.0f}% tolerance.",
    )


def gate_allows_equivalents_lookup(composition: ResolvedComposition) -> bool:
    return composition.confidence == ConfidenceTier.HIGH


def gate_allows_interaction_check(composition: ResolvedComposition) -> bool:
    return composition.confidence in (ConfidenceTier.HIGH, ConfidenceTier.MEDIUM)