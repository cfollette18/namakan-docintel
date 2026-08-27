from __future__ import annotations

from typing import Any


class ValidationError(ValueError):
    pass


INVOICE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["vendor_name", "invoice_number", "total"],
    "properties": {
        "vendor_name": {"type": "string"},
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string"},
        "po_number": {"type": "string"},
        "currency": {"type": "string"},
        "subtotal": {"type": "number"},
        "tax": {"type": "number"},
        "total": {"type": "number"},
        "line_items": {"type": "array"},
    },
}

PO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["buyer_name", "po_number", "vendor_name"],
    "properties": {
        "buyer_name": {"type": "string"},
        "po_number": {"type": "string"},
        "vendor_name": {"type": "string"},
        "order_date": {"type": "string"},
        "promise_date": {"type": "string"},
        "total": {"type": "number"},
        "line_items": {"type": "array"},
    },
}

RFQ_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["requestor", "rfq_number"],
    "properties": {
        "requestor": {"type": "string"},
        "rfq_number": {"type": "string"},
        "due_date": {"type": "string"},
        "part": {"type": "string"},
        "qty_breaks": {"type": "array"},
    },
}

SCHEMAS = {
    "invoice": INVOICE_SCHEMA,
    "purchase-order": PO_SCHEMA,
    "po": PO_SCHEMA,
    "rfq": RFQ_SCHEMA,
}


def validate(payload: dict, schema: dict | None = None) -> dict:
    schema = schema or INVOICE_SCHEMA
    if not isinstance(payload, dict):
        raise ValidationError("payload must be an object")
    for key in schema.get("required", []):
        if key not in payload or payload[key] in (None, ""):
            raise ValidationError(f"missing required field: {key}")
    return payload
