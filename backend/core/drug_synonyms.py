SYNONYMS = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "frusemide": "furosemide",
    "adrenaline": "epinephrine",
    "noradrenaline": "norepinephrine",
    "diclofenac sodium": "diclofenac",
    "glimepiride ": "glimepiride",
}


def canonical_name(ingredient: str) -> str:
    """Normalize to a US/FDA-style generic name for cross-source matching."""
    key = ingredient.strip().lower()
    return SYNONYMS.get(key, key)