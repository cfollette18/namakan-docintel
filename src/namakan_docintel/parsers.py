"""Heuristic parsers so extract works with no LLM. Swap in a vision model later."""

from __future__ import annotations

import re
from typing import Any, Callable


def _money(text: str, label: str) -> float | None:
    pattern = re.compile(r"(?:" + label + r")[:\s]*\$?\s*([0-9][0-9,]*\.?[0-9]*)", re.I)
    match = pattern.search(text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def _field(text: str, label: str) -> str:
    pattern = re.compile(r"(?:" + label + r")[:\s]+(.+)", re.I)
    match = pattern.search(text)
    if not match or match.group(1) is None:
        return "unknown"
    return match.group(1).strip().split("\n")[0].strip()


def parse_invoice(text: str) -> dict[str, Any]:
    invoice_number = _field(text, r"invoice\s*(?:number|#|no\.?)")
    if invoice_number == "unknown":
        found = re.search(r"\bINV[- ]?\d+\b", text, re.I)
        invoice_number = found.group(0) if found else "unknown"
    po_number = _field(text, r"p\.?o\.?\s*(?:number|#|no\.?)")
    if po_number == "unknown":
        found = re.search(r"\bPO[- ]?\d+\b", text, re.I)
        po_number = found.group(0) if found else "unknown"
    vendor = _field(text, r"vendor(?: name)?")
    if vendor == "unknown":
        vendor = _field(text, r"from")
    total = _money(text, r"total(?: due)?") or 0.0
    return {
        "vendor_name": vendor,
        "invoice_number": invoice_number,
        "invoice_date": _field(text, r"invoice date|date"),
        "po_number": po_number,
        "currency": "USD",
        "subtotal": _money(text, r"subtotal") or 0.0,
        "tax": _money(text, r"tax") or 0.0,
        "total": total,
    }


def parse_purchase_order(text: str) -> dict[str, Any]:
    po = _field(text, r"p\.?o\.?\s*(?:number|#|no\.?)")
    if po == "unknown":
        found = re.search(r"\bPO[- ]?\d+\b", text, re.I)
        po = found.group(0) if found else "unknown"
    return {
        "buyer_name": _field(text, r"buyer|bill to|sold to"),
        "po_number": po,
        "vendor_name": _field(text, r"vendor|ship from"),
        "order_date": _field(text, r"order date|date"),
        "promise_date": _field(text, r"promise date|need date|due date"),
        "total": _money(text, r"total") or 0.0,
    }


def parse_rfq(text: str) -> dict[str, Any]:
    number = _field(text, r"rfq\s*(?:number|#|no\.?)")
    if number == "unknown":
        found = re.search(r"\bRFQ[- ]?\d[\w-]*\b", text, re.I)
        number = found.group(0) if found else "unknown"
    qty = [int(x) for x in re.findall(r"\b(\d{2,5})\b", text)]
    return {
        "requestor": _field(text, r"from|requestor|buyer"),
        "rfq_number": number,
        "due_date": _field(text, r"due date|respond by"),
        "part": _field(text, r"part|description|item"),
        "qty_breaks": qty[:4] or [],
    }


PARSERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "invoice": parse_invoice,
    "purchase-order": parse_purchase_order,
    "po": parse_purchase_order,
    "rfq": parse_rfq,
}


def get_parser(doc_type: str) -> Callable[[str], dict[str, Any]]:
    try:
        return PARSERS[doc_type]
    except KeyError as exc:
        raise ValueError(f"unknown document type {doc_type!r}; choose {sorted(PARSERS)}") from exc
