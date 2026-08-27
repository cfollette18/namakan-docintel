"""Extract invoices / POs / RFQs with the built-in parsers. No API key required."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from namakan_docintel import __version__
from namakan_docintel.adapters import to_jsonl, to_sql_inserts
from namakan_docintel.extract import extract
from namakan_docintel.parsers import get_parser
from namakan_docintel.queue import ReviewQueue
from namakan_docintel.schema import SCHEMAS

SAMPLE_INVOICE = """\
INVOICE
Vendor: Example Fasteners LLC
Invoice number: INV-1001
Invoice date: 2026-03-14
PO number: PO-1001
Subtotal: 250.00
Tax: 0.00
Total: 250.00
"""


def _extract_path(path: Path, doc_type: str, review_below: float):
    text = path.read_text(encoding="utf-8")
    return extract(
        text,
        get_parser(doc_type),
        schema=SCHEMAS[doc_type if doc_type != "po" else "purchase-order"],
        review_below=review_below,
    )


def _print_doc(doc_id: str, extracted) -> None:
    payload = {
        "id": doc_id,
        "fields": extracted.fields,
        "needs_review": extracted.needs_review,
        "injection_flags": extracted.injection_flags,
        "scores": [{"name": s.name, "confidence": s.confidence} for s in extracted.scores],
    }
    print(json.dumps(payload, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="namakan-docintel",
        description="Extract structured fields from invoices, POs, and RFQs.",
    )
    parser.add_argument("--version", action="version", version=f"namakan-docintel {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Parse the bundled sample invoice")
    extract_p = sub.add_parser("extract", help="Parse one or more text files")
    extract_p.add_argument("files", nargs="+", type=Path)
    extract_p.add_argument("--type", dest="doc_type", default="invoice", choices=sorted(SCHEMAS))
    extract_p.add_argument("--review-below", type=float, default=0.7)
    extract_p.add_argument("--jsonl", type=Path, help="Write fields as JSONL")
    extract_p.add_argument("--sql", type=Path, help="Write INSERT statements")
    extract_p.add_argument("--table", default="invoices")

    types = sub.add_parser("types", help="List document types and required fields")

    args = parser.parse_args(argv)
    if args.cmd == "types":
        for name, schema in SCHEMAS.items():
            print(f"{name}: required {schema['required']}")
        return 0
    if args.cmd == "demo":
        extracted = extract(SAMPLE_INVOICE, get_parser("invoice"))
        _print_doc("demo-invoice", extracted)
        return 0

    queue = ReviewQueue()
    docs = []
    for path in args.files:
        extracted = _extract_path(path, args.doc_type, args.review_below)
        queue.enqueue(path.name, extracted)
        docs.append(extracted)
        _print_doc(path.name, extracted)
    rows = queue.to_json_rows(docs)
    if args.jsonl:
        to_jsonl(rows, args.jsonl)
        print(f"wrote {args.jsonl}", file=sys.stderr)
    if args.sql:
        args.sql.write_text(to_sql_inserts(rows, table=args.table), encoding="utf-8")
        print(f"wrote {args.sql}", file=sys.stderr)
    pending = len(queue.pending)
    if pending:
        print(f"{pending} document(s) have low-confidence fields (needs_review)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
