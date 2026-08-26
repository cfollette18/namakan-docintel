from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from namakan_docintel.schema import INVOICE_SCHEMA, validate

try:
    from namakan_guardrails import scan_text
except ImportError:
    def scan_text(text: str):
        return []


@dataclass
class FieldScore:
    name: str
    value: Any
    confidence: float


@dataclass
class ExtractedDoc:
    fields: dict[str, Any]
    scores: list[FieldScore]
    needs_review: list[str]
    injection_flags: list[str] = field(default_factory=list)


def _confidence(value: Any) -> float:
    if value in (None, "", [], {}):
        return 0.0
    if isinstance(value, str) and value.strip().lower() in {"unknown", "n/a", "tbd"}:
        return 0.2
    return 0.9


def extract(
    text: str,
    parser: Callable[[str], dict],
    *,
    schema: dict | None = None,
    review_below: float = 0.7,
) -> ExtractedDoc:
    """Run parser, validate schema, score fields, queue low-confidence ones.

    `parser` is supplied by the caller (vision LLM, regex, etc.). This package
    owns validation, confidence, and the review split — not a specific model.
    """
    flags = [f.kind for f in scan_text(text)]
    raw = parser(text)
    payload = validate(raw, schema or INVOICE_SCHEMA)
    scores = [FieldScore(k, v, _confidence(v)) for k, v in payload.items()]
    needs = [s.name for s in scores if s.confidence < review_below]
    return ExtractedDoc(
        fields=payload,
        scores=scores,
        needs_review=needs,
        injection_flags=sorted(set(flags)),
    )
