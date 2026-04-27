from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

PAPER_MODEL_CATEGORIES = (
    "problem",
    "method",
    "variables",
    "mechanism",
    "evidence",
    "limitations",
    "implications",
)

EDGE_RELATIONSHIPS = (
    "supports",
    "contradicts",
    "extends",
    "depends_on",
    "uses_method",
    "has_evidence",
    "maps_to_axiom",
    "reframes",
    "weakens",
)

NODE_TYPES = ("paper", "claim", "variable", "method", "concept", "evidence", "axiom")


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    doi: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    sections: Mapped[list[PaperSection]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    model_items: Mapped[list[PaperModelItem]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    axiom_mappings: Mapped[list[AxiomMapping]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    evidence: Mapped[list[EvidenceItem]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    score: Mapped[PaperScore | None] = relationship(
        back_populates="paper", cascade="all, delete-orphan", uselist=False
    )
    snapshots: Mapped[list[HtmlSnapshot]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )


class PaperSection(Base):
    __tablename__ = "paper_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    heading: Mapped[str | None] = mapped_column(Text)
    section_type: Mapped[str | None] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    paper: Mapped[Paper] = relationship(back_populates="sections")


class PaperModelItem(Base):
    __tablename__ = "paper_model_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    source_quote: Mapped[str | None] = mapped_column(Text)
    source_section_id: Mapped[int | None] = mapped_column(
        ForeignKey("paper_sections.id", ondelete="SET NULL")
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    uncertainty_note: Mapped[str | None] = mapped_column(Text)

    paper: Mapped[Paper] = relationship(back_populates="model_items")
    evidence: Mapped[list[EvidenceItem]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class Axiom(Base):
    __tablename__ = "axioms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    mappings: Mapped[list[AxiomMapping]] = relationship(
        back_populates="axiom", cascade="all, delete-orphan"
    )


class AxiomMapping(Base):
    __tablename__ = "axiom_mappings"
    __table_args__ = (UniqueConstraint("paper_id", "axiom_id", name="uq_paper_axiom"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    axiom_id: Mapped[int] = mapped_column(
        ForeignKey("axioms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    source_quote: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    paper: Mapped[Paper] = relationship(back_populates="axiom_mappings")
    axiom: Mapped[Axiom] = relationship(back_populates="mappings")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claim_id: Mapped[int | None] = mapped_column(
        ForeignKey("paper_model_items.id", ondelete="CASCADE"), index=True
    )
    evidence_type: Mapped[str | None] = mapped_column(String(64))
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_quote: Mapped[str | None] = mapped_column(Text)
    strength_score: Mapped[float | None] = mapped_column(Float)
    weakness_note: Mapped[str | None] = mapped_column(Text)

    paper: Mapped[Paper] = relationship(back_populates="evidence")
    claim: Mapped[PaperModelItem | None] = relationship(back_populates="evidence")


class PaperScore(Base):
    __tablename__ = "paper_scores"
    __table_args__ = (UniqueConstraint("paper_id", name="uq_paper_score"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    methodological_rigor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_strength: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reproducibility: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clarity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bias_risk: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    signals: Mapped[dict | None] = mapped_column(JSONB)
    scoring_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="score")


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    paper_id: Mapped[int | None] = mapped_column(
        ForeignKey("papers.id", ondelete="SET NULL"), index=True
    )
    ref_table: Mapped[str | None] = mapped_column(String(64))
    ref_id: Mapped[int | None] = mapped_column(Integer)


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    strength: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(Text)
    source_quote: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)


class PaperComparison(Base):
    __tablename__ = "paper_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_a_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_b_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    comparison_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class HtmlSnapshot(Base):
    __tablename__ = "html_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_type: Mapped[str] = mapped_column(String(32), nullable=False, default="paper")
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="snapshots")
