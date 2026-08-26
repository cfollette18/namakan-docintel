from namakan_docintel import INVOICE_SCHEMA, ReviewQueue, extract, validate
from namakan_docintel.schema import ValidationError


def parser(text: str) -> dict:
    # Toy parser for tests — production uses a vision LLM behind namakan-guardrails.
    return {
        "vendor_name": "Northwoods Fasteners LLC",
        "invoice_number": "INV-10482",
        "total": 13739.00,
        "po_number": "unknown",
    }


def test_schema_requires_total():
    try:
        validate({"vendor_name": "x", "invoice_number": "1"}, INVOICE_SCHEMA)
        assert False
    except ValidationError:
        pass


def test_extract_queues_low_confidence():
    doc = extract("invoice text", parser)
    assert "po_number" in doc.needs_review
    q = ReviewQueue()
    item = q.enqueue("doc-1", doc)
    assert item is not None
    fields = q.resolve("doc-1", {"po_number": "PO-7781"})
    assert fields["po_number"] == "PO-7781"
    assert q.to_json_rows([doc])[0]["vendor_name"]
