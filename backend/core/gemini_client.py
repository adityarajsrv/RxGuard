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