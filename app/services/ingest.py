"""Paper ingestion helpers.

Accepts text, markdown, or PDF bytes; returns a normalised string and a best-
effort split into PaperSection rows.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dep
    PdfReader = None  # type: ignore[assignment]


HEADING_RE = re.compile(r"^(#{1,3}\s+.+|[A-Z][A-Z0-9 \-:]{3,}|\d+\.\s+[A-Z].+)$", re.MULTILINE)


@dataclass
class IngestedSection:
    heading: str | None
    content: str
    order_index: int


def extract_text_from_pdf(data: bytes) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf not installed; cannot parse PDF")
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n\n".join(parts).strip()


def split_sections(text: str) -> list[IngestedSection]:
    """Cheap section splitter. Good enough for v1; replace with grobid/etc. later."""
    if not text.strip():
        return []

    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [IngestedSection(heading=None, content=text.strip(), order_index=0)]

    sections: list[IngestedSection] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading_line = match.group(0).strip()
        body = text[match.end() : end].strip()
        if not body:
            continue
        sections.append(
            IngestedSection(heading=heading_line, content=body, order_index=i)
        )

    if not sections:
        return [IngestedSection(heading=None, content=text.strip(), order_index=0)]
    return sections
