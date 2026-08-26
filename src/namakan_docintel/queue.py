from __future__ import annotations

from dataclasses import dataclass, field
from namakan_docintel.extract import ExtractedDoc


@dataclass
class ReviewItem:
    doc_id: str
    fields: list[str]
    extracted: ExtractedDoc


@dataclass
class ReviewQueue:
    pending: list[ReviewItem] = field(default_factory=list)
    resolved: list[ReviewItem] = field(default_factory=list)

    def enqueue(self, doc_id: str, extracted: ExtractedDoc) -> ReviewItem | None:
        if not extracted.needs_review:
            return None
        item = ReviewItem(doc_id, list(extracted.needs_review), extracted)
        self.pending.append(item)
        return item

    def resolve(self, doc_id: str, patches: dict) -> dict:
        for i, item in enumerate(self.pending):
            if item.doc_id == doc_id:
                item.extracted.fields.update(patches)
                for key in patches:
                    if key in item.extracted.needs_review:
                        item.extracted.needs_review.remove(key)
                self.pending.pop(i)
                self.resolved.append(item)
                return item.extracted.fields
        raise KeyError(doc_id)

    def to_json_rows(self, docs: list[ExtractedDoc]) -> list[dict]:
        return [d.fields for d in docs]
