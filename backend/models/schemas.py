from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ConfidenceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    UNVERIFIED = "unverified"


class SourceExtraction(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    active_ingredients: list[str]
    strength_mg: dict[str, float] = Field(default_factory=dict)
    raw_text_snippet: Optional[str] = None


class ResolvedComposition(BaseModel):
    drug_name_input: str
    confidence: ConfidenceTier
    active_ingredients: list[str] = Field(default_factory=list)
    strength_mg: dict[str, float] = Field(default_factory=dict)
    sources_checked: list[SourceExtraction] = Field(default_factory=list)
    disagreement_reason: Optional[str] = None
    usage_context: Optional[str] = None
    plain_summary: Optional[str] = None


class EquivalentDrug(BaseModel):
    brand_name: str
    price_inr: Optional[float] = None
    seller: Optional[str] = None
    source_url: Optional[str] = None


class InteractionVerdict(str, Enum):
    KNOWN_INTERACTION = "known_interaction"
    NO_KNOWN_INTERACTION = "no_known_interaction"
    CANNOT_VERIFY = "cannot_verify"


class InteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    verdict: InteractionVerdict
    severity: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None


class DrugCardResult(BaseModel):
    composition: ResolvedComposition
    equivalents: list[EquivalentDrug] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    drug_names: list[str] = Field(..., min_length=1, max_length=10)


class VerifyResponse(BaseModel):
    drugs: list[DrugCardResult]
    interactions: list[InteractionResult] = Field(default_factory=list)