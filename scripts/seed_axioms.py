"""Seed a starter set of axioms.

Usage:
    python scripts/seed_axioms.py
"""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import Axiom

SEED = [
    ("Causality requires mechanism",
     "epistemology",
     "A causal claim must specify a mechanism, not just correlation."),
    ("Evidence strength depends on reproducibility",
     "epistemology",
     "Findings that cannot be reproduced should not be treated as established."),
    ("A variable must be operationalized",
     "method",
     "Every claimed variable must have a concrete measurement procedure."),
    ("Negative results carry information",
     "method",
     "Failure to find an effect is itself evidence and must be reported."),
    ("Conservation laws constrain claims",
     "physics",
     "Physical claims that violate conservation principles bear a higher burden of proof."),
    ("Falsifiability is required",
     "epistemology",
     "A scientific claim must specify what observation would refute it."),
]


def main() -> None:
    db = SessionLocal()
    try:
        for name, category, description in SEED:
            db.add(Axiom(name=name, category=category, description=description))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                print(f"  skip (already exists): {name}")
            else:
                print(f"  added: {name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
