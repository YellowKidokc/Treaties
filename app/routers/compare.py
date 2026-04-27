from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Paper, PaperComparison
from app.schemas import ComparisonRequest
from app.services.comparison import compare_papers

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("")
def run_comparison(payload: ComparisonRequest, db: Session = Depends(get_db)) -> dict:
    if payload.paper_a_id == payload.paper_b_id:
        raise HTTPException(400, "paper_a_id and paper_b_id must differ")
    paper_a = db.get(Paper, payload.paper_a_id)
    paper_b = db.get(Paper, payload.paper_b_id)
    if paper_a is None or paper_b is None:
        raise HTTPException(404, "one or both papers not found")
    record = compare_papers(db, paper_a, paper_b)
    return {"comparison_id": record.id, "comparison": record.comparison_json}


@router.get("/{comparison_id}")
def get_comparison(comparison_id: int, db: Session = Depends(get_db)) -> dict:
    record = db.get(PaperComparison, comparison_id)
    if record is None:
        raise HTTPException(404, "comparison not found")
    return {
        "id": record.id,
        "paper_a_id": record.paper_a_id,
        "paper_b_id": record.paper_b_id,
        "comparison": record.comparison_json,
    }


@router.get("")
def list_comparisons(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": r.id,
            "paper_a_id": r.paper_a_id,
            "paper_b_id": r.paper_b_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in db.query(PaperComparison).order_by(PaperComparison.id.desc()).all()
    ]
