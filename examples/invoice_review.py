"""Generic invoice extract + review queue. Synthetic data only."""

from namakan_docintel import ReviewQueue, extract


def parser(text: str) -> dict:
    return {
        "vendor_name": "Example Fasteners LLC",
        "invoice_number": "INV-1001",
        "total": 250.0,
        "po_number": "unknown",
    }


doc = extract("synthetic invoice text", parser)
queue = ReviewQueue()
queue.enqueue("syn-1", doc)
print("needs review:", doc.needs_review)
print("json row:", queue.to_json_rows([doc])[0])
