"""Document intelligence: schema validation, confidence, review queue, adapters."""

from namakan_docintel.adapters import to_jsonl, to_sql_inserts
from namakan_docintel.extract import ExtractedDoc, extract
from namakan_docintel.parsers import get_parser, parse_invoice, parse_purchase_order, parse_rfq
from namakan_docintel.queue import ReviewQueue
from namakan_docintel.schema import (
    INVOICE_SCHEMA,
    PO_SCHEMA,
    RFQ_SCHEMA,
    SCHEMAS,
    ValidationError,
    validate,
)

__version__ = "0.2.0"
__all__ = [
    "ExtractedDoc",
    "INVOICE_SCHEMA",
    "PO_SCHEMA",
    "RFQ_SCHEMA",
    "ReviewQueue",
    "SCHEMAS",
    "ValidationError",
    "extract",
    "get_parser",
    "parse_invoice",
    "parse_purchase_order",
    "parse_rfq",
    "to_jsonl",
    "to_sql_inserts",
    "validate",
    "__version__",
]
