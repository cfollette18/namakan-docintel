# Agent map

Public extraction engine. Generic invoice schema only.

- Validate at the boundary (`schema.py`)
- Confidence + review queue (`extract.py`, `queue.py`)
- Do not add real client documents or private eval corpora
- Model calls go through `namakan-guardrails`
