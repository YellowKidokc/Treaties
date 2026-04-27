"""Promote ORM rows into the typed graph.

For each paper we materialize:

    [paper] --has_claim--> [claim] --has_evidence--> [evidence]
                                  \\--maps_to_axiom--> [axiom]

Cross-paper edges (supports / contradicts / extends / reframes) are written by
the comparison engine, not here.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    Axiom,
    AxiomMapping,
    EvidenceItem,
    GraphEdge,
    GraphNode,
    Paper,
    PaperModelItem,
)


def _upsert_node(
    db: Session,
    *,
    node_type: str,
    label: str,
    description: str | None = None,
    paper_id: int | None = None,
    ref_table: str | None = None,
    ref_id: int | None = None,
) -> GraphNode:
    if ref_table and ref_id is not None:
        existing = (
            db.query(GraphNode)
            .filter(GraphNode.ref_table == ref_table, GraphNode.ref_id == ref_id)
            .one_or_none()
        )
        if existing is not None:
            existing.label = label
            existing.description = description
            existing.paper_id = paper_id
            return existing

    node = GraphNode(
        node_type=node_type,
        label=label,
        description=description,
        paper_id=paper_id,
        ref_table=ref_table,
        ref_id=ref_id,
    )
    db.add(node)
    db.flush()
    return node


def _add_edge(
    db: Session,
    *,
    source: GraphNode,
    target: GraphNode,
    relationship_type: str,
    strength: float | None = None,
    explanation: str | None = None,
    source_quote: str | None = None,
    confidence: float | None = None,
) -> GraphEdge:
    edge = GraphEdge(
        source_node_id=source.id,
        target_node_id=target.id,
        relationship_type=relationship_type,
        strength=strength,
        explanation=explanation,
        source_quote=source_quote,
        confidence=confidence,
    )
    db.add(edge)
    return edge


def build_graph_for_paper(db: Session, paper: Paper) -> dict[str, int]:
    # Wipe this paper's intra-paper edges so re-runs are idempotent.
    paper_node_ids = (
        db.query(GraphNode.id).filter(GraphNode.paper_id == paper.id).subquery()
    )
    db.query(GraphEdge).filter(
        GraphEdge.source_node_id.in_(paper_node_ids)
        | GraphEdge.target_node_id.in_(paper_node_ids)
    ).filter(
        GraphEdge.relationship_type.in_(("has_evidence", "maps_to_axiom", "depends_on"))
    ).delete(synchronize_session=False)

    paper_node = _upsert_node(
        db,
        node_type="paper",
        label=paper.title or f"Paper {paper.id}",
        description=paper.abstract,
        paper_id=paper.id,
        ref_table="papers",
        ref_id=paper.id,
    )

    claim_nodes: dict[int, GraphNode] = {}
    for claim in db.query(PaperModelItem).filter(PaperModelItem.paper_id == paper.id):
        node = _upsert_node(
            db,
            node_type="claim",
            label=claim.claim,
            description=f"[{claim.category}] confidence={claim.confidence}",
            paper_id=paper.id,
            ref_table="paper_model_items",
            ref_id=claim.id,
        )
        claim_nodes[claim.id] = node
        _add_edge(
            db,
            source=paper_node,
            target=node,
            relationship_type="depends_on",
            confidence=claim.confidence,
        )

    for ev in db.query(EvidenceItem).filter(EvidenceItem.paper_id == paper.id):
        ev_node = _upsert_node(
            db,
            node_type="evidence",
            label=ev.evidence_text,
            description=ev.evidence_type,
            paper_id=paper.id,
            ref_table="evidence_items",
            ref_id=ev.id,
        )
        if ev.claim_id and ev.claim_id in claim_nodes:
            _add_edge(
                db,
                source=claim_nodes[ev.claim_id],
                target=ev_node,
                relationship_type="has_evidence",
                strength=ev.strength_score,
                source_quote=ev.source_quote,
            )

    for mapping in db.query(AxiomMapping).filter(AxiomMapping.paper_id == paper.id):
        axiom: Axiom = mapping.axiom
        axiom_node = _upsert_node(
            db,
            node_type="axiom",
            label=axiom.name,
            description=axiom.description,
            ref_table="axioms",
            ref_id=axiom.id,
        )
        _add_edge(
            db,
            source=paper_node,
            target=axiom_node,
            relationship_type="maps_to_axiom",
            confidence=mapping.confidence,
            explanation=mapping.interpretation,
            source_quote=mapping.source_quote,
        )

    db.commit()

    return {
        "claims": len(claim_nodes),
        "axioms": db.query(AxiomMapping).filter(AxiomMapping.paper_id == paper.id).count(),
        "evidence": db.query(EvidenceItem).filter(EvidenceItem.paper_id == paper.id).count(),
    }
