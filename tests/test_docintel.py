from namakan_docintel import extract, parse_invoice, parse_purchase_order
from namakan_docintel.cli import main
from namakan_docintel.schema import INVOICE_SCHEMA, ValidationError, validate


def test_schema_requires_total():
    try:
        validate({"vendor_name": "x", "invoice_number": "1"}, INVOICE_SCHEMA)
        assert False
    except ValidationError:
        pass


def test_heuristic_invoice():
    text = "Vendor: Acme\nInvoice number: INV-9\nTotal: 12.50\nPO number: PO-1\n"
    doc = extract(text, parse_invoice)
    assert doc.fields["invoice_number"] == "INV-9"
    assert doc.fields["total"] == 12.5


def test_po_parser():
    text = "Buyer: Plant A\nVendor: Steel Co\nPO number: PO-88\n"
    assert parse_purchase_order(text)["po_number"] == "PO-88"


def test_demo_cli():
    assert main(["demo"]) == 0
