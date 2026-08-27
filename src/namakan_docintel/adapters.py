"""JSON rows and a naive SQL INSERT generator — destination adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def to_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str) + "\n")


def to_sql_inserts(rows: list[dict[str, Any]], table: str = "invoices") -> str:
    if not rows:
        return f"-- no rows for {table}\n"
    statements: list[str] = []
    for row in rows:
        cols = ", ".join(_ident(k) for k in row)
        vals = ", ".join(_sql_literal(v) for v in row.values())
        statements.append(f"INSERT INTO {_ident(table)} ({cols}) VALUES ({vals});")
    return "\n".join(statements) + "\n"


def _ident(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    return cleaned or "col"


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, dict)):
        text = json.dumps(value)
    else:
        text = str(value)
    return "'" + text.replace("'", "''") + "'"
