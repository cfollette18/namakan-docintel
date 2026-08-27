"""Generic invoice extract + review queue. Synthetic data only."""

from namakan_docintel import ReviewQueue, extract, parse_invoice, to_sql_inserts

text = open("examples/sample_invoice.txt", encoding="utf-8").read()
doc = extract(text, parse_invoice)
queue = ReviewQueue()
queue.enqueue("syn-1", doc)
print("fields:", doc.fields)
print("needs review:", doc.needs_review)
print(to_sql_inserts(queue.to_json_rows([doc])))
