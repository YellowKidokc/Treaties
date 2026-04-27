"""Import the sample paper for smoke testing.

Usage:
    python scripts/import_sample.py
"""
from __future__ import annotations

from pathlib import Path

from app.db import SessionLocal
from app.models import Paper, PaperSection
from app.services.ingest import split_sections


def main() -> None:
    text = Path(__file__).parent.joinpath("sample_paper.txt").read_text(encoding="utf-8")
    db = SessionLocal()
    try:
        paper = Paper(
            title="Mild Sleep Restriction and Working Memory",
            authors="A. Researcher, B. Collaborator",
            year=2024,
            abstract=(
                "Within-subjects study (n=32) of 5h sleep restriction; "
                "14% drop in 2-back accuracy with partial recovery."
            ),
            full_text=text,
            source_path="sample_paper.txt",
        )
        db.add(paper)
        db.flush()
        for sec in split_sections(text):
            db.add(
                PaperSection(
                    paper_id=paper.id,
                    heading=sec.heading,
                    content=sec.content,
                    order_index=sec.order_index,
                )
            )
        db.commit()
        print(f"imported paper id={paper.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
