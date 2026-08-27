from namakan_docintel.protocol import handle_rpc
from namakan_docintel.server import VERSION, handle, list_tools, main, run_workflow


def _rpc(method: str, params: dict | None = None, req_id: int = 1):
    req = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        req["params"] = params
    return handle_rpc(
        req,
        server_name="namakan-docintel",
        version=VERSION,
        list_tools=list_tools,
        call_tool=handle,
    )


def test_initialize():
    assert _rpc("initialize")["result"]["serverInfo"]["name"] == "namakan-docintel"


def test_types():
    out = handle("docintel_types", {})
    assert "invoice" in out["data"]
    assert "total" in out["data"]["invoice"]["required"]


def test_extract_invoice():
    text = "Vendor: Acme\nInvoice number: INV-9\nTotal: 12.50\nPO number: PO-1\n"
    out = handle("docintel_extract", {"text": text, "doc_type": "invoice"})
    assert out["ok"]
    assert out["data"]["fields"]["invoice_number"] == "INV-9"
    assert out["data"]["fields"]["total"] == 12.5


def test_to_sql():
    out = handle("docintel_to_sql", {"rows": [{"invoice_number": "INV-1", "total": 10}], "table": "invoices"})
    assert "INSERT INTO invoices" in out["data"]["sql"]


def test_workflow():
    out = run_workflow("ap-invoice-intake")
    assert out["ok"]
    fields = out["steps"][1]["data"]["fields"]
    assert fields["invoice_number"] == "INV-1001"
    assert "INSERT INTO staging_docs" in out["steps"][3]["data"]["sql"]


def test_cli():
    assert main(["tools"]) == 0
    assert main(["demo"]) == 0
