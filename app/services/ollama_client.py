"""Strict-JSON Ollama client.

We use Ollama's /api/generate with format="json" so the model is constrained to
emit valid JSON. Every response is validated against a Pydantic model before the
caller is allowed to touch it. If parsing fails we raise OllamaJSONError with
the raw text — callers can decide whether to retry, log, or surface to the UI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

T = TypeVar("T", bound=BaseModel)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class OllamaJSONError(RuntimeError):
    def __init__(self, raw: str, detail: str):
        super().__init__(f"Ollama returned non-conforming JSON: {detail}\n--- RAW ---\n{raw}")
        self.raw = raw
        self.detail = detail


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def render_prompt(name: str, **substitutions: str) -> str:
    template = load_prompt(name)
    for key, value in substitutions.items():
        template = template.replace("{" + key + "}", value)
    return template


def _post_generate(prompt: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    with httpx.Client(timeout=settings.ollama_timeout_seconds) as client:
        resp = client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
    return data.get("response", "")


def call_json(prompt: str, schema: type[T]) -> T:
    raw = _post_generate(prompt)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise OllamaJSONError(raw, f"json.loads failed: {e}") from e
    try:
        return schema.model_validate(parsed)
    except ValidationError as e:
        raise OllamaJSONError(raw, f"schema validation failed: {e}") from e


def call_json_template(name: str, schema: type[T], **substitutions: str) -> T:
    return call_json(render_prompt(name, **substitutions), schema)
