import json
from .db import connect, init_db
from .llm_call import call_llm
from .prompts import SYSTEM_PROMPT


def extract_for_source(source):
    prompt = f"""
Company: {source["company"]}
Role: {source["role"]}
Reported date: {source["reported_date"]}
Source: {source["source_name"]}

Interview experience:
{source["raw_text"]}

Extract the interview questions from this experience.
"""

    result = call_llm(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT
    )
    
    print("\nRAW LLM RESPONSE:")
    print(result)

    result = result.strip()

    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    return json.loads(result)


def run():
    init_db()

    with connect() as conn:
        sources = conn.execute(
            "SELECT * FROM sources"
        ).fetchall()

        total = 0

        for source in sources:
            print(f"\nProcessing: {source['source_name']}")

            try:
                result = extract_for_source(dict(source))

                for q in result.get("questions", []):
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO questions
                        (
                            company,
                            role,
                            question,
                            normalized_question,
                            topic,
                            question_type,
                            interview_round,
                            difficulty,
                            reported_date,
                            source_name,
                            source_url,
                            confidence,
                            question_origin,
                            report_count
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                        source["company"],
                        source["role"],
                        q["question"],
                        q["normalized_question"],
                        q.get("topic"),
                        q.get("question_type"),
                        q.get("interview_round"),
                        q.get("difficulty"),
                        source["reported_date"],
                        source["source_name"],
                        source["source_url"],
                        q.get("confidence", "medium"),
                        "reported",
                        1
                    )
                    )

                    total += 1

                print(f"Extracted: {len(result.get('questions', []))}")

            except Exception as e:
                print(f"ERROR: {e}")

        conn.commit()

    print(f"\nTotal questions processed: {total}")


if __name__ == "__main__":
    run()