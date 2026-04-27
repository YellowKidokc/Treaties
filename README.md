# Treaties

Local-first research intelligence engine.

Ingest scientific papers → extract a Universal Paper Model → map them onto your custom Axiom Model → grade evidence quality from extracted signals → connect claims into a knowledge graph → compare papers → export a standalone HTML snapshot.

**Postgres is the source of truth. HTML is generated output.**

---

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL (via SQLAlchemy 2.0 + Alembic)
- Ollama (local LLM, strict-JSON prompts)
- Jinja2 (HTML snapshots)
- pypdf (optional PDF text extraction)

## Project layout

```
app/
  main.py              FastAPI entrypoint
  config.py            env/settings
  db.py                engine + session
  models.py            SQLAlchemy ORM
  schemas.py           Pydantic request/response models
  routers/             HTTP routes
    papers.py
    axioms.py
    graph.py
    compare.py
    snapshots.py
  services/
    ollama_client.py   strict-JSON LLM caller
    extraction.py      paper-model + axiom mapping
    scoring.py         signals -> component scores -> overall
    graph_builder.py   builds nodes/edges
    comparison.py      two-paper comparison
  prompts/             prompt templates (text files)
  templates/           Jinja2 templates
alembic/               migrations
scripts/seed_axioms.py seed example axioms
```

## Quickstart

```bash
# 1. Postgres
createdb treaties
psql treaties -c "CREATE USER treaties WITH PASSWORD 'treaties';"
psql treaties -c "GRANT ALL ON DATABASE treaties TO treaties;"

# 2. Python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 3. Env
cp .env.example .env

# 4. Migrate
alembic upgrade head

# 5. Ollama (separate terminal)
ollama pull llama3.1:8b-instruct-q4_K_M
ollama serve

# 6. Seed axioms (optional)
python scripts/seed_axioms.py

# 7. Run
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## Core flow

1. `POST /papers/import` — upload `.txt`, `.md`, `.pdf`, or paste text.
2. `POST /papers/{id}/extract-model` — Ollama extracts problem/method/variables/mechanism/evidence/limitations/implications as JSON, validated, written to `paper_model_items`.
3. `POST /papers/{id}/map-axioms` — for each axiom, Ollama returns interpretation + source quote + confidence.
4. `POST /papers/{id}/grade` — Ollama returns boolean *signals*; Python computes component scores and overall.
5. `POST /papers/{id}/build-graph` — promotes paper, claims, evidence, axioms to `graph_nodes`; writes typed `graph_edges`.
6. `POST /compare` — two papers in, JSONB comparison out (shared concepts, contradictions, evidence deltas).
7. `POST /papers/{id}/snapshot` — render Jinja2 to a standalone HTML file (also cached in `html_snapshots`).

## Design rules

- **Postgres canonical.** HTML is a cached artifact, not source.
- **LLM extracts signals; Python decides scores.** Never ask Ollama "give a score 1-10".
- **Every claim carries traceability:** `claim → source_quote → source paper`.
- **Strict JSON.** All Ollama calls request JSON and are validated against Pydantic before insert.
- **Tight relationship vocabulary.** `supports / contradicts / extends / depends_on / uses_method / has_evidence / maps_to_axiom`.

## One-week plan

| Day | Deliverable |
|-----|-------------|
| 1 | Import + Postgres + paper detail page |
| 2 | Universal Paper Model extraction |
| 3 | Axiom mapping |
| 4 | Scoring signals + scoring engine + scorecard UI |
| 5 | Graph nodes/edges + JSON endpoint |
| 6 | Two-paper comparison |
| 7 | Jinja2 snapshot, polish, demo |

## What's intentionally NOT in v1

- Auth, multi-user
- Reference parsing / citation graph
- Full-text PDF figure/table extraction
- Live graph visualisation (a JSON endpoint ships; D3/Cytoscape is v2)
- GUI (PySide6) — web UI only for v1
