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