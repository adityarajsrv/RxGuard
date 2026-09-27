import os
import json
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

_EXTRACTION_PROMPT = """You are extracting structured drug composition data from a search result snippet. Return ONLY valid JSON, no markdown fences, no commentary.

Snippet source: {source_name}
Title: {title}
Snippet: {snippet}

Extract the active pharmaceutical ingredients and their strengths in milligrams.
If the snippet does not clearly state a composition, return an empty ingredients list — DO NOT guess.
If an ingredient is named but no dosage is stated, omit it from strength_mg rather than guessing a number.

Return exactly this JSON shape:
{{"active_ingredients": ["IngredientName", ...], "strength_mg": {{"IngredientName": number, ...}}}}
"""


def extract_composition_from_snippet(source_name: str, title: str, snippet: str) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    prompt = _EXTRACTION_PROMPT.format(source_name=source_name, title=title, snippet=snippet)

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0, "response_mime_type": "application/json"},
        )
        data = json.loads(response.text.strip())

        if not isinstance(data.get("active_ingredients"), list):
            return {"active_ingredients": [], "strength_mg": {}}

        raw_strength = data.get("strength_mg", {})
        if not isinstance(raw_strength, dict):
            raw_strength = {}

        clean_strength = {}
        for k, v in raw_strength.items():
            if isinstance(v, (int, float)):
                clean_strength[k] = float(v)
        data["strength_mg"] = clean_strength

        return data
    except Exception as e:
        print(f"GEMINI EXTRACTION FAILED: {type(e).__name__}: {e}")
        return {"active_ingredients": [], "strength_mg": {}}
    
def summarize_fda_interaction(raw_excerpt: str, drug_a: str, drug_b: str) -> dict:
    if not GEMINI_API_KEY:
        return {"plain_description": raw_excerpt, "severity": "unspecified"}

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    prompt = f"""This raw text is from an FDA drug label, confirming that {drug_a} \
and {drug_b} have a documented interaction:

"{raw_excerpt}"

Write ONE plain-language sentence a non-medical person could understand, explaining \
what kind of risk this interaction poses. Then classify severity as exactly one of: \
mild, moderate, severe, unspecified (use unspecified only if the text gives no way \
to judge severity). Return ONLY this JSON:
{{"plain_description": "...", "severity": "..."}}"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0, "response_mime_type": "application/json"},
        )
        data = json.loads(response.text.strip())
        if "plain_description" not in data or "severity" not in data:
            return {"plain_description": raw_excerpt, "severity": "unspecified"}
        return data
    except Exception:
        return {"plain_description": raw_excerpt, "severity": "unspecified"}
    
def summarize_usage_context(raw_text: str, drug_name: str) -> str:
    if not GEMINI_API_KEY:
        return raw_text[:300]

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    prompt = f"""This raw text is from an FDA drug label describing what {drug_name} \
is used for:

"{raw_text}"

Write ONE or TWO plain-language sentences a non-medical person could understand, \
explaining what condition(s) this medicine is typically prescribed for. Do not add \
any dosing instructions or advice — only describe the general purpose. Return ONLY \
the sentence(s), no JSON, no preamble."""

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0})
        return response.text.strip()
    except Exception:
        return raw_text[:300]
    
def generate_plain_summary(drug_name: str, ingredients: list[str], usage_text: str | None, confidence: str) -> str:
    if not GEMINI_API_KEY:
        return ""

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    usage_part = usage_text if usage_text else "no official usage information was found"

    prompt = f"""Write ONE short, warm, plain-English paragraph (2-3 sentences max) for a \
person with no medical background, explaining medicine "{drug_name}" which contains \
{', '.join(ingredients) if ingredients else 'unconfirmed ingredients'}.

Usage information found: {usage_part}
Confidence level of this data: {confidence}

Do not give dosing instructions. Do not sound clinical or robotic — sound like a knowledgeable \
friend explaining it simply. If confidence is low, say so gently and suggest asking a pharmacist."""

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.3})
        return response.text.strip()
    except Exception:
        return ""
    
def extract_drug_names_from_image(image_bytes: bytes, mime_type: str) -> list[str]:
    if not GEMINI_API_KEY:
        return []

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    prompt = """Look at this photo of medicine packaging or a prescription. List every \
distinct medicine name you can read, one per line, no other text. If you cannot read \
any medicine name clearly, return nothing."""

    try:
        response = model.generate_content([
            {"mime_type": mime_type, "data": image_bytes},
            prompt,
        ])
        lines = [l.strip() for l in response.text.strip().split("\n") if l.strip()]
        return lines[:10]
    except Exception:
        return []