# One-Week Build Plan

This is the operational plan handed to whoever finishes the MVP. The scaffold in this repo already implements every layer end-to-end against a `Paper.full_text` blob; the work below is about making it actually robust on real PDFs.

## Definition of Done

By the end of the week:

1. Import two real papers via `/papers/upload`.
2. `POST /papers/{id}/run-all` completes for both.
3. `POST /compare` produces a non-trivial JSONB comparison.
4. The standalone HTML at `/papers/{id}/snapshot` looks like the inspiration file `proof-explorer-fp-005-enhanced.html`.
5. `pytest` passes.

## Day-by-day

| Day | Task | Files |
|-----|------|-------|
| 1 | DB up, `alembic upgrade head`, smoke `scripts/import_sample.py` + `scripts/seed_axioms.py`. Confirm `/` lists papers/axioms. | `app/db.py`, `alembic/`, `scripts/` |
| 2 | Wire Ollama. Run `/papers/{id}/extract-model`. Tune `paper_model.txt` if local model returns junk. | `app/services/ollama_client.py`, `app/prompts/paper_model.txt` |
| 3 | Run `/papers/{id}/extract-evidence` then `/map-axioms`. Verify rows in `evidence_items` and `axiom_mappings`. | `app/services/extraction.py`, `app/prompts/evidence.txt`, `axiom_mapping.txt` |
| 4 | Run `/papers/{id}/grade`. Verify `paper_scores.signals` JSONB matches what's on the snapshot. Tune scoring weights in `app/services/scoring.py`. | `app/services/scoring.py` |
| 5 | `/papers/{id}/build-graph`. Inspect `/graph?paper_id=X` JSON. Add a basic Cytoscape.js renderer to `paper_detail.html` if time allows. | `app/services/graph_builder.py`, `app/routers/graph.py` |
| 6 | `POST /compare` with two papers. Check the cross-paper edges land in `graph_edges` with `relationship_type in (supports, contradicts, extends, reframes)`. | `app/services/comparison.py` |
| 7 | `/papers/{id}/snapshot` polish. Match the visual feel of `proof-explorer-fp-005-enhanced.html`. Run `pytest`. Demo. | `app/templates/snapshot.html` |

## Hand-off prompt for an AI programmer

> Repo: `yellowkidokc/treaties` on branch `claude/add-axiom-model-layer-eNlpA`.
>
> The scaffold already has FastAPI + SQLAlchemy + Alembic + Ollama + Jinja2 wired end-to-end. Schema lives in `app/models.py` with one Alembic migration. The pipeline is: import → extract paper-model → extract evidence → map axioms → grade → build graph → snapshot. Every stage is its own POST endpoint under `/papers/{id}/...`, plus `/papers/{id}/run-all` for convenience. Two papers can be compared via `POST /compare`; cross-paper edges land in `graph_edges`.
>
> Hard rules: Postgres is canonical, HTML is generated. Ollama returns strict JSON only (we use `format="json"` and Pydantic-validate every response). The LLM extracts boolean *signals*; Python computes scores in `app/services/scoring.py`. Every claim carries `source_quote` for traceability.
>
> Your job is to (a) run it locally, (b) tune prompts where the local model misbehaves, (c) make the snapshot look like `proof-explorer-fp-005-enhanced.html`, (d) wire a graph view (Cytoscape.js) into `paper_detail.html`, and (e) keep `pytest` green. Do not add features outside the seven pipeline stages.

## What is intentionally NOT scaffolded

- AuthN/Z, multi-user.
- Reference graph (incoming/outgoing citations).
- PDF figure/table extraction.
- Live graph visualisation in the web UI (only the JSON endpoint ships).
- Background-job queue. The pipeline is synchronous; long Ollama calls can wedge a request. v2: enqueue with rq/dramatiq.
- Embedding-based similarity. v2 candidate.
