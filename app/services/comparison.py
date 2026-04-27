"""Two-paper comparison.

Ollama generates a structured JSON comparison; we persist it to
paper_comparisons and write cross-paper edges into the graph for any row whose
relationship is one of {supports, contradicts, extends, reframes}.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import GraphEdge, GraphNode, Paper, PaperComparison, PaperModelItem
from app.schemas import ComparisonResult
from app.services.extraction import _truncate
from app.services.ollama_client import call_json_template

CROSS_PAPER_REL = {"supports", "contradicts", "extends", "reframes", "weakens"}


def _claims_block(db: Session, paper_id: int) -> str:
    rows = db.query(PaperModelItem).filter(PaperModelItem.paper_id == paper_id).all()
    if not rows:
        return "(no extracted claims)"
    return "\n".join(f"- [{r.category}] {r.claim}" for r in rows)


def _claim_node_by_text(db: Session, paper_id: int, claim_text: str) -> GraphNode | None:
    claim = (
        db.query(PaperModelItem)
        .filter(PaperModelItem.paper_id == paper_id, PaperModelItem.claim == claim_text)
        .one_or_none()
    )
    if claim is None:
        return None
    return (
        db.query(GraphNode)
        .filter(GraphNode.ref_table == "paper_model_items", GraphNode.ref_id == claim.id)
        .one_or_none()
    )


def compare_papers(db: Session, paper_a: Paper, paper_b: Paper) -> PaperComparison:
    result: ComparisonResult = call_json_template(
        "comparison",
        ComparisonResult,
        claims_a_block=_claims_block(db, paper_a.id),
        claims_b_block=_claims_block(db, paper_b.id),
        paper_a_text=_truncate(paper_a.full_text, max_chars=12000),
        paper_b_text=_truncate(paper_b.full_text, max_chars=12000),
    )

    record = PaperComparison(
        paper_a_id=paper_a.id,
        paper_b_id=paper_b.id,
        comparison_json=result.model_dump(),
    )
    db.add(record)

    for row in result.rows:
        rel = row.relationship.strip().lower()
        if rel not in CROSS_PAPER_REL:
            continue
        node_a = _claim_node_by_text(db, paper_a.id, row.claim_a)
        node_b = _claim_node_by_text(db, paper_b.id, row.claim_b)
        if node_a is None or node_b is None:
            continue
        db.add(
            GraphEdge(
                source_node_id=node_a.id,
                target_node_id=node_b.id,
                relationship_type=rel,
                strength=(row.evidence_strength_a or 0) + (row.evidence_strength_b or 0),
                explanation=row.why,
            )
        )

    db.commit()
    db.refresh(record)
    return record
