"""Read before/after pairs from the formats people already have them in.

Deliberately no database adapter. Wherever your edits live, getting them into
JSONL or CSV is one query, and that keeps this package free of any assumption
about your stack.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

# Accepted column/key names, in preference order. `original_text`/`edited_text`
# match the common DB shape; `before`/`after` match what people type by hand.
BEFORE_KEYS = ("original_text", "before", "original", "old", "source")
AFTER_KEYS = ("edited_text", "after", "edited", "new", "final")


def _pick(row: dict, keys: tuple[str, ...]) -> str:
    for k in keys:
        if row.get(k):
            return str(row[k])
    return ""


def normalize(rows: list[dict]) -> list[dict]:
    """Map whatever column names you used onto before/after."""
    out = []
    for r in rows:
        before, after = _pick(r, BEFORE_KEYS), _pick(r, AFTER_KEYS)
        if before and after:
            out.append({"original_text": before, "edited_text": after})
    return out


def load_jsonl(path: str | Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return normalize(rows)


def load_json(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("edits") or data.get("rows") or []
    return normalize(data)


def load_csv(path: str | Path) -> list[dict]:
    with Path(path).open(newline="") as f:
        return normalize(list(csv.DictReader(f)))


def load(path: str | Path) -> list[dict]:
    """Dispatch on extension. .jsonl, .json, .csv, or .tsv."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".jsonl":
        return load_jsonl(p)
    if suffix == ".json":
        return load_json(p)
    if suffix in (".csv", ".tsv"):
        return load_csv(p)
    raise ValueError(f"unsupported file type {suffix!r}. Use .jsonl, .json, or .csv")
