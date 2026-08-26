# namakan-docintel

Document intelligence for POs, RFQs, vendor quotes, invoices, and blueprints.

The public engine validates a schema, scores per-field confidence, and parks low-confidence fields in a human review queue. Golden eval sets per document type stay private — they are the actual moat.

Ships with a **generic invoice schema**. Client schemas never belong in this repo.

## Install

```bash
pip install namakan-docintel
pip install namakan-docintel[guardrails]
```

## Example

```python
from namakan_docintel import extract, ReviewQueue, INVOICE_SCHEMA

def parser(text: str) -> dict:
    # plug in a vision LLM wrapped by namakan-guardrails
    return {"vendor_name": "Example Vendor", "invoice_number": "INV-1", "total": 100.0}

doc = extract(open("sample.txt").read(), parser, schema=INVOICE_SCHEMA)
queue = ReviewQueue()
queue.enqueue("inv-1", doc)
rows = queue.to_json_rows([doc])
```

See [`examples/invoice_review.py`](examples/invoice_review.py).

## License

MIT. Copyright (c) 2026 Namakan AI Engineering.
