from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Axiom, Paper, PaperComparison
from app.routers import axioms, compare, graph, papers

app = FastAPI(title="Treaties — Research Intelligence Engine", version="0.1.0")

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

app.include_router(papers.router)
app.include_router(axioms.router)
app.include_router(graph.router)
app.include_router(compare.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "papers": db.query(Paper).order_by(Paper.id.desc()).all(),
            "axioms": db.query(Axiom).order_by(Axiom.id).all(),
            "comparisons": db.query(PaperComparison)
            .order_by(PaperComparison.id.desc())
            .limit(20)
            .all(),
        },
    )


@app.get("/papers/{paper_id}/view", response_class=HTMLResponse)
def paper_view(paper_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    paper = db.get(Paper, paper_id)
    if paper is None:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    return templates.TemplateResponse(
        "paper_detail.html", {"request": request, "paper": paper}
    )


@app.get("/health")
def health() -> dict:
    return {"ok": True}
