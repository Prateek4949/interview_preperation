import json
from pathlib import Path
from .db import connect, init_db

ROOT = Path(__file__).resolve().parents[1]

def seed():
    init_db()
    rows = json.loads((ROOT / "data" / "raw_sources.json").read_text(encoding="utf-8"))
    with connect() as conn:
        for r in rows:
            conn.execute(
                '''INSERT OR IGNORE INTO sources
                (company, role, source_name, source_url, reported_date, raw_text)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (r["company"], r["role"], r["source_name"], r["source_url"],
                 r.get("reported_date"), r["raw_text"])
            )
    print(f"Seeded {len(rows)} source records.")

if __name__ == "__main__":
    seed()
