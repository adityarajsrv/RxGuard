import os
import json
import hashlib
import numpy as np
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
EMBED_MODEL = "models/gemini-embedding-001"

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _embed(text: str, task_type: str) -> list[float]:
    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        task_type=task_type,
    )
    return result["embedding"]


def _cache_key(prefix: str, task_type: str, text: str) -> str:
    h = hashlib.sha256(text.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"embed_{prefix}_{task_type}_{h}.json")


def _embed_cached(prefix: str, text: str, task_type: str) -> list[float]:
    path = _cache_key(prefix, task_type, text)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    vec = _embed(text, task_type)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vec, f)
    return vec


def _cosine_sim(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_label_chunks(drug_name: str, sections: dict[str, str | None]) -> list[dict]:
    chunks = []
    for section_name, text in sections.items():
        if text:
            chunks.append({"section": section_name, "text": text[:2000]})
    return chunks

def verify_answer_against_chunks(answer: str, chunks: list[dict]) -> dict:
    context = "\n\n".join(f"[{c['section']}]: {c['text']}" for c in chunks)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    prompt = f"""You are a strict fact-checking auditor. Your job is to find problems, \
not to agree.

Source excerpts (the ONLY ground truth):
{context}

Generated answer to audit:
"{answer}"

Go through the answer sentence by sentence. For each factual claim, ask: is this \
EXPLICITLY stated in the source excerpts, or is it inferred, generalized, or added \
by the model beyond what the source says?

Common issues to catch:
- The answer adds a recommendation, comparison, or detail not present in the excerpts
- The answer generalizes a specific condition into a broader claim
- The answer states something as fact that the excerpts only imply or don't mention

If EVERY factual claim traces directly to the excerpts, respond: SUPPORTED
If ANY claim goes beyond, generalizes, or isn't directly stated in the excerpts, respond: UNSUPPORTED

Respond with ONLY one word."""

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0})
        verdict = response.text.strip().upper()
        print(f"AUDIT RAW VERDICT: {verdict!r}")
        return {"verified": "SUPPORTED" in verdict and "UNSUPPORTED" not in verdict}
    except Exception as e:
        print(f"AUDIT CALL FAILED: {e}")
        return {"verified": None}

def answer_from_chunks(question: str, chunks: list[dict], drug_name: str) -> dict:
    if not chunks:
        return {
            "answer": f"I don't have official FDA label information for {drug_name} yet to answer that safely — it's best to check with a pharmacist on this one.",
            "grounded": False,
        }

    q_vec = _embed_cached("query", question, task_type="retrieval_query")
    scored = []
    for chunk in chunks:
        c_vec = _embed_cached("chunk", chunk["text"], task_type="retrieval_document")
        score = _cosine_sim(q_vec, c_vec)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for score, c in scored[:2] if score > 0.5]

    if not top_chunks:
        return {
            "answer": f"That's outside what I can verify from {drug_name}'s official label right now — a pharmacist would be able to give you a reliable answer on this specific question.",
            "grounded": False,
        }

    context = "\n\n".join(f"[{c['section']}]: {c['text']}" for c in top_chunks)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    prompt = f"""Using ONLY the FDA label excerpts below about {drug_name}, answer the \
user's question in warm, plain language, like a knowledgeable friend, not a legal document.

If the excerpts don't actually answer the question, say so honestly and kindly — \
acknowledge what you DO know about {drug_name} from the excerpts if anything is relevant, \
then suggest they ask a pharmacist for the specific answer. Never say things like "the \
provided text does not state" — instead say something like "I don't have reliable \
information on that specific point for {drug_name}, but here's what I do know..." \
or, if nothing is relevant at all, "I'd recommend checking with a pharmacist for that \
one — it's outside what I can verify from the official label."

Excerpts:
{context}

Question: {question}

Answer in 2-3 sentences, plain English, no medical jargon, no clinical coldness."""

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0})
        answer_text = response.text.strip()
        audit = verify_answer_against_chunks(answer_text, top_chunks)
        return {"answer": answer_text, "grounded": True, "verified": audit["verified"]}
    except Exception:
        return {"answer": "Could not generate an answer right now.", "grounded": False, "verified": None}
