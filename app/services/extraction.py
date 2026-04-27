"""Extraction services: paper-model, axioms, evidence.

Each function (a) calls Ollama with a strict-JSON prompt, (b) validates the
response against a Pydantic schema, (c) writes structured rows to Postgres,
(d) returns the persisted ORM rows.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    PAPER_MODEL_CATEGORIES,
    Axiom,
    AxiomMapping,
    EvidenceItem,
    Paper,
    PaperModelItem,
)
from app.schemas import (
    AxiomMappingResponse,
    EvidenceExtractionResponse,
    PaperModelExtractionResponse,
)
from app.services.ollama_client import call_json_template


def _truncate(text: str, max_chars: int = 24000) -> str:
    """Most local Ollama models choke past ~32k tokens; trim aggressively.

    For v1 we just truncate. v2 should chunk + map/reduce.
    """
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3) :]
    return f"{head}\n\n[...truncated...]\n\n{tail}"


def extract_paper_model(db: Session, paper: Paper) -> list[PaperModelItem]:
    response = call_json_template(
        "paper_model",
        PaperModelExtractionResponse,
        paper_text=_truncate(paper.full_text),
    )

    db.query(PaperModelItem).filter(PaperModelItem.paper_id == paper.id).delete()

    items: list[PaperModelItem] = []
    for entry in response.items:
        category = entry.category.lower().strip()
        if category not in PAPER_MODEL_CATEGORIES:
            continue
        item = PaperModelItem(
            paper_id=paper.id,
            category=category,
            claim=entry.claim.strip(),
            source_quote=(entry.source_quote or None),
            confidence=max(0.0, min(1.0, entry.confidence or 0.0)),
            uncertainty_note=entry.uncertainty_note,
        )
        db.add(item)
        items.append(item)

    db.commit()
    for item in items:
        db.refresh(item)
    return items


def map_axioms(db: Session, paper: Paper) -> list[AxiomMapping]:
    axioms: list[Axiom] = db.query(Axiom).order_by(Axiom.id).all()
    if not axioms:
        return []

    axioms_block = "\n".join(
        f"- {a.name}" + (f": {a.description}" if a.description else "") for a in axioms
    )

    response = call_json_template(
        "axiom_mapping",
        AxiomMappingResponse,
        axioms_block=axioms_block,
        paper_text=_truncate(paper.full_text),
    )

    by_name = {a.name: a for a in axioms}

    db.query(AxiomMapping).filter(AxiomMapping.paper_id == paper.id).delete()

    mappings: list[AxiomMapping] = []
    for m in response.mappings:
        axiom = by_name.get(m.axiom_name)
        if axiom is None:
            continue
        mapping = AxiomMapping(
            paper_id=paper.id,
            axiom_id=axiom.id,
            interpretation=m.interpretation.strip(),
            source_quote=(m.source_quote or None),
            confidence=max(0.0, min(1.0, m.confidence or 0.0)),
        )
        db.add(mapping)
        mappings.append(mapping)

    db.commit()
    for mapping in mappings:
        db.refresh(mapping)
    return mappings


def extract_evidence(db: Session, paper: Paper) -> list[EvidenceItem]:
    """Evidence is bound to claims by exact text match. Run AFTER paper-model extraction."""
    claims: list[PaperModelItem] = (
        db.query(PaperModelItem).filter(PaperModelItem.paper_id == paper.id).all()
    )
    if not claims:
        return []

    claims_block = "\n".join(f"- [{c.category}] {c.claim}" for c in claims)
    by_text = {c.claim.strip(): c for c in claims}

    response = call_json_template(
        "evidence",
        EvidenceExtractionResponse,
        claims_block=claims_block,
        paper_text=_truncate(paper.full_text),
    )

    db.query(EvidenceItem).filter(EvidenceItem.paper_id == paper.id).delete()

    items: list[EvidenceItem] = []
    for e in response.items:
        claim_obj = by_text.get(e.claim.strip())
        item = EvidenceItem(
            paper_id=paper.id,
            claim_id=claim_obj.id if claim_obj else None,
            evidence_type=e.evidence_type,
            evidence_text=e.evidence_text.strip(),
            source_quote=(e.source_quote or None),
            strength_score=max(0.0, min(1.0, e.strength_score or 0.0)),
            weakness_note=e.weakness_note,
        )
        db.add(item)
        items.append(item)

    db.commit()
    for item in items:
        db.refresh(item)
    return items
