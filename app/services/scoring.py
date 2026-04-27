"""Scoring engine.

Hard rule: Ollama extracts BOOLEAN SIGNALS. Python computes the SCORES.
Never ask the LLM to grade on a 1-100 scale.

Component scores are 0-100. Overall is a weighted sum.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Paper, PaperScore
from app.schemas import ScoringSignals
from app.services.extraction import _truncate
from app.services.ollama_client import call_json_template

# Component weights (sum to 1.0)
WEIGHT_RIGOR = 0.30
WEIGHT_EVIDENCE = 0.30
WEIGHT_REPRO = 0.20
WEIGHT_CLARITY = 0.10
WEIGHT_LOW_BIAS = 0.10  # applied to (100 - bias_risk)


def _component_scores(s: ScoringSignals) -> dict[str, int]:
    rigor = (
        25 * int(s.variables_defined)
        + 25 * int(s.method_clear)
        + 25 * int(s.controls_present)
        + 25 * int(s.sample_size_mentioned)
    )
    evidence = (
        40 * int(s.direct_evidence_present)
        + 30 * int(s.statistical_results_present)
        + 30 * int(s.controls_present)
    )
    reproducibility = (
        50 * int(s.reproducible_steps)
        + 30 * int(s.data_available)
        + 20 * int(s.method_clear)
    )
    clarity = (
        50 * int(s.method_clear)
        + 30 * int(s.variables_defined)
        + 20 * int(s.limitations_discussed)
    )
    # bias_risk: HIGH risk when limitations are not discussed and conflicts not declared.
    bias_risk = (
        40 * int(not s.limitations_discussed)
        + 40 * int(not s.funding_or_conflicts_mentioned)
        + 20 * int(not s.direct_evidence_present)
    )
    return {
        "methodological_rigor": min(100, rigor),
        "evidence_strength": min(100, evidence),
        "reproducibility": min(100, reproducibility),
        "clarity": min(100, clarity),
        "bias_risk": min(100, bias_risk),
    }


def _overall(components: dict[str, int]) -> int:
    return round(
        components["methodological_rigor"] * WEIGHT_RIGOR
        + components["evidence_strength"] * WEIGHT_EVIDENCE
        + components["reproducibility"] * WEIGHT_REPRO
        + components["clarity"] * WEIGHT_CLARITY
        + (100 - components["bias_risk"]) * WEIGHT_LOW_BIAS
    )


def grade_paper(db: Session, paper: Paper) -> PaperScore:
    signals = call_json_template(
        "scoring_signals",
        ScoringSignals,
        paper_text=_truncate(paper.full_text),
    )
    components = _component_scores(signals)
    overall = _overall(components)

    existing = db.query(PaperScore).filter(PaperScore.paper_id == paper.id).one_or_none()
    if existing is None:
        existing = PaperScore(paper_id=paper.id)
        db.add(existing)

    for k, v in components.items():
        setattr(existing, k, v)
    existing.overall_score = overall
    existing.signals = signals.model_dump()
    existing.scoring_notes = signals.notes

    db.commit()
    db.refresh(existing)
    return existing
