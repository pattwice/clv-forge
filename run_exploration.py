"""Run exploration.sql and print results with coverage labels."""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shopdata.db"
SQL_PATH = Path(__file__).parent / "exploration.sql"

COVERAGE = [
    ("1", "Uniqueness", "Duplicate customer_id"),
    ("2", "Completeness", "Missing email -> cleaning: unknown@domain.com"),
    ("3", "Validity", "Phone format -> cleaning: strip non-digits"),
    ("4", "Completeness", "Missing phone"),
    ("5", "Validity", "total_amount <= 0 -> cleaning: filter out"),
    ("6", "Completeness", "Missing currency -> cleaning: assume USD"),
    ("7", "Referential integrity", "Orphan orders (no matching customer)"),
    ("8", "Consistency", "Non-USD order missing rate for order_date"),
    ("9", "Consistency", "Currency in orders not in exchange_rates"),
    ("10", "Completeness", "Missing order_date"),
]


def parse_queries(sql: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for block in sql.split(";"):
        label = "?"
        lines: list[str] = []
        for line in block.splitlines():
            stripped = line.strip()
            match = re.match(r"--\s*(\d+)", stripped)
            if match:
                label = match.group(1)
            elif stripped and not stripped.startswith("--"):
                lines.append(line)
        query = "\n".join(lines).strip()
        if query:
            blocks.append((label, query))
    return blocks


def main() -> None:
    queries = parse_queries(SQL_PATH.read_text(encoding="utf-8"))
    coverage_by_id = {cid: (dim, desc) for cid, dim, desc in COVERAGE}

    conn = sqlite3.connect(DB_PATH)
    print(f"Database: {DB_PATH.name}\n")

    for label, query in queries:
        dim, desc = coverage_by_id.get(label, ("?", "Unmapped"))
        rows = conn.execute(query).fetchall()
        print(f"Query {label} | {dim} | {desc}")
        print(f"  rows: {len(rows)}")
        for row in rows:
            print(f"  {row}")
        print()

    print("Coverage checklist (assignment cleaning rules):")
    for cid, dim, desc in COVERAGE:
        print(f"  [{cid}] {dim}: {desc}")


if __name__ == "__main__":
    main()
