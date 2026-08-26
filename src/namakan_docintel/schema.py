from __future__ import annotations

from typing import Any


class ValidationError(ValueError):
    pass


# Generic invoice schema shipped publicly. Client schemas stay private.
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


def validate(payload: dict, schema: dict | None = None) -> dict:
    schema = schema or INVOICE_SCHEMA
    if not isinstance(payload, dict):
        raise ValidationError("payload must be an object")
    for key in schema.get("required", []):
        if key not in payload or payload[key] in (None, ""):
            raise ValidationError(f"missing required field: {key}")
    return payload
