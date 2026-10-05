import csv
from pathlib import Path
from .db import connect, init_db

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "zomato_questions.csv"

def export_csv():
    init_db()
    with connect() as conn:
        rows = conn.execute('''
            SELECT id, company, role, normalized_question AS question,
                   topic, question_type, interview_round, difficulty,
                   reported_date, source_name, source_url, confidence
            FROM questions
            ORDER BY topic, id
        ''').fetchall()

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "company", "role", "question", "topic", "question_type",
            "interview_round", "difficulty", "reported_date", "source_name",
            "source_url", "confidence"
        ])
        writer.writerows([tuple(r) for r in rows])

    print(f"Exported {len(rows)} questions to {OUT}")

if __name__ == "__main__":
    export_csv()
