from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import HtmlSnapshot, Paper, PaperSection
from app.schemas import PaperImportRequest, PaperOut, PaperScoreOut
from app.services import extraction, scoring
from app.services.graph_builder import build_graph_for_paper
from app.services.ingest import extract_text_from_pdf, split_sections
from app.services.snapshot import render_paper_snapshot

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[PaperOut])
def list_papers(db: Session = Depends(get_db)) -> list[Paper]:
    return db.query(Paper).order_by(Paper.id.desc()).all()


@router.post("/import", response_model=PaperOut)
def import_paper_json(payload: PaperImportRequest, db: Session = Depends(get_db)) -> Paper:
    paper = Paper(
        title=payload.title,
        authors=payload.authors,
        year=payload.year,
        doi=payload.doi,
        abstract=payload.abstract,
        full_text=payload.full_text,
        source_path=payload.source_path,
    )
    db.add(paper)
    db.flush()
    _persist_sections(db, paper, payload.full_text)
    db.commit()
    db.refresh(paper)
    return paper


@router.post("/upload", response_model=PaperOut)
async def import_paper_upload(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    authors: str | None = Form(None),
    year: int | None = Form(None),
    db: Session = Depends(get_db),
) -> Paper:
    raw = await file.read()
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        text = extract_text_from_pdf(raw)
    else:
        text = raw.decode("utf-8", errors="replace")
    if not text.strip():
        raise HTTPException(status_code=400, detail="empty document")

    paper = Paper(
        title=title or file.filename,
        authors=authors,
        year=year,
        full_text=text,
        source_path=file.filename,
    )
    db.add(paper)
    db.flush()
    _persist_sections(db, paper, text)
    db.commit()
    db.refresh(paper)
    return paper


@router.post("/paste")
async def import_paper_paste(
    title: str = Form("Untitled"),
    authors: str = Form(""),
    year: int = Form(None),
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    """Import a paper by pasting text directly."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    paper = Paper(
        title=title or "Pasted Paper",
        authors=authors,
        year=year,
        full_text=text.strip(),
        source_path="paste",
    )
    db.add(paper)
    db.flush()
    _persist_sections(db, paper, text.strip())
    db.commit()
    db.refresh(paper)
    return RedirectResponse(f"/papers/{paper.id}/view", status_code=303)


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)) -> Paper:
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(404, "paper not found")
    return paper


@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(404, "paper not found")
    db.delete(paper)
    db.commit()
    return {"ok": True}


# ---------- pipeline endpoints ----------


@router.post("/{paper_id}/extract-model")
def extract_model(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = _require_paper(db, paper_id)
    items = extraction.extract_paper_model(db, paper)
    return {"count": len(items)}


@router.post("/{paper_id}/extract-evidence")
def extract_evidence(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = _require_paper(db, paper_id)
    items = extraction.extract_evidence(db, paper)
    return {"count": len(items)}


@router.post("/{paper_id}/map-axioms")
def map_axioms(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = _require_paper(db, paper_id)
    mappings = extraction.map_axioms(db, paper)
    return {"count": len(mappings)}


@router.post("/{paper_id}/grade", response_model=PaperScoreOut)
def grade(paper_id: int, db: Session = Depends(get_db)) -> PaperScoreOut:
    paper = _require_paper(db, paper_id)
    score = scoring.grade_paper(db, paper)
    return PaperScoreOut.model_validate(score)


@router.post("/{paper_id}/build-graph")
def build_graph(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = _require_paper(db, paper_id)
    return build_graph_for_paper(db, paper)


@router.post("/{paper_id}/snapshot")
def make_snapshot(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = _require_paper(db, paper_id)
    snap = render_paper_snapshot(db, paper)
    return {"snapshot_id": snap.id, "bytes": len(snap.html_content)}


@router.get("/{paper_id}/snapshot", response_class=HTMLResponse)
def view_snapshot(paper_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    snap = (
        db.query(HtmlSnapshot)
        .filter(HtmlSnapshot.paper_id == paper_id)
        .order_by(HtmlSnapshot.id.desc())
        .first()
    )
    if snap is None:
        raise HTTPException(404, "no snapshot yet; POST /papers/{id}/snapshot first")
    return HTMLResponse(snap.html_content)


@router.post("/{paper_id}/run-all")
def run_full_pipeline(paper_id: int, db: Session = Depends(get_db)) -> dict:
    """Convenience endpoint: extract -> evidence -> axioms -> grade -> graph -> snapshot."""
    paper = _require_paper(db, paper_id)
    extraction.extract_paper_model(db, paper)
    extraction.extract_evidence(db, paper)
    extraction.map_axioms(db, paper)
    scoring.grade_paper(db, paper)
    build_graph_for_paper(db, paper)
    snap = render_paper_snapshot(db, paper)
    return JSONResponse({"ok": True, "snapshot_id": snap.id})


# ---------- helpers ----------


def _require_paper(db: Session, paper_id: int) -> Paper:
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(404, "paper not found")
    return paper


def _persist_sections(db: Session, paper: Paper, text: str) -> None:
    for sec in split_sections(text):
        db.add(
            PaperSection(
                paper_id=paper.id,
                heading=sec.heading,
                content=sec.content,
                order_index=sec.order_index,
            )
        )
