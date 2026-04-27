"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-27

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "papers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text),
        sa.Column("authors", sa.Text),
        sa.Column("year", sa.Integer),
        sa.Column("doi", sa.Text),
        sa.Column("abstract", sa.Text),
        sa.Column("full_text", sa.Text, nullable=False),
        sa.Column("source_path", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "paper_sections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("heading", sa.Text),
        sa.Column("section_type", sa.String(64)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "paper_model_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("category", sa.String(32), nullable=False, index=True),
        sa.Column("claim", sa.Text, nullable=False),
        sa.Column("source_quote", sa.Text),
        sa.Column(
            "source_section_id",
            sa.Integer,
            sa.ForeignKey("paper_sections.id", ondelete="SET NULL"),
        ),
        sa.Column("confidence", sa.Float),
        sa.Column("uncertainty_note", sa.Text),
    )

    op.create_table(
        "axioms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("category", sa.String(64)),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "axiom_mappings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "axiom_id",
            sa.Integer,
            sa.ForeignKey("axioms.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("interpretation", sa.Text, nullable=False),
        sa.Column("source_quote", sa.Text),
        sa.Column("confidence", sa.Float),
        sa.UniqueConstraint("paper_id", "axiom_id", name="uq_paper_axiom"),
    )

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "claim_id",
            sa.Integer,
            sa.ForeignKey("paper_model_items.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("evidence_type", sa.String(64)),
        sa.Column("evidence_text", sa.Text, nullable=False),
        sa.Column("source_quote", sa.Text),
        sa.Column("strength_score", sa.Float),
        sa.Column("weakness_note", sa.Text),
    )

    op.create_table(
        "paper_scores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("methodological_rigor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_strength", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reproducibility", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clarity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bias_risk", sa.Integer, nullable=False, server_default="0"),
        sa.Column("overall_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("signals", postgresql.JSONB),
        sa.Column("scoring_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("paper_id", name="uq_paper_score"),
    )

    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("node_type", sa.String(32), nullable=False, index=True),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column("ref_table", sa.String(64)),
        sa.Column("ref_id", sa.Integer),
    )

    op.create_table(
        "graph_edges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "source_node_id",
            sa.Integer,
            sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_node_id",
            sa.Integer,
            sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("relationship_type", sa.String(32), nullable=False, index=True),
        sa.Column("strength", sa.Float),
        sa.Column("explanation", sa.Text),
        sa.Column("source_quote", sa.Text),
        sa.Column("confidence", sa.Float),
    )

    op.create_table(
        "paper_comparisons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_a_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "paper_b_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("comparison_json", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "html_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "paper_id",
            sa.Integer,
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("snapshot_type", sa.String(32), nullable=False, server_default="paper"),
        sa.Column("html_content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "html_snapshots",
        "paper_comparisons",
        "graph_edges",
        "graph_nodes",
        "paper_scores",
        "evidence_items",
        "axiom_mappings",
        "axioms",
        "paper_model_items",
        "paper_sections",
        "papers",
    ):
        op.drop_table(table)
