# RxGuard

A medicine safety verification tool that refuses to guess. RxGuard checks what's actually in a medicine, whether it's safe alongside other medicines, and what it's typically used for — using live search data and the FDA's own drug label database, not a static dataset and not a language model's memory.

Built for the SerpApi India Hackathon 2026, track: **Knowledge & Public Interest**.

---

## The problem

Medicine names on Indian pharmacy shelves are often brand names (Crocin, Combiflam, Dolo) that don't tell you what's actually inside. Two medicines with different names can contain the same active ingredient, risking an accidental overdose. Two medicines with different purposes can interact dangerously. Most people have no fast, free way to check any of this before they combine medications.

## What RxGuard actually does

1. **Resolves composition.** Given a medicine name, RxGuard cross-checks multiple independent pharmacy sources (via live Google Search) and extracts the active ingredients and strength. It only trusts a result when two or more sources agree — one source gets "Medium confidence," and disagreement or no data gets "Unverified." A recognized generic name (e.g. "Warfarin") is treated as its own verification, since no brand-to-ingredient guess is needed.
2. **Checks interactions.** For verified medicines, RxGuard queries the FDA's structured drug label database (openFDA) for documented interactions, with a small curated dataset as a fallback. It also flags when two medicines share the same active ingredient — a common, under-recognized overdose risk (e.g. two different paracetamol-containing products).
3. **Explains usage in plain language.** Pulls the official FDA indication text and rewrites it in one or two plain sentences — never inventing dosing advice.
4. **Finds cheaper equivalents**, but only when strength is confirmed and the drug isn't prescription-only, since substitution decisions on prescription medicines belong to a doctor or pharmacist, not a lookup tool.
5. **Answers free-text questions** ("can I take this with alcohol?") using retrieval-augmented generation grounded in the same FDA label text — and audits its own answer against the source before showing it, flagging anything that isn't directly supported.
6. **Reads a photo of the strip or prescription**, extracting the printed name, ingredients, and strength directly from the packaging as an independent source, cross-checked against the web the same way.

At every step, when the system can't verify something, it says so — it does not guess and present the guess as fact. This is the core design decision the whole tool is built around.

---

## Why it's built this way (not a chatbot wrapper)

The single most important architectural decision in RxGuard is this: **the language model never decides what to trust.** Gemini is used only to *read* messy web/label text and extract structured data, or to *rephrase* a result already found by deterministic code. The confidence tier (High / Medium / Unverified) is decided by plain Python logic that can be read, tested, and audited — not by asking a model if it's confident.

This connects to a documented direction in recent safety-critical LLM research:

- **["Trust but Verify: Mitigating Medical Hallucinations via Post-Hoc Adversarial Auditing and Multi-Agent Feedback Loops"](https://arxiv.org/abs/2606.14149)** (Osama et al., 2026) — tests whether LLMs recommend banned or withdrawn pharmaceuticals when answering clinical questions, and evaluates a multi-agent, post-hoc adversarial auditing approach to catch these errors after generation rather than trusting the model's first answer. Two things from this paper directly shaped RxGuard: first, that a model's training-time knowledge of drugs can be outdated or wrong in ways it won't flag on its own, which is why RxGuard queries openFDA live on every request instead of relying on Gemini's internal knowledge; second, the core idea of auditing an answer *after* it's generated, which RxGuard implements directly — every "Ask" answer is checked in a second pass against the source text it was supposedly grounded in, before being shown to the user.
- **["Retrieval-augmented generation for medication safety: A case study using drug package inserts"](https://sciencedirect.com/science/article/abs/pii/S1386505626003394)** (2026) — evaluates RAG grounded specifically in drug package insert / label text for patient medication safety education, reporting strong performance in structured lookups and real limitations in more complex clinical reasoning. This is the direct precedent for RxGuard's scoping decision: fixed-field lookups (composition, interactions, usage) for the safety-critical checks, with free-text RAG offered only as a secondary "Ask" feature, explicitly labeled, with a visible self-audit and an honest refusal path rather than a forced answer.
- **["A multi-agent GraphRAG framework for pharmacotherapy safety verification in clinical decision support systems"](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1898857/full)** (Frontiers in Medicine, 2026) — argues that an LLM's internal knowledge is frozen at training time while drug safety data (recalls, new findings) updates continuously, so live retrieval from external sources is necessary rather than optional in this domain. This is the same justification behind querying openFDA live rather than caching a static snapshot of drug data.

---

## Architecture

```
User input (typed names, or a photo of a strip)
        │
        ▼
Composition resolution
  ├─ Recognized generic name?
  │     → openFDA identity match (no brand ambiguity to resolve)
  └─ Brand name?
        → SerpApi search across 1mg, Netmeds, PharmEasy, Apollo Pharmacy
        → Gemini extracts structured {ingredient, strength} per source
        → deterministic confidence gate compares all sources
        │
        ▼
Confidence tier: High / Medium / Unverified
        │
        ├─ High only
        │     → SerpApi Shopping search for equivalents
        │       (filtered, deduped, blocked for prescription-only drugs)
        │
        ├─ High or Medium
        │     → openFDA interaction + usage + warnings lookup
        │     → Gemini paraphrases FDA text into plain language
        │
        └─ Unverified
              → nothing further attempted; system says so explicitly
        │
        ▼
Free-text "Ask" (optional, per drug)
  → openFDA label sections embedded (gemini-embedding-001)
  → question embedded, cosine similarity retrieves relevant sections
  → Gemini answers using only retrieved text
  → second Gemini pass audits the answer against the source, flags if unsupported
```

**Backend:** Python, FastAPI
**Frontend:** Next.js, TypeScript, Tailwind CSS
**Search data:** [SerpApi](https://serpapi.com/) — Google Search API (composition sourcing) and Google Shopping API (equivalent pricing)
**Regulatory data:** [openFDA Drug Label API](https://open.fda.gov/apis/drug/label/) — official FDA structured drug labels, free, no license restrictions
**AI:** Google Gemini (`gemini-3.1-flash-lite` for extraction/generation, `gemini-embedding-001` for retrieval embeddings)

---

## Known limitations (stated honestly, not hidden)

- **Composition resolution depends on live web search quality**, which can vary run to run. When independent sources genuinely disagree — including when one source is a mismatched or low-quality page — RxGuard reports "Unverified" rather than guessing which source is right. This is by design, but it means occasionally a real, correctly-composed medicine will show as unverified rather than confidently resolved.
- **openFDA interaction and label data is strongest for prescription and widely-marketed US drugs.** Some India-specific OTC combination products have thin or no FDA label coverage; the curated fallback dataset covers a deliberately scoped set of well-documented interactions, not an exhaustive pharmacology database.
- **"Prescription-only" status is inferred from FDA label metadata**, which may not always match a drug's regulatory status in India specifically.
- **This is a prototype, not a certified medical device.** Every result carries this disclaimer in the UI. Users are directed to a pharmacist or doctor for actual medical decisions.

---

## Disclosures

**Did this project exist before the hackathon?** No — built entirely during the hackathon window.

**AI tools used:**
- **Claude (Anthropic)** — used throughout development for architecture design, debugging, and code generation assistance.
- **Google Gemini API** (`gemini-3.1-flash-lite`, `gemini-embedding-001`) — used *within the product itself* at runtime for structured extraction, plain-language summarization, and retrieval-augmented question answering. This is a core product dependency, not a development tool.
- **Lovable** — used for initial frontend UI scaffolding.

---

## Setup

Each subfolder has its own `README.md` with exact run commands. Quick start:

### Backend
```bash
cd backend
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # fill in SERPAPI_KEY and GEMINI_API_KEY
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### Required API keys
- **SerpApi:** free account at [serpapi.com](https://serpapi.com/) — 250 searches/month free tier
- **Gemini:** free key at [Google AI Studio](https://aistudio.google.com/apikey)

---

## Data sources

- [SerpApi](https://serpapi.com/) — Google Search API and Google Shopping API
- [openFDA Drug Label API](https://open.fda.gov/apis/drug/label/) — U.S. FDA structured drug labeling data
- Curated interaction dataset (`data/interactions.csv`) — compiled from well-documented, widely-referenced drug interactions, used as a fallback when openFDA label data doesn't cover a specific pair