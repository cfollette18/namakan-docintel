"""MCP server: extract invoices/POs/RFQs — plus a bundled AI workflow."""

from __future__ import annotations

import sys
from typing import Any

from namakan_docintel.adapters import to_sql_inserts
from namakan_docintel.extract import extract
from namakan_docintel.parsers import get_parser
from namakan_docintel.protocol import as_object, cli_main
from namakan_docintel.queue import ReviewQueue
from namakan_docintel.schema import SCHEMAS

VERSION = "0.3.0"

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

SAMPLE_PO = """\
PURCHASE ORDER
Buyer: Example Plant A
Vendor: Example Fasteners LLC
PO number: PO-1001
Order date: 2026-03-10
"""

SAMPLE_RFQ = """\
REQUEST FOR QUOTE
Requestor: Purchasing
RFQ number: RFQ-44
"""

SAMPLES = {"invoice": SAMPLE_INVOICE, "po": SAMPLE_PO, "rfq": SAMPLE_RFQ}


def _normalize_type(doc_type: str) -> str:
    if doc_type in {"po", "purchase-order", "purchase_order"}:
        return "purchase-order"
    if doc_type in {"invoice", "rfq"}:
        return doc_type
    return doc_type


def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return {"name": name, "description": description, "inputSchema": schema}


def list_tools() -> list[dict[str, Any]]:
    return [
        _tool(
            "docintel_types",
            "List document types and required schema fields (invoice, purchase-order, rfq).",
            {},
        ),
        _tool(
            "docintel_extract",
            "Extract structured fields from document text. Returns fields, confidence, needs_review, injection_flags.",
            {
                "text": {"type": "string"},
                "doc_type": {"type": "string"},
                "review_below": {"type": "number"},
            },
            ["text"],
        ),
        _tool(
            "docintel_to_sql",
            "Turn extracted field objects into INSERT statements for a staging table.",
            {
                "rows": {"type": "array"},
                "table": {"type": "string"},
            },
            ["rows"],
        ),
        _tool(
            "docintel_run_workflow",
            "Full AI workflow out of the box: sample invoice → extract → review queue → SQL. No model required.",
            {"use_case": {"type": "string"}, "doc_type": {"type": "string"}},
        ),
    ]


def _serialize_extracted(doc_id: str, extracted) -> dict[str, Any]:
    return {
        "id": doc_id,
        "fields": extracted.fields,
        "needs_review": extracted.needs_review,
        "injection_flags": extracted.injection_flags,
        "scores": [{"name": s.name, "confidence": s.confidence} for s in extracted.scores],
    }


def handle(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        if tool == "docintel_types":
            return {
                "ok": True,
                "data": {name: {"required": schema["required"]} for name, schema in SCHEMAS.items()},
            }
        if tool == "docintel_extract":
            doc_type = _normalize_type(str(arguments.get("doc_type") or "invoice"))
            if doc_type not in SCHEMAS:
                return {"ok": False, "error": f"unknown doc_type {doc_type}"}
            extracted = extract(
                str(arguments["text"]),
                get_parser(doc_type),
                schema=SCHEMAS[doc_type],
                review_below=float(arguments.get("review_below") or 0.7),
            )
            return {"ok": True, "data": _serialize_extracted("doc", extracted)}
        if tool == "docintel_to_sql":
            rows = as_object(arguments["rows"])
            if not isinstance(rows, list):
                return {"ok": False, "error": "rows must be a list of objects"}
            table = str(arguments.get("table") or "invoices")
            return {"ok": True, "data": {"table": table, "sql": to_sql_inserts(rows, table=table)}}
        if tool == "docintel_run_workflow":
            return run_workflow(str(arguments.get("use_case") or "ap-invoice-intake"))
    except KeyError as exc:
        return {"ok": False, "error": f"missing argument {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": False, "error": f"unknown tool {tool}"}


def run_workflow(use_case: str = "ap-invoice-intake") -> dict[str, Any]:
    mapping = {
        "ap-invoice-intake": ("invoice", SAMPLE_INVOICE),
        "po-confirmation": ("purchase-order", SAMPLE_PO),
        "rfq-triage": ("rfq", SAMPLE_RFQ),
    }
    if use_case not in mapping:
        return {"ok": False, "error": f"unknown use_case {use_case}"}
    doc_type, text = mapping[use_case]
    extracted = handle("docintel_extract", {"text": text, "doc_type": doc_type})
    fields = extracted.get("data", {}).get("fields") or {}
    sql = handle("docintel_to_sql", {"rows": [fields], "table": "staging_docs"})
    queue = ReviewQueue()
    raw = extract(text, get_parser(doc_type), schema=SCHEMAS[doc_type])
    queue.enqueue("sample", raw)
    steps = [
        {"tool": "docintel_types", **handle("docintel_types", {})},
        {"tool": "docintel_extract", **extracted},
        {
            "tool": "review_queue",
            "ok": True,
            "data": {"pending": [item.doc_id for item in queue.pending], "needs_review": raw.needs_review},
        },
        {"tool": "docintel_to_sql", **sql},
    ]
    return {
        "ok": True,
        "workflow": use_case,
        "summary": (
            f"Extracted a sample {doc_type}. Weak fields go to the review queue before SQL/ERP. "
            "Nothing is posted to a live system."
        ),
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    return cli_main(
        argv,
        prog="namakan-docintel",
        description="MCP server for invoice / PO / RFQ extraction.",
        version=VERSION,
        server_name="namakan-docintel",
        list_tools=list_tools,
        call_tool=handle,
        run_workflow=run_workflow,
    )


if __name__ == "__main__":
    sys.exit(main())
