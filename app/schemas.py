from __future__ import annotations

from pydantic import BaseModel, Field

# ---------- Paper import ----------


class PaperImportRequest(BaseModel):
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    full_text: str = Field(..., min_length=1)
    source_path: str | None = None


class PaperOut(BaseModel):
    id: int
    title: str | None
    authors: str | None
    year: int | None
    doi: str | None
    abstract: str | None

    model_config = {"from_attributes": True}


# ---------- Universal Paper Model ----------


class PaperModelExtractedItem(BaseModel):
    category: str
    claim: str
    source_quote: str | None = None
    confidence: float = 0.0
    uncertainty_note: str | None = None


class PaperModelExtractionResponse(BaseModel):
    items: list[PaperModelExtractedItem]


# ---------- Axioms ----------


class AxiomCreate(BaseModel):
    name: str
    category: str | None = None
    description: str | None = None


class AxiomOut(BaseModel):
    id: int
    name: str
    category: str | None
    description: str | None

    model_config = {"from_attributes": True}


class AxiomMappingExtracted(BaseModel):
    axiom_name: str
    interpretation: str
    source_quote: str | None = None
    confidence: float = 0.0


class AxiomMappingResponse(BaseModel):
    mappings: list[AxiomMappingExtracted]


# ---------- Evidence ----------


class EvidenceExtractedItem(BaseModel):
    claim: str  # the claim text this evidence backs (used to re-link by content)
    evidence_type: str | None = None
    evidence_text: str
    source_quote: str | None = None
    strength_score: float = 0.0
    weakness_note: str | None = None


class EvidenceExtractionResponse(BaseModel):
    items: list[EvidenceExtractedItem]


# ---------- Scoring signals (Ollama returns booleans; Python computes scores) ----------


class ScoringSignals(BaseModel):
    sample_size_mentioned: bool = False
    variables_defined: bool = False
    method_clear: bool = False
    controls_present: bool = False
    limitations_discussed: bool = False
    data_available: bool = False
    reproducible_steps: bool = False
    funding_or_conflicts_mentioned: bool = False
    statistical_results_present: bool = False
    direct_evidence_present: bool = False
    notes: str | None = None


class PaperScoreOut(BaseModel):
    methodological_rigor: int
    evidence_strength: int
    reproducibility: int
    clarity: int
    bias_risk: int
    overall_score: int
    signals: dict | None
    scoring_notes: str | None

    model_config = {"from_attributes": True}


# ---------- Graph ----------


class GraphNodeOut(BaseModel):
    id: int
    node_type: str
    label: str
    description: str | None
    paper_id: int | None
    ref_table: str | None
    ref_id: int | None

    model_config = {"from_attributes": True}


class GraphEdgeOut(BaseModel):
    id: int
    source_node_id: int
    target_node_id: int
    relationship_type: str
    strength: float | None
    explanation: str | None
    source_quote: str | None
    confidence: float | None

    model_config = {"from_attributes": True}


class GraphPayload(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


# ---------- Comparison ----------


class ComparisonRequest(BaseModel):
    paper_a_id: int
    paper_b_id: int


class ComparisonRow(BaseModel):
    claim_a: str
    claim_b: str
    relationship: str  # supports / contradicts / extends / reframes / unrelated
    why: str
    evidence_strength_a: float | None = None
    evidence_strength_b: float | None = None


class ComparisonResult(BaseModel):
    shared_concepts: list[str] = []
    rows: list[ComparisonRow] = []
    notes: str | None = None
