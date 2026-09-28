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
    entered_strength_mg: Optional[float] = None
    verification_basis: str = "web_sources"
    prescription_only: Optional[bool] = None
    equivalents_note: Optional[str] = None


class EquivalentDrug(BaseModel):
    brand_name: str
    price_inr: Optional[float] = None
    seller: Optional[str] = None
    source_url: Optional[str] = None
    pack_size: Optional[int] = None
    price_per_unit: Optional[float] = None


class InteractionVerdict(str, Enum):
    KNOWN_INTERACTION = "known_interaction"
    DUPLICATE_INGREDIENT = "duplicate_ingredient"
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


class AskRequest(BaseModel):
    drug_name: str = Field(..., min_length=1, max_length=80)
    question: str = Field(..., min_length=1, max_length=300)
    confidence: Optional[str] = None


class VerifyResponse(BaseModel):
    drugs: list[DrugCardResult]
    interactions: list[InteractionResult] = Field(default_factory=list)