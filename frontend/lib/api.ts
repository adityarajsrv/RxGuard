export type ConfidenceTier = "high" | "medium" | "unverified";

export interface SourceExtraction {
  source_name: string;
  source_url: string | null;
  active_ingredients: string[];
  strength_mg: Record<string, number>;
}

export interface ResolvedComposition {
  drug_name_input: string;
  confidence: ConfidenceTier;
  active_ingredients: string[];
  strength_mg: Record<string, number>;
  sources_checked: SourceExtraction[];
  disagreement_reason: string | null;
  usage_context: string | null;
  plain_summary: string | null;
}

export interface EquivalentDrug {
  brand_name: string;
  price_inr: number | null;
  seller: string | null;
  source_url: string | null;
}

export type InteractionVerdict =
  | "known_interaction"
  | "no_known_interaction"
  | "cannot_verify";

export interface InteractionResult {
  drug_a: string;
  drug_b: string;
  verdict: InteractionVerdict;
  severity: string | null;
  description: string | null;
  source: string | null;
}

export interface DrugCardResult {
  composition: ResolvedComposition;
  equivalents: EquivalentDrug[];
}

export interface VerifyResponse {
  drugs: DrugCardResult[];
  interactions: InteractionResult[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function verifyDrugs(drugNames: string[]): Promise<VerifyResponse> {
  const res = await fetch(`${API_BASE}/api/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drug_names: drugNames }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Verification failed (${res.status})`);
  }

  return res.json();
}

export async function verifyImage(file: File): Promise<VerifyResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/verify-image`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Image verification failed (${res.status})`);
  }

  return res.json();
}

export interface AskResponse {
  answer: string;
  grounded: boolean;
  verified: boolean | null;
}

export async function askAboutDrug(drugName: string, question: string, confidence: string): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drug_name: drugName, question, confidence }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Could not get an answer.");
  }

  return res.json();
}